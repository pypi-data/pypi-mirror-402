# Agent Collection Scaffolding & Routing Guide

## Purpose of This Document
This document is guidance **for an AI coding assistant and future agent designers**, not an implementation spec.

Its goal is to explain:
- A **universal starter set of collections** for a RAG memory MCP server
- **Optional extensions** (e.g. business ownership)
- The *intent* behind each collection (why it exists)
- How an agent should reason about **routing**, **fallbacks**, and **evolution over time**

This is designed to work with:
- Vector-based similarity search
- Knowledge graph (temporal + relational) storage
- Collection-based partitioning

It deliberately avoids prescribing schemas, database changes, or tool APIs.

---

## Core Design Principles

1. **Capture first, decide later**
   - The system must never block capture due to uncertainty

2. **Collections reflect intent, not topic**
   - Collections answer *"why is this being stored?"*, not *"what is it about?"*

3. **Routing should be confident most of the time**
   - When confidence is low, use a safe fallback

4. **Structure must be easy to change**
   - Documents can move between collections over time

5. **This is a starter scaffold, not a permanent ontology**

---

## Universal Base Collections (Created for All Users)

These collections should be created by default for *any* new user, regardless of role (employee, student, creator, etc.).

### 1. Inbox / Unsorted
**Purpose:** Frictionless capture with no decision required

**Use cases:**
- Quick thoughts
- "Save this for later"
- Agent uncertainty during routing
- Auto-ingested content not yet reviewed

**Routing rule:**
- If the agent is unsure → route here

---

### 2. Ideas & Exploration
**Purpose:** Early-stage thinking that may become something later

**Use cases:**
- Ideas for projects, courses, products
- Things to research or explore
- "What if" thinking

**Routing signal:**
- Future-oriented
- No commitment or next steps yet

---

### 3. Projects
**Purpose:** Things the user is actively working on or planning to deliver

**Use cases:**
- Work initiatives
- Personal goals with momentum
- Courses being built
- Active repositories

**Routing signal:**
- Clear intent + trajectory

---

### 4. Ways of Working & Procedures
**Purpose:** How the user actually does things

**Use cases:**
- SOPs
- AI-native workflows
- Teaching methods
- "This is how I do X now"

**Routing signal:**
- Repeatable, instructional, operational knowledge

---

### 5. Decisions & Preferences
**Purpose:** Durable choices the user does not want to revisit

**Use cases:**
- Tech stack decisions
- Tooling preferences
- Constraints and tradeoffs
- "We decided this, and here’s why"

**Routing signal:**
- Declarative, authoritative statements

---

### 6. Knowledge & Reference
**Purpose:** External knowledge deliberately retained

**Use cases:**
- Official documentation (URLs)
- API references
- Tutorials
- Research material
- Synced GitHub repository knowledge

**Routing signal:**
- Reference material, not personal opinion

---

### 7. Personal Life & Reflections
**Purpose:** Non-work human context

**Use cases:**
- Memories
- Life planning
- Reflections
- Personal notes

**Routing signal:**
- Not work-related

---

### 8. Personal Finance & Admin
**Purpose:** Personal money and life logistics

**Use cases:**
- Banking
- Benefits (HSA, etc.)
- Budgets
- Subscriptions
- Financial exports

---

## Optional Extension: Business Owner

Only create this collection **if the user explicitly indicates they run a business**.

### Business Finance & Operations
**Purpose:** Business systems and operational reality

**Use cases:**
- Accounting software knowledge
- Financial reports and exports
- Categorization logic
- Internal ops knowledge
- High-level client context

**Important:**
- Do **not** assume this applies to all users

---

## Collection Naming Guidance

- Names should be:
  - Short
  - Human-readable
  - Clear at a glance

Examples are titles, not identifiers. Spaces and punctuation are fine.

---

## Domain & Domain Scope Guidance

Each collection should have:
- A **domain**: a short label for the broad area
- A **domain scope**: 1–2 sentences describing what belongs *and what does not*

These are:
- Stable context
- Used for explanation and reasoning
- Not strict enforcement mechanisms

---

## Routing Guidance for Agents

### Default routing behavior

1. Attempt to route confidently based on intent
2. If confidence is high → route directly
3. If confidence is low → route to **Inbox / Unsorted**

### Important rules
- Do **not** create new collections automatically
- Do **not** over-ask the user
- Prefer safe capture over perfect classification

---

## Evolution Over Time

Agents should assume:
- Users will move documents later
- Collections may be split or renamed
- The initial scaffold is temporary

This system is designed to **adapt**, not to be correct on day one.

---

## Summary

This collection scaffold:
- Works for individuals and professionals
- Supports personal life, work, learning, and operations
- Is agent-friendly and human-correctable
- Avoids premature structure

It is intentionally minimal, flexible, and durable.

