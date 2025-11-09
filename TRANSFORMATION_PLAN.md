# GC Video Scope Analyzer - Transformation Plan

**Project:** Scope Build (Multi-tenant SaaS for General Contractors)
**Timeline:** 30 days to launch-ready MVP
**Strategy:** Hybrid rebuild with safe AI stack
**Date Created:** 2025-11-09

---

## Executive Summary

Transform the existing Team Builders single-tenant video scope analyzer into a multi-tenant SaaS product that accepts multiple input formats (video, audio, photos, text) and generates professional, white-labeled scope documentation for general contractors.

### Key Changes
- **Architecture:** Rebuild for multi-tenancy with Supabase
- **AI Stack:** Replace OpenAI → Claude + AssemblyAI (ban-proof)
- **Inputs:** Expand from video-only → video + audio + photos + text
- **Outputs:** Add white-label branding + multiple templates + photo embedding
- **Database:** Redis-only → Supabase (PostgreSQL + Auth + Storage)

---

## Current State Analysis

### What Exists (Team Builders App)
- ✅ Video file upload (MOV, MP4, up to 500MB)
- ✅ OpenAI Whisper transcription
- ✅ OpenAI GPT-4 scope parsing
- ✅ TeamBuilders cost code system (19 categories, hard-coded)
- ✅ Document generation (DOCX, PDF)
- ✅ Web UI (Next.js + React + Tailwind)
- ✅ Backend (FastAPI + Redis)
- ✅ Real-time progress (WebSocket)
- ✅ Saved analysis history (Redis)
- ✅ Deployed (Netlify + Render)

### What's Missing (Must Build)
- ❌ Multi-tenant architecture
- ❌ User authentication
- ❌ Multi-input support (audio, photos, text)
- ❌ White-label branding per client
- ❌ Custom cost codes per client
- ❌ Multiple output templates
- ❌ Photo embedding in documents
- ❌ Proper database (currently Redis-only)
- ❌ Consent/legal protection

### Technical Debt & Risks
- 🚨 **OpenAI ban risk:** Account banned 3x for video uploads (policy violation)
- 🚨 **No database:** Redis ephemeral storage, data loss risk
- 🚨 **Single tenant:** Hard-coded Team Builders branding
- 🚨 **No auth:** Anyone with URL can access
- 🚨 **No legal protection:** No consent checkbox or ToS

---

## Target State (30-Day MVP)

### Core Features (Phase 1 - Must Have)

#### 1. Multi-Input Support
Accept multiple file types in a single project:
- **Video:** MP4, MOV, WebM
- **Audio:** MP3, WAV, M4A, OGG
- **Photos:** JPG, PNG, HEIC
- **Text:** TXT, DOCX, PDF, or paste directly
- **Mixed:** Combine any/all inputs in one analysis

#### 2. White-Label Branding
Per-client customization:
- Upload company logo
- Select primary/secondary colors
- Custom company name, address, phone, email
- Branded cover pages on DOCX/PDF
- Custom footer text

#### 3. Custom Cost Codes
Client-specific cost code systems:
- Import/define custom codes (CSV or manual)
- Support different structures (2-digit, 4-digit, custom format)
- Map AI categories to client codes
- Fallback to TeamBuilders codes if none defined
- Store in client profile

#### 4. Multiple Output Templates
Three professional formats:
- **JRAL-style:** Checkbox/timeline format (Demolition → Construction)
- **Trade-organized:** Tables by Plumbing, Electrical, Fit & Finish
- **Narrative:** Paragraph format with embedded photos
- Template selection per project

#### 5. Photo Integration
Visual documentation throughout:
- AI analysis of photos (materials, conditions, scope items)
- Auto-generated captions
- Link photos to specific scope categories
- Embed photos in DOCX/PDF outputs
- Photo gallery in web UI

#### 6. Multi-Tenant Architecture
Secure SaaS foundation:
- User authentication (Supabase Auth)
- Client/organization accounts
- Row-level security (data isolation)
- Role-based access (future: admin, estimator, viewer)
- Usage tracking per client

---

## Technical Architecture

### Technology Stack

#### Frontend
- **Framework:** Next.js 15 + React 19
- **Language:** TypeScript 5
- **Styling:** Tailwind CSS 4
- **Auth:** Supabase Auth (built-in)
- **State:** React hooks + Context
- **Deployment:** Vercel (automatic from GitHub)

#### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Database:** Supabase (PostgreSQL)
- **Storage:** Supabase Storage (S3-compatible)
- **Job Queue:** Redis + RQ (Python Redis Queue)
- **Real-time:** Supabase Realtime or polling
- **Deployment:** Render (web service + worker)

#### AI Services
- **Transcription:** AssemblyAI SDK (~$1.50/hr audio)
  - Speaker diarization
  - Construction terminology support
  - No content policy issues (business-friendly)
- **Scope Parsing:** Anthropic Claude 3.5 Sonnet (~$2-3/project)
  - Structured JSON extraction
  - Custom construction-expert prompts
  - Client-specific cost code integration
- **Photo Analysis:** Claude Vision (~$0.50/project)
  - Material/condition identification
  - Caption generation
  - Risk/concern flagging

**Total AI Cost:** ~$4-5 per project (vs $2-3 with OpenAI)

#### Document Generation
- **DOCX:** python-docx (existing, enhanced)
- **PDF:** ReportLab (existing, enhanced)
- **Templates:** Jinja2-style rendering engine

#### Infrastructure
- **Frontend Host:** Vercel (free SSL, CDN, preview URLs)
- **Backend Host:** Render (Python + Redis)
- **Database:** Supabase (PostgreSQL + Auth + Storage)
- **Cache/Queue:** Redis on Render
- **Version Control:** GitHub (aininja-pro/scope_build)

### Database Schema (Supabase PostgreSQL)

```sql
-- Users (managed by Supabase Auth)
-- auth.users table automatically created

-- Clients (organizations/companies)
CREATE TABLE clients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  logo_url TEXT,
  primary_color TEXT DEFAULT '#000000',
  secondary_color TEXT DEFAULT '#FFFFFF',
  company_address TEXT,
  company_phone TEXT,
  company_email TEXT,
  footer_text TEXT,
  cost_codes JSONB, -- Custom cost code structure
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User-Client relationship (for multi-user in Phase 2)
CREATE TABLE user_clients (
  user_id UUID REFERENCES auth.users(id),
  client_id UUID REFERENCES clients(id),
  role TEXT DEFAULT 'admin', -- admin, estimator, viewer
  PRIMARY KEY (user_id, client_id)
);

-- Projects (container for multi-input analyses)
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID REFERENCES clients(id),
  user_id UUID REFERENCES auth.users(id),
  name TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'draft', -- draft, processing, completed, failed
  template_type TEXT DEFAULT 'jral', -- jral, trade, narrative
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Project Files (multi-input support)
CREATE TABLE project_files (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  file_type TEXT NOT NULL, -- video, audio, photo, text
  file_url TEXT NOT NULL, -- Supabase Storage URL
  file_name TEXT NOT NULL,
  file_size_mb NUMERIC,
  mime_type TEXT,
  uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Analyses (AI processing results)
CREATE TABLE analyses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  transcript TEXT, -- Combined transcript from all audio/video
  project_summary JSONB, -- {overview, keyRequirements, concerns, decisionPoints, notes}
  scope_items JSONB, -- Array of scope items with cost codes
  scope_completeness_score INTEGER, -- 1-100
  processing_time_seconds INTEGER,
  ai_cost_usd NUMERIC(10,4),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Documents (generated outputs)
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  analysis_id UUID REFERENCES analyses(id) ON DELETE CASCADE,
  document_type TEXT NOT NULL, -- docx, pdf
  file_url TEXT NOT NULL, -- Supabase Storage URL
  file_name TEXT NOT NULL,
  template_used TEXT,
  generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Photo Annotations (linking photos to scope items)
CREATE TABLE photo_annotations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_file_id UUID REFERENCES project_files(id) ON DELETE CASCADE,
  analysis_id UUID REFERENCES analyses(id) ON DELETE CASCADE,
  caption TEXT,
  scope_category TEXT, -- Which cost code category
  ai_analysis JSONB, -- {materials, conditions, risks}
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Row Level Security (RLS) Policies
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Example RLS: Users can only see their own client's data
CREATE POLICY "Users see own client data" ON projects
  FOR SELECT USING (
    client_id IN (
      SELECT client_id FROM user_clients WHERE user_id = auth.uid()
    )
  );
```

### Supabase Storage Buckets

```
uploads/
  ├── {client_id}/
  │   ├── {project_id}/
  │   │   ├── video_001.mp4
  │   │   ├── audio_001.mp3
  │   │   ├── photo_001.jpg
  │   │   └── notes.txt

documents/
  ├── {client_id}/
  │   ├── {project_id}/
  │   │   ├── scope_report.docx
  │   │   └── scope_report.pdf

logos/
  ├── {client_id}_logo.png
```

---

## Development Phases (30-Day Breakdown)

### Phase 1: Foundation & Database (Days 1-5)

#### Day 1-2: Supabase Setup
- [ ] Create Supabase project (scope_build)
- [ ] Create database tables (schema above)
- [ ] Configure RLS policies for multi-tenancy
- [ ] Create Storage buckets (uploads, documents, logos)
- [ ] Setup Supabase Auth (email/password)
- [ ] Test authentication flow
- [ ] Document environment variables needed

#### Day 3-4: Backend Foundation
- [ ] New FastAPI project structure
- [ ] Install dependencies: supabase-py, anthropic, assemblyai, redis, rq
- [ ] Supabase client integration
- [ ] JWT authentication middleware
- [ ] File upload endpoints (multipart/form-data)
- [ ] Supabase Storage upload helpers
- [ ] Basic CRUD for projects, files
- [ ] Health check endpoint

#### Day 5: AI Integration Setup
- [ ] AssemblyAI SDK integration
- [ ] Anthropic Claude SDK integration
- [ ] Test transcription with sample audio
- [ ] Test scope parsing with sample transcript
- [ ] Test vision analysis with sample photo
- [ ] Environment variables: ANTHROPIC_API_KEY, ASSEMBLYAI_API_KEY
- [ ] Error handling for API failures

**Deliverable:** Working backend with Supabase, auth, and AI integrations tested

---

### Phase 2: Multi-Input Processing (Days 6-10)

#### Day 6-7: File Handling & Upload
- [ ] Multi-file upload endpoint (video + audio + photos + text)
- [ ] File type validation (MIME types, extensions)
- [ ] File size limits (500MB per file)
- [ ] Upload to Supabase Storage (organized by client/project)
- [ ] Create project_files records in database
- [ ] Consent checkbox requirement
- [ ] Progress tracking for uploads
- [ ] Error handling (network failures, storage errors)

#### Day 8: Transcription Pipeline (AssemblyAI)
- [ ] Replace OpenAI Whisper with AssemblyAI
- [ ] Support video files (extract audio first if needed)
- [ ] Support audio files directly
- [ ] Speaker diarization (multiple speakers)
- [ ] Merge multiple transcripts (if multiple audio/video files)
- [ ] Store combined transcript in analyses.transcript
- [ ] Timestamp tracking
- [ ] Cost tracking per transcription

#### Day 9: Scope Parsing (Claude)
- [ ] Replace OpenAI GPT-4 with Claude 3.5 Sonnet
- [ ] Adapt construction-expert prompt for Claude
- [ ] Dynamic cost code injection (client-specific or TeamBuilders)
- [ ] Structured JSON extraction with schema validation
- [ ] Enhanced decision point identification
- [ ] Scope completeness scoring (1-100)
- [ ] Conflict detection between scope items
- [ ] Store scope_items in analyses table
- [ ] Cost tracking per analysis

#### Day 10: Photo Analysis (Claude Vision)
- [ ] Analyze each uploaded photo with Claude Vision
- [ ] Extract: materials, conditions, scope items visible
- [ ] Generate captions/descriptions
- [ ] Identify risks/concerns from photos
- [ ] Link photos to scope categories (cost codes)
- [ ] Store in photo_annotations table
- [ ] Embed photo references in scope items JSON

**Deliverable:** Complete multi-input processing pipeline working end-to-end

---

### Phase 3: White-Label & Customization (Days 11-15)

#### Day 11-12: Client Settings System
- [ ] Client profile CRUD endpoints
- [ ] Logo upload to Supabase Storage
- [ ] Color scheme storage (primary, secondary, accent)
- [ ] Company info fields (name, address, phone, email)
- [ ] Custom footer text
- [ ] Default template selection per client
- [ ] Settings validation
- [ ] Admin-only access control

#### Day 13-14: Custom Cost Code Management
- [ ] Cost code CRUD endpoints
- [ ] CSV import for bulk cost codes
- [ ] Manual entry interface (API)
- [ ] Support different code structures (2-digit, 4-digit, custom)
- [ ] Validate code format
- [ ] Store in clients.cost_codes (JSONB)
- [ ] Category mapping (AI categories → client codes)
- [ ] Fallback logic: use TeamBuilders if none defined

#### Day 15: White-Label Integration
- [ ] Update scope parsing to use client cost codes
- [ ] Inject client terminology into Claude prompts
- [ ] Test with multiple client configurations
- [ ] Validate cost code mapping works
- [ ] Preview endpoint (show how output will look)

**Deliverable:** White-label branding and custom cost codes fully working

---

### Phase 4: Output Templates (Days 16-20)

#### Day 16-17: Template System Architecture
- [ ] Template engine setup (Jinja2 or similar)
- [ ] Template data structure design
- [ ] Create JRAL-style template:
  - Cover page with client branding
  - Project summary section
  - Demolition timeline (checkbox format)
  - Construction timeline (trade-organized tables)
  - Additional scope items
  - Notes section
- [ ] Create Trade-organized template:
  - Cover page
  - Overview with photos
  - Sections by trade (Plumbing, Electrical, etc.)
  - Trade tables with scope details
- [ ] Create Narrative template:
  - Cover page
  - Executive summary
  - Narrative scope description
  - Embedded photos throughout
  - Appendix with detailed items

#### Day 18-19: Enhanced Document Generation
- [ ] Update doc_generator.py for template system
- [ ] DOCX generation:
  - Client logo embedding
  - Dynamic color scheme (headings, tables)
  - Photo embedding in relevant sections
  - Photo captions
  - Checkbox formatting
  - Trade tables
  - Page breaks at logical points
  - Headers/footers with client info
- [ ] PDF generation:
  - Same features as DOCX
  - Professional formatting (ReportLab)
  - Color-coded sections (Concerns=red, Decision Points=blue)
  - Print-optimized layout

#### Day 20: Template Testing
- [ ] Generate all 3 templates with sample data
- [ ] Test with photos embedded
- [ ] Test with different client branding
- [ ] Verify formatting consistency
- [ ] Test print output (PDF)
- [ ] Store documents in Supabase Storage
- [ ] Create documents table records

**Deliverable:** All 3 templates generating professional DOCX/PDF with photos

---

### Phase 5: Frontend Rebuild (Days 21-25)

#### Day 21: Project Setup & Authentication
- [ ] New Next.js 15 project (App Router)
- [ ] TypeScript configuration
- [ ] Tailwind CSS 4 setup
- [ ] Supabase JS client integration
- [ ] Authentication pages:
  - `/login` - Email/password form
  - `/signup` - Registration form
  - `/forgot-password` - Password reset
- [ ] Auth state management (Supabase Auth)
- [ ] Protected routes middleware
- [ ] Mobile-responsive layout

#### Day 22: Dashboard & Project Creation
- [ ] `/dashboard` page:
  - Project list (grid/list view)
  - Filter/search projects
  - Status indicators (draft, processing, completed)
  - Delete project
  - Mobile-responsive cards
- [ ] `/project/new` page (multi-step wizard):
  - Step 1: Project name + description
  - Step 2: File upload (drag-drop for all types)
  - Step 3: Review uploads, add text notes
  - Step 4: Processing status
- [ ] FileUpload component (multi-file, all types)
- [ ] Chunked upload for large files
- [ ] Upload progress bars

#### Day 23: Analysis Results View
- [ ] `/project/[id]` page:
  - Tab navigation: Transcript, Summary, Scope, Photos, Documents
  - Transcript view (with timestamps if available)
  - Project summary (color-coded sections)
  - Scope items table (with photo thumbnails)
  - Photo gallery (lightbox view)
  - Document download buttons (DOCX, PDF)
  - Template selector (regenerate with different template)
- [ ] Components:
  - ProcessingStatus (real-time progress)
  - ScopeItemsTable (sortable, filterable)
  - ProjectSummary (formatted sections)
  - PhotoGallery (grid with captions)
  - DocumentDownload (DOCX/PDF buttons)

#### Day 24: Settings & White-Label Config
- [ ] `/settings` page:
  - User profile (name, email)
  - Password change
  - Account info
- [ ] `/settings/branding` page (admin only):
  - Logo upload (drag-drop)
  - Color picker (primary, secondary)
  - Company info form
  - Footer text
  - Preview white-label output
  - Save button
- [ ] `/settings/cost-codes` page:
  - Cost code list (table)
  - Add/edit/delete codes
  - CSV import
  - Category mapping

#### Day 25: Polish & Mobile Optimization
- [ ] Mobile testing on actual phone
- [ ] Touch-friendly buttons/inputs
- [ ] Responsive tables (stack on mobile)
- [ ] Loading states for all actions
- [ ] Error handling UI (toast notifications)
- [ ] Empty states (no projects, no files)
- [ ] Progressive Web App (PWA) manifest
- [ ] Favicon and app icons
- [ ] Performance optimization (lazy loading, code splitting)

**Deliverable:** Complete, mobile-responsive frontend working end-to-end

---

### Phase 6: Testing & Deployment (Days 26-30)

#### Day 26-27: Testing
- [ ] **Multi-tenant isolation:**
  - Create 2 test clients
  - Verify data isolation (RLS policies)
  - Test user can't see other client's data
- [ ] **All input combinations:**
  - Video only
  - Audio only
  - Photos only
  - Text only
  - Video + photos
  - Audio + photos + text
  - Full combo: video + audio + photos + text
- [ ] **Template generation:**
  - All 3 templates with same data
  - Photos embedded correctly
  - Client branding applied
  - DOCX formatting correct
  - PDF formatting correct
- [ ] **White-label:**
  - Different logos
  - Different color schemes
  - Different cost codes
- [ ] **Mobile testing:**
  - Test on your actual phone
  - Upload files from phone
  - View results on phone
  - Download documents on phone
- [ ] **Performance:**
  - Measure processing time
  - Optimize for <5 minutes target
  - Database query optimization
  - Frontend bundle size
- [ ] **Error handling:**
  - Network failures
  - Upload errors
  - API failures (AssemblyAI, Claude)
  - Invalid files
  - Large files (>500MB)

#### Day 28: Production Deployment - Supabase
- [ ] Upgrade to Supabase production tier (if needed)
- [ ] Configure production secrets
- [ ] Enable database backups (automatic)
- [ ] Configure Supabase Auth settings
- [ ] Set up custom email templates (optional)
- [ ] Test production database connection

#### Day 29: Production Deployment - Backend (Render)
- [ ] Create Render web service (Python)
- [ ] Configure build command: `pip install -r requirements.txt`
- [ ] Configure start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Add environment variables:
  - ANTHROPIC_API_KEY
  - ASSEMBLYAI_API_KEY
  - SUPABASE_URL
  - SUPABASE_SERVICE_KEY (service role key)
  - REDIS_URL
- [ ] Create Redis instance on Render
- [ ] Create background worker service:
  - Build command: `pip install -r requirements.txt`
  - Start command: `python workers.py`
  - Same environment variables
- [ ] Configure health check endpoint
- [ ] Test backend production URL

#### Day 30: Production Deployment - Frontend (Vercel)
- [ ] Connect GitHub repo to Vercel
- [ ] Configure project:
  - Framework: Next.js
  - Root directory: `video-scope-analyzer/`
  - Build command: `npm run build`
  - Output directory: `.next/` (automatic)
- [ ] Add environment variables:
  - NEXT_PUBLIC_SUPABASE_URL
  - NEXT_PUBLIC_SUPABASE_ANON_KEY
  - NEXT_PUBLIC_API_URL (Render backend URL)
- [ ] Deploy
- [ ] Configure custom domain (optional)
- [ ] Test production frontend
- [ ] Verify API calls to backend work
- [ ] Test authentication flow
- [ ] Test full workflow end-to-end
- [ ] Test on mobile phone (production URL)

**Deliverable:** Production-ready SaaS app deployed and tested

---

## Success Metrics (30-Day MVP)

### Technical Success
- ✅ User can create account and login
- ✅ User can upload video + audio + photos + text in one project
- ✅ Processing completes in <5 minutes for typical project
- ✅ Generates professional DOCX/PDF with embedded photos
- ✅ Works on mobile browser (tested on your phone)
- ✅ Multi-tenant isolation verified (RLS working)
- ✅ No data loss (Supabase persistence)
- ✅ 99%+ uptime (Vercel + Render)

### Feature Completeness
- ✅ Multi-input support (4 types)
- ✅ White-label branding (logo, colors, company info)
- ✅ Custom cost codes per client
- ✅ 3 output templates
- ✅ Photo embedding in documents
- ✅ Consent checkbox for legal protection
- ✅ Professional formatting (color-coded sections)

### Business Readiness
- ✅ Can onboard first paying customer
- ✅ Can customize per client (white-label)
- ✅ Can scale to 10+ clients (multi-tenant)
- ✅ No OpenAI ban risk (Claude + AssemblyAI)
- ✅ Legal protection (consent, ToS)
- ✅ Pricing model viable (~$4-5 AI cost per project)

---

## What We're NOT Building (Phase 1)

### Phase 2 Features (Months 2-3)
- ❌ Multi-user collaboration
- ❌ Team member accounts per client
- ❌ Role-based permissions (admin, estimator, viewer)
- ❌ Comment/annotation system
- ❌ Approval workflow
- ❌ Revision tracking
- ❌ Client portal (share with property owners)
- ❌ Version comparison

### Phase 3 Features (Months 4+)
- ❌ Advanced analytics
- ❌ Historical project intelligence
- ❌ Project templates for common types
- ❌ API access for integrations
- ❌ Webhook notifications
- ❌ Export to estimating software
- ❌ Mobile native app (iOS/Android)

### Out of Scope (Won't Build)
- ❌ Pricing/estimating features
- ❌ Project management tools
- ❌ Accounting integration
- ❌ Time tracking
- ❌ Bid management

---

## Key Decisions & Rationale

### 1. Why Claude + AssemblyAI instead of OpenAI?
**Problem:** OpenAI banned account 3x for video uploads (policy violations)

**Solution:**
- **AssemblyAI:** Built for business transcription, no content policy issues
- **Claude:** More permissive for commercial use, excellent at structured extraction
- **Trade-off:** ~$2 more expensive per project ($4-5 vs $2-3)
- **Benefit:** Zero ban risk, better legal standing

### 2. Why Supabase instead of custom PostgreSQL?
**Rationale:**
- Built-in authentication (saves 3-5 days of dev time)
- Storage buckets included (S3-compatible)
- Row-level security (multi-tenancy built-in)
- Real-time subscriptions (if needed)
- Free tier for development
- Faster time to market

### 3. Why Hybrid Rebuild instead of Full Rebuild?
**Rationale:**
- Reuse proven AI processing logic (transcribe, parse, doc gen concepts)
- Avoid "not invented here" syndrome
- Focus effort on new features (multi-input, white-label, templates)
- Faster to market (~40% time savings)
- Lower risk (proven patterns)

### 4. Why Vercel + Render instead of all-in-one?
**Rationale:**
- Vercel best for Next.js (made by same company)
- Render good for Python + Redis workers
- Separation of concerns (frontend vs backend)
- Can scale independently
- Familiar to you (already using Render)

### 5. Why 3 templates instead of customizable template builder?
**Rationale:**
- Template builder is complex (2-3 weeks of work)
- 3 templates cover 80% of use cases
- Can add more templates incrementally
- Keeps Phase 1 achievable in 30 days
- Template builder is Phase 2 feature

---

## Risk Mitigation

### Risk 1: AI API Bans
**Mitigation:**
- Use business-friendly AI providers (Claude, AssemblyAI)
- Add consent checkbox (user confirms rights to content)
- Clear ToS with indemnification clause
- Monitor API usage patterns

### Risk 2: 30-Day Timeline Too Aggressive
**Mitigation:**
- Phased approach (can ship after Phase 4 if needed)
- Focus on MVP features only
- Reuse existing code where possible
- Cut scope if necessary (e.g., reduce to 2 templates)

### Risk 3: Multi-Tenancy Data Leaks
**Mitigation:**
- Use Supabase RLS (battle-tested)
- Test multi-tenant isolation thoroughly (Day 26)
- Code review RLS policies
- Penetration testing before launch

### Risk 4: Processing Time >5 Minutes
**Mitigation:**
- Optimize file size (compression)
- Parallel processing where possible
- Use faster AI models if needed
- Set user expectations (progress bar)

### Risk 5: Mobile Experience Poor
**Mitigation:**
- Mobile-first design from Day 1
- Test on your actual phone throughout development
- Touch-friendly UI components
- Responsive tables/layouts

---

## Cost Analysis

### Development Costs (30 Days)
- **Your Time:** 30 days full-time development
- **AI Services (Testing):** ~$50-100 (testing transcription/parsing)
- **Supabase:** Free tier (up to 500MB database, 1GB storage)
- **Vercel:** Free tier
- **Render:** Free tier or ~$7/month (Starter)
- **Redis:** Free tier on Render
- **Total:** ~$50-100 for 30-day development

### Production Costs (Per Month)
**Assuming 100 analyses/month:**
- **AI Services:** $400-500 (100 × $4-5 per analysis)
- **Supabase:** $25/month (Pro tier for production)
- **Vercel:** $20/month (Pro tier, optional)
- **Render:** $25-50/month (backend + worker + Redis)
- **Total:** ~$470-595/month

**Revenue Target (10 customers @ $497/month):** $4,970/month
**Gross Margin:** ~90% ($4,375/month profit)

### Per-Customer Economics
- **Subscription:** $497/month
- **AI Costs:** $40-50 (assuming 10 analyses/month)
- **Infrastructure:** ~$5/customer
- **Gross Profit:** $442-452 per customer/month
- **LTV (12 months):** ~$5,300 per customer

---

## Next Steps After 30-Day MVP

### Week 5-6: Customer Onboarding
- Onboard first 3 beta customers
- Gather feedback on UX
- Identify missing features
- Fix critical bugs
- Optimize processing performance

### Week 7-8: Polish & Iteration
- Improve based on customer feedback
- Add minor features (email notifications, etc.)
- Performance optimization
- Documentation (user guides)
- Sales materials (demo videos, case studies)

### Month 3: Phase 2 Kickoff
- Multi-user collaboration
- Client approval portal
- Revision tracking
- Enhanced analytics

---

## Questions to Resolve Before Starting

1. **Supabase Account:** Do you have a Supabase account, or should we create one?
2. **API Keys:** Do you have Anthropic and AssemblyAI API keys, or need to sign up?
3. **GitHub Repo:** Confirmed as aininja-pro/scope_build - correct?
4. **Render Account:** Do you have access to existing Render account?
5. **Vercel Account:** Do you have a Vercel account, or should we create one?
6. **Domain:** Do you have a custom domain, or use default Vercel domain?
7. **Terms of Service:** Do you have a ToS template, or should we create one?
8. **Consent Language:** What should the consent checkbox say?

---

## File Structure (New Project)

```
scope_build/
├── README.md
├── TRANSFORMATION_PLAN.md (this file)
├── product_requirements.md (existing)
├── .gitignore
├── .env.example
│
├── backend/
│   ├── main.py (FastAPI app)
│   ├── workers.py (RQ background workers)
│   ├── requirements.txt
│   ├── .env (gitignored)
│   │
│   ├── config/
│   │   ├── supabase.py (Supabase client)
│   │   ├── redis.py (Redis client)
│   │   └── settings.py (env vars)
│   │
│   ├── routes/
│   │   ├── auth.py
│   │   ├── projects.py
│   │   ├── files.py
│   │   ├── analyses.py
│   │   ├── documents.py
│   │   └── clients.py
│   │
│   ├── services/
│   │   ├── transcription.py (AssemblyAI)
│   │   ├── parsing.py (Claude)
│   │   ├── vision.py (Claude Vision)
│   │   └── doc_generator.py (DOCX/PDF)
│   │
│   ├── models/
│   │   └── schemas.py (Pydantic models)
│   │
│   └── templates/
│       ├── jral_template.py
│       ├── trade_template.py
│       └── narrative_template.py
│
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.js
│   ├── .env.local (gitignored)
│   │
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx (redirect to /dashboard or /login)
│   │   │   ├── login/
│   │   │   ├── signup/
│   │   │   ├── dashboard/
│   │   │   ├── project/
│   │   │   │   ├── new/
│   │   │   │   └── [id]/
│   │   │   └── settings/
│   │   │       ├── page.tsx
│   │   │       ├── branding/
│   │   │       └── cost-codes/
│   │   │
│   │   ├── components/
│   │   │   ├── FileUpload.tsx
│   │   │   ├── ProcessingStatus.tsx
│   │   │   ├── ScopeItemsTable.tsx
│   │   │   ├── ProjectSummary.tsx
│   │   │   ├── PhotoGallery.tsx
│   │   │   ├── DocumentDownload.tsx
│   │   │   └── Header.tsx
│   │   │
│   │   ├── utils/
│   │   │   ├── supabase.ts (Supabase client)
│   │   │   └── api.ts (API helpers)
│   │   │
│   │   └── types/
│   │       └── index.ts (TypeScript types)
│   │
│   └── public/
│       ├── favicon.ico
│       └── manifest.json (PWA)
│
└── documentation/ (existing)
```

---

## Appendix: TeamBuilders Cost Codes (Reference)

For fallback when client has no custom codes:

```
01: General Conditions
02: Site Preparation / Demolition
03: Excavation / Grading / Landscape
04: Concrete & Masonry
05: Rough Carpentry / Framing
06: Doors, Windows, Trim
07: Mechanical (HVAC)
08: Electrical
09: Plumbing
10: Wall & Ceiling Coverings (Drywall, Plaster)
11: Finish Carpentry
12: Cabinets, Vanities, Countertops
13: Flooring / Tile
14: Specialties (Appliances, Fixtures)
15: Decking
16: Fencing
17: Exterior Facade (Siding, Brick, Stone)
18: Soffit, Fascia, Gutters
19: Roofing
```

Each category has 4-digit subcodes (e.g., 5600 = Kitchen Cabinets).

---

## Version History

- **v1.0** - 2025-11-09: Initial transformation plan created
  - Analyzed existing codebase (Team Builders app)
  - Compared against product_requirements.md
  - Defined 30-day MVP scope
  - Selected AI stack (Claude + AssemblyAI)
  - Designed Supabase multi-tenant architecture
  - Created phase-by-phase development plan

---

**Ready to build?** Share this document in future chats to maintain context and track progress against the plan.
