import streamlit as st
import os
from dotenv import load_dotenv
import tempfile
import datetime
from typing import List, Dict
import traceback

# Import our custom modules
from transcribe import transcribe_video, validate_file_duration
from parse_scope import parse_scope, format_scope_items_for_display
from doc_generator import generate_docx, generate_pdf_from_scope_items

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Video-to-Scope-Summary",
    page_icon="🎥",
    layout="wide"
)

# Initialize session state
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'transcript' not in st.session_state:
    st.session_state.transcript = ""
if 'scope_items' not in st.session_state:
    st.session_state.scope_items = []
if 'project_summary' not in st.session_state:
    st.session_state.project_summary = None
if 'docx_path' not in st.session_state:
    st.session_state.docx_path = ""
if 'pdf_path' not in st.session_state:
    st.session_state.pdf_path = ""
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False

def validate_api_keys():
    """Check if required API keys are configured."""
    openai_key = os.getenv('OPENAI_API_KEY')
    
    missing = []
    if not openai_key:
        missing.append("OPENAI_API_KEY")
    
    return len(missing) == 0, missing

def process_video():
    """Main processing function that orchestrates the entire pipeline."""
    if not st.session_state.uploaded_file:
        st.error("No file uploaded")
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
    
    try:
        # Step 1: Validate file
        upload_status.info("📋 Validating file...")
        upload_progress.progress(25)
        
        # Check file duration if possible
        is_valid, duration_msg = validate_file_duration(file_bytes, filename)
        if not is_valid:
            st.warning(f"⚠️ {duration_msg}")
        
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
        parsing_status.info("🔍 Extracting scope items & summary...")
        parsing_progress.progress(25)
        
        parsed_data = parse_scope(transcript)
        raw_scope_items = parsed_data.get('scopeItems', [])
        project_summary = parsed_data.get('projectSummary', {})
        
        formatted_scope_items = format_scope_items_for_display(raw_scope_items)
        st.session_state.scope_items = formatted_scope_items
        st.session_state.project_summary = project_summary
        
        parsing_progress.progress(100)
        parsing_status.success(f"✅ Extracted {len(raw_scope_items)} scope items")
        
        # Step 4: Document generation
        generation_status.info("📄 Generating documents...")
        generation_progress.progress(25)
        
        # Generate DOCX and PDF using both scope items and the project summary
        docx_path = generate_docx(formatted_scope_items, st.session_state.project_summary, job_name, version=1)
        st.session_state.docx_path = docx_path
        generation_progress.progress(50)
        
        pdf_path = generate_pdf_from_scope_items(formatted_scope_items, st.session_state.project_summary, job_name, version=1)
        st.session_state.pdf_path = pdf_path
        generation_progress.progress(100)
        generation_status.success("✅ Documents generated and ready for download")
        
        # Mark processing as complete
        st.session_state.processing_complete = True
        
        # Show success message
        st.success("🎉 Processing completed successfully! Your documents are ready for download.")
        st.balloons()
        
    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
        with st.expander("Show error details"):
            st.code(traceback.format_exc())

def main():
    st.title("🎥 Video-to-Scope-Summary")

    # --- CUSTOM STYLES ---
    st.markdown("""
        <style>
            /* Main title: Video-to-Scope-Summary */
            h1 {
                font-size: 1.8rem !important;
                font-weight: 600 !important;
                padding-top: 1rem !important;
                padding-bottom: 0.25rem !important;
            }
            
            /* Section headers: Upload, Transcript, etc. */
            h2 {
                font-size: 1.4rem !important;
                font-weight: 600 !important;
                padding-top: 1rem !important;
                padding-bottom: 0.25rem !important;
            }

            /* Make key components more compact */
            div[data-testid="stFileUploader"],
            div[data-testid="stTextArea"],
            div[data-testid="stDataFrame"],
            div[data-testid="stButton"] > button {
                margin-bottom: 0.5rem !important;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("Transform your job videos into structured scope summaries with AI-powered transcription and parsing.")
    
    # Check API keys
    keys_valid, missing_keys = validate_api_keys()
    if not keys_valid:
        st.error(f"❌ Missing required API keys: {', '.join(missing_keys)}")
        st.info("Please add the missing keys to your .env file and restart the application.")
        return
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📁 Upload Job Video or Audio")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a video or audio file",
            type=['mp4', 'mov', 'mpeg', 'webm', 'mp3', 'm4a', 'wav', 'mpga', 'flac', 'oga', 'ogg'],
            accept_multiple_files=False,
            help="Supports video (MP4, MOV, MPEG, WebM) and audio (MP3, M4A, WAV, FLAC, OGA, OGG) files up to 500MB. MOV files are automatically converted to MP4."
        )
        
        if uploaded_file is not None:
            st.session_state.uploaded_file = uploaded_file
            
            # Display file info
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.info(f"📄 **File:** {uploaded_file.name}")
            st.info(f"📊 **Size:** {file_size_mb:.2f} MB")
            
            # Validate file size with different warning levels
            if file_size_mb > 500:
                st.error("🚫 File size exceeds 500MB. Please use a smaller file or split the video into segments.")
            elif file_size_mb > 350:
                st.warning("⚠️ Large file detected! Processing will take longer and may incur higher costs. The file will be automatically compressed for transcription.")
            elif file_size_mb > 200:
                st.info("ℹ️ Medium-sized file. Will be compressed if needed for transcription.")
            
            # Processing section
            st.header("🔄 Processing")
            
            # Start processing button
            if st.button("🚀 Start Processing", disabled=st.session_state.processing_complete):
                process_video()
            
            # Reset button
            if st.session_state.processing_complete:
                if st.button("🔄 Process Another File"):
                    # Reset session state
                    st.session_state.uploaded_file = None
                    st.session_state.transcript = ""
                    st.session_state.scope_items = []
                    st.session_state.project_summary = None
                    st.session_state.docx_path = ""
                    st.session_state.pdf_path = ""
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
        
        st.header("📝 Project Summary")
        if st.session_state.project_summary:
            summary = st.session_state.project_summary
            st.markdown(f"**Sentiment:** {summary.get('sentiment', 'N/A')}")
            
            with st.expander("Show Full Project Summary", expanded=True):
                st.subheader("Overview")
                st.write(summary.get('overview', 'No overview provided.'))

                st.subheader("Key Requirements")
                for item in summary.get('keyRequirements', []):
                    st.markdown(f"- {item}")

                st.subheader("Concerns")
                for item in summary.get('concerns', []):
                    st.markdown(f"- {item}")

                st.subheader("Decision Points")
                for item in summary.get('decisionPoints', []):
                    st.markdown(f"- {item}")
                
                st.subheader("Important Notes")
                for item in summary.get('importantNotes', []):
                    st.markdown(f"- {item}")
        else:
            st.info("Project summary will appear here after parsing")
        
        st.header("📊 Scope Items")
        if st.session_state.scope_items:
            st.dataframe(st.session_state.scope_items, use_container_width=True)
        else:
            st.info("Scope items will appear here after parsing")
        
        st.header("⬇️ Download Documents")
        
        # Download buttons
        col_docx, col_pdf = st.columns(2)
        
        with col_docx:
            if st.session_state.docx_path and os.path.exists(st.session_state.docx_path):
                with open(st.session_state.docx_path, "rb") as file:
                    st.download_button(
                        label="📄 Download DOCX",
                        data=file.read(),
                        file_name=f"scope_summary_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
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
                        file_name=f"scope_summary_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
            else:
                st.button("📄 Download PDF", disabled=True)

if __name__ == "__main__":
    main() 