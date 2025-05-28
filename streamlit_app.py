import streamlit as st
import os
import openai
from dotenv import load_dotenv
import ffmpeg
from docx import Document
import pdfkit
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
import json
import tempfile
import datetime
from typing import List, Dict
import traceback

# Import our custom modules
from transcribe import transcribe_video, validate_file_duration
from parse_scope import parse_scope, format_scope_items_for_display
from doc_generator import generate_docx, generate_pdf, create_filename
from drive_helper import get_drive_service, upload_file, validate_drive_setup, create_shareable_link

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Video-to-Scope-Summary",
    page_icon="🎥",
    layout="wide"
)

# Initialize session state
if 'drive_folder_id' not in st.session_state:
    st.session_state.drive_folder_id = ""
if 'template_file_id' not in st.session_state:
    st.session_state.template_file_id = ""
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'transcript' not in st.session_state:
    st.session_state.transcript = ""
if 'scope_items' not in st.session_state:
    st.session_state.scope_items = []
if 'docx_path' not in st.session_state:
    st.session_state.docx_path = ""
if 'pdf_path' not in st.session_state:
    st.session_state.pdf_path = ""
if 'drive_links' not in st.session_state:
    st.session_state.drive_links = {}
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False

def validate_api_keys():
    """Check if required API keys are configured."""
    openai_key = os.getenv('OPENAI_API_KEY')
    google_creds = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
    
    missing = []
    if not openai_key:
        missing.append("OPENAI_API_KEY")
    if not google_creds:
        missing.append("GOOGLE_SERVICE_ACCOUNT_JSON")
    
    return len(missing) == 0, missing

def process_video():
    """Main processing function that orchestrates the entire pipeline."""
    if not st.session_state.uploaded_file:
        st.error("No file uploaded")
        return
    
    if not st.session_state.drive_folder_id or not st.session_state.template_file_id:
        st.error("Please configure Google Drive settings in the sidebar")
        return
    
    # Get file details
    uploaded_file = st.session_state.uploaded_file
    file_bytes = uploaded_file.read()
    filename = uploaded_file.name
    job_name = os.path.splitext(filename)[0]
    
    # Progress indicators
    upload_progress = st.progress(0)
    upload_status = st.empty()
    
    transcription_progress = st.progress(0)
    transcription_status = st.empty()
    
    parsing_progress = st.progress(0)
    parsing_status = st.empty()
    
    generation_progress = st.progress(0)
    generation_status = st.empty()
    
    saving_progress = st.progress(0)
    saving_status = st.empty()
    
    try:
        # Step 1: Validate file
        upload_status.info("📋 Validating file...")
        upload_progress.progress(25)
        
        # Check file duration if possible
        is_valid, duration = validate_file_duration(file_bytes, filename)
        if not is_valid:
            st.warning(f"⚠️ File duration ({duration:.1f} minutes) exceeds 30 minutes. Processing may be slow and expensive.")
        
        upload_progress.progress(100)
        upload_status.success("✅ File validated successfully")
        
        # Step 2: Transcription
        transcription_status.info("🎤 Transcribing audio...")
        transcription_progress.progress(25)
        
        transcript = transcribe_video(file_bytes, filename)
        st.session_state.transcript = transcript
        
        transcription_progress.progress(100)
        transcription_status.success("✅ Transcription completed")
        
        # Step 3: Parsing
        parsing_status.info("🔍 Extracting scope items...")
        parsing_progress.progress(25)
        
        scope_items = parse_scope(transcript)
        st.session_state.scope_items = format_scope_items_for_display(scope_items)
        
        parsing_progress.progress(100)
        parsing_status.success(f"✅ Extracted {len(scope_items)} scope items")
        
        # Step 4: Document generation
        generation_status.info("📄 Generating documents...")
        generation_progress.progress(25)
        
        # Generate DOCX
        docx_path = generate_docx(scope_items, job_name, version=1)
        st.session_state.docx_path = docx_path
        generation_progress.progress(50)
        
        # Generate PDF
        pdf_path = generate_pdf(docx_path, job_name, version=1)
        st.session_state.pdf_path = pdf_path
        generation_progress.progress(100)
        generation_status.success("✅ Documents generated")
        
        # Step 5: Upload to Google Drive
        saving_status.info("☁️ Saving to Google Drive...")
        saving_progress.progress(25)
        
        # Get Drive service
        service = get_drive_service()
        
        # Create filenames
        docx_filename = create_filename(job_name, 1, 'docx')
        pdf_filename = create_filename(job_name, 1, 'pdf')
        
        # Upload DOCX
        docx_file_id = upload_file(service, docx_path, st.session_state.drive_folder_id, docx_filename)
        saving_progress.progress(60)
        
        # Upload PDF
        pdf_file_id = upload_file(service, pdf_path, st.session_state.drive_folder_id, pdf_filename)
        saving_progress.progress(80)
        
        # Create shareable links
        docx_link = create_shareable_link(service, docx_file_id)
        pdf_link = create_shareable_link(service, pdf_file_id)
        
        st.session_state.drive_links = {
            'docx': docx_link,
            'pdf': pdf_link
        }
        
        saving_progress.progress(100)
        saving_status.success("✅ Files saved to Google Drive")
        
        # Mark processing as complete
        st.session_state.processing_complete = True
        
        # Show success message
        st.success("🎉 Processing completed successfully!")
        st.balloons()
        
    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
        with st.expander("Show error details"):
            st.code(traceback.format_exc())

def main():
    st.title("🎥 Video-to-Scope-Summary")
    st.markdown("Transform your job videos into structured scope summaries with AI-powered transcription and parsing.")
    
    # Check API keys
    keys_valid, missing_keys = validate_api_keys()
    if not keys_valid:
        st.error(f"❌ Missing required API keys: {', '.join(missing_keys)}")
        st.info("Please add the missing keys to your .env file and restart the application.")
        return
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Drive folder ID input
        drive_folder_id = st.text_input(
            "Google Drive Folder ID",
            value=st.session_state.drive_folder_id,
            help="Enter the Google Drive folder ID where files will be saved"
        )
        
        # Template file ID input
        template_file_id = st.text_input(
            "Template File ID",
            value=st.session_state.template_file_id,
            help="Enter the Google Drive file ID of the blank Scope-Summary.docx template"
        )
        
        # Save settings button
        if st.button("💾 Save Settings"):
            st.session_state.drive_folder_id = drive_folder_id
            st.session_state.template_file_id = template_file_id
            
            # Validate Drive setup
            if drive_folder_id and template_file_id:
                is_valid, message = validate_drive_setup(drive_folder_id, template_file_id)
                if is_valid:
                    st.success("✅ Settings saved and validated!")
                else:
                    st.error(f"❌ {message}")
            else:
                st.success("💾 Settings saved!")
        
        # Show current status
        if st.session_state.drive_folder_id and st.session_state.template_file_id:
            st.info("✅ Google Drive configured")
        else:
            st.warning("⚠️ Google Drive not configured")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📁 Upload Job Video or Audio")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose an MP4 or MP3 file",
            type=['mp4', 'mp3'],
            accept_multiple_files=False,
            help="Maximum file size: 200MB, Maximum duration: 30 minutes"
        )
        
        if uploaded_file is not None:
            st.session_state.uploaded_file = uploaded_file
            
            # Display file info
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.info(f"📄 **File:** {uploaded_file.name}")
            st.info(f"📊 **Size:** {file_size_mb:.2f} MB")
            
            # Validate file size
            if file_size_mb > 200:
                st.warning("⚠️ File size exceeds 200MB. This may result in high processing costs and longer wait times.")
            
            # Processing section
            st.header("🔄 Processing")
            
            # Start processing button
            if st.button("🚀 Start Processing", disabled=st.session_state.processing_complete):
                if not st.session_state.drive_folder_id or not st.session_state.template_file_id:
                    st.error("Please configure Google Drive settings in the sidebar first.")
                else:
                    process_video()
            
            # Reset button
            if st.session_state.processing_complete:
                if st.button("🔄 Process Another File"):
                    # Reset session state
                    st.session_state.uploaded_file = None
                    st.session_state.transcript = ""
                    st.session_state.scope_items = []
                    st.session_state.docx_path = ""
                    st.session_state.pdf_path = ""
                    st.session_state.drive_links = {}
                    st.session_state.processing_complete = False
                    st.rerun()
    
    with col2:
        st.header("📋 Transcript Preview")
        if st.session_state.transcript:
            # Show first 500 characters
            preview_text = st.session_state.transcript[:500]
            if len(st.session_state.transcript) > 500:
                preview_text += "..."
            st.text_area("Transcript", preview_text, height=200, disabled=True)
            
            # Show full transcript in expander
            with st.expander("Show full transcript"):
                st.text(st.session_state.transcript)
        else:
            st.info("Transcript will appear here after processing")
        
        st.header("📊 Scope Items")
        if st.session_state.scope_items:
            st.dataframe(st.session_state.scope_items, use_container_width=True)
        else:
            st.info("Scope items will appear here after parsing")
        
        st.header("⬇️ Download")
        
        # Download buttons
        col_docx, col_pdf = st.columns(2)
        
        with col_docx:
            if st.session_state.docx_path and os.path.exists(st.session_state.docx_path):
                with open(st.session_state.docx_path, "rb") as file:
                    st.download_button(
                        label="📄 Download DOCX",
                        data=file.read(),
                        file_name="scope_summary.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
            else:
                st.button("📄 Download DOCX", disabled=True)
        
        with col_pdf:
            if st.session_state.pdf_path and os.path.exists(st.session_state.pdf_path):
                with open(st.session_state.pdf_path, "rb") as file:
                    st.download_button(
                        label="📄 Download PDF",
                        data=file.read(),
                        file_name="scope_summary.pdf",
                        mime="application/pdf"
                    )
            else:
                st.button("📄 Download PDF", disabled=True)
        
        # Google Drive links
        if st.session_state.drive_links:
            st.header("☁️ Google Drive Links")
            if st.session_state.drive_links.get('docx'):
                st.markdown(f"[📄 View DOCX in Drive]({st.session_state.drive_links['docx']})")
            if st.session_state.drive_links.get('pdf'):
                st.markdown(f"[📄 View PDF in Drive]({st.session_state.drive_links['pdf']})")

if __name__ == "__main__":
    main() 