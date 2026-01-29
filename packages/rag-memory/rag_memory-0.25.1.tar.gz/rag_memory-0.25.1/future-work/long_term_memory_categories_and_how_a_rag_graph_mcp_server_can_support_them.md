# Long‑Term Memory Categories (Agent Design) and How a Vector+Graph MCP Knowledge Base Can Support Them

## Goal of this note
Provide a shared vocabulary for **long‑term memory** in AI agents, with **clear examples** and **how a general MCP knowledge base** (vector similarity + temporal/relationship graph + collections) can support each category. This is **not** a solution spec—use it to evaluate your MCP server’s existing capabilities and gaps.

---

## Mental model: “Memory” = persistent knowledge + retrieval behaviors
In agent systems, “memory” typically means **durable information** that can be retrieved later to improve decisions, personalization, continuity, and execution. Different memory categories differ mainly by:
- **What is stored** (facts, events, procedures, preferences)
- **How it is retrieved** (semantic similarity, entity/relationship, temporal)
- **How it is used** (recall, planning, policy enforcement, personalization)

Your MCP server already provides three powerful primitives:
1) **Document storage** (canonical source docs)
2) **Vector similarity search** (semantic recall)
3) **Knowledge graph queries** (entity/relationship + temporal reasoning)
4) **Collections** (partitioning + scoping)

---

## Categories of long‑term memory (with crisp examples)

### 1) Semantic memory (facts / knowledge)
**What it is:** Stable knowledge about the world or your org.

**Example:** “Our billing system uses Stripe; invoices are generated in Service X; refund policy is 14 days.”

**How MCP can support it:**
- Store authoritative docs (policies, architecture notes, product docs) as documents.
- Retrieve via **semantic similarity** for “what is our refund policy?”
- Use **graph** to connect entities (Stripe ↔ billing service ↔ refund policy) and answer multi-hop questions.

---

### 2) Episodic memory (events / what happened, when, and with whom)
**What it is:** Time-bounded experiences, decisions, meetings, incidents, outcomes.

**Example:** “On 2025‑11‑12 we decided to deprecate Feature A because of churn; rollback plan agreed with Ops.”

**How MCP can support it:**
- Ingest meeting notes, decision logs, incident reports.
- Use **temporal graph** fields (valid_from/valid_until, superseded/current) to track knowledge evolution.
- Retrieve with: “What did we decide about Feature A last quarter?” (time + entities + similarity).

---

### 3) Procedural memory (how to do things / SOPs)
**What it is:** Step-by-step procedures, playbooks, runbooks, checklists.

**Example:** “How we deploy: run tests → bump version → tag release → roll to staging → validate → production.”

**How MCP can support it:**
- Store SOP docs as documents; optionally chunk for step-level retrieval.
- Graph can represent relationships like Procedure ↔ System ↔ Tool ↔ Preconditions.
- Retrieval: semantic (“How do we cut a release?”) + relationship (“Which procedures touch payments?”).

---

### 4) Preference / profile memory (stable personal or org preferences)
**What it is:** Reusable preferences, constraints, style, principles.

**Example:** “Prefer Postgres over Mongo for transactional systems; use IaC; keep prompts as schemas.”

**How MCP can support it:**
- Store “principles” and “preferences” as documents (short notes are fine).
- Similarity search for “What do we prefer for DB choices?”
- Graph can attach preferences to entities (DB → Postgres preference; Tooling → Terraform).

---

### 5) Identity / mission memory (purpose and goals)
**What it is:** Mission, vision, positioning, business goals, north-star metrics.

**Example:** “Mission: teach engineers AI-native workflows responsibly; success metric: cohort completion + retention.”

**How MCP can support it:**
- Store mission/vision docs and strategy notes.
- Retrieval: “Given our mission, how should we frame this course module?”
- Graph: Mission ↔ Products ↔ Audience ↔ Messaging.

---

### 6) Decision memory (why a decision was made)
**What it is:** Rationale, tradeoffs, alternatives considered, constraints at the time.

**Example:** “Chose pgvector over X for simplicity; accepted recall tradeoff for ops reliability.”

**How MCP can support it:**
- Ingest ADRs / decision logs as documents.
- Graph connects Decision ↔ Alternatives ↔ Constraints ↔ Consequences.
- Temporal graph captures when a decision becomes superseded.

---

### 7) Task / commitment memory (open loops)
**What it is:** Actionable commitments and reminders (often time-sensitive).

**Example:** “Follow up with vendor next Tuesday; renew certificate before 2026‑02‑01.”

**How MCP can support it (as a knowledge base):**
- Store tasks as documents or structured notes; graph can attach due dates/relationships.
- Temporal query: “What commitments are due this week?”
- (Note: notifications/scheduling usually live outside the KB; the KB provides retrieval + state.)

---

### 8) Social / relationship memory (people context)
**What it is:** People profiles, relationships, prior interactions, commitments.

**Example:** “Alice prefers async updates; last spoke about onboarding pain; follow up about feature request.”

**How MCP can support it:**
- Ingest lightweight person notes.
- Graph: Person ↔ Projects ↔ Topics ↔ Follow-ups.
- Retrieval: “What should I remember before meeting Alice?” (person entity pivot + recency).

---

## How “collections” fit (partitioning strategy)
Collections are primarily:
- **A scoping mechanism** (limit retrieval to relevant domains)
- **A governance mechanism** (separate business vs personal vs client vs public docs)
- **A quality/safety boundary** (reduce accidental leakage across contexts)

Collections do **not** need to be universally standardized across users.
What matters is that each collection has:
- A **description** (human intent)
- A **domain_scope** (what belongs / what doesn’t)
- Enough metadata to help routing and retrieval

---

## How a general MCP KB could serve these memory types (non-prescriptive)
Your MCP server can plausibly serve as a **universal long‑term memory substrate** if:
- Documents can represent each memory category (facts, events, SOPs, preferences, decisions).
- Retrieval supports multiple modes:
  - **Similarity** for semantic recall and fuzzy prompts
  - **Graph** for entity pivots and multi-hop reasoning
  - **Temporal** for “when/what changed”
- Collections provide scoping and governance.

Key “fit checks” (for the coding assistant to assess in the codebase):
1) **Can every memory category be represented as a document type + metadata?**
2) **Do retrieval APIs allow scoping by collection and optionally global search?**
3) **Do graph queries provide enough linkage back to source documents to explain/justify answers?**
4) **Is there a clear path to store ‘events’ and their time validity (current vs superseded)?**
5) **Does ingestion support URLs, files, directories, and short notes uniformly?**

---

## Practical examples (mapping category → retrieval mode)
- “What’s our refund policy?” → Semantic memory → **Similarity** + optionally graph entity pivot
- “What did we decide about Feature A last quarter?” → Episodic/Decision memory → **Temporal graph** + similarity
- “How do we deploy?” → Procedural memory → **Similarity** (step-level chunks) + graph links to systems/tools
- “What DB do we prefer and why?” → Preference + Decision memory → **Similarity** + graph to ADRs
- “What commitments are due this week?” → Task memory → **Temporal query** (if dates modeled) + collection scoping

---

## What this document intentionally does NOT do
- It does not prescribe your trust/review/eval schema.
- It does not prescribe how the agent routes content into collections.
- It does not prescribe a specific taxonomy of collections.

Use it to evaluate whether the MCP server’s primitives (documents + vectors + graph + collections) are sufficient to implement these memory behaviors across many users.

