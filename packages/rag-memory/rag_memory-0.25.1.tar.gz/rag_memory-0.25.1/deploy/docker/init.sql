-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Collection management table
CREATE TABLE collections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    metadata_schema JSONB NOT NULL DEFAULT '{"custom": {}, "system": []}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Source documents table (stores full documents before chunking)
CREATE TABLE source_documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    file_type VARCHAR(50),
    file_size INTEGER,
    metadata JSONB DEFAULT '{}',
    -- Human review flag (set only on explicit user confirmation)
    reviewed_by_human BOOLEAN NOT NULL DEFAULT FALSE,
    -- LLM evaluation fields (always populated on every ingest)
    quality_score DECIMAL(4,3),              -- 0.000-1.000
    quality_summary TEXT,
    -- Topic relevance (only when caller provides topic, NULL otherwise)
    topic_relevance_score DECIMAL(4,3),      -- 0.000-1.000, NULL if no topic
    topic_relevance_summary TEXT,             -- NULL if no topic
    topic_provided TEXT,                      -- The topic caller provided for evaluation, NULL if none
    -- Evaluation metadata
    eval_model VARCHAR(100),
    eval_timestamp TIMESTAMP,
    -- Content hash for duplicate detection (SHA256 of content)
    content_hash VARCHAR(64),
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for filtering
CREATE INDEX source_documents_reviewed_idx ON source_documents(reviewed_by_human);
CREATE INDEX source_documents_quality_idx ON source_documents(quality_score);
CREATE INDEX source_documents_topic_relevance_idx ON source_documents(topic_relevance_score);
CREATE INDEX idx_source_documents_content_hash ON source_documents(content_hash);

-- Document chunks table (stores chunks for vector search)
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    source_document_id INTEGER REFERENCES source_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    char_start INTEGER,
    char_end INTEGER,
    metadata JSONB DEFAULT '{}',
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_document_id, chunk_index)
);

-- Chunk-collection relationship
CREATE TABLE chunk_collections (
    chunk_id INTEGER REFERENCES document_chunks(id) ON DELETE CASCADE,
    collection_id INTEGER REFERENCES collections(id) ON DELETE CASCADE,
    PRIMARY KEY (chunk_id, collection_id)
);

-- HNSW index for chunk embeddings
CREATE INDEX document_chunks_embedding_idx ON document_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Index for chunk lookups
CREATE INDEX document_chunks_source_idx ON document_chunks(source_document_id);

-- Index for chunk metadata queries
CREATE INDEX document_chunks_metadata_idx ON document_chunks USING gin (metadata);

-- Trigger for source_documents updated_at
CREATE TRIGGER update_source_documents_updated_at
    BEFORE UPDATE ON source_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Ingest audit log table (append-only audit trail for all ingestion operations)
-- Records "what happened" - provenance ledger, NOT a trust system
CREATE TABLE ingest_audit_log (
    id SERIAL PRIMARY KEY,
    source_document_id INTEGER REFERENCES source_documents(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    -- Actor identification
    actor_type VARCHAR(50) NOT NULL,
    actor_id VARCHAR(255),
    -- Ingestion details
    ingest_method VARCHAR(50) NOT NULL,
    collection_name VARCHAR(255) NOT NULL,
    -- Dry run tracking
    dry_run_performed BOOLEAN NOT NULL DEFAULT FALSE,
    dry_run_recommendation VARCHAR(20),
    dry_run_score DECIMAL(3,2),
    dry_run_summary TEXT,
    -- Provenance: "model recommended skip but user proceeded"
    user_override BOOLEAN NOT NULL DEFAULT FALSE,
    -- Source information
    mcp_server_version VARCHAR(50),
    source_url TEXT,
    source_file_path TEXT,
    -- Extensible metadata (can store evaluation object here)
    metadata JSONB DEFAULT '{}',
    -- Constraints
    CONSTRAINT audit_actor_type_valid CHECK (actor_type IN ('user', 'agent', 'api')),
    CONSTRAINT audit_ingest_method_valid CHECK (ingest_method IN ('text', 'file', 'directory', 'url')),
    CONSTRAINT audit_dry_run_recommendation_valid CHECK (dry_run_recommendation IS NULL OR dry_run_recommendation IN ('ingest', 'review', 'skip'))
);

-- Indexes for audit log queries
CREATE INDEX ingest_audit_log_doc_idx ON ingest_audit_log(source_document_id);
CREATE INDEX ingest_audit_log_collection_idx ON ingest_audit_log(collection_name);
CREATE INDEX ingest_audit_log_created_idx ON ingest_audit_log(created_at DESC);
