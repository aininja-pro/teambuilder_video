# Product Requirements Document: GC Video Scope Analyzer

## Product Vision
A scope creation specialist tool for general contractors that accepts multiple input formats (video, audio, transcripts, photos, meeting recordings) and generates professional, comprehensive scope documentation that prevents change orders and protects profit margins.

## Product Positioning
**"However you capture project information - video, audio, transcript, notes, meeting recording - we turn it into professional scope documentation."**

**Target Customer:** Mid-market general contractors ($5M-50M annual revenue) who bid 15-30+ projects monthly and have experienced costly scope disputes/change orders.

**Core Value Proposition:** Eliminate $50K-150K in annual scope dispute costs by ensuring comprehensive, documented, professional scope creation from any input format.

---

## CURRENT STATE (What's Already Built)

Based on the Iowa client deployment, the existing system includes:

### Input Capabilities
- Video file upload (MOV, MP4, etc.)
- Large file handling with compression (350MB+ files)
- File format support: MP4, MOV, MP3, WAV, max 500MB

### Processing
- Video transcription using AI
- AI-powered scope analysis using custom construction-expert prompt
- Custom TeamBuilders cost code integration
- Extraction of scope items organized by trade categories

### Output Generation
- **Full transcript** - Complete transcription of walkthrough
- **Project Summary** with:
  - Overview description
  - Key Requirements list
  - Concerns/challenges identified
  - Decision Points requiring client input
  - Important Notes section
- **Scope Items** with detailed structure:
  - Cost code (2-digit main code)
  - Category name
  - Sub-code (4-digit when applicable)
  - Sub-category name
  - Description of work
  - Location in building
  - Material specifications
  - Quantity estimates (when mentioned)
  - Notes and special requirements
- **Export formats:**
  - PDF download
  - DOCX download

### User Interface
- Web-based application (React + Tailwind)
- Works on mobile browsers (responsive design)
- Professional branded interface
- Upload interface with drag-and-drop
- "View Saved Analyses" project history
- "Start Analysis" button
- Analysis results display with sections:
  - Transcript
  - Project Summary (Overview, Key Requirements, Concerns, Decision Points, Important Notes)
  - Scope Items table (Code, Category, Description with details)
  - Download Documents section

### Backend
- Python backend
- Integration with OpenAI GPT-4 for analysis
- Custom construction-expert prompt with TeamBuilders cost codes
- Deployed on Render
- Supabase database for data storage

### Branding
- Currently white-labeled for Team Builders (Iowa client)
- Team Builders logo and branding
- Professional cover page on exports
- Company contact information on outputs

---

## TARGET STATE (What We Want to Build)

### Phase 1: Multi-Input Scope Generation (Priority 1 - Build Now)

#### Input Method Expansion

**1. Video Inputs**
- ✅ Video file upload (EXISTING)
- ➕ Live video recording in app (NEW)
- ➕ Cloud storage import (Dropbox, Google Drive) (NEW)
- ➕ Multiple video uploads per project (NEW)
- ➕ Video trimming/editing capability (FUTURE)

**2. Audio Inputs** (NEW - All)
- Audio file upload (MP3, WAV, M4A, OGG)
- Live audio recording in app
- Phone call recording upload
- Voice memo upload

**3. Meeting Recording Integration** (NEW - All)
- Zoom meeting file import
- Google Meet recording import
- Microsoft Teams recording import
- Generic video meeting file support

**4. Text/Transcript Inputs** (NEW - All)
- Transcript file upload (TXT, PDF, DOCX)
- Paste transcript directly into text box
- Manual text entry/editing
- Email content paste
- Notes input

**5. Photo Integration** (NEW - All)
- Photo file upload (JPG, PNG, HEIC)
- Take photos within app
- Photo with voice annotation
- Batch photo upload
- Photos embedded in scope output
- Photo captions/descriptions
- Link photos to specific scope items

**6. Mixed Media Projects** (NEW - All)
- Combine multiple input types in single project
- Video + photos + audio + notes
- Multiple files of same type (e.g., 3 videos + 10 photos)
- Unified analysis across all inputs

#### Processing Enhancements

**Universal Input Processing:**
- Auto-detect input type
- Route to appropriate transcription/parsing
- Combine multiple inputs into unified analysis
- Handle mixed media intelligently

**Enhanced AI Analysis:**
- Improved construction-expert prompt
- Better decision point identification
- Enhanced risk/concern flagging
- Missing scope item suggestions
- Scope completeness scoring (1-100)
- Conflict detection between scope items

**Custom Cost Code Support:**
- Client can input their own cost code system (not just TeamBuilders)
- Ability to map AI categories to client-specific codes
- Support for different code structures (2-digit, 4-digit, custom)
- Client code library storage

#### Output Improvements

**Professional Templates:**
- Multiple scope sheet templates (like JRAL Maintenance example)
- Template options:
  - Checkbox/timeline format
  - Trade-organized format
  - Narrative format
  - Custom client formats
- Client can select preferred template

**Enhanced Scope Output Structure:**
- Trade-organized sections (Plumbing, Electrical, Fit & Finish, etc.)
- Demolition vs. Construction timeline separation
- Checkbox format for tracking
- Enhanced detail fields:
  - More granular location tracking
  - Better quantity estimation
  - Material specification capture
  - Labor/trade requirements
  - Risk level indicators (low/medium/high)
  - Dependencies on other work

**Photo Integration in Output:**
- Photos embedded in relevant scope sections
- Photo captions/annotations
- Before/after photo organization
- Visual documentation throughout scope

**Enhanced Sections:**
- Improved Decision Points section
- Enhanced Concerns/Risks section
- Better Important Notes organization
- Project complexity assessment
- Coordination requirements

**Export Enhancements:**
- Better formatted PDFs
- Better formatted DOCX
- Excel/CSV export option
- Print-optimized versions
- Email delivery from app

#### Customization & Branding

**White-Label Capabilities:**
- Client logo upload and placement
- Custom primary color selection
- Custom company name
- Custom contact information
- Branded cover pages
- Custom footer information

**Template Customization:**
- Client can modify section names
- Add/remove sections
- Reorder sections
- Custom field additions
- Save custom templates

**Terminology Customization:**
- Client's preferred language/terms
- Custom category names
- Trade-specific terminology

---

### Phase 2: Collaboration & Workflow (Priority 2 - Build After Launch)

#### Multi-User Access
- Team member accounts per client
- Role-based permissions (Admin, Estimator, Viewer)
- User management interface
- Activity tracking

#### Review & Approval
- Comment/annotation system on scope items
- Internal team discussion
- Approval workflow (multi-stage review)
- Revision tracking and version history
- "Changes since last version" view

#### Client Portal
- Share scopes with property owners
- Client review and approval interface
- Client comment capability
- Branded client-facing experience
- Approval signatures/timestamps

---

### Phase 3: Advanced Features (Priority 3 - Build Based on Customer Demand)

#### Documentation & Evidence
- Full transcript with timestamps
- Video timestamp linking (click scope item → see video moment)
- Change order documentation (original vs. final scope comparison)
- Dispute evidence package export

#### Project Library & Intelligence
- Searchable project history
- Similar project suggestions
- Scope item library (reusable items)
- Project templates for common types
- Tagging and categorization

#### Analytics & Reporting
- Scope completeness metrics
- Common missed items analysis
- Estimator performance comparison
- Time savings tracking
- ROI calculation

#### Integration & API
- API access for custom integrations
- Webhook notifications
- Calendar integration
- Email system integration
- Export to estimating software formats

---

## TECHNICAL REQUIREMENTS

### Frontend (React + Tailwind)
- Mobile-responsive design (essential)
- Progressive Web App (PWA) capabilities
- Clean, professional UI
- Fast load times
- Intuitive navigation
- Real-time upload progress
- Error handling and user feedback
- Multi-file upload interface
- Drag-and-drop support
- Preview capabilities for uploads

### Backend (Python)
- Handle multiple file types
- Efficient transcription processing
- Scalable AI prompt processing
- Secure file storage
- Fast response times
- Error handling
- Rate limiting
- Database optimization

### Storage
- Secure file storage
- Client data isolation (multi-tenancy)
- Efficient retrieval
- Backup systems
- GDPR/privacy compliance

### AI/ML
- OpenAI GPT-4 integration
- Custom construction-expert prompts
- Prompt versioning
- Quality assurance on outputs
- Fallback handling

### Security
- User authentication
- Data encryption
- Client data separation
- Secure file upload
- HTTPS everywhere
- Compliance with construction industry standards

### Performance
- Fast upload handling
- Efficient transcription processing
- Quick scope generation (target: <5 minutes for 15-min video)
- Responsive UI
- Minimal downtime

---

## USER WORKFLOWS

### Workflow 1: Video Walkthrough Upload (Current)
1. User logs in
2. Clicks "Analyze Video" or "New Project"
3. Names project
4. Uploads video file
5. Waits for processing
6. Reviews generated scope
7. Downloads PDF/DOCX

### Workflow 2: Multi-Input Project (New)
1. User logs in
2. Creates new project
3. Names project and adds description
4. Uploads multiple files:
   - 2 walkthrough videos
   - 10 photos
   - 1 audio note
   - Pastes email from client with requirements
5. Clicks "Generate Scope"
6. System processes all inputs
7. Reviews unified scope with embedded photos
8. Makes edits/annotations
9. Selects template format
10. Downloads or shares with client

### Workflow 3: Quick Audio Scope (New)
1. User in field after client meeting
2. Opens app on phone
3. Records 5-minute voice memo summarizing discussion
4. Uploads 3 photos of site
5. Clicks "Generate Scope"
6. Receives scope within minutes
7. Reviews and sends to client same day

### Workflow 4: Meeting Recording Analysis (New)
1. User conducts Zoom pre-construction meeting
2. Downloads Zoom recording
3. Uploads to app
4. Selects "Meeting Recording" type
5. System transcribes and analyzes
6. Generates scope from discussion
7. Reviews for accuracy
8. Shares with attendees for confirmation

---

## OUTPUT EXAMPLES

### Required Output Format (Based on JRAL Maintenance Example)

**Cover Page:**
- Project title: "Scope of Work - [Date]"
- Project address
- Client/GC branding:
  - Company logo
  - Company name
  - Company address
  - Company phone
- Prepared by information
- Date

**Overview Section:**
- Narrative project description
- Key project parameters
- Photos (4-6 relevant images)

**Project Summary:**
- Overview paragraph
- Key Requirements (bulleted list)
- Concerns (bulleted list, color-coded warning)
- Decision Points (bulleted list, color-coded info)
- Important Notes (bulleted list, color-coded neutral)

**Scope of Work Sections:**

**Demolition Timeline:**
- Checkbox list of demolition items
- Clear, actionable descriptions

**Construction Timeline:**
Organized by area/room with tables:

| Plumbing | Electrical | Fit & Finish |
|----------|------------|--------------|
| Detailed scope | Detailed scope | Detailed scope |
| Materials specified | Materials specified | Materials specified |
| Quantities | Quantities | Quantities |

**Additional Scope Items:**
- Checkbox list format
- Grouped logically
- Clear descriptions

**Notes Section:**
- Additional considerations
- Special instructions

**Professional Formatting:**
- Clean, readable typography
- Consistent spacing
- Professional color scheme
- Page breaks at logical points
- Headers/footers with project info

---

## SUCCESS METRICS

### Product Success
- User can create comprehensive scope from ANY input format
- Processing time < 5 minutes for typical project
- Scope completeness score > 85/100 average
- User satisfaction with output quality > 90%

### Business Success
- Time savings: 2+ hours per scope (vs manual process)
- 10 paying customers in first 30 days
- < 10% monthly churn rate
- Customer reports measurable reduction in scope disputes

### Technical Success
- 99.5% uptime
- Fast upload/processing times
- Zero data loss
- Secure multi-tenant operation

---

## CONSTRAINTS & ASSUMPTIONS

### Constraints
- Budget: Bootstrap/self-funded (no VC money)
- Timeline: Launch-ready in 30 days
- Team: Solo developer + sales partner
- Must work with existing tech stack (React, Python, Render, Supabase)

### Assumptions
- Target customers have internet access
- Target customers can record video/audio on phones
- Customers willing to pay $497-997/month
- Construction industry will adopt AI tools
- Scope disputes cost more than subscription

---

## PRIORITIZATION FRAMEWORK

### Must Have (Phase 1 - Build Now)
Features required to launch and sell:
- Multi-input support (video, audio, photos, text)
- Professional scope output with photos
- Custom cost codes
- White-label branding
- Multiple templates
- PDF/DOCX export

### Should Have (Phase 2 - Build Month 2-3)
Features that improve retention:
- Multi-user collaboration
- Scope comparison tools
- Client portal
- Revision tracking

### Could Have (Phase 3 - Build Month 4+)
Features that justify premium pricing:
- Advanced analytics
- API integration
- Historical project intelligence
- Mobile native app

### Won't Have (Not Building)
Out of scope:
- Pricing/estimating features
- Project management tools
- Accounting integration
- Time tracking
- Bid management

---

## COMPARISON INSTRUCTIONS FOR CLAUDE CODE

**Please analyze the existing codebase and compare against this PRD:**

1. **What EXISTS and WORKS:**
   - List all features from "CURRENT STATE" that are present
   - Confirm functionality matches description
   - Note any differences from described behavior

2. **What's PARTIALLY IMPLEMENTED:**
   - Features that exist but need enhancement
   - Incomplete implementations
   - Areas needing polish

3. **What's MISSING (Priority 1):**
   - Features in "Phase 1" that don't exist yet
   - Critical gaps for launch readiness
   - Must-build items for market viability

4. **What's MISSING (Priority 2-3):**
   - Features in later phases
   - Future enhancements
   - Nice-to-haves

5. **Technical Debt & Issues:**
   - Code quality concerns
   - Performance bottlenecks
   - Security vulnerabilities
   - Scalability issues

6. **Architecture Assessment:**
   - Current architecture vs. requirements
   - Multi-tenancy readiness
   - File handling capability
   - Database schema adequacy

7. **Development Recommendations:**
   - What to build first
   - What to refactor
   - What to leave as-is
   - Estimated effort for gaps

**Please provide:**
- Feature completion percentage
- Critical path to launch (what MUST be built)
- Quick wins (high value, low effort)
- Technical risks
- Build time estimates for Phase 1 features