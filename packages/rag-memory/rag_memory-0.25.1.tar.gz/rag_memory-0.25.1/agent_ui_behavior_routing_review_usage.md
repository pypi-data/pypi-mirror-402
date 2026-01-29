# Agent & UI Behavior – Routing, Review, Usage

## Purpose
This document defines **expected agent and UI behavior** when interacting with the MCP server. It does NOT describe MCP server implementation details.

---

## Routing Behavior (Agent Responsibility)

### Normal path (expected ~99%)
1. Agent receives user intent (thought, URLs, files, directory).
2. Agent selects an existing collection using:
   - collection description
   - domain / domain_scope
   - user intent
3. Agent ingests content directly into that collection.

### Exception path (rare)
- If the agent cannot confidently select a collection:
  - Ask the user which collection to use, OR
  - Route into a single fixed fallback collection: **Unsorted**

Rules:
- Agent must NEVER create collections automatically.
- Unsorted is an exception, not a default.

---

## Human Review Semantics

### Reviewed by human
- Means: *A human explicitly confirmed this document is useful for its collection.*
- This may happen:
  - At ingest time (explicit confirmation)
  - Later, via UI toggle

### Not reviewed by human
- Default state for all ingested content
- Content remains searchable and usable

The agent must not infer review status.

---

## How Agents Use Review Status

- Default queries: include both reviewed and not-reviewed content
- Strict / canonical queries: filter to `reviewed_by_human=true`
- Ranking: reviewed content may be boosted

Review status is a **filtering/ranking signal**, not a truth claim.

---

## Use of LLM Evaluation Signals

Agents may use LLM evaluation fields to:
- Explain why a document was included
- Rank results
- Decide whether to ask the user for confirmation

Agents must NOT:
- Convert eval scores into trust
- Treat eval scores as correctness

---

## Knowledge Graph Usage

- KG queries return relationships.
- If source documents are requested:
  - Agent fetches document metadata separately
  - Agent may explain or rank relationships using document eval + review status

Agents should not assume KG edges are authoritative.

---

## UI Expectations

- UI must expose:
  - `reviewed_by_human` toggle
  - Document evaluation metadata
- Deleting a document is the only way to discard content

---

## Design Principle

> **Agents route; humans review; the system remembers facts without pretending to know truth.**

