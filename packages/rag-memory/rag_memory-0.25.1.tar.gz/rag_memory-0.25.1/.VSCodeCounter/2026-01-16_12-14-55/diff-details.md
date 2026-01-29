# Diff Details

Date : 2026-01-16 12:14:55

Directory /Users/timkitchens/projects/ai-projects/rag-memory

Total : 53 files,  8879 codes, 654 comments, 2296 blanks, all 11829 lines

[Summary](results.md) / [Details](details.md) / [Diff Summary](diff.md) / Diff Details

## Files
| filename | language | code | comment | blank | total |
| :--- | :--- | ---: | ---: | ---: | ---: |
| [backend/alembic/versions/209efbed60a4\_add\_langgraph\_checkpointer\_tables.py](/backend/alembic/versions/209efbed60a4_add_langgraph_checkpointer_tables.py) | Python | -30 | -2 | -4 | -36 |
| [backend/app/config.py](/backend/app/config.py) | Python | 1 | 0 | 0 | 1 |
| [backend/app/main.py](/backend/app/main.py) | Python | 60 | 4 | 18 | 82 |
| [backend/app/rag/mcp\_proxy.py](/backend/app/rag/mcp_proxy.py) | Python | 7 | 0 | 0 | 7 |
| [backend/app/rag\_agent/agent.py](/backend/app/rag_agent/agent.py) | Python | -5 | -1 | -1 | -7 |
| [backend/tests/conftest.py](/backend/tests/conftest.py) | Python | 86 | 5 | 31 | 122 |
| [backend/tests/integration/test\_mcp\_proxy.py](/backend/tests/integration/test_mcp_proxy.py) | Python | 486 | 8 | 170 | 664 |
| [backend/tests/integration/test\_router.py](/backend/tests/integration/test_router.py) | Python | 227 | 9 | 71 | 307 |
| [backend/tests/unit/test\_agent.py](/backend/tests/unit/test_agent.py) | Python | 112 | 9 | 45 | 166 |
| [backend/tests/unit/test\_agent\_factory.py](/backend/tests/unit/test_agent_factory.py) | Python | 55 | 0 | 26 | 81 |
| [backend/tests/unit/test\_checkpointer.py](/backend/tests/unit/test_checkpointer.py) | Python | 78 | 6 | 31 | 115 |
| [backend/tests/unit/test\_database.py](/backend/tests/unit/test_database.py) | Python | 76 | 1 | 30 | 107 |
| [backend/tests/unit/test\_main.py](/backend/tests/unit/test_main.py) | Python | 115 | 9 | 45 | 169 |
| [backend/tests/unit/test\_search\_tools.py](/backend/tests/unit/test_search_tools.py) | Python | 185 | 5 | 67 | 257 |
| [backend/tests/unit/test\_ui\_tools.py](/backend/tests/unit/test_ui_tools.py) | Python | 119 | 0 | 44 | 163 |
| [frontend/e2e/example.spec.ts](/frontend/e2e/example.spec.ts) | TypeScript | 7 | 1 | 3 | 11 |
| [frontend/playwright.config.ts](/frontend/playwright.config.ts) | TypeScript | 32 | 15 | 5 | 52 |
| [frontend/src/rag/components/ConversationSidebar.tsx](/frontend/src/rag/components/ConversationSidebar.tsx) | TypeScript JSX | 1 | 0 | 0 | 1 |
| [frontend/src/rag/components/dashboard/ReviewStatusChart.tsx](/frontend/src/rag/components/dashboard/ReviewStatusChart.tsx) | TypeScript JSX | -18 | 0 | 0 | -18 |
| [frontend/src/rag/ragApi.ts](/frontend/src/rag/ragApi.ts) | TypeScript | 6 | 0 | 1 | 7 |
| [frontend/tests/components/ChatInput.test.tsx](/frontend/tests/components/ChatInput.test.tsx) | TypeScript JSX | 248 | 33 | 80 | 361 |
| [frontend/tests/components/CollectionBrowser.test.tsx](/frontend/tests/components/CollectionBrowser.test.tsx) | TypeScript JSX | 390 | 37 | 112 | 539 |
| [frontend/tests/components/ConfirmDeleteModal.test.tsx](/frontend/tests/components/ConfirmDeleteModal.test.tsx) | TypeScript JSX | 169 | 9 | 31 | 209 |
| [frontend/tests/components/ConversationSidebar.test.tsx](/frontend/tests/components/ConversationSidebar.test.tsx) | TypeScript JSX | 300 | 23 | 89 | 412 |
| [frontend/tests/components/DocumentModal.test.tsx](/frontend/tests/components/DocumentModal.test.tsx) | TypeScript JSX | 306 | 21 | 56 | 383 |
| [frontend/tests/components/IngestionModal.test.tsx](/frontend/tests/components/IngestionModal.test.tsx) | TypeScript JSX | 572 | 59 | 145 | 776 |
| [frontend/tests/components/KnowledgeGraphView.test.tsx](/frontend/tests/components/KnowledgeGraphView.test.tsx) | TypeScript JSX | 133 | 10 | 21 | 164 |
| [frontend/tests/components/MessageBubble.test.tsx](/frontend/tests/components/MessageBubble.test.tsx) | TypeScript JSX | 217 | 11 | 58 | 286 |
| [frontend/tests/components/MessageList.test.tsx](/frontend/tests/components/MessageList.test.tsx) | TypeScript JSX | 184 | 11 | 47 | 242 |
| [frontend/tests/components/SearchResults.test.tsx](/frontend/tests/components/SearchResults.test.tsx) | TypeScript JSX | 120 | 10 | 24 | 154 |
| [frontend/tests/components/SearchView.test.tsx](/frontend/tests/components/SearchView.test.tsx) | TypeScript JSX | 308 | 17 | 100 | 425 |
| [frontend/tests/components/StarterPrompts.test.tsx](/frontend/tests/components/StarterPrompts.test.tsx) | TypeScript JSX | 135 | 10 | 40 | 185 |
| [frontend/tests/components/TemporalTimeline.test.tsx](/frontend/tests/components/TemporalTimeline.test.tsx) | TypeScript JSX | 105 | 9 | 17 | 131 |
| [frontend/tests/components/ToolProposalCard.test.tsx](/frontend/tests/components/ToolProposalCard.test.tsx) | TypeScript JSX | 273 | 21 | 56 | 350 |
| [frontend/tests/components/dashboard/Charts.test.tsx](/frontend/tests/components/dashboard/Charts.test.tsx) | TypeScript JSX | 104 | 9 | 21 | 134 |
| [frontend/tests/components/dashboard/DashboardView.test.tsx](/frontend/tests/components/dashboard/DashboardView.test.tsx) | TypeScript JSX | 216 | 13 | 46 | 275 |
| [frontend/tests/components/dashboard/StatsCards.test.tsx](/frontend/tests/components/dashboard/StatsCards.test.tsx) | TypeScript JSX | 118 | 7 | 31 | 156 |
| [frontend/tests/components/layout/AppLayout.test.tsx](/frontend/tests/components/layout/AppLayout.test.tsx) | TypeScript JSX | 135 | 7 | 27 | 169 |
| [frontend/tests/components/layout/LeftNavigation.test.tsx](/frontend/tests/components/layout/LeftNavigation.test.tsx) | TypeScript JSX | 124 | 17 | 40 | 181 |
| [frontend/tests/components/layout/MainContent.test.tsx](/frontend/tests/components/layout/MainContent.test.tsx) | TypeScript JSX | 98 | 7 | 32 | 137 |
| [frontend/tests/components/layout/RightPanel.test.tsx](/frontend/tests/components/layout/RightPanel.test.tsx) | TypeScript JSX | 22 | 7 | 6 | 35 |
| [frontend/tests/components/layout/TopBar.test.tsx](/frontend/tests/components/layout/TopBar.test.tsx) | TypeScript JSX | 35 | 6 | 9 | 50 |
| [frontend/tests/components/views/DocumentsView.test.tsx](/frontend/tests/components/views/DocumentsView.test.tsx) | TypeScript JSX | 290 | 16 | 70 | 376 |
| [frontend/tests/integration/chat-streaming.test.tsx](/frontend/tests/integration/chat-streaming.test.tsx) | TypeScript JSX | 219 | 40 | 29 | 288 |
| [frontend/tests/mocks/handlers.ts](/frontend/tests/mocks/handlers.ts) | TypeScript | 353 | 15 | 34 | 402 |
| [frontend/tests/mocks/server.ts](/frontend/tests/mocks/server.ts) | TypeScript | 3 | 1 | 2 | 6 |
| [frontend/tests/mocks/sse-mock.ts](/frontend/tests/mocks/sse-mock.ts) | TypeScript | 149 | 34 | 21 | 204 |
| [frontend/tests/setup.ts](/frontend/tests/setup.ts) | TypeScript | 38 | 8 | 9 | 55 |
| [frontend/tests/unit/ragApi.test.ts](/frontend/tests/unit/ragApi.test.ts) | TypeScript | 445 | 33 | 97 | 575 |
| [frontend/tests/unit/sseClient.test.ts](/frontend/tests/unit/sseClient.test.ts) | TypeScript | 497 | 28 | 118 | 643 |
| [frontend/tests/unit/store.test.ts](/frontend/tests/unit/store.test.ts) | TypeScript | 899 | 46 | 241 | 1,186 |
| [frontend/vitest.config.ts](/frontend/vitest.config.ts) | TypeScript | 27 | 7 | 2 | 36 |
| [mcp-server/src/mcp/http\_routes.py](/mcp-server/src/mcp/http_routes.py) | Python | 47 | 3 | 3 | 53 |

[Summary](results.md) / [Details](details.md) / [Diff Summary](diff.md) / Diff Details