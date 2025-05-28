import openai
import os
import tempfile
from typing import BinaryIO
import streamlit as st

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
        
        # Set up OpenAI client
        openai.api_key = api_key
        
        # Create a temporary file to store the audio/video
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            temp_file.write(file_bytes)
            temp_file_path = temp_file.name
        
        try:
            # Open the temporary file and transcribe
            with open(temp_file_path, 'rb') as audio_file:
                # Call OpenAI Whisper API
                transcript = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
                
            return transcript
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        raise Exception(f"Transcription failed: {str(e)}")

def validate_file_duration(file_bytes: bytes, filename: str, max_duration_minutes: int = 30) -> tuple[bool, float]:
    """
    Validate file duration using ffmpeg.
    
    Args:
        file_bytes: The audio/video file content as bytes
        filename: Original filename for proper file extension handling
        max_duration_minutes: Maximum allowed duration in minutes
        
    Returns:
        tuple: (is_valid, duration_in_minutes)
    """
    try:
        import ffmpeg
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            temp_file.write(file_bytes)
            temp_file_path = temp_file.name
        
        try:
            # Get file info using ffmpeg
            probe = ffmpeg.probe(temp_file_path)
            duration_seconds = float(probe['streams'][0]['duration'])
            duration_minutes = duration_seconds / 60
            
            is_valid = duration_minutes <= max_duration_minutes
            return is_valid, duration_minutes
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        # If ffmpeg fails, we'll just return True and let the user proceed
        st.warning(f"Could not validate file duration: {str(e)}")
        return True, 0.0 