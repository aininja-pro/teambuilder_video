import os
import tempfile
from typing import BinaryIO
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import ffmpeg

# Load environment variables
load_dotenv()

def compress_audio_for_whisper(input_path: str, max_size_mb: int = 24) -> str:
    """
    Compress audio/video file to meet Whisper API size requirements.
    Handles very large files (285MB+) with aggressive compression.
    
    Args:
        input_path: Path to the input file
        max_size_mb: Maximum file size in MB (default 24MB to be safe)
        
    Returns:
        str: Path to the compressed file
    """
    try:
        # Create output path
        output_path = input_path.replace('.mp4', '_compressed.mp3').replace('.mp3', '_compressed.mp3')
        
        # Get file info
        probe = ffmpeg.probe(input_path)
        duration = float(probe['streams'][0]['duration'])
        
        # Calculate target bitrate (in kbps) to achieve target file size
        # Formula: (target_size_mb * 8 * 1024) / duration_seconds
        target_bitrate = int((max_size_mb * 8 * 1024) / duration)
        
        # For very large files, we need more aggressive compression
        # Minimum 16kbps for very long files, maximum 64kbps for speech
        target_bitrate = max(16, min(64, target_bitrate))
        
        st.info(f"🔧 Compressing {duration/60:.1f} minute file to ~{max_size_mb}MB using {target_bitrate}kbps...")
        
        # Compress the file with aggressive settings for large files
        (
            ffmpeg
            .input(input_path)
            .output(
                output_path,
                acodec='mp3',
                audio_bitrate=f'{target_bitrate}k',
                ac=1,  # Mono audio (reduces size by ~50%)
                ar=16000,  # 16kHz sample rate (good for speech, reduces size)
                **{'q:a': 9}  # Lower quality for smaller size (0-9, 9 is smallest)
            )
            .overwrite_output()
            .run(quiet=True)
        )
        
        # Check if the compressed file is still too large
        compressed_size = os.path.getsize(output_path) / (1024 * 1024)
        
        if compressed_size > max_size_mb:
            st.warning(f"⚠️ First compression resulted in {compressed_size:.1f}MB. Applying additional compression...")
            
            # Second pass with even more aggressive settings
            output_path_2 = output_path.replace('.mp3', '_ultra.mp3')
            target_bitrate_2 = max(12, int(target_bitrate * 0.7))  # Reduce bitrate by 30%
            
            (
                ffmpeg
                .input(output_path)
                .output(
                    output_path_2,
                    acodec='mp3',
                    audio_bitrate=f'{target_bitrate_2}k',
                    ac=1,
                    ar=12000,  # Even lower sample rate
                    **{'q:a': 9}
                )
                .overwrite_output()
                .run(quiet=True)
            )
            
            # Remove the first compressed file and use the ultra-compressed one
            os.unlink(output_path)
            output_path = output_path_2
            
            final_size = os.path.getsize(output_path) / (1024 * 1024)
            st.success(f"✅ Final compressed size: {final_size:.1f}MB")
        else:
            st.success(f"✅ Compressed to {compressed_size:.1f}MB")
        
        return output_path
        
    except Exception as e:
        raise Exception(f"Audio compression failed: {str(e)}")

def convert_mov_to_mp4(file_bytes: bytes, filename: str) -> bytes:
    """
    Convert MOV file to MP4 format using FFmpeg.
    
    Args:
        file_bytes: The MOV file as bytes
        filename: Original filename
        
    Returns:
        bytes: The converted MP4 file as bytes
        
    Raises:
        Exception: If conversion fails
    """
    temp_mov_path = None
    temp_mp4_path = None
    
    try:
        st.info("🔧 Starting MOV to MP4 conversion...")
        
        # Check if FFmpeg is available
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                raise Exception("FFmpeg not found or not working")
            st.info("✅ FFmpeg detected and working")
        except Exception as e:
            error_msg = f"FFmpeg is not available on this server: {str(e)}"
            st.error(error_msg)
            raise Exception(error_msg)
        
        # Create temporary files with better error handling
        try:
            with tempfile.NamedTemporaryFile(suffix='.mov', delete=False) as temp_mov:
                temp_mov.write(file_bytes)
                temp_mov_path = temp_mov.name
            st.info(f"📁 Created temporary MOV file: {os.path.basename(temp_mov_path)}")
        except Exception as e:
            raise Exception(f"Failed to create temporary MOV file: {str(e)}")
            
        temp_mp4_path = temp_mov_path.replace('.mov', '.mp4')
        
        # Convert using FFmpeg with detailed error handling
        try:
            st.info("🔄 Running FFmpeg conversion...")
            stream = ffmpeg.input(temp_mov_path)
            stream = ffmpeg.output(
                stream, 
                temp_mp4_path, 
                vcodec='libx264',
                acodec='aac',
                **{
                    'preset': 'fast',  # Faster encoding
                    'crf': '23',       # Good quality/size balance
                    'movflags': '+faststart'  # Web optimization
                }
            )
            
            # Run conversion with detailed error capture
            stdout, stderr = ffmpeg.run(
                stream, 
                overwrite_output=True, 
                quiet=False,  # Show output for debugging
                capture_stdout=True, 
                capture_stderr=True
            )
            
            st.info("✅ FFmpeg conversion completed")
            
        except ffmpeg.Error as e:
            error_details = f"FFmpeg error: {e.stderr.decode() if e.stderr else 'Unknown error'}"
            st.error(f"❌ FFmpeg conversion failed: {error_details}")
            raise Exception(f"FFmpeg conversion failed: {error_details}")
        except Exception as e:
            error_msg = f"Conversion process failed: {str(e)}"
            st.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        # Check if output file was created and validate it
        if not os.path.exists(temp_mp4_path):
            raise Exception("Conversion failed - output MP4 file not created")
        
        file_size = os.path.getsize(temp_mp4_path)
        if file_size == 0:
            raise Exception("Conversion failed - output MP4 file is empty")
        
        st.info(f"📊 Converted MP4 size: {file_size / (1024*1024):.1f} MB")
        
        # Read the converted file
        try:
            with open(temp_mp4_path, 'rb') as f:
                converted_bytes = f.read()
                
            if len(converted_bytes) == 0:
                raise Exception("Failed to read converted MP4 file")
                
            st.success(f"✅ MOV successfully converted to MP4 ({len(converted_bytes) / (1024*1024):.1f} MB)")
            return converted_bytes
            
        except Exception as e:
            raise Exception(f"Failed to read converted file: {str(e)}")
        
    except Exception as e:
        error_msg = f"MOV to MP4 conversion failed: {str(e)}"
        st.error(error_msg)
        
        # Provide helpful troubleshooting info
        with st.expander("🔍 Troubleshooting Information"):
            st.code(f"""
Error Details: {str(e)}
Original file: {filename}
File size: {len(file_bytes) / (1024*1024):.1f} MB

Possible solutions:
1. Try converting the MOV to MP4 on your computer first
2. Use a different video format (MP4, WEBM)
3. Extract just the audio as MP3
4. Try a smaller/shorter video file

Server Environment Issues:
- FFmpeg may not be installed on the deployment server
- Different codec support than local environment
- Memory or disk space limitations
            """)
        
        raise Exception(error_msg)
        
    finally:
        # Clean up temporary files with better error handling
        for temp_path in [temp_mov_path, temp_mp4_path]:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as cleanup_error:
                    st.warning(f"Could not clean up temp file {temp_path}: {cleanup_error}")
                    pass  # Don't fail the whole process for cleanup issues

def transcribe_video(file_bytes: bytes, filename: str) -> str:
    """
    Transcribe video/audio to text using OpenAI Whisper.
    Automatically converts MOV files to MP4 before transcription.
    """
    try:
        # Check if conversion is needed
        if filename.lower().endswith('.mov'):
            st.info("🔄 Converting MOV to MP4 format...")
            try:
                file_bytes = convert_mov_to_mp4(file_bytes, filename)
                filename = filename.rsplit('.', 1)[0] + '.mp4'  # Change extension
                st.success("✅ MOV conversion completed")
            except Exception as e:
                # MOV conversion failed - provide helpful alternatives
                st.error(f"❌ MOV conversion failed: {str(e)}")
                
                # Show alternative options
                with st.expander("💡 Alternative Solutions", expanded=True):
                    st.markdown("""
                    **Since MOV conversion failed, here are your options:**
                    
                    1. **Convert locally first** (Recommended):
                       - Use QuickTime, VLC, or any video converter
                       - Convert your MOV to MP4 format
                       - Upload the MP4 file instead
                    
                    2. **Extract audio only**:
                       - Use software to extract MP3 from your MOV
                       - Upload just the audio (much smaller file)
                       - Same transcription quality, faster upload
                    
                    3. **Try different format**:
                       - Most screen recording software can save as MP4
                       - Re-record or re-export in MP4 format
                    
                    4. **Use online converter**:
                       - CloudConvert, Online-Convert, or similar
                       - Convert MOV to MP4 online first
                    
                    **Why this happens:**
                    - Live servers may have different video codec support
                    - Your local computer has more complete video libraries
                    - MP4 is more universally supported than MOV
                    """)
                
                raise Exception(f"MOV conversion failed in live environment. Please convert to MP4 first or try the alternative solutions shown above.")
        
        # Get OpenAI API key from environment
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
        
        # Set up OpenAI client (new v1.0+ API)
        client = OpenAI(api_key=api_key)
        
        # Create a temporary file with the correct extension
        file_extension = os.path.splitext(filename)[1].lower()
        if not file_extension:
            file_extension = '.mp4'  # Default extension
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(file_bytes)
            temp_file_path = temp_file.name
        
        try:
            # Check file size (Whisper API has a 25MB limit)
            file_size_mb = len(file_bytes) / (1024 * 1024)
            
            if file_size_mb > 25:
                st.info(f"📦 File size ({file_size_mb:.1f}MB) exceeds Whisper API limit. Compressing...")
                # Compress the file
                compressed_path = compress_audio_for_whisper(temp_file_path)
                transcription_file_path = compressed_path
            else:
                transcription_file_path = temp_file_path
            
            # Transcribe using the new API structure
            st.info("🎤 Sending file to OpenAI Whisper...")
            with open(transcription_file_path, 'rb') as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            # Validate that we got actual text back
            if not isinstance(transcript, str):
                raise Exception("Invalid response from Whisper API - not a string")
            
            # Check if transcript looks like binary data or is empty
            if not transcript.strip():
                raise Exception("Transcription returned empty text")
            
            # Check for binary-like content (lots of non-printable characters)
            printable_chars = sum(1 for c in transcript[:1000] if c.isprintable() or c.isspace())
            if len(transcript) > 100 and printable_chars / min(len(transcript), 1000) < 0.7:
                raise Exception("Transcription appears to contain binary data")
            
            st.success(f"✅ Transcription completed - {len(transcript)} characters")
            return transcript
            
        finally:
            # Clean up the temporary files
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            # Clean up compressed file if it was created
            compressed_path = temp_file_path.replace('.mp4', '_compressed.mp3').replace('.mp3', '_compressed.mp3')
            if os.path.exists(compressed_path):
                os.unlink(compressed_path)
                
    except Exception as e:
        error_msg = f"Transcription failed: {str(e)}"
        st.error(error_msg)
        raise Exception(error_msg)

def validate_file_duration(file_bytes: bytes, filename: str, max_duration_minutes: int = 30) -> tuple[bool, str]:
    """
    Validate if the audio/video file duration is within limits.
    
    Args:
        file_bytes: The file content as bytes
        filename: Original filename
        max_duration_minutes: Maximum allowed duration in minutes
        
    Returns:
        tuple: (is_valid, message)
    """
    try:
        import ffmpeg
        
        # Create a temporary file
        file_extension = os.path.splitext(filename)[1].lower()
        if not file_extension:
            file_extension = '.mp4'
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(file_bytes)
            temp_file_path = temp_file.name
        
        try:
            # Get file info using ffmpeg
            probe = ffmpeg.probe(temp_file_path)
            duration = float(probe['streams'][0]['duration'])
            duration_minutes = duration / 60
            
            if duration_minutes > max_duration_minutes:
                return False, f"File duration ({duration_minutes:.1f} minutes) exceeds the {max_duration_minutes} minute limit."
            else:
                return True, f"File duration: {duration_minutes:.1f} minutes"
                
        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        # If we can't check duration, just warn but allow processing
        return True, f"Could not validate duration: {str(e)}" 