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

def transcribe_video(file_bytes: bytes, filename: str) -> str:
    """
    Transcribe video/audio file using OpenAI Whisper API.
    
    Args:
        file_bytes: The audio/video file content as bytes
        filename: Original filename for proper file extension handling
        
    Returns:
        str: The transcribed text
        
    Raises:
        Exception: If transcription fails
    """
    try:
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
            with open(transcription_file_path, 'rb') as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            # The new API returns the transcript directly as a string
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
        raise Exception(f"Transcription failed: {str(e)}")

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