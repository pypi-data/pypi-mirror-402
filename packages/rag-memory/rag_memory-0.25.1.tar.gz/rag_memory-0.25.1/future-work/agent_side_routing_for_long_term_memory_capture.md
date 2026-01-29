# Agent‑Side Routing for Long‑Term Memory Capture

## Purpose of this note
This document describes **AI‑agent behavior**, not MCP server internals. It captures the routing logic an agent should follow when a user asks it to “remember,” “store,” or “capture” something using an MCP‑backed knowledge base. It is meant to guide agent design and policy, not dictate storage schemas.

---

## Core idea (from the YouTube inspiration, generalized)
The agent’s job is to:
1. **Understand user intent** (“this is an idea,” “this relates to a project,” “store this for later”).
2. **Route content to the best existing collection** with high confidence.
3. **Avoid creating new collections automatically.**
4. **Use a temporary holding collection only when routing confidence is genuinely low.**
5. **Ask the human when ambiguity matters.**

The system should feel *low‑friction* most of the time, *deliberate* only when needed.

---

## Assumptions
- The agent has read access to:
  - collection names
  - collection descriptions
  - domain / domain_scope metadata
  - example or sample documents (lightweight preview)
- The agent can ingest content via MCP tools (text, URLs, files, directories).
- The agent does **not** directly manipulate storage outside MCP tools.

---

## High‑confidence routing (the 90–99% case)

### Typical user inputs
- “I had an idea about Project X — save this.”
- “Here are some URLs about Cloud Code skills — ingest them.”
- “Capture this decision we just made.”

### Agent behavior
1. **Classify the content’s intent** (idea, project work, procedure, decision, reference, etc.).
2. **Match intent + content against existing collections** using:
   - collection description
   - domain_scope
   - prior successful patterns (implicit learning)
3. **Select the best‑fit collection** when confidence is high.
4. **Proceed with ingest** without interrupting the user.

> Key rule: If the agent is confident, it should *just do it*.

---

## Ambiguous routing (the exception case)

### When ambiguity arises
- Content plausibly fits multiple collections.
- Content is very short (“random thought”) with little context.
- Content spans domains (e.g., personal + business).
- No existing collection clearly matches.

### Agent behavior
1. **Pause ingestion** (or perform a dry run if supported).
2. **Ask a minimal clarification question**, e.g.:
   - “Should this go under *Projects* or *Ideas*?”
   - “Is this personal or work‑related?”
3. **Only ask one question** unless absolutely necessary.

The goal is *resolution*, not interrogation.

---

## The holding / unsorted collection

### Why it exists
- To avoid blocking capture when certainty is low.
- To prevent the agent from guessing incorrectly.
- To give the human a clean review queue.

### When it is used
- The agent cannot confidently choose a collection **and**
- The user does not want to decide right now.

### Properties
- Rarely used (target: <5–10% of ingests).
- Explicitly labeled as “Needs review” / “Unsorted.”
- Items are expected to be moved later by a human or admin UI.

> Important: This is not an “inbox for everything.” It is an exception path.

---

## Interaction patterns

### Low‑friction capture
User: “I just had a thought about how we teach AI workflows.”
Agent: *routes to Ideas or Teaching collection and ingests*

### Assisted discovery
User: “Help me find good URLs about X and save them.”
Agent:
- searches
- presents candidates
- user approves
- agent routes and ingests

### Deferral
User: “Save this, I’ll organize it later.”
Agent:
- confirms
- ingests into holding collection
- optionally reminds user it can be re‑sorted later

---

## Explicit non‑goals
- The agent should **not** auto‑create collections.
- The agent should **not** over‑optimize taxonomy up front.
- The agent should **not** require human input for routine cases.

---

## Design principle to keep in mind
> *Capture first, organize with confidence, and defer only when necessary.*

The agent’s routing logic exists to reduce cognitive load, not increase it. Most content should land in the right place automatically; only genuinely ambiguous cases should involve the user.

