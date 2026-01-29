# Long-Term Memory Categories: RAG Memory Implementation Guide

> **Audience:** AI Agents (conceptual guidance) + Developers (implementation details)
> **Last Updated:** 2025-01-12
> **Status:** Current

This guide bridges theoretical long-term memory categories with RAG Memory's actual capabilities. Use it to understand how to store and retrieve different types of knowledge effectively.

---

## Table of Contents

- [Part 1: Overview](#part-1-overview)
- [Part 2: Memory Category Deep Dives](#part-2-memory-category-deep-dives)
  - [2.1 Semantic Memory](#21-semantic-memory-factsknowledge)
  - [2.2 Episodic Memory](#22-episodic-memory-eventswhat-happened)
  - [2.3 Procedural Memory](#23-procedural-memory-sopshow-to)
  - [2.4 Preference/Profile Memory](#24-preferenceprofile-memory)
  - [2.5 Identity/Mission Memory](#25-identitymission-memory)
  - [2.6 Decision Memory](#26-decision-memory-rationaleadrs)
  - [2.7 Task/Commitment Memory](#27-taskcommitment-memory-open-loops)
  - [2.8 Social/Relationship Memory](#28-socialrelationship-memory-people-context)
- [Part 3: Cross-Cutting Guidance](#part-3-cross-cutting-guidance)
- [Part 4: Gap Analysis Summary](#part-4-gap-analysis-summary)
- [Part 5: Quick Reference Cards](#part-5-quick-reference-cards)

---

## Part 1: Overview

### Why Memory Categories Matter

Different memory types serve different retrieval needs. An AI agent that can effectively store and retrieve organizational facts, past decisions, procedures, and people context will provide far more value than one that treats all knowledge the same.

**Mental model:** Memory = persistent knowledge + retrieval behaviors

Memory categories differ by:
- **What is stored** (facts, events, procedures, preferences)
- **How it is retrieved** (semantic similarity, entity/relationship, temporal)
- **How it is used** (recall, planning, policy enforcement, personalization)

### RAG Memory Primitives at a Glance

RAG Memory provides four core primitives:

| Primitive | Description | Primary Use |
|-----------|-------------|-------------|
| **Document Storage** | Source docs with flexible metadata schemas | Store any text content |
| **Vector Similarity Search** | Semantic recall via embeddings | "What do we know about X?" |
| **Knowledge Graph** | Entity relationships + temporal reasoning | "How does X relate to Y?" |
| **Collections** | Domain scoping + governance | Partition knowledge by purpose |

### Retrieval Strategy Quick Reference

**For Agents:** Use this decision tree to choose the right retrieval tool.

```
Question about WHAT something IS?
  → search_documents (semantic similarity)

Question about HOW things RELATE?
  → query_relationships (graph connections)

Question about WHEN/HOW things CHANGED?
  → query_temporal (evolution over time)

Need HIGH CONFIDENCE answers?
  → Add: reviewed_by_human=True, min_quality_score=0.7

Need SPECIFIC CATEGORY of content?
  → Add: metadata_filter with appropriate fields
```

| Question Type | Primary Tool | When to Use |
|--------------|--------------|-------------|
| "What is X?" | `search_documents` | Factual recall |
| "How does X relate to Y?" | `query_relationships` | Connection discovery |
| "How has X changed?" | `query_temporal` | Evolution tracking |
| "What should I remember about person X?" | `search_documents` + metadata | People context |

---

## Part 2: Memory Category Deep Dives

### 2.1 Semantic Memory (Facts/Knowledge)

#### Definition

Stable knowledge about the world or your domain. Facts that don't change frequently.

**Examples:**
- "Our billing system uses Stripe"
- "Refund policy is 14 days"
- "PostgreSQL is our primary database"
- "The API rate limit is 1000 requests per minute"

#### RAG Memory Support

**Primary tools:**
- `search_documents` — Semantic similarity for "What is our refund policy?"
- `query_relationships` — Multi-hop connections (Stripe ↔ billing ↔ refund)

**Support level:** ✅ Excellent

#### Collection Design

```python
# Example: Collection for company policies
create_collection(
    name="company-policies",
    description="Official company policies: HR, security, compliance, refunds",
    domain="policies",
    domain_scope="Formal policies and guidelines. Excludes informal preferences or architecture.",
    metadata_schema={
        "custom": {
            "policy_area": {"type": "string"},     # "hr", "security", "compliance", "customer"
            "effective_date": {"type": "string"},  # ISO date
            "last_reviewed": {"type": "string"}    # ISO date
        }
    }
)

# Example: Collection for system architecture facts
create_collection(
    name="system-architecture",
    description="Technical architecture: services, databases, integrations",
    domain="engineering",
    domain_scope="How systems are built and connected. Excludes procedures and ADRs.",
    metadata_schema={
        "custom": {
            "system": {"type": "string"},          # "billing", "auth", "api"
            "confidence": {"type": "string"},      # "verified", "assumed"
            "last_verified": {"type": "string"}    # ISO date
        }
    }
)
```

#### Usage Patterns

**Ingestion:**
```python
ingest_text(
    content="Our refund policy allows returns within 14 days of purchase. "
            "Refunds are processed to the original payment method within 5 business days.",
    collection_name="company-policies",
    document_title="Refund Policy",
    metadata={"policy_area": "customer", "effective_date": "2025-01-01"},
    reviewed_by_human=True  # User confirmed accuracy
)
```

**Retrieval:**
```python
# Semantic search for facts
search_documents(
    query="What is our return policy for customers?",
    collection_name="company-policies",
    min_quality_score=0.7,
    reviewed_by_human=True
)

# Graph for connections
query_relationships(
    query="How does refund policy relate to billing system?",
    collection_name="company-policies"
)
```

#### Gap Analysis

| Aspect | Status | Notes |
|--------|--------|-------|
| Semantic recall | ✅ Excellent | Core strength |
| Metadata filtering | ✅ Excellent | Custom fields supported |
| Human review tracking | ✅ Excellent | `reviewed_by_human` flag |
| Fact versioning | ⚠️ Limited | Use `mode="reingest"` or temporal graph |
| Contradiction detection | ❌ Not supported | Manual review required |
| Auto-deduplication | ⚠️ Limited | Content hash detects exact duplicates only |

**Workarounds:**
- Use `mode="reingest"` to update facts
- Check `get_collection_info()` before ingesting to avoid duplicates
- Use `query_temporal()` to see if facts were superseded

---

### 2.2 Episodic Memory (Events/What Happened)

#### Definition

Time-bounded experiences: decisions, meetings, incidents, outcomes.

**Examples:**
- "On 2025-11-12 we decided to deprecate Feature A"
- "Customer outage on 2025-10-15 caused by DNS issue"
- "Q4 planning meeting agreed on 3 priorities"

#### RAG Memory Support

**Primary tools:**
- `query_temporal` — "What happened with Feature A last quarter?"
- `search_documents` — Find meeting notes, incident reports
- `query_relationships` — Who was involved, what was affected

**Support level:** ✅ Good (temporal graph is strong)

#### Collection Design

```python
create_collection(
    name="meeting-notes",
    description="Meeting notes, decisions, and outcomes with temporal context",
    domain="episodic",
    domain_scope="Time-bounded events: meetings, decisions, incidents. Includes who, what, when.",
    metadata_schema={
        "custom": {
            "event_date": {"type": "string"},      # ISO date
            "event_type": {"type": "string"},      # "meeting", "incident", "decision"
            "participants": {"type": "array"},     # ["alice", "bob"]
            "outcome": {"type": "string"}          # Summary of what was decided
        }
    }
)
```

#### Usage Patterns

**Ingestion:**
```python
ingest_text(
    content="""Q4 Planning Meeting - November 12, 2025

    Attendees: Alice, Bob, Carol

    Decisions:
    1. Deprecate Feature A due to low adoption (3% usage)
    2. Prioritize mobile app performance improvements
    3. Hire 2 additional backend engineers

    Action items assigned to respective owners.""",
    collection_name="meeting-notes",
    document_title="Q4 Planning - 2025-11-12",
    metadata={
        "event_date": "2025-11-12",
        "event_type": "meeting",
        "participants": ["alice", "bob", "carol"],
        "outcome": "Feature A deprecated, mobile prioritized"
    }
)
```

**Retrieval:**
```python
# Temporal query for decisions
query_temporal(
    query="What decisions were made about Feature A?",
    collection_name="meeting-notes",
    valid_from="2025-10-01",
    valid_until="2025-12-31"
)

# Search with event type filter
search_documents(
    query="What happened in the Q4 planning meeting?",
    collection_name="meeting-notes",
    metadata_filter={"event_type": "meeting"}
)
```

#### Gap Analysis

| Aspect | Status | Notes |
|--------|--------|-------|
| Temporal tracking | ✅ Excellent | `valid_from`/`valid_until` in graph |
| Superseded status | ✅ Excellent | Graph tracks current vs superseded |
| Rich metadata | ✅ Excellent | Custom fields for context |
| Calendar integration | ❌ Not supported | Dates must be in content/metadata |
| Automatic event extraction | ❌ Not supported | Manual structuring required |
| Recurrence patterns | ❌ Not supported | Create separate documents |

**Workarounds:**
- Structure content with dates in document title
- Use `metadata_filter` by `event_date`
- Create separate documents for recurring events

---

### 2.3 Procedural Memory (SOPs/How-To)

#### Definition

Step-by-step procedures, playbooks, runbooks, checklists.

**Examples:**
- "How to deploy to production"
- "Customer escalation process"
- "Database backup procedure"
- "New employee onboarding checklist"

#### RAG Memory Support

**Primary tools:**
- `search_documents` — Find procedure by description
- `query_relationships` — Procedure ↔ System ↔ Tool connections

**Support level:** ✅ Good

#### Collection Design

```python
create_collection(
    name="procedures",
    description="Step-by-step processes, runbooks, and SOPs",
    domain="operational",
    domain_scope="Procedures and how-to guides. Includes deployment, incident response, onboarding.",
    metadata_schema={
        "custom": {
            "procedure_type": {"type": "string"},  # "deployment", "incident", "onboarding"
            "systems_involved": {"type": "array"}, # ["kubernetes", "aws", "datadog"]
            "complexity": {"type": "string"},      # "simple", "moderate", "complex"
            "last_tested": {"type": "string"}      # ISO date
        }
    }
)
```

#### Usage Patterns

**Ingestion:**
```python
ingest_text(
    content="""# Production Deployment Procedure

    ## Prerequisites
    - All tests passing on main branch
    - Approval from tech lead

    ## Steps
    1. Run tests: `npm test`
    2. Bump version: `npm version patch`
    3. Tag release: `git tag v1.2.3`
    4. Deploy to staging: `kubectl apply -f staging/`
    5. Validate: Check health endpoint returns 200
    6. Deploy to production: `kubectl apply -f prod/`
    7. Monitor: Watch Datadog for 15 minutes

    ## Rollback
    If issues occur: `kubectl rollout undo deployment/app`""",
    collection_name="procedures",
    document_title="Production Deployment SOP",
    metadata={
        "procedure_type": "deployment",
        "systems_involved": ["kubernetes", "npm", "git", "datadog"],
        "complexity": "moderate",
        "last_tested": "2025-11-01"
    },
    reviewed_by_human=True
)
```

**Retrieval:**
```python
# Find procedure
search_documents(
    query="How do I deploy to production?",
    collection_name="procedures",
    reviewed_by_human=True  # Verified procedures only
)

# Find procedures by system
query_relationships(
    query="Which procedures involve Kubernetes?",
    collection_name="procedures"
)
```

#### Gap Analysis

| Aspect | Status | Notes |
|--------|--------|-------|
| Procedure storage | ✅ Excellent | Markdown structure preserved |
| Metadata filtering | ✅ Excellent | Filter by system, type |
| Human review | ✅ Excellent | Critical for procedures |
| Full procedure retrieval | ✅ Excellent | `get_document_by_id` returns complete document |
| Prerequisite tracking | ⚠️ Manual | Include in content structure |
| Execution state | ❌ Not supported | Procedures are reference only |

**Retrieval pattern:**
1. Use `search_documents` to find relevant procedure chunks
2. Use `get_document_by_id(source_document_id)` to retrieve the complete procedure with all steps
3. Agents can then present the full procedure to users

**Note:** Include prerequisites in the procedure content itself. Track execution state externally (procedures are reference documents, not workflow state).

---

### 2.4 Preference/Profile Memory

#### Definition

Stable preferences, constraints, style, principles for a person or org.

**Examples:**
- "Prefer PostgreSQL over MongoDB for transactional data"
- "Use Infrastructure as Code for all infrastructure"
- "Tim likes concise responses"
- "Always use TypeScript, never JavaScript"

#### RAG Memory Support

**Primary tools:**
- `search_documents` — "What do we prefer for databases?"
- `query_relationships` — Preference ↔ Entity connections

**Support level:** ✅ Good

#### Collection Design

```python
create_collection(
    name="preferences",
    description="Organizational and personal preferences, constraints, and principles",
    domain="preferences",
    domain_scope="Stable preferences about technology, communication, and ways of working.",
    metadata_schema={
        "custom": {
            "preference_type": {"type": "string"},  # "technical", "communication", "style"
            "applies_to": {"type": "string"},       # "tim", "org", "engineering"
            "strength": {"type": "string"},         # "strong", "moderate", "weak"
            "source": {"type": "string"}            # Where preference was stated
        }
    }
)
```

#### Usage Patterns

**Ingestion:**
```python
ingest_text(
    content="For transactional systems, prefer PostgreSQL over MongoDB. "
            "Reasons: ACID compliance, mature tooling, team expertise. "
            "Exception: Use MongoDB for document-heavy analytics workloads.",
    collection_name="preferences",
    document_title="Database Technology Preference",
    metadata={
        "preference_type": "technical",
        "applies_to": "engineering",
        "strength": "strong",
        "source": "Architecture Decision Record ADR-001"
    },
    reviewed_by_human=True
)
```

**Retrieval:**
```python
# Before making a recommendation
search_documents(
    query="What database should I recommend for a new transactional service?",
    collection_name="preferences",
    metadata_filter={"preference_type": "technical"}
)
```

#### Gap Analysis

| Aspect | Status | Notes |
|--------|--------|-------|
| Preference storage | ✅ Excellent | Short notes work well |
| Metadata categorization | ✅ Excellent | Filter by type, strength |
| Entity attachment | ✅ Good | Via graph |
| Conflict resolution | ❌ Not supported | Manual review |
| Inheritance hierarchy | ❌ Not supported | No org → team → individual cascading |
| Auto-extraction | ❌ Not supported | Manually ingest preferences |

**Workarounds:**
- Include context and exceptions in preference content
- Use separate collections for org vs personal preferences
- Manually ingest preferences when stated in conversations

---

### 2.5 Identity/Mission Memory

#### Definition

Mission, vision, positioning, goals, north-star metrics.

**Examples:**
- "Mission: Teach engineers AI-native workflows"
- "Success metric: Course completion + retention"
- "Positioning: Premium quality over low price"
- "Vision: Every developer uses AI tools daily"

#### RAG Memory Support

**Primary tools:**
- `search_documents` — "Given our mission, how should we...?"
- `query_relationships` — Mission ↔ Products ↔ Audience

**Support level:** ✅ Good

#### Collection Design

```python
create_collection(
    name="company-strategy",
    description="Mission, vision, strategic goals, and north-star metrics",
    domain="strategic",
    domain_scope="Company identity: mission, vision, positioning, OKRs. Evergreen and time-bound goals.",
    metadata_schema={
        "custom": {
            "strategy_type": {"type": "string"},  # "mission", "vision", "goal", "metric"
            "timeframe": {"type": "string"},      # "evergreen", "Q4-2025", "2025"
            "priority": {"type": "string"}        # "primary", "secondary"
        }
    }
)
```

#### Usage Patterns

**Ingestion:**
```python
ingest_text(
    content="Mission: Empower engineers to build AI-native applications "
            "through hands-on courses and production-ready templates. "
            "We believe every developer should be able to leverage AI "
            "without needing ML expertise.",
    collection_name="company-strategy",
    document_title="Company Mission Statement",
    metadata={
        "strategy_type": "mission",
        "timeframe": "evergreen",
        "priority": "primary"
    },
    topic="company mission and strategic direction",  # Enables relevance scoring
    reviewed_by_human=True
)
```

**Retrieval:**
```python
# Align decisions with mission
search_documents(
    query="What is our company mission and how should it guide product decisions?",
    collection_name="company-strategy",
    metadata_filter={"strategy_type": "mission"}
)

# Find content highly aligned with mission (ingested with topic)
search_documents(
    query="What strategic content is most aligned with our mission?",
    collection_name="company-strategy",
    min_topic_relevance=0.7  # High alignment with ingested topic
)
```

#### Gap Analysis

| Aspect | Status | Notes |
|--------|--------|-------|
| Central storage | ✅ Excellent | Single source of truth |
| Human review | ✅ Excellent | Critical for strategic docs |
| Graph connections | ✅ Good | Mission ↔ Products ↔ Audience |
| Topic relevance scoring | ✅ Good | Use `topic` param on ingest, filter by `min_topic_relevance` |
| Cross-doc alignment | ⚠️ Manual | No auto "does X align with mission?" check |
| Goal tracking | ⚠️ Manual | Include status in metadata |
| OKR hierarchy | ❌ Not supported | Flat document structure |

**Topic relevance pattern:**
When ingesting strategic content, provide a `topic` parameter (e.g., "company mission alignment"). The LLM evaluates and scores relevance. Later, use `min_topic_relevance` filter to retrieve only highly-aligned content.

**Note:** Cross-document alignment (e.g., "does this decision align with our mission?") requires the agent to retrieve both documents and compare. Use separate documents for goals at different levels.

---

### 2.6 Decision Memory (Rationale/ADRs)

#### Definition

Rationale, tradeoffs, alternatives considered, constraints at the time.

**Examples:**
- "Chose pgvector over Pinecone for simplicity"
- "ADR-003: Use REST over GraphQL for public API"
- "Rejected MongoDB due to ops complexity"

#### RAG Memory Support

**Primary tools:**
- `search_documents` — "Why did we choose pgvector?"
- `query_relationships` — Decision ↔ Alternatives ↔ Consequences
- `query_temporal` — When decision was made, if superseded

**Support level:** ✅ Excellent (temporal graph shines here)

#### Collection Design

```python
create_collection(
    name="decisions",
    description="Architecture Decision Records (ADRs) with rationale and tradeoffs",
    domain="architectural",
    domain_scope="Technical decisions, alternatives considered, and rationale. ADR format preferred.",
    metadata_schema={
        "custom": {
            "decision_id": {"type": "string"},     # "ADR-003"
            "decision_date": {"type": "string"},   # ISO date
            "status": {"type": "string"},          # "accepted", "superseded", "deprecated"
            "domain": {"type": "string"},          # "database", "api", "infrastructure"
            "superseded_by": {"type": "string"}    # "ADR-007" if applicable
        }
    }
)
```

#### Usage Patterns

**Ingestion:**
```python
ingest_text(
    content="""# ADR-003: Use pgvector for Vector Search

    ## Status
    Accepted

    ## Context
    Need vector similarity search for RAG application.
    Evaluated options in October 2025.

    ## Decision
    Use pgvector extension with PostgreSQL.

    ## Alternatives Considered
    - Pinecone: Higher cost ($70/mo), external dependency
    - Weaviate: More complex ops, separate service
    - Milvus: Overkill for our scale (<1M vectors)

    ## Consequences
    - Simpler architecture (single database)
    - Lower cost (included in existing Postgres)
    - Accepted tradeoff: Slightly lower recall than dedicated vector DB
    - Team can use familiar SQL tooling""",
    collection_name="decisions",
    document_title="ADR-003: pgvector for Vector Search",
    metadata={
        "decision_id": "ADR-003",
        "decision_date": "2025-10-01",
        "status": "accepted",
        "domain": "database"
    },
    reviewed_by_human=True
)
```

**Retrieval:**
```python
# Find decision rationale
search_documents(
    query="Why did we choose pgvector over Pinecone?",
    collection_name="decisions"
)

# Check if decision was superseded
query_temporal(
    query="How has our vector database choice evolved?",
    collection_name="decisions"
)

# Find all database decisions
search_documents(
    query="What architectural decisions have we made about databases?",
    collection_name="decisions",
    metadata_filter={"domain": "database"}
)
```

#### Gap Analysis

| Aspect | Status | Notes |
|--------|--------|-------|
| ADR storage | ✅ Excellent | Format maps perfectly |
| Temporal tracking | ✅ Excellent | Superseded status in graph |
| Relationship discovery | ✅ Excellent | Decision ↔ Alternatives |
| Auto status updates | ❌ Not supported | Manual update needed |
| Consequence tracking | ❌ Not supported | No outcome verification |
| Decision dependencies | ⚠️ Limited | Via graph, not explicit |

**Workarounds:**
- Manually update status via `update_document()`
- Include outcome reviews as separate documents
- Use graph queries to find related decisions

---

### 2.7 Task/Commitment Memory (Open Loops)

#### Definition

Actionable commitments and reminders, often time-sensitive.

**Examples:**
- "Follow up with vendor next Tuesday"
- "Renew SSL certificate before 2026-02-01"
- "Send Tim the architecture diagram"

#### RAG Memory Support

**Primary tools:**
- `search_documents` — "What commitments do I have?"
- `query_relationships` — Task ↔ Person ↔ Project

**Support level:** ⚠️ Limited (RAG Memory is a knowledge base, not a task manager)

#### Collection Design

```python
create_collection(
    name="tasks",
    description="Open commitments, follow-ups, and time-bound tasks",
    domain="tasks",
    domain_scope="Actionable items and commitments. For context storage, not task management.",
    metadata_schema={
        "custom": {
            "due_date": {"type": "string"},        # ISO date
            "status": {"type": "string"},          # "open", "completed", "cancelled"
            "assigned_to": {"type": "string"},     # Person responsible
            "related_to": {"type": "string"},      # Project or context
            "priority": {"type": "string"}         # "high", "medium", "low"
        }
    }
)
```

#### Usage Patterns

**Ingestion:**
```python
ingest_text(
    content="Follow up with Alice about the API integration timeline. "
            "She mentioned concerns about the Q1 deadline during our Nov 10 call. "
            "Need to check if they need additional documentation.",
    collection_name="tasks",
    document_title="Follow-up: Alice API Integration",
    metadata={
        "due_date": "2025-11-19",
        "status": "open",
        "assigned_to": "self",
        "related_to": "api-project",
        "priority": "high"
    }
)
```

**Retrieval:**
```python
# Find open tasks
search_documents(
    query="What open commitments do I have?",
    collection_name="tasks",
    metadata_filter={"status": "open"}
)

# High priority tasks
search_documents(
    query="What urgent tasks need attention?",
    collection_name="tasks",
    metadata_filter={"status": "open", "priority": "high"}
)
```

#### Gap Analysis

| Aspect | Status | Notes |
|--------|--------|-------|
| Task storage | ✅ Good | Basic storage works |
| Metadata filtering | ✅ Good | Filter by status, priority |
| Relationship tracking | ✅ Good | Via graph |
| **Date-range queries** | ❌ **Not supported** | Cannot query "due before X" |
| **Notifications** | ❌ **Not supported** | No reminder system |
| Recurring tasks | ❌ Not supported | Create new documents |
| Completion triggers | ❌ Not supported | Manual status update |

**Recommendation:**
RAG Memory is a **knowledge base**, not a task manager. Store task context and commitments here for retrieval, but use dedicated task tools (Todoist, Linear, etc.) for:
- Due date notifications
- Recurring tasks
- Task scheduling
- Completion workflows

**Workarounds:**
- Agent must calculate dates externally and filter
- Manually update status to "completed" via `update_document()`
- Create new documents for recurring tasks

---

### 2.8 Social/Relationship Memory (People Context)

#### Definition

People profiles, relationships, prior interactions, preferences.

**Examples:**
- "Alice prefers async updates"
- "Last spoke with Bob about onboarding pain"
- "Carol is the decision-maker for Project X"

#### RAG Memory Support

**Primary tools:**
- `search_documents` — "What should I know before meeting Alice?"
- `query_relationships` — Person ↔ Projects ↔ Topics ↔ Preferences

**Support level:** ✅ Good

#### Collection Design

```python
create_collection(
    name="people",
    description="People profiles, relationship context, and interaction history",
    domain="social",
    domain_scope="People notes: preferences, past interactions, roles, relationships.",
    metadata_schema={
        "custom": {
            "person_name": {"type": "string"},     # Canonical name
            "relationship": {"type": "string"},    # "colleague", "client", "vendor"
            "last_contact": {"type": "string"},    # ISO date
            "topics": {"type": "array"},           # ["onboarding", "api"]
            "communication_preference": {"type": "string"}  # "async", "sync", "email"
        }
    }
)
```

#### Usage Patterns

**Ingestion:**
```python
ingest_text(
    content="""Alice Chen - Engineering Manager at Acme Corp

    Communication: Prefers async communication via Slack.
    Responds quickly to direct questions, less to open-ended asks.

    Recent discussions:
    - Nov 10, 2025: Concerns about API rate limits for their use case
    - Oct 15, 2025: Initial integration kickoff meeting

    Key context:
    - Decision-maker for their integration project
    - Reports to VP Engineering (Bob)
    - Timezone: PST (usually available 9am-5pm)

    Follow-up: Check on rate limit concerns after our capacity review.""",
    collection_name="people",
    document_title="Person: Alice Chen",
    metadata={
        "person_name": "Alice Chen",
        "relationship": "client",
        "last_contact": "2025-11-10",
        "topics": ["api", "integration", "rate-limits"],
        "communication_preference": "async"
    }
)
```

**Retrieval:**
```python
# Before a meeting
search_documents(
    query="What should I remember before meeting with Alice Chen?",
    collection_name="people",
    metadata_filter={"person_name": "Alice Chen"}
)

# Find people by topic
search_documents(
    query="Who have I discussed API issues with?",
    collection_name="people"
)

# Graph: How is Alice connected to projects?
query_relationships(
    query="What is Alice Chen's involvement in our projects?",
    collection_name="people"
)
```

#### Gap Analysis

| Aspect | Status | Notes |
|--------|--------|-------|
| Person profiles | ✅ Excellent | Rich documents work well |
| Metadata filtering | ✅ Excellent | Filter by name, relationship |
| Graph connections | ✅ Excellent | Person ↔ Topics ↔ Projects |
| Contact linking | ❌ Not supported | No CRM integration |
| Interaction aggregation | ❌ Not supported | Manual summary updates |
| Relationship strength | ❌ Not supported | No frequency scoring |
| Duplicate detection | ⚠️ Limited | Use canonical names |

**Workarounds:**
- Use canonical names in metadata consistently
- Create summary documents periodically
- Include recent interactions in person doc
- Manual deduplication via search before ingest

---

## Part 3: Cross-Cutting Guidance

### Collection Design Strategy

#### Principles

1. **One domain per collection** — Don't mix unrelated content
2. **Clear scope descriptions** — Help agents route content correctly
3. **Consistent metadata schemas** — Enable reliable filtering
4. **Human review for critical content** — Use `reviewed_by_human` flag

#### For Agent-Side Routing

If building an AI agent that routes content on behalf of users, see:
- `future-work/agent_collection_scaffolding_routing_guide.md` — Universal 9-collection scaffold for individuals
- `future-work/agent_memory_routing_prd_foundation.md` — PRD foundation with routing heuristics

The collections below are domain-specific examples. The scaffolding guide provides a universal starter set organized by **intent** (why content is stored) rather than by topic.

#### Recommended Collection Structure (Domain-Specific Examples)

Collections should be **purpose-driven** with domain-specific names. Avoid generic names like "knowledge-base" (the entire system is the knowledge base).

```
# Semantic memory - split by domain
company-policies/       # Formal policies (HR, security, compliance)
  domain: "policies"
  scope: "Official company policies and guidelines"

system-architecture/    # Technical architecture facts
  domain: "engineering"
  scope: "How systems are built and connected"

product-specs/          # Product documentation
  domain: "product"
  scope: "Product features, specs, and capabilities"

# Episodic memory
meeting-notes/          # Meeting outcomes and decisions
  domain: "episodic"
  scope: "Meeting notes, decisions, and outcomes"

incident-reports/       # Incidents and post-mortems
  domain: "incidents"
  scope: "Outages, bugs, and root cause analyses"

# Procedural memory
deployment-runbooks/    # Deployment procedures
  domain: "operations"
  scope: "Step-by-step deployment and rollback procedures"

onboarding-guides/      # Onboarding procedures
  domain: "hr-ops"
  scope: "New employee and contractor onboarding"

# Other memory types
architecture-decisions/ # ADRs and rationale
  domain: "architectural"
  scope: "Architecture Decision Records with tradeoffs"

stakeholders/           # People context
  domain: "social"
  scope: "People profiles and relationship history"

tech-preferences/       # Technical preferences
  domain: "preferences"
  scope: "Organizational and personal preferences"

company-strategy/       # Mission, vision, OKRs
  domain: "strategic"
  scope: "Mission, vision, and strategic goals"
```

### Retrieval Strategy Selection

#### When to Use Each Tool

| Tool | Best For | Example Query |
|------|----------|---------------|
| `search_documents` | Factual questions, finding content | "What is our deployment process?" |
| `query_relationships` | Connection questions | "How does billing relate to Stripe?" |
| `query_temporal` | Evolution questions | "How has our pricing changed?" |

#### Quality and Trust Filters

```python
# High-trust retrieval (human-verified, high quality)
search_documents(
    query="What is our security policy?",
    collection_name="company-policies",
    reviewed_by_human=True,
    min_quality_score=0.7
)

# Exploratory retrieval (all content, ranked by relevance)
search_documents(
    query="What have we discussed about microservices?",
    threshold=0.3,
    limit=20
)

# Topic-focused retrieval (when ingested with topic)
search_documents(
    query="How do we handle authentication?",
    collection_name="deployment-runbooks",
    min_topic_relevance=0.6
)
```

### Cross-Collection Search

When content might exist in multiple collections:

```python
# Search all collections (omit collection_name)
search_documents(
    query="What do we know about Kubernetes?",
    limit=10
)

# Then filter results by source collection if needed
```

### Linking Documents Across Collections

When content belongs in multiple domains:

```python
# Document exists in "deployment-runbooks"
# Also relevant to "system-architecture" (explains how deployment works)
link_to_collection(
    document_id=42,
    collection_name="system-architecture"
)
# Now searchable in both collections without duplication
```

---

## Part 4: Gap Analysis Summary

### What RAG Memory Does Well

| Capability | Memory Types | Notes |
|-----------|--------------|-------|
| Semantic similarity search | All types | Core strength |
| Flexible metadata schemas | All types | Custom fields per collection |
| Knowledge graph relationships | Semantic, Episodic, Decision, Social | Entity connections |
| Temporal tracking | Episodic, Decision | Current vs superseded |
| Human review tracking | All types | `reviewed_by_human` flag |
| Quality scoring | All types | Automatic on ingest |
| Topic relevance scoring | Identity, Decision, all | Use `topic` param on ingest |
| Collection scoping | All types | Domain partitioning |
| Cross-collection linking | Shared content | `link_to_collection` |
| Full document retrieval | Procedural, all | `get_document_by_id` for complete docs |

### Known Limitations

| Limitation | Affected Types | Workaround |
|-----------|---------------|------------|
| No date-range queries | Task, Episodic | External date calculation + metadata filter |
| No notifications/reminders | Task | Use external task manager |
| No contradiction detection | Semantic, Decision | Manual review |
| No automatic deduplication | All types | Check collection before ingest |
| No inheritance hierarchy | Preference | Separate collections by scope |
| No execution state tracking | Procedural | Procedures are reference only |
| No calendar integration | Episodic, Task | Dates in metadata |
| No cross-doc alignment check | Identity | Agent retrieves both docs to compare |

### Future Work Recommendations

These are capabilities that would enhance memory support:

1. **Date-range query support** — Enable "due before X" queries
2. **Contradiction detection** — Flag conflicting facts during ingest
3. **Smarter deduplication** — Semantic similarity check before ingest
4. **Preference inheritance** — Org → Team → Individual cascading
5. **Person entity linking** — Auto-link mentions to person profiles
6. **Cross-document alignment** — Automatic "does X align with Y?" checking

---

## Part 5: Quick Reference Cards

### Memory Type → Tool Mapping

| Memory Type | Primary Tool | Secondary Tool | Example Collections |
|------------|--------------|----------------|---------------------|
| Semantic (facts) | `search_documents` | `query_relationships` | `company-policies`, `system-architecture` |
| Episodic (events) | `query_temporal` | `search_documents` | `meeting-notes`, `incident-reports` |
| Procedural (SOPs) | `search_documents` | `get_document_by_id` | `deployment-runbooks`, `onboarding-guides` |
| Preference | `search_documents` | `query_relationships` | `tech-preferences` |
| Identity/Mission | `search_documents` | `query_relationships` | `company-strategy` |
| Decision (ADRs) | `search_documents` | `query_temporal` | `architecture-decisions` |
| Task/Commitment | `search_documents` | N/A | `commitments` (or use external task manager) |
| Social (people) | `search_documents` | `query_relationships` | `stakeholders`, `contacts` |

### Common Metadata Fields by Category

```yaml
# System fields (automatic)
reviewed_by_human: boolean    # Human verification flag
quality_score: float          # 0.0-1.0, computed on ingest
topic_relevance_score: float  # 0.0-1.0, if topic provided

# Semantic/Knowledge
fact_type: string            # policy, architecture, product
confidence: string           # verified, assumed

# Episodic/Events
event_date: string           # ISO date
event_type: string           # meeting, incident, decision
participants: array          # ["alice", "bob"]

# Procedural/SOPs
procedure_type: string       # deployment, incident, onboarding
systems_involved: array      # ["kubernetes", "aws"]
complexity: string           # simple, moderate, complex

# Decision/ADRs
decision_id: string          # ADR-003
decision_date: string        # ISO date
status: string               # accepted, superseded, deprecated

# Task/Commitments
due_date: string             # ISO date
status: string               # open, completed, cancelled
priority: string             # high, medium, low

# Social/People
person_name: string          # Canonical name
relationship: string         # colleague, client, vendor
last_contact: string         # ISO date
```

### Tool Parameter Quick Reference

```python
# Vector search
search_documents(
    query: str,                    # Natural language question (REQUIRED)
    collection_name: str = None,   # Scope to collection
    limit: int = 5,                # Max results (max: 50)
    threshold: float = 0.35,       # Min similarity score
    metadata_filter: dict = None,  # Custom field filters
    reviewed_by_human: bool = None,# True/False/None (all)
    min_quality_score: float = None,
    min_topic_relevance: float = None
)

# Graph relationships
query_relationships(
    query: str,                    # Natural language (REQUIRED)
    collection_name: str = None,
    num_results: int = 5,          # Max: 20
    threshold: float = 0.35,
    include_source_docs: bool = False,
    reviewed_by_human: bool = None,
    min_quality_score: float = None
)

# Temporal evolution
query_temporal(
    query: str,                    # Natural language (REQUIRED)
    collection_name: str = None,
    num_results: int = 10,         # Max: 50
    valid_from: str = None,        # ISO date filter
    valid_until: str = None,       # ISO date filter
    include_source_docs: bool = False,
    reviewed_by_human: bool = None,
    min_quality_score: float = None
)

# Ingest content
ingest_text(
    content: str,                  # Text to ingest (REQUIRED)
    collection_name: str,          # Target collection (REQUIRED)
    document_title: str = None,    # Auto-generated if None
    metadata: dict = None,         # Custom fields
    mode: str = "ingest",          # "ingest" or "reingest"
    topic: str = None,             # For relevance scoring
    reviewed_by_human: bool = False
)
```

---

## Related Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) — System architecture overview
- [FLOWS.md](./FLOWS.md) — Operational flows and patterns
- [MCP Server Instructions](../mcp-server/src/mcp/server.py) — Full tool documentation
