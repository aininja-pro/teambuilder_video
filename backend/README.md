# GC Video Scope Analyzer - Backend

Multi-tenant SaaS backend for construction scope analysis with Claude + AssemblyAI.

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Redis (local or remote)
- Supabase account
- Anthropic API key (Claude)
- AssemblyAI API key

### Installation

1. **Install Python dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Setup environment variables**:
```bash
cp .env.example .env
# Edit .env and fill in all required values
```

3. **Setup Supabase**:
   - Create a new Supabase project at https://supabase.com
   - Run the database schema:
     - Go to SQL Editor in Supabase dashboard
     - Copy/paste contents of `database_schema.sql`
     - Execute the SQL
   - Create storage buckets:
     - Go to Storage in Supabase dashboard
     - Create buckets: `uploads`, `documents`, `logos`
     - Set policies to allow authenticated access

4. **Start Redis** (if running locally):
```bash
# macOS (via Homebrew)
brew services start redis

# Or with Docker
docker run -d -p 6379:6379 redis:alpine
```

5. **Run the application**:
```bash
python main.py
```

The API will be available at: http://localhost:8000

## 📋 API Endpoints

### Health Check
```bash
GET /health
```

### Authentication
```bash
POST /api/auth/signup
POST /api/auth/login
POST /api/auth/logout
```

### Projects
```bash
GET    /api/projects          # List all projects
POST   /api/projects          # Create new project
GET    /api/projects/{id}     # Get project details
PATCH  /api/projects/{id}     # Update project
DELETE /api/projects/{id}     # Delete project
```

### Files
```bash
POST   /api/files/upload      # Upload file (video, audio, photo, text)
GET    /api/files/{id}        # Get file details
DELETE /api/files/{id}        # Delete file
```

### Analyses
```bash
POST   /api/analyses/start    # Start scope analysis
GET    /api/analyses/{id}     # Get analysis results
GET    /api/analyses/{id}/documents  # Get generated documents
```

## 🔧 Configuration

### Environment Variables

See `.env.example` for all available configuration options.

**Required variables:**
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Supabase anon/public key
- `SUPABASE_SERVICE_KEY` - Supabase service role key
- `ANTHROPIC_API_KEY` - Claude API key
- `ASSEMBLYAI_API_KEY` - AssemblyAI API key
- `REDIS_URL` - Redis connection URL

### AI Service Configuration

**Claude (Anthropic):**
- Model: `claude-3-5-sonnet-20241022`
- Used for: Scope parsing, photo analysis
- Cost: ~$2-3 per project

**AssemblyAI:**
- Used for: Audio/video transcription
- Features: Speaker diarization, construction terminology
- Cost: ~$0.25-1.50 per hour of audio

## 🗄️ Database Schema

The application uses Supabase (PostgreSQL) with the following tables:

- `clients` - White-label client organizations
- `user_clients` - User-client relationships
- `projects` - Multi-input project containers
- `project_files` - Uploaded files metadata
- `analyses` - AI analysis results
- `documents` - Generated DOCX/PDF documents
- `photo_annotations` - Photo analysis with scope links

See `database_schema.sql` for complete schema with RLS policies.

## 📁 Project Structure

```
backend/
├── main.py                    # FastAPI application entry point
├── workers.py                 # Background job workers (TODO)
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── database_schema.sql       # Supabase database schema
│
├── config/
│   ├── settings.py           # Application settings
│   ├── supabase.py           # Supabase client configuration
│   └── redis_client.py       # Redis job queue configuration
│
├── models/
│   └── schemas.py            # Pydantic models for validation
│
├── routes/
│   ├── auth.py               # Authentication endpoints (TODO)
│   ├── projects.py           # Project CRUD endpoints (TODO)
│   ├── files.py              # File upload endpoints (TODO)
│   ├── analyses.py           # Analysis endpoints (TODO)
│   ├── documents.py          # Document generation endpoints (TODO)
│   └── clients.py            # Client management endpoints (TODO)
│
├── services/
│   ├── transcription.py      # AssemblyAI transcription service
│   ├── parsing.py            # Claude scope parsing service
│   ├── vision.py             # Claude Vision photo analysis
│   └── doc_generator.py      # Document generation (TODO)
│
└── templates/
    ├── jral_template.py      # JRAL-style document template (TODO)
    ├── trade_template.py     # Trade-organized template (TODO)
    └── narrative_template.py # Narrative template (TODO)
```

## 🧪 Testing

### Test Health Check
```bash
curl http://localhost:8000/health
```

### Test Transcription Service
```python
from services.transcription import transcribe_audio

result = await transcribe_audio("https://example.com/audio.mp3")
print(result["text"])
```

### Test Scope Parsing
```python
from services.parsing import parse_construction_scope

result = await parse_construction_scope(
    transcript="Need to replace kitchen cabinets and install new tile floor...",
    cost_codes=None  # Uses TeamBuilders default
)
print(result["scope_items"])
```

### Test Photo Analysis
```python
from services.vision import analyze_construction_photo

result = await analyze_construction_photo(
    image_url="https://example.com/photo.jpg",
    context="Kitchen renovation project"
)
print(result["caption"])
```

## 🚢 Deployment

### Deploy to Render

1. **Create web service:**
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

2. **Create Redis instance:**
   - Choose Redis as service type
   - Note the Redis URL

3. **Create worker service:**
   - Build command: `pip install -r requirements.txt`
   - Start command: `python workers.py`

4. **Add environment variables** to all services

### Deploy to other platforms

The application works with any platform that supports Python/FastAPI:
- Heroku
- Railway
- Fly.io
- AWS (EC2, ECS, Lambda)
- Google Cloud Run
- Azure App Service

## 🔐 Security

### Row Level Security (RLS)

The database uses Supabase RLS policies to ensure multi-tenant data isolation:
- Users can only see their own client's data
- Admin role required for client settings changes
- Service role key bypasses RLS for system operations

### Authentication

Uses Supabase Auth with JWT tokens:
- Email/password authentication
- Token-based API access
- Automatic token refresh

## 📊 Monitoring

### Logs

The application uses Python logging:
```bash
# Development (DEBUG level)
DEBUG=true python main.py

# Production (INFO level)
DEBUG=false python main.py
```

### Health Checks

- `GET /health` - Database and Redis connectivity
- Returns 200 if healthy, 503 if unhealthy

## 🤝 Contributing

This is a private project for scope_build SaaS development.

## 📝 License

Proprietary - All rights reserved

## 🆘 Troubleshooting

### Redis connection refused
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Start Redis if needed
brew services start redis  # macOS
```

### Supabase connection error
- Verify SUPABASE_URL and SUPABASE_KEY in .env
- Check network connectivity
- Verify project is active in Supabase dashboard

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### API key errors
- Verify all API keys are valid and active
- Check for typos in .env file
- Ensure .env file is in backend/ directory

## 📞 Support

For issues or questions, refer to:
- `TRANSFORMATION_PLAN.md` - Full development plan
- `product_requirements.md` - Product requirements
- Supabase docs: https://supabase.com/docs
- Anthropic docs: https://docs.anthropic.com
- AssemblyAI docs: https://www.assemblyai.com/docs
