# Setup Guide - Phase 1 Complete!

## ✅ What We've Built

Phase 1 foundation is complete! Here's what's ready:

### Backend Structure
- ✅ FastAPI application (`backend/main.py`)
- ✅ Supabase integration (PostgreSQL + Auth + Storage)
- ✅ AssemblyAI transcription service
- ✅ Claude (Anthropic) scope parsing service
- ✅ Claude Vision photo analysis service
- ✅ Redis job queue configuration
- ✅ Complete database schema with RLS
- ✅ Pydantic models for validation
- ✅ Environment configuration

### Files Created
```
backend/
├── main.py                 ✅ FastAPI app
├── requirements.txt        ✅ Dependencies
├── .env.example           ✅ Environment template
├── .gitignore             ✅ Git ignore rules
├── README.md              ✅ Setup docs
├── database_schema.sql    ✅ Complete DB schema
│
├── config/
│   ├── settings.py        ✅ App settings
│   ├── supabase.py        ✅ Supabase client
│   └── redis_client.py    ✅ Redis client
│
├── models/
│   └── schemas.py         ✅ Pydantic models
│
├── services/
│   ├── transcription.py   ✅ AssemblyAI service
│   ├── parsing.py         ✅ Claude parsing
│   └── vision.py          ✅ Claude Vision
│
├── routes/               (Next: Phase 2)
├── templates/            (Next: Phase 4)
└── workers.py            (Next: Phase 2)
```

---

## 🚀 Next Steps: Setup Your Environment

### Step 1: Get API Keys

You'll need to sign up for these services:

#### 1.1 Supabase (Database + Auth + Storage)
1. Go to https://supabase.com
2. Click "Start your project"
3. Create a new organization (free)
4. Create a new project named "scope_build"
5. Wait for project to finish provisioning (~2 minutes)
6. Get your keys:
   - Go to Settings → API
   - Copy "Project URL" → `SUPABASE_URL`
   - Copy "anon public" key → `SUPABASE_KEY`
   - Copy "service_role" key → `SUPABASE_SERVICE_KEY`

#### 1.2 Anthropic (Claude)
1. Go to https://console.anthropic.com
2. Sign up or log in
3. Go to Settings → API Keys
4. Create new key → Copy it → `ANTHROPIC_API_KEY`
5. Add $25+ credits to your account (Pay-as-you-go)

#### 1.3 AssemblyAI (Transcription)
1. Go to https://www.assemblyai.com
2. Click "Start building for free"
3. Sign up with email
4. Go to Dashboard
5. Copy your API key → `ASSEMBLYAI_API_KEY`
6. Free tier includes 5 hours/month (perfect for testing)

### Step 2: Setup Supabase Database

1. **Run database schema:**
   - Open Supabase dashboard
   - Go to SQL Editor (left sidebar)
   - Click "New query"
   - Copy entire contents of `backend/database_schema.sql`
   - Paste into SQL editor
   - Click "Run" (bottom right)
   - Should see "Success" message

2. **Create storage buckets:**
   - Go to Storage (left sidebar)
   - Click "New bucket"
   - Create bucket named `uploads` (make it **private**)
   - Repeat for `documents` (private)
   - Repeat for `logos` (private)

3. **Verify setup:**
   - Go to Table Editor
   - You should see: clients, user_clients, projects, project_files, analyses, documents, photo_annotations
   - Go to Storage
   - You should see: uploads, documents, logos buckets

### Step 3: Setup Local Environment

#### 3.1 Install Redis

**macOS:**
```bash
brew install redis
brew services start redis

# Test it works
redis-cli ping
# Should return: PONG
```

**Windows (via WSL):**
```bash
sudo apt-get install redis-server
sudo service redis-server start
redis-cli ping
```

**Docker (any OS):**
```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

#### 3.2 Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

If you get errors, try:
```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

#### 3.3 Create .env File

```bash
cd backend
cp .env.example .env
```

Now edit `.env` and fill in your API keys:
```bash
# Use nano, vim, or VS Code
nano .env
```

Replace all the placeholder values with your actual keys from Step 1.

### Step 4: Test the Backend

```bash
cd backend
python main.py
```

You should see:
```
INFO:     Starting GC Video Scope Analyzer v2.0.0
INFO:     ✓ Supabase connection established
INFO:     ✓ Redis connection established
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Open http://localhost:8000 in your browser - you should see:
```json
{
  "app": "GC Video Scope Analyzer",
  "version": "2.0.0",
  "status": "running"
}
```

Test health check: http://localhost:8000/health

### Step 5: Test AI Services (Optional)

#### Test Transcription

Create a test file `test_transcription.py`:
```python
import asyncio
from services.transcription import transcribe_audio

async def test():
    # Use a sample audio URL (or your own)
    result = await transcribe_audio(
        "https://github.com/AssemblyAI-Examples/audio-examples/raw/main/20230607_me_canadian_wildfires.mp3"
    )
    print("Transcript:", result["text"][:200])
    print("Duration:", result["audio_duration"], "seconds")
    print("Cost:", result["cost_usd"], "USD")

asyncio.run(test())
```

Run it:
```bash
python test_transcription.py
```

#### Test Scope Parsing

Create `test_parsing.py`:
```python
import asyncio
from services.parsing import parse_construction_scope

async def test():
    transcript = """
    We need to completely renovate the master bathroom.
    Remove the existing vanity and install a new 60-inch double sink vanity.
    Replace all the tile - floor and shower.
    New fixtures throughout - toilet, faucets, showerhead.
    The ceiling has some water damage that needs repair.
    """

    result = await parse_construction_scope(transcript)

    print("Overview:", result["project_summary"]["overview"])
    print("\nScope Items Found:", len(result["scope_items"]))

    for item in result["scope_items"][:3]:
        print(f"\n- {item['cost_code']}: {item['category']}")
        print(f"  Description: {item['description']}")
        print(f"  Location: {item['location']}")

    print("\nCompleteness Score:", result["scope_completeness_score"])
    print("Cost:", result["metadata"]["cost_usd"], "USD")

asyncio.run(test())
```

Run it:
```bash
python test_parsing.py
```

---

## 🎉 Success!

If all tests passed, Phase 1 is complete! You now have:

✅ Supabase database with multi-tenant schema
✅ FastAPI backend with AI integrations
✅ AssemblyAI transcription working
✅ Claude scope parsing working
✅ Claude Vision ready for photo analysis
✅ Foundation for multi-input processing

---

## 🐛 Troubleshooting

### "Connection refused" error
- Make sure Redis is running: `redis-cli ping`
- Check .env has correct REDIS_URL

### "Invalid API key" error
- Double-check API keys in .env file
- No extra spaces or quotes
- Make sure .env is in backend/ directory

### "Module not found" error
```bash
pip install -r requirements.txt --upgrade
```

### Supabase connection error
- Verify SUPABASE_URL and keys in .env
- Make sure database schema was run
- Check project is active in Supabase dashboard

### Python version issues
```bash
python --version
# Should be 3.11 or higher

# If not, install Python 3.11+
# macOS: brew install python@3.11
# Windows: Download from python.org
```

---

## 📋 What's Next?

**Phase 2 (Days 6-10): Multi-Input Processing**
- File upload endpoints
- Multi-file handling
- Process video + audio + photos + text together
- Background job workers

See `TRANSFORMATION_PLAN.md` for full roadmap.

---

## 💰 Cost Tracking

For testing, you'll use:
- **Supabase**: Free tier (500MB database, 1GB storage)
- **AssemblyAI**: Free tier (5 hours/month)
- **Anthropic (Claude)**: Pay-as-you-go (~$2-5 for testing)

For production (100 analyses/month):
- ~$470-595/month total (see TRANSFORMATION_PLAN.md for breakdown)

---

## 🤔 Questions?

Refer to:
- `backend/README.md` - Backend documentation
- `TRANSFORMATION_PLAN.md` - Full development plan
- `product_requirements.md` - Product requirements

In future chats, just say "Continue with Phase 2" and reference this setup!
