# MCP Server Changes – Evaluation, Review, KG Integration

## Purpose
This document defines **what must change in the MCP server / RAG memory system**. It intentionally excludes agent behavior, prompts, routing logic, or UI workflows. This is the *irreversible* part of the design, so it focuses only on durable storage semantics and server responsibilities.

---

## Core Decisions (Locked In)

1. **No trust system** (no `trusted/untrusted`, no promotion, no policy-based trust).
2. **One human signal only**: `reviewed_by_human` (boolean).
3. **LLM evaluation is universal and separate** from human review.
4. **Knowledge Graph stores no new interpretive or aggregate metrics**.

---

## Document-Level Schema Changes (PostgreSQL)

### Add the following fields to `source_documents`

### Human review flag
- `reviewed_by_human` (boolean, default: `false`)
- Meaning: *A human explicitly confirmed this document is useful for its collection.*
- Does NOT imply correctness, authority, or factual accuracy.

### LLM evaluation metadata (always produced)
These fields are written for **every ingest type** (URL, file, directory, raw text):

- `eval_relevance_score` (float 0.0–1.0)
- `eval_quality_score` (float 0.0–1.0)
- `eval_summary` (short text)
- `eval_recommendation` (`ingest | review | skip`)
- `eval_topic` (string used during evaluation)
- `eval_model` (string)
- `eval_timestamp` (datetime)

---

## LLM Evaluation Rules (Server-Side)

- An LLM evaluation runs for **every ingest**.
- A **dry run**:
  - Runs the same evaluation logic
  - Returns evaluation results to the caller
  - Does NOT persist content or documents
- A **real ingest**:
  - Persists content
  - Persists all evaluation fields listed above

### What evaluation is used for
- Filtering and ranking in vector search
- Diagnostic / explanatory signals for callers

### What evaluation is NOT used for
- It does NOT set or infer `reviewed_by_human`
- It does NOT block ingestion
- It does NOT create trust or authority semantics

---

## Knowledge Graph Integration (Graphiti)

### What stays unchanged
- Each document creates one Graphiti Episode (`doc_{id}`)
- Entity nodes are deduplicated
- Edges reference contributing episode UUIDs

### What we explicitly add
- **Nothing is persisted on edges**

### Optional KG query behavior
KG query endpoints MAY support an optional parameter (e.g., `include_source_docs=true`).

If enabled:
- Return the list of contributing **document IDs** derived from episodes
- Do NOT compute or store:
  - averages
  - ratios
  - confidence scores
  - quality metrics

All interpretation happens outside the MCP server.

---

## UI / Admin Storage Capabilities (Server Only)

- MCP server must allow:
  - Reading `reviewed_by_human`
  - Updating `reviewed_by_human`
- Deleting a document replaces any notion of rejection

---

## What We Explicitly Will NOT Implement

- No `trust_state`, `trusted`, `untrusted`, or promotion workflows
- No KG edge-level quality, confidence, or support metrics
- No server-side filtering of KG edges by evaluation scores
- No automatic changes to `reviewed_by_human`

---

## Design Principle (Non-Negotiable)

> **Persist only primitive facts that are durable and hard to regret.**

Anything interpretive or policy-driven must be computed by consumers (agents/UI), not baked into the MCP server.

