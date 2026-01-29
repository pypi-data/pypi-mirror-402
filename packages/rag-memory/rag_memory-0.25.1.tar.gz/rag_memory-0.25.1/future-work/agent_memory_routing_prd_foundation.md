# Agent Memory Routing - PRD Foundation

## Purpose

This document consolidates foundational knowledge for writing a PRD that specifies an AI agent capability for:
1. Creating a scaffold of collections for new users
2. Routing content to appropriate collections with confidence
3. Managing the Inbox as a fallback
4. Enabling content migration as needs evolve

This is the **input to writing the PRD**, not the PRD itself.

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `long_term_memory_categories_...md` | Conceptual framework (8 memory types) |
| `docs/MEMORY_CATEGORIES.md` | RAG Memory tool/capability mapping |
| `agent_side_routing_for_long_term_memory_capture.md` | Agent routing behavior principles |
| `agent_collection_scaffolding_routing_guide.md` | Universal collections + routing rules |

---

## Part 1: The Collection Scaffold

### 9 Universal Base Collections

Created for **all users** regardless of role (employee, student, creator, business owner).

| # | Collection | Purpose | Routing Signal |
|---|-----------|---------|----------------|
| 1 | **Inbox / Unsorted** | Frictionless capture, fallback | Agent uncertain, "save for later" |
| 2 | **Ideas & Exploration** | Early-stage thinking | Future-oriented, no commitment yet |
| 3 | **Projects** | Active work or initiatives | Clear intent + trajectory |
| 4 | **Ways of Working & Procedures** | How-to, SOPs, workflows | Repeatable, instructional |
| 5 | **Decisions & Preferences** | Durable choices | "We decided", "I prefer", authoritative |
| 6 | **Knowledge & Reference** | External knowledge retained | Reference material, docs, APIs |
| 7 | **Personal Life & Reflections** | Non-work human context | Not work-related |
| 8 | **Personal Finance & Admin** | Money and life logistics | Banking, benefits, budgets |
| 9 | **People & Relationships** | Person-centric memory | "Remember this about a person" |

### Optional Extension

| Collection | When to Create |
|------------|---------------|
| **Business Finance & Operations** | Only if user explicitly indicates they run a business |

---

## Part 2: Collection Specifications

### Inbox / Unsorted

**Purpose:** Frictionless capture with no decision required

**Use cases:**
- Quick thoughts
- "Save this for later"
- Agent uncertainty during routing
- Auto-ingested content not yet reviewed

**Routing rule:** If the agent is unsure → route here

**Special metadata (for PRD):**
- `original_intent`: What the agent thought the content might be about
- `suggested_collection`: Agent's best guess if one exists
- `needs_review`: Boolean flag for surfacing in admin/review UI

---

### Ideas & Exploration

**Purpose:** Early-stage thinking that may become something later

**Use cases:**
- Ideas for projects, courses, products
- Things to research or explore
- "What if" thinking

**Routing signals:**
- Future-oriented language
- No commitment or next steps yet
- Speculative, exploratory tone

---

### Projects

**Purpose:** Things the user is actively working on or planning to deliver

**Use cases:**
- Work initiatives
- Personal goals with momentum
- Courses being built
- Active repositories

**Routing signals:**
- Clear intent + trajectory
- Active work language ("working on", "building", "delivering")
- References to timelines or milestones

---

### Ways of Working & Procedures

**Purpose:** How the user actually does things

**Use cases:**
- SOPs
- AI-native workflows
- Teaching methods
- "This is how I do X now"

**Routing signals:**
- Repeatable, instructional, operational knowledge
- Step-by-step structure
- "How to" language

---

### Decisions & Preferences

**Purpose:** Durable choices the user does not want to revisit

**Use cases:**
- Tech stack decisions
- Tooling preferences
- Constraints and tradeoffs
- "We decided this, and here's why"

**Routing signals:**
- Declarative, authoritative statements
- "I prefer", "always use", "we decided"
- Rationale or tradeoff language

---

### Knowledge & Reference

**Purpose:** External knowledge deliberately retained

**Use cases:**
- Official documentation (URLs)
- API references
- Tutorials
- Research material
- Synced GitHub repository knowledge

**Routing signals:**
- Reference material, not personal opinion
- External source (URLs, docs)
- Factual, instructional content

---

### Personal Life & Reflections

**Purpose:** Non-work human context

**Use cases:**
- Memories
- Life planning
- Reflections
- Personal notes

**Routing signals:**
- Not work-related
- Personal, reflective tone
- Life events, relationships, personal goals

---

### Personal Finance & Admin

**Purpose:** Personal money and life logistics

**Use cases:**
- Banking
- Benefits (HSA, etc.)
- Budgets
- Subscriptions
- Financial exports

**Routing signals:**
- Financial terminology
- Account/budget references
- Administrative life tasks

---

### People & Relationships

**Purpose:** Person-centric memory for relationship context

Store information *about a person* that you want to recall over time—not general documents that merely mention people.

**What belongs:**
- Who the person is and how the user knows them
- Role or relationship context (client, colleague, friend, stakeholder)
- Preferences, constraints, sensitivities
- Relationship history summaries
- Follow-ups or "remember next time" notes

**What does NOT belong:**
- Project plans, meeting notes, invoices, proposals, emails
- Any artifact where a person is mentioned but is not the main subject

**Routing rule (authoritative):**
- Primary purpose is "remember this about a person" → route here
- Primary purpose is project, operation, reference, or finance → appropriate collection

**One-line test:** "Is this document mainly about the person or about something the person was involved in?"

---

## Part 3: Routing Confidence Heuristics

### High Confidence (route directly)

The agent should route directly when:

| Signal | Example |
|--------|---------|
| Explicit collection mention | "Save this to my procedures" |
| Clear domain_scope match | Content clearly fits one collection's scope |
| Explicit routing instruction | "Remember this decision", "This is how I do X" |
| Unambiguous content type | URL → Knowledge, SOP → Ways of Working |
| User confirms routing | Agent suggested, user approved |

### Low Confidence (route to Inbox)

The agent should use Inbox when:

| Signal | Example |
|--------|---------|
| Very short with no context | "Random thought" |
| Multiple collections fit | Could be Ideas OR Projects |
| Spans domains | Personal + work content |
| User defers | "Save this, I'll organize later" |
| Cannot determine purpose | Agent genuinely unsure |

### Routing Rule Precedence

1. **Explicit user instruction** → follow it exactly
2. **High confidence match** → route directly, no confirmation needed
3. **Moderate confidence** → route directly, optionally mention where
4. **Low confidence** → route to Inbox / Unsorted
5. **Never** auto-create collections
6. **Never** over-ask (max 1 clarifying question if truly ambiguous)

---

## Part 4: User Phrase → Collection Mapping

Examples of how user language maps to routing decisions:

| User phrase pattern | Target collection |
|---------------------|-------------------|
| "I had an idea about..." | Ideas & Exploration |
| "What if we..." | Ideas & Exploration |
| "I'm working on..." | Projects |
| "Here's the project plan for..." | Projects |
| "This is how I do..." | Ways of Working & Procedures |
| "Our process for X is..." | Ways of Working & Procedures |
| "We decided to..." | Decisions & Preferences |
| "I always prefer..." | Decisions & Preferences |
| "Save this documentation..." | Knowledge & Reference |
| "Here's the API for..." | Knowledge & Reference |
| "For my personal records..." | Personal Life or Finance |
| "Remember to renew my..." | Personal Finance & Admin |
| "Remember that Alice..." | People & Relationships |
| "About Bob, he prefers..." | People & Relationships |
| "Just save this" | Inbox / Unsorted |
| "I'll organize it later" | Inbox / Unsorted |

---

## Part 5: RAG Memory Features for Routing

### Relevant MCP Tools

| Tool | Use in Routing Workflow |
|------|------------------------|
| `list_collections` | Agent reads available collections before routing |
| `get_collection_info` | Agent reads domain_scope to validate routing choice |
| `create_collection` | Scaffold creation (one-time setup per user) |
| `ingest_text` | Primary capture tool with metadata |
| `ingest_url` | Capture web content → typically Knowledge & Reference |
| `link_to_collection` | Migrate content from Inbox to proper collection |
| `search_documents` | Find existing content, validate no duplicates |

### Relevant Metadata Fields

| Field | Routing Use |
|-------|-------------|
| `quality_score` | Flag low-quality content for Inbox review |
| `topic` parameter | Pass intended topic, validate routing matches |
| `reviewed_by_human` | Mark after user confirms routing is correct |
| `metadata_filter` | Find Inbox items needing review |

### Inbox-Specific Metadata (Proposed)

When routing to Inbox, agent should store:

```json
{
  "routing_status": "needs_review",
  "original_intent": "User said 'save this thought'",
  "suggested_collection": "Ideas & Exploration",
  "confidence_score": 0.4,
  "capture_timestamp": "2025-01-12T..."
}
```

---

## Part 6: Memory Categories Mapping

How the 8 theoretical memory categories map to the 9 practical collections:

| Memory Category | Primary Collection(s) | Notes |
|----------------|----------------------|-------|
| Semantic (facts) | Knowledge & Reference | External knowledge, reference material |
| Episodic (events) | Projects, Personal Life | Time-bounded, what happened |
| Procedural (SOPs) | Ways of Working & Procedures | "How to", repeatable processes |
| Preference | Decisions & Preferences | "I prefer", authoritative choices |
| Identity/Mission | Ideas, Projects, Decisions | Depends on stage/formality |
| Decision (ADRs) | Decisions & Preferences | "We decided", tradeoffs |
| Task/Commitment | Projects | Active work, commitments |
| Social (people) | People & Relationships | About the person specifically |

**Key insight:** Collections are organized by **intent** (why it's being stored), not by **memory type** (what kind of memory). This means:
- One memory type can span multiple collections
- One collection can hold multiple memory types

---

## Part 7: PRD Scope Sections

The PRD should cover these areas:

### 1. Scaffold Creation
- Trigger: When user first connects to RAG Memory
- Action: Create 9 base collections with appropriate domain/domain_scope
- Optional: Create Business Finance if user indicates business ownership
- Idempotency: Don't recreate if collections already exist

### 2. Routing Decision Logic
- How agent classifies content intent
- Confidence scoring mechanism (high/medium/low)
- When to route directly vs use Inbox
- When to ask clarifying question (max 1, only when truly ambiguous)

### 3. Inbox Management
- Metadata schema for Inbox items
- How items are surfaced for review (admin UI, periodic prompts)
- Migration workflow: user reviews → agent moves to proper collection
- Cleanup: mark as reviewed or delete

### 4. Evolution Support
- How users can customize collection names/descriptions
- When to suggest splitting a collection (growth heuristics)
- Content migration patterns using `link_to_collection`
- How to handle user-created collections

---

## Part 8: Design Principles (from source docs)

1. **Capture first, decide later**
   - The system must never block capture due to uncertainty

2. **Collections reflect intent, not topic**
   - Collections answer "why is this being stored?", not "what is it about?"

3. **Routing should be confident most of the time**
   - Target: >90% of captures route directly without Inbox
   - Inbox is an exception path, not a default

4. **Structure must be easy to change**
   - Documents can move between collections over time
   - Initial scaffold is temporary, not permanent

5. **Low-friction capture, deliberate organization**
   - Most content lands in the right place automatically
   - Only genuinely ambiguous cases involve the user

---

## Part 9: Success Criteria

After PRD is implemented, the agent capability should:

1. **Create scaffold** for new user with 9 collections + optional extension
2. **Route content** with >90% accuracy on first attempt
3. **Use Inbox** for <10% of captures (truly ambiguous cases)
4. **Enable migration** from Inbox to proper collections with low friction
5. **Support evolution** as user needs grow
6. **Never over-ask** - max 1 clarifying question per capture
7. **Never auto-create** collections without explicit user request

---

## Appendix: Collection Domain/Domain_Scope Suggestions

For scaffold creation, suggested values:

| Collection | Domain | Domain Scope |
|------------|--------|--------------|
| Inbox / Unsorted | inbox | Temporary holding for content awaiting review or classification. Does not contain finalized content. |
| Ideas & Exploration | ideas | Early-stage thinking, speculative ideas, things to explore. Not committed work or finalized decisions. |
| Projects | projects | Active work initiatives with clear trajectory. Excludes ideas without momentum or completed archived work. |
| Ways of Working & Procedures | procedures | Repeatable processes, SOPs, how-tos. Excludes one-time actions or reference documentation. |
| Decisions & Preferences | decisions | Durable choices and preferences with rationale. Excludes speculative thinking or temporary constraints. |
| Knowledge & Reference | reference | External knowledge retained for lookup. Excludes personal opinions or internal decisions. |
| Personal Life & Reflections | personal | Non-work human context. Excludes professional work or business operations. |
| Personal Finance & Admin | finance-personal | Personal money and life logistics. Excludes business finances or work-related admin. |
| People & Relationships | people | Information about specific people for relationship context. Excludes documents where people are incidental. |
| Business Finance & Operations | finance-business | Business systems, accounting, operations. Only for users who run a business. |
