# Video-to-Scope-Summary App

A Streamlit-based application that transforms job site videos into structured scope summaries using AI-powered transcription and parsing.

## Features

- 🎥 **Video/Audio Upload**: Support for MP4 and MP3 files up to 200MB
- 🎤 **AI Transcription**: Uses OpenAI Whisper for accurate audio transcription
- 🔍 **Scope Extraction**: GPT-4 powered parsing to extract scope items by cost codes (01-19)
- 📄 **Document Generation**: Creates both DOCX and PDF scope summary documents
- ☁️ **Google Drive Integration**: Automatically saves documents to your Google Drive
- 📊 **Progress Tracking**: Real-time progress indicators for each processing step

## Prerequisites

Before running the application, you need to install the following system dependencies:

### macOS
```bash
# Install Homebrew if you haven't already
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required packages
brew install wkhtmltopdf ffmpeg
```

### Windows
```bash
# Using Chocolatey
choco install wkhtmltopdf ffmpeg

# Or download and install manually:
# - wkhtmltopdf: https://wkhtmltopdf.org/downloads.html
# - ffmpeg: https://ffmpeg.org/download.html
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install wkhtmltopdf ffmpeg
```

## Installation

1. **Clone or download the project files**
   ```bash
   git clone <repository-url>
   cd TeamBuilders
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the project root with the following content:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   GOOGLE_SERVICE_ACCOUNT_JSON=your_google_service_account_json_here
   ```

## Configuration

### OpenAI API Key

1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add it to your `.env` file as `OPENAI_API_KEY`

### Google Drive Setup

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable Google Drive API**
   - In the Google Cloud Console, go to "APIs & Services" > "Library"
   - Search for "Google Drive API" and enable it

3. **Create Service Account**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Fill in the service account details
   - Download the JSON key file

4. **Configure Service Account**
   - Add the JSON content to your `.env` file as `GOOGLE_SERVICE_ACCOUNT_JSON`
   - You can either paste the entire JSON content or provide the file path

5. **Set up Google Drive Folders**
   - Create a folder in Google Drive for your job files
   - Create a blank Word document template named "Scope-Summary.docx"
   - Share both the folder and template with your service account email (found in the JSON file)
   - Note down the folder ID and template file ID from their URLs

## Usage

1. **Start the application**
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Configure Google Drive settings**
   - Open the sidebar in the app
   - Enter your Google Drive folder ID
   - Enter your template file ID
   - Click "Save Settings"

3. **Process a video**
   - Upload an MP4 or MP3 file (max 200MB, 30 minutes)
   - Click "Start Processing"
   - Wait for the AI to transcribe and parse the content
   - Download the generated DOCX and PDF files
   - Access the files directly in Google Drive via the provided links

## File Structure

```
TeamBuilders/
├── streamlit_app.py          # Main Streamlit application
├── transcribe.py             # OpenAI Whisper integration
├── parse_scope.py            # GPT-4 scope parsing
├── doc_generator.py          # Document generation (DOCX/PDF)
├── drive_helper.py           # Google Drive integration
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this)
├── .gitignore               # Git ignore file
├── README.md                # This file
└── documentation/           # Project documentation
```

## Cost Code Mapping

The application uses standard construction cost codes (01-19):

- **01**: General Requirements
- **02**: Existing Conditions
- **03**: Concrete
- **04**: Masonry
- **05**: Metals
- **06**: Wood, Plastics, and Composites
- **07**: Thermal and Moisture Protection
- **08**: Openings
- **09**: Finishes
- **10**: Specialties
- **11**: Equipment
- **12**: Furnishings
- **13**: Special Construction
- **14**: Conveying Equipment
- **21**: Fire Suppression
- **22**: Plumbing
- **23**: HVAC
- **26**: Electrical
- **27**: Communications
- **28**: Electronic Safety and Security

## Troubleshooting

### Common Issues

1. **"wkhtmltopdf not found"**
   - Make sure wkhtmltopdf is installed and in your system PATH
   - On macOS: `brew install wkhtmltopdf`

2. **"ffmpeg not found"**
   - Install ffmpeg using your system package manager
   - On macOS: `brew install ffmpeg`

3. **Google Drive authentication errors**
   - Verify your service account JSON is correct
   - Ensure the service account has access to your Drive folder and template
   - Check that the folder and file IDs are correct

4. **OpenAI API errors**
   - Verify your API key is correct and has sufficient credits
   - Check that you have access to GPT-4 and Whisper APIs

### Getting Help

If you encounter issues:

1. Check the error details in the expandable error section
2. Verify all prerequisites are installed
3. Ensure your `.env` file is properly configured
4. Check that all required permissions are granted

## Security Notes

- Never commit your `.env` file to version control
- Keep your API keys and service account credentials secure
- The service account only needs access to specific folders, not your entire Drive
- Consider using environment-specific API keys for development vs. production

## License

This project is for internal use. Please ensure you comply with the terms of service for OpenAI and Google APIs. 