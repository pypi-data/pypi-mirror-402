# Implementation Plan: KB-8

**Add date range filtering to search_documents and list_documents**

---

## ⚠️ MANDATORY IMPLEMENTATION RULES - READ FIRST

**PAUSE AFTER EVERY COMMIT:**
- This plan contains 7 commits = 7 mandatory pause points
- After EACH commit: generate summary, STOP, wait for user approval
- Do NOT proceed to next unit without explicit "continue" response
- If --auto flag: skip pauses and run all units continuously

**Progress Tracking:**
- Current format: "Unit X of 7"
- Each unit = exactly one commit
- After each unit: STOP and wait for approval (unless --auto)

**Non-Negotiable:**
- 7 commits in this plan = 7 pauses during implementation
- Read the Incremental Implementation Schedule below for explicit pause points

**TDD Mode: ENABLED**
- Write failing tests FIRST (RED)
- Implement minimal code to pass (GREEN)
- Clean up and optimize (REFACTOR)

---

## Issue Summary

- **Type:** Executable Spec
- **Key:** KB-8
- **Summary:** Add date range filtering to search_documents and list_documents
- **Priority:** Medium
- **Status:** To Do
- **URL:** https://codingthefuturewithai.atlassian.net/browse/KB-8

**Background:** Users and agents working with RAG Memory need to segment knowledge by when it was captured. Currently, search and list operations return all matching documents regardless of when they were created or updated. This makes it difficult to focus on recent content or exclude stale information.

**Goal:** Enable date range filtering on search_documents and list_documents to let users scope queries to specific time periods.

---

## Acceptance Criteria

### 1. Date Parameters on Search
Users can pass optional `created_after`, `created_before`, `updated_after`, and `updated_before` parameters to `search_documents` to filter results by timestamp.

### 2. Date Parameters on List
Users can pass the same date parameters to `list_documents` to browse documents within a time window.

### 3. Combined Filtering
Date filters work in combination with existing collection and metadata filters - they narrow results, not replace other filters.

### 4. Web UI Date Picker
Web interface provides a date range picker component that applies these filters when browsing or searching documents.

---

## Codebase Analysis

### Test Framework
- **Framework:** pytest with anyio (async tests)
- **Test directory:** `mcp-server/tests/`
- **Integration tests:** `mcp-server/tests/integration/mcp/`
- **Test pattern:** `TestClassName` with `async def test_*` methods
- **Fixtures:** `mcp_session`, `setup_test_collection` from `conftest.py`

### Test Commands
```bash
# Run all tests
uv run pytest mcp-server/tests/

# Run specific test file
uv run pytest mcp-server/tests/integration/mcp/test_search_documents.py -v

# Run with coverage
uv run pytest mcp-server/tests/ --cov=mcp-server/src --cov-report=html
```

### Existing Date Filter Pattern (from query_temporal)
- Parameters: `valid_from: str | None = None`, `valid_until: str | None = None`
- Format: ISO 8601 date strings (e.g., `"2024-01-15"`)
- Docstring: `"ISO 8601 date (return facts valid AFTER/BEFORE this date)"`

### Files to Modify

| Layer | File | Line | Purpose |
|-------|------|------|---------|
| MCP Wrapper | `mcp-server/src/mcp/server.py` | 568, 1428 | Add 4 date params to `search_documents()` and `list_documents()` |
| Tool Impl | `mcp-server/src/mcp/tools.py` | 734, 3919 | Add 4 date params to impl functions |
| Search Layer | `mcp-server/src/retrieval/search.py` | 127 | Add date WHERE clauses to `search_chunks()` |
| Document Store | `mcp-server/src/ingestion/document_store.py` | 318 | Add date WHERE clauses to `list_source_documents()` |
| Backend API | `backend/app/main.py` | - | Add date params to REST endpoints |
| Frontend API | `frontend/src/rag/ragApi.ts` | 66, 78 | Add date params to API calls |
| Frontend UI | `frontend/src/rag/components/views/SearchView.tsx` | - | Add DatePicker |
| Frontend UI | `frontend/src/rag/components/views/DocumentsView.tsx` | - | Add DatePicker |

### Code Patterns to Follow
- MCP params: `param: str | None = None` (NO `Optional[]` - per CLAUDE.md rules)
- Date format: ISO 8601 strings
- WHERE clause pattern from existing filters (see `search.py:194-205`)

---

## Implementation Plan

### Phase 1: Tests (TDD RED Phase)
1. Create unit tests for date filtering SQL generation
2. Create integration tests for MCP tools with date params

### Phase 2: Backend - MCP Layer (TDD GREEN Phase)
3. Add date params to `search_documents` in `server.py:568`
4. Add date params to `list_documents` in `server.py:1428`
5. Add date params to `search_documents_impl` in `tools.py:734`
6. Add date params to `list_documents_impl` in `tools.py:3919`

### Phase 3: Backend - Data Layer (TDD GREEN Phase)
7. Add date filter WHERE clauses to `SimilaritySearch.search_chunks()` in `search.py:127`
8. Add date filter WHERE clauses to `DocumentStore.list_source_documents()` in `document_store.py:318`

### Phase 4: Backend REST API
9. Add date query params to REST endpoints in `backend/app/main.py`

### Phase 5: Frontend
10. Install `@mantine/dates` and `dayjs` dependencies
11. Add DatePicker to `SearchView.tsx` with preset options
12. Add DatePicker to `DocumentsView.tsx` for filtering
13. Update `ragApi.ts` to pass date params to API calls

---

## Testing Strategy

### TDD Workflow

**RED Phase - Write Failing Tests First:**

```python
# mcp-server/tests/unit/test_date_filtering.py
class TestDateFiltering:
    """Unit tests for date filtering logic."""

    def test_created_after_filters_older_documents(self):
        """Verify created_after excludes documents created before the date."""
        pass

    def test_created_before_filters_newer_documents(self):
        """Verify created_before excludes documents created after the date."""
        pass

    def test_updated_after_filters_by_update_time(self):
        """Verify updated_after uses updated_at column, not created_at."""
        pass

    def test_date_filters_combine_with_collection_filter(self):
        """Verify date filters AND with collection filter."""
        pass

    def test_date_filters_combine_with_metadata_filter(self):
        """Verify date filters AND with metadata filter."""
        pass

    def test_invalid_date_format_raises_error(self):
        """Verify non-ISO-8601 dates raise ValueError."""
        pass

    def test_future_dates_return_empty_results(self):
        """Verify future created_after returns no results."""
        pass
```

```python
# mcp-server/tests/integration/mcp/test_search_documents.py (extend)
class TestSearchDocumentsDateFiltering:
    """Integration tests for search_documents date filtering via MCP."""

    async def test_search_with_created_after(self, mcp_session, setup_test_collection):
        """Test that created_after filters search results."""
        pass

    async def test_search_with_created_before(self, mcp_session, setup_test_collection):
        """Test that created_before filters search results."""
        pass

    async def test_search_with_date_range(self, mcp_session, setup_test_collection):
        """Test created_after + created_before together."""
        pass

    async def test_search_date_filters_with_collection_scope(self, mcp_session, setup_test_collection):
        """Test date filters work with collection_name filter."""
        pass
```

```python
# mcp-server/tests/integration/mcp/test_document_crud.py (extend)
class TestListDocumentsDateFiltering:
    """Integration tests for list_documents date filtering via MCP."""

    async def test_list_with_created_after(self, mcp_session, setup_test_collection):
        """Test that created_after filters list results."""
        pass

    async def test_list_with_date_range(self, mcp_session, setup_test_collection):
        """Test created_after + created_before together."""
        pass
```

**GREEN Phase - Implement to Pass:**
- Implement date filtering in each layer
- Run tests after each implementation step

**REFACTOR Phase:**
- Clean up SQL query building
- Ensure consistent parameter naming
- Add docstrings

---

## Context7 Research

### Mantine DatePicker (v8)

**Package:** `@mantine/dates` (requires `dayjs`)

**Usage:**
```tsx
import { DatePickerInput } from '@mantine/dates';
import dayjs from 'dayjs';

function DateFilter() {
  const [dateRange, setDateRange] = useState<[Date | null, Date | null]>([null, null]);
  const today = dayjs();

  return (
    <DatePickerInput
      type="range"
      label="Filter by date"
      placeholder="Select date range"
      value={dateRange}
      onChange={setDateRange}
      clearable
      presets={[
        {
          value: [today.subtract(7, 'day').toDate(), today.toDate()],
          label: 'Last 7 days',
        },
        {
          value: [today.subtract(30, 'day').toDate(), today.toDate()],
          label: 'Last 30 days',
        },
        {
          value: [today.subtract(1, 'year').toDate(), today.toDate()],
          label: 'Last year',
        },
      ]}
    />
  );
}
```

**Key Points:**
- `type="range"` enables date range selection
- `presets` prop adds quick selection buttons
- Returns `[Date | null, Date | null]` tuple
- Convert to ISO 8601 for API: `date.toISOString().split('T')[0]`

---

## Documentation Updates

- Update MCP tool docstrings in `server.py` to document new date parameters
- No changes to `CLAUDE.md` expected (existing patterns apply)

---

## Commit Strategy

| # | Title | Description |
|---|-------|-------------|
| 1 | test: Add date filtering unit and integration tests | RED phase - write failing tests for date filtering |
| 2 | feat: Add date params to MCP search_documents and list_documents | GREEN phase - add params to MCP wrapper layer |
| 3 | feat: Implement date filtering in SimilaritySearch | GREEN phase - add WHERE clauses to search.py |
| 4 | feat: Implement date filtering in DocumentStore | GREEN phase - add WHERE clauses to document_store.py |
| 5 | feat: Add date params to REST API endpoints | Add date query params to backend API |
| 6 | chore: Install @mantine/dates and dayjs | Add frontend date picker dependencies |
| 7 | feat: Add DatePicker to SearchView and DocumentsView | UI implementation with presets |

---

## 🔄 Incremental Implementation Schedule

**CRITICAL: Each unit below = ONE mandatory pause point for user review**

**Total Pause Points:** 7

---

### Unit 1 of 7: Tests - Date filtering unit and integration tests

**Changes:**
- Create `mcp-server/tests/unit/test_date_filtering.py` with unit tests
- Extend `mcp-server/tests/integration/mcp/test_search_documents.py` with `TestSearchDocumentsDateFiltering`
- Extend `mcp-server/tests/integration/mcp/test_document_crud.py` with `TestListDocumentsDateFiltering`
- All tests should FAIL initially (RED phase)

**Commit message:**
```
test: Add date filtering unit and integration tests

RED phase - write failing tests for KB-8 date range filtering:
- Unit tests for date filter SQL generation
- Integration tests for search_documents with date params
- Integration tests for list_documents with date params

refs KB-8
```

⏸️ 🛑 **PAUSE POINT #1 - STOP AND WAIT FOR USER APPROVAL**

After committing this unit:
1. Generate unit summary showing what changed
2. Display "What would you like to do?" prompt with options: continue/review/revise/stop
3. STOP and WAIT for user response
4. Only proceed to Unit 2 after explicit approval

---

### Unit 2 of 7: Backend - Add date params to MCP tools

**Changes:**
- Add `created_after`, `created_before`, `updated_after`, `updated_before` params to `search_documents()` in `server.py:568`
- Add same params to `list_documents()` in `server.py:1428`
- Add params to `search_documents_impl()` in `tools.py:734`
- Add params to `list_documents_impl()` in `tools.py:3919`
- Pass params through to lower layers (but filtering not implemented yet)

**Commit message:**
```
feat: Add date params to MCP search_documents and list_documents

Add created_after, created_before, updated_after, updated_before
parameters to search_documents and list_documents MCP tools.
Parameters passed through to impl functions but filtering not
yet implemented in data layer.

refs KB-8
```

⏸️ 🛑 **PAUSE POINT #2 - STOP AND WAIT FOR USER APPROVAL**

After committing this unit:
1. Generate unit summary showing what changed
2. Display "What would you like to do?" prompt with options: continue/review/revise/stop
3. STOP and WAIT for user response
4. Only proceed to Unit 3 after explicit approval

---

### Unit 3 of 7: Backend - Implement date filtering in search.py

**Changes:**
- Add date params to `SimilaritySearch.search_chunks()` in `search.py:127`
- Add WHERE clauses for `sd.created_at` and `sd.updated_at` filtering
- Follow existing pattern from `reviewed_by_human` filter (lines 194-205)
- Parse ISO 8601 strings and validate format

**Commit message:**
```
feat: Implement date filtering in SimilaritySearch

Add WHERE clauses for created_after, created_before, updated_after,
updated_before to search_chunks() query. Filters on source_documents
table timestamps. Follows existing filter pattern.

refs KB-8
```

⏸️ 🛑 **PAUSE POINT #3 - STOP AND WAIT FOR USER APPROVAL**

After committing this unit:
1. Generate unit summary showing what changed
2. Run search tests: `uv run pytest mcp-server/tests/integration/mcp/test_search_documents.py -v`
3. Display "What would you like to do?" prompt with options: continue/review/revise/stop
4. STOP and WAIT for user response
5. Only proceed to Unit 4 after explicit approval

---

### Unit 4 of 7: Backend - Implement date filtering in document_store.py

**Changes:**
- Add date params to `DocumentStore.list_source_documents()` in `document_store.py:318`
- Add WHERE clauses for `sd.created_at` and `sd.updated_at` filtering
- Update both count query and main query

**Commit message:**
```
feat: Implement date filtering in DocumentStore

Add WHERE clauses for created_after, created_before, updated_after,
updated_before to list_source_documents() query. Applies to both
count and main queries.

refs KB-8
```

⏸️ 🛑 **PAUSE POINT #4 - STOP AND WAIT FOR USER APPROVAL**

After committing this unit:
1. Generate unit summary showing what changed
2. Run all backend tests: `uv run pytest mcp-server/tests/ -v`
3. Display "What would you like to do?" prompt with options: continue/review/revise/stop
4. STOP and WAIT for user response
5. Only proceed to Unit 5 after explicit approval

---

### Unit 5 of 7: Backend - Add date params to REST API

**Changes:**
- Add date query parameters to `/api/rag-memory/search` endpoint
- Add date query parameters to `/api/rag-memory/documents` endpoint
- Pass params through to MCP proxy calls

**Commit message:**
```
feat: Add date params to REST API endpoints

Add created_after, created_before, updated_after, updated_before
query parameters to /api/rag-memory/search and /api/rag-memory/documents
REST endpoints.

refs KB-8
```

⏸️ 🛑 **PAUSE POINT #5 - STOP AND WAIT FOR USER APPROVAL**

After committing this unit:
1. Generate unit summary showing what changed
2. Display "What would you like to do?" prompt with options: continue/review/revise/stop
3. STOP and WAIT for user response
4. Only proceed to Unit 6 after explicit approval

---

### Unit 6 of 7: Frontend - Install date picker dependencies

**Changes:**
- Add `@mantine/dates` to package.json dependencies
- Add `dayjs` to package.json dependencies
- Run `npm install`

**Commit message:**
```
chore: Install @mantine/dates and dayjs

Add Mantine dates package and dayjs for date range picker
functionality in SearchView and DocumentsView.

refs KB-8
```

⏸️ 🛑 **PAUSE POINT #6 - STOP AND WAIT FOR USER APPROVAL**

After committing this unit:
1. Generate unit summary showing what changed
2. Display "What would you like to do?" prompt with options: continue/review/revise/stop
3. STOP and WAIT for user response
4. Only proceed to Unit 7 after explicit approval

---

### Unit 7 of 7: Frontend - Add DatePicker to views

**Changes:**
- Add `DatePickerInput` component to `SearchView.tsx` with presets (Last 7 days, Last 30 days, Last year)
- Add `DatePickerInput` component to `DocumentsView.tsx`
- Update `ragApi.ts` to pass date params to API calls
- Wire up state management for date range selection

**Commit message:**
```
feat: Add DatePicker to SearchView and DocumentsView

Add date range filtering UI with Mantine DatePickerInput:
- Presets for Last 7 days, Last 30 days, Last year
- Date range state wired to API calls
- ragApi.ts updated to pass date params

refs KB-8
```

⏸️ 🛑 **PAUSE POINT #7 - FINAL UNIT - STOP AND WAIT FOR USER APPROVAL**

After committing this unit:
1. Generate unit summary showing what changed
2. Display "What would you like to do?" prompt
3. STOP and WAIT for user response
4. After approval: Proceed to Implementation Summary

---

## Implementation Complete Checklist

After all units are implemented:

- [ ] All tests pass: `uv run pytest mcp-server/tests/ -v`
- [ ] Frontend builds: `cd frontend && npm run build`
- [ ] Manual testing of date filtering in UI
- [ ] Security review recommended before PR

**Next Step:** Run `/devflow:complete-issue KB-8` to create PR and close issue.
