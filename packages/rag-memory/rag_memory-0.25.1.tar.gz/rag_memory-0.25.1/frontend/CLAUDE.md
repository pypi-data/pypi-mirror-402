# CLAUDE.md

This file provides guidance to Claude Code when working with the RAG Memory frontend.

## Critical Rules

### Ask Permission Before Installing Dependencies

**Ask before running:** `npm install`, `npm add`, or modifying `package.json` dependencies.

### Never Edit dist/ Manually

The `dist/` directory contains build output. Always run `npm run build` to regenerate it.

### State Updates Must Flow Through Zustand

Never mutate state directly. All state changes go through store actions:
```typescript
// Correct
useRagStore.getState().selectCollection(id)

// Wrong - direct mutation
useRagStore.setState({ selectedCollectionId: id })
```

### SSE Not WebSocket

The chat streaming uses `ChatSSEClient` which implements Server-Sent Events (fetch + ReadableStream), not WebSocket protocol. Don't try to add WebSocket features.

---

## Quick Reference

```bash
# Development
npm install                      # Install dependencies
npm run dev                      # Start dev server (localhost:5173)
npm run build                    # Build for production
npm run typecheck                # Type-check without emitting

# The backend must be running on localhost:8000 for API calls to work
```

**Environment Variables (.env):**
```bash
VITE_API_URL=http://localhost:8000        # Backend URL
VITE_MCP_SERVER_URL=http://localhost:3001 # MCP server (for direct file uploads)
```

---

## Project Structure

```
src/
├── main.tsx                    # Entry point, MantineProvider setup
├── App.tsx                     # Root component, store init
└── rag/
    ├── api.ts                  # ChatSSEClient (SSE streaming)
    ├── ragApi.ts               # REST API functions
    ├── store.ts                # Zustand state management (~300 actions)
    ├── types.ts                # TypeScript interfaces
    ├── theme/
    │   └── lumentor.ts         # Mantine theme (Amber/Teal palette)
    ├── styles/
    │   └── global.css          # Global CSS, animations, utilities
    └── components/
        ├── layout/
        │   ├── AppLayout.tsx   # 3-column container
        │   ├── TopBar.tsx      # Header with branding
        │   ├── LeftNavigation.tsx  # Nav + conversation sidebar
        │   └── MainContent.tsx # View router
        ├── views/
        │   ├── DocumentsView.tsx   # Document grid
        │   └── SearchView.tsx      # 3-tab search (semantic/graph/temporal)
        ├── modals/
        │   ├── IngestionModal.tsx  # Text/URL/File upload
        │   └── ConfirmDeleteModal.tsx
        ├── visualizations/
        │   ├── GraphVisualization.tsx   # vis-network graph
        │   └── TimelineVisualization.tsx # vis-timeline
        ├── ChatInput.tsx       # Message input
        ├── MessageList.tsx     # Message history
        ├── MessageBubble.tsx   # Individual message
        ├── CollectionBrowser.tsx # Collection CRUD
        └── ConversationSidebar.tsx # Conversation list
```

---

## Architecture

### Tech Stack

- **React 19** + **TypeScript** (strict mode)
- **Vite** (dev server on 5173, proxies /api → localhost:8000)
- **Mantine 8** (UI components + theming)
- **Zustand** (global state management)
- **vis-network/vis-timeline** (graph/timeline visualizations)

### View-Based Navigation

No React Router. `AppLayout` manages a simple `View` state:
```typescript
type View = 'chat' | 'collections' | 'documents' | 'search'
```
`MainContent` renders the appropriate component based on `activeView`.

### State Management (Zustand)

Single store in `store.ts` with sections:
- **Chat State:** messages, conversations, sseClient, streaming, tool executions
- **RAG State:** collections, documents, search results
- **Streaming Content:** temporary results cleared after each message

Actions are grouped by feature and follow the pattern:
```typescript
loadCollections: async () => {
  try {
    const collections = await api.getCollections()
    set({ collections })
  } catch (error) {
    set({ error: error.message })
  }
}
```

### API Layer

Two integration points:

1. **SSE Stream** (`api.ts`): `ChatSSEClient` handles chat completions via `fetch()` + `ReadableStream`
   - Events: `token`, `done`, `error`, `tool_start`, `tool_end`, `search_results`, etc.
   - Uses `AbortController` for cancellation

2. **REST API** (`ragApi.ts`): Standard Axios calls for CRUD
   - Collections: `GET/POST/DELETE /api/rag-memory/collections`
   - Documents: `GET/DELETE /api/rag-memory/documents`
   - Search: `POST /api/rag-memory/search`

### Proxy Configuration

Vite proxies `/api/*` to the backend. Frontend never calls MCP server directly except for file uploads.

---

## Design System (Lumentor)

### Color Palette

```css
--charcoal: #1a1714      /* Base background */
--charcoal-light: #2a2520
--amber: #f59e0b         /* Primary accent */
--amber-dark: #d97706
--teal: #0f766e          /* Secondary accent */
--sienna: #ea580c        /* Destructive/error */
--cream: #fafaf9         /* Text */
--warm-gray: #a8a29e     /* Secondary text */
```

### Typography

- **Headings:** Playfair Display (serif)
- **Body:** IBM Plex Sans (sans-serif)
- **Code:** Fira Code (monospace)

### CSS Utilities

```css
.display-font    /* Playfair Display */
.code-font       /* Fira Code */
.text-gradient   /* Amber gradient */
.text-amber      /* Amber color */
.card-hover      /* 3D lift on hover */
.shimmer         /* Loading animation */
```

---

## Code Patterns

### Adding a New View

1. Create component in `components/views/NewView.tsx`
2. Add to `View` type in `AppLayout.tsx`
3. Add navigation button in `LeftNavigation.tsx`
4. Add render case in `MainContent.tsx`

### Adding a New Modal

1. Create component in `components/modals/NewModal.tsx`
2. Add open/close state to Zustand store
3. Add action to toggle: `openNewModal: () => set({ newModalOpen: true })`
4. Render modal in parent component with Mantine's `<Modal>`

### Adding New SSE Events

1. Add event type to `SSEEventType` in `types.ts`
2. Add handler case in `handleEvent()` in `api.ts`
3. Add state field in store if needed
4. Update `MessageBubble.tsx` to render the new content type

### Adding API Endpoints

1. Add function in `ragApi.ts`:
   ```typescript
   export const newEndpoint = async (params: Params): Promise<Response> => {
     const response = await axios.post('/api/new-endpoint', params)
     return response.data
   }
   ```
2. Add store action that calls it
3. Call action from component

---

## Known Quirks

**Tool execution tracking:** Tools identified by `id`, not insertion order. The `currentToolExecutions` map handles parallel tool calls correctly.

**Streaming content lifecycle:** `currentSearchResults`, `currentKnowledgeGraph`, etc. are cleared on each new message. They're temporary display state.

**Mantine v8 breaking changes:** Component APIs differ from v7 docs online. Check actual imports.

**vis-network performance:** Large graphs (500+ nodes) can lag. Consider pagination for relationship queries.

---

## Debugging

**Check Vite proxy:**
```bash
# API calls should appear in terminal running npm run dev
# If 404, check vite.config.ts proxy settings
```

**Check SSE stream:**
```javascript
// In browser DevTools > Network > filter "stream"
// Look for /api/chat/stream request
// Events tab shows SSE messages
```

**Check Zustand state:**
```javascript
// In browser console
window.__ZUSTAND_DEVTOOLS__ // if devtools enabled
// Or add to any component:
console.log(useRagStore.getState())
```

**Common fixes:**
- "Failed to fetch" → Backend not running on port 8000
- "CORS error" → Vite proxy misconfigured or hitting MCP server directly
- "TypeError: Cannot read property" → Check SSE event parsing in api.ts
- Stale state after action → Ensure store action calls `set()` correctly
- Modal not closing → Check if `opened` prop tied to correct store state
