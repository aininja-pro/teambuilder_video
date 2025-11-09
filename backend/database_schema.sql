-- =====================================================
-- GC Video Scope Analyzer - Database Schema
-- Multi-tenant SaaS application with Row Level Security
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- CLIENTS TABLE
-- Stores white-label client/organization information
-- =====================================================
CREATE TABLE clients (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  logo_url TEXT,
  primary_color TEXT DEFAULT '#000000',
  secondary_color TEXT DEFAULT '#4B5563',
  accent_color TEXT DEFAULT '#10B981',
  company_address TEXT,
  company_phone TEXT,
  company_email TEXT,
  footer_text TEXT,
  cost_codes JSONB DEFAULT '[]'::jsonb,  -- Array of custom cost code objects
  default_template TEXT DEFAULT 'jral',  -- jral, trade, narrative
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for active clients
CREATE INDEX idx_clients_active ON clients(is_active);

-- =====================================================
-- USER_CLIENTS TABLE
-- Many-to-many relationship between users and clients
-- Supports multi-user organizations (Phase 2)
-- =====================================================
CREATE TABLE user_clients (
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
  role TEXT DEFAULT 'admin' CHECK (role IN ('admin', 'estimator', 'viewer')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (user_id, client_id)
);

-- Index for quick user lookup
CREATE INDEX idx_user_clients_user ON user_clients(user_id);
CREATE INDEX idx_user_clients_client ON user_clients(client_id);

-- =====================================================
-- PROJECTS TABLE
-- Container for multi-input analyses
-- =====================================================
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  client_id UUID REFERENCES clients(id) ON DELETE CASCADE NOT NULL,
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  name TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'processing', 'completed', 'failed')),
  template_type TEXT DEFAULT 'jral' CHECK (template_type IN ('jral', 'trade', 'narrative')),
  processing_started_at TIMESTAMPTZ,
  processing_completed_at TIMESTAMPTZ,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for queries
CREATE INDEX idx_projects_client ON projects(client_id);
CREATE INDEX idx_projects_user ON projects(user_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_created ON projects(created_at DESC);

-- =====================================================
-- PROJECT_FILES TABLE
-- Stores metadata for all uploaded files (multi-input)
-- =====================================================
CREATE TABLE project_files (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
  file_type TEXT NOT NULL CHECK (file_type IN ('video', 'audio', 'photo', 'text')),
  file_url TEXT NOT NULL,  -- Supabase Storage URL
  file_name TEXT NOT NULL,
  file_size_mb NUMERIC(10, 2),
  mime_type TEXT,
  duration_seconds INTEGER,  -- For audio/video files
  uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_project_files_project ON project_files(project_id);
CREATE INDEX idx_project_files_type ON project_files(file_type);

-- =====================================================
-- ANALYSES TABLE
-- Stores AI processing results
-- =====================================================
CREATE TABLE analyses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE NOT NULL,

  -- AI Results
  transcript TEXT,  -- Combined transcript from all audio/video
  project_summary JSONB,  -- {overview, keyRequirements, concerns, decisionPoints, importantNotes}
  scope_items JSONB,  -- Array of scope item objects with cost codes
  scope_completeness_score INTEGER CHECK (scope_completeness_score BETWEEN 0 AND 100),

  -- Metadata
  processing_time_seconds INTEGER,
  ai_cost_usd NUMERIC(10, 4),
  ai_provider_metadata JSONB,  -- Store AssemblyAI/Claude response details

  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_analyses_project ON analyses(project_id);
CREATE INDEX idx_analyses_created ON analyses(created_at DESC);

-- GIN index for JSONB searching
CREATE INDEX idx_analyses_scope_items ON analyses USING GIN(scope_items);
CREATE INDEX idx_analyses_project_summary ON analyses USING GIN(project_summary);

-- =====================================================
-- DOCUMENTS TABLE
-- Stores generated document outputs
-- =====================================================
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  analysis_id UUID REFERENCES analyses(id) ON DELETE CASCADE NOT NULL,
  document_type TEXT NOT NULL CHECK (document_type IN ('docx', 'pdf')),
  file_url TEXT NOT NULL,  -- Supabase Storage URL
  file_name TEXT NOT NULL,
  file_size_mb NUMERIC(10, 2),
  template_used TEXT NOT NULL CHECK (template_used IN ('jral', 'trade', 'narrative')),
  generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_documents_analysis ON documents(analysis_id);
CREATE INDEX idx_documents_type ON documents(document_type);

-- =====================================================
-- PHOTO_ANNOTATIONS TABLE
-- Links photos to scope items with AI analysis
-- =====================================================
CREATE TABLE photo_annotations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_file_id UUID REFERENCES project_files(id) ON DELETE CASCADE NOT NULL,
  analysis_id UUID REFERENCES analyses(id) ON DELETE CASCADE NOT NULL,

  caption TEXT,  -- AI-generated caption
  scope_category TEXT,  -- Which cost code category this relates to
  ai_analysis JSONB,  -- {materials: [], conditions: [], risks: []}

  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_photo_annotations_file ON photo_annotations(project_file_id);
CREATE INDEX idx_photo_annotations_analysis ON photo_annotations(analysis_id);
CREATE INDEX idx_photo_annotations_category ON photo_annotations(scope_category);

-- =====================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- Multi-tenant data isolation
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE photo_annotations ENABLE ROW LEVEL SECURITY;

-- CLIENTS POLICIES
-- Users can only see clients they belong to
CREATE POLICY "Users see own clients" ON clients
  FOR SELECT USING (
    id IN (
      SELECT client_id FROM user_clients WHERE user_id = auth.uid()
    )
  );

-- Only admins can update client settings
CREATE POLICY "Admins can update clients" ON clients
  FOR UPDATE USING (
    id IN (
      SELECT client_id FROM user_clients
      WHERE user_id = auth.uid() AND role = 'admin'
    )
  );

-- USER_CLIENTS POLICIES
CREATE POLICY "Users see own relationships" ON user_clients
  FOR SELECT USING (user_id = auth.uid());

-- PROJECTS POLICIES
-- Users can only see projects for their clients
CREATE POLICY "Users see own client projects" ON projects
  FOR SELECT USING (
    client_id IN (
      SELECT client_id FROM user_clients WHERE user_id = auth.uid()
    )
  );

-- Users can create projects for their clients
CREATE POLICY "Users can create projects" ON projects
  FOR INSERT WITH CHECK (
    client_id IN (
      SELECT client_id FROM user_clients WHERE user_id = auth.uid()
    )
  );

-- Users can update their own projects
CREATE POLICY "Users can update own projects" ON projects
  FOR UPDATE USING (
    client_id IN (
      SELECT client_id FROM user_clients WHERE user_id = auth.uid()
    )
  );

-- Users can delete their own projects
CREATE POLICY "Users can delete own projects" ON projects
  FOR DELETE USING (
    client_id IN (
      SELECT client_id FROM user_clients WHERE user_id = auth.uid()
    )
  );

-- PROJECT_FILES POLICIES
CREATE POLICY "Users see files for own projects" ON project_files
  FOR SELECT USING (
    project_id IN (
      SELECT id FROM projects WHERE client_id IN (
        SELECT client_id FROM user_clients WHERE user_id = auth.uid()
      )
    )
  );

CREATE POLICY "Users can upload files" ON project_files
  FOR INSERT WITH CHECK (
    project_id IN (
      SELECT id FROM projects WHERE client_id IN (
        SELECT client_id FROM user_clients WHERE user_id = auth.uid()
      )
    )
  );

CREATE POLICY "Users can delete files" ON project_files
  FOR DELETE USING (
    project_id IN (
      SELECT id FROM projects WHERE client_id IN (
        SELECT client_id FROM user_clients WHERE user_id = auth.uid()
      )
    )
  );

-- ANALYSES POLICIES
CREATE POLICY "Users see analyses for own projects" ON analyses
  FOR SELECT USING (
    project_id IN (
      SELECT id FROM projects WHERE client_id IN (
        SELECT client_id FROM user_clients WHERE user_id = auth.uid()
      )
    )
  );

CREATE POLICY "System can create analyses" ON analyses
  FOR INSERT WITH CHECK (true);

-- DOCUMENTS POLICIES
CREATE POLICY "Users see documents for own analyses" ON documents
  FOR SELECT USING (
    analysis_id IN (
      SELECT a.id FROM analyses a
      JOIN projects p ON a.project_id = p.id
      WHERE p.client_id IN (
        SELECT client_id FROM user_clients WHERE user_id = auth.uid()
      )
    )
  );

CREATE POLICY "System can create documents" ON documents
  FOR INSERT WITH CHECK (true);

-- PHOTO_ANNOTATIONS POLICIES
CREATE POLICY "Users see annotations for own analyses" ON photo_annotations
  FOR SELECT USING (
    analysis_id IN (
      SELECT a.id FROM analyses a
      JOIN projects p ON a.project_id = p.id
      WHERE p.client_id IN (
        SELECT client_id FROM user_clients WHERE user_id = auth.uid()
      )
    )
  );

CREATE POLICY "System can create annotations" ON photo_annotations
  FOR INSERT WITH CHECK (true);

-- =====================================================
-- STORAGE BUCKETS
-- Configure Supabase Storage buckets (run in Supabase dashboard)
-- =====================================================

-- Uploads bucket (for video, audio, photos, text files)
-- INSERT INTO storage.buckets (id, name, public) VALUES ('uploads', 'uploads', false);

-- Documents bucket (for generated DOCX/PDF)
-- INSERT INTO storage.buckets (id, name, public) VALUES ('documents', 'documents', false);

-- Logos bucket (for client logos)
-- INSERT INTO storage.buckets (id, name, public) VALUES ('logos', 'logos', false);

-- =====================================================
-- FUNCTIONS & TRIGGERS
-- Automatic timestamp updates
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for clients table
CREATE TRIGGER update_clients_updated_at
BEFORE UPDATE ON clients
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Trigger for projects table
CREATE TRIGGER update_projects_updated_at
BEFORE UPDATE ON projects
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- SEED DATA
-- Insert default TeamBuilders cost codes as a template
-- =====================================================

-- Note: This will be inserted via the application when creating first client
-- Example cost codes structure:
-- [
--   {"code": "01", "name": "General Conditions", "subcodes": []},
--   {"code": "02", "name": "Site Preparation / Demolition", "subcodes": []},
--   ... etc
-- ]

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- Additional indexes for common queries
-- =====================================================

-- Composite index for project listing by client
CREATE INDEX idx_projects_client_created ON projects(client_id, created_at DESC);

-- Index for finding files by project and type
CREATE INDEX idx_project_files_project_type ON project_files(project_id, file_type);

-- Index for finding analyses by project
CREATE INDEX idx_analyses_project_created ON analyses(project_id, created_at DESC);

-- =====================================================
-- COMMENTS
-- Add helpful comments to tables and columns
-- =====================================================

COMMENT ON TABLE clients IS 'White-label client organizations with branding and cost codes';
COMMENT ON TABLE user_clients IS 'Many-to-many relationship between users and clients';
COMMENT ON TABLE projects IS 'Container for multi-input scope analysis projects';
COMMENT ON TABLE project_files IS 'Metadata for uploaded files (video, audio, photos, text)';
COMMENT ON TABLE analyses IS 'AI-generated scope analysis results';
COMMENT ON TABLE documents IS 'Generated DOCX and PDF documents';
COMMENT ON TABLE photo_annotations IS 'AI analysis of photos linked to scope categories';

COMMENT ON COLUMN clients.cost_codes IS 'JSONB array of custom cost code objects';
COMMENT ON COLUMN projects.status IS 'Project status: draft, processing, completed, failed';
COMMENT ON COLUMN projects.template_type IS 'Output template: jral, trade, narrative';
COMMENT ON COLUMN project_files.file_type IS 'File type: video, audio, photo, text';
COMMENT ON COLUMN analyses.scope_items IS 'JSONB array of scope item objects with cost codes';
COMMENT ON COLUMN analyses.project_summary IS 'JSONB with overview, keyRequirements, concerns, decisionPoints, notes';
COMMENT ON COLUMN photo_annotations.ai_analysis IS 'JSONB with materials, conditions, risks arrays';
