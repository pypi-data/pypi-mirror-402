# Details

Date : 2026-01-14 17:53:37

Directory /Users/timkitchens/projects/ai-projects/rag-memory

Total : 395 files,  90342 codes, 6471 comments, 17040 blanks, all 113853 lines

[Summary](results.md) / Details / [Diff Summary](diff.md) / [Diff Details](diff-details.md)

## Files
| filename | language | code | comment | blank | total |
| :--- | :--- | ---: | ---: | ---: | ---: |
| [backend/alembic.ini](/backend/alembic.ini) | Ini | 93 | 0 | 25 | 118 |
| [backend/alembic/env.py](/backend/alembic/env.py) | Python | 55 | 14 | 25 | 94 |
| [backend/alembic/versions/209efbed60a4\_add\_langgraph\_checkpointer\_tables.py](/backend/alembic/versions/209efbed60a4_add_langgraph_checkpointer_tables.py) | Python | 47 | 6 | 13 | 66 |
| [backend/alembic/versions/eb0488e04b85\_initial\_schema.py](/backend/alembic/versions/eb0488e04b85_initial_schema.py) | Python | 50 | 5 | 10 | 65 |
| [backend/alembic/versions/f72298d0b136\_add\_is\_pinned\_to\_conversations.py](/backend/alembic/versions/f72298d0b136_add_is_pinned_to_conversations.py) | Python | 17 | 3 | 9 | 29 |
| [backend/app/\_\_init\_\_.py](/backend/app/__init__.py) | Python | 1 | 0 | 1 | 2 |
| [backend/app/config.py](/backend/app/config.py) | Python | 35 | 9 | 16 | 60 |
| [backend/app/database.py](/backend/app/database.py) | Python | 36 | 3 | 11 | 50 |
| [backend/app/main.py](/backend/app/main.py) | Python | 47 | 9 | 18 | 74 |
| [backend/app/rag/\_\_init\_\_.py](/backend/app/rag/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [backend/app/rag/mcp\_proxy.py](/backend/app/rag/mcp_proxy.py) | Python | 376 | 51 | 81 | 508 |
| [backend/app/rag/models.py](/backend/app/rag/models.py) | Python | 32 | 2 | 16 | 50 |
| [backend/app/rag/router.py](/backend/app/rag/router.py) | Python | 287 | 23 | 77 | 387 |
| [backend/app/rag/schemas.py](/backend/app/rag/schemas.py) | Python | 72 | 5 | 35 | 112 |
| [backend/app/rag\_agent/\_\_init\_\_.py](/backend/app/rag_agent/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [backend/app/rag\_agent/agent.py](/backend/app/rag_agent/agent.py) | Python | 91 | 15 | 34 | 140 |
| [backend/app/rag\_agent/prompts.py](/backend/app/rag_agent/prompts.py) | Python | 154 | 14 | 65 | 233 |
| [backend/app/shared/\_\_init\_\_.py](/backend/app/shared/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [backend/app/shared/agent\_factory.py](/backend/app/shared/agent_factory.py) | Python | 35 | 2 | 18 | 55 |
| [backend/app/shared/chat\_bridge.py](/backend/app/shared/chat_bridge.py) | Python | 572 | 83 | 151 | 806 |
| [backend/app/shared/checkpointer.py](/backend/app/shared/checkpointer.py) | Python | 28 | 6 | 15 | 49 |
| [backend/app/tools/\_\_init\_\_.py](/backend/app/tools/__init__.py) | Python | 8 | 0 | 4 | 12 |
| [backend/app/tools/search\_tools.py](/backend/app/tools/search_tools.py) | Python | 479 | 31 | 126 | 636 |
| [backend/app/tools/ui\_tools.py](/backend/app/tools/ui_tools.py) | Python | 93 | 3 | 17 | 113 |
| [backend/inspect\_checkpointer\_schema.py](/backend/inspect_checkpointer_schema.py) | Python | 39 | 2 | 9 | 50 |
| [backend/scripts/setup\_langgraph\_schema.py](/backend/scripts/setup_langgraph_schema.py) | Python | 49 | 9 | 19 | 77 |
| [backend/seed\_data.py](/backend/seed_data.py) | Python | 98 | 5 | 21 | 124 |
| [backend/test\_endpoints.py](/backend/test_endpoints.py) | Python | 313 | 50 | 51 | 414 |
| [config/config.example.yaml](/config/config.example.yaml) | YAML | 15 | 26 | 8 | 49 |
| [config/config.local.yaml](/config/config.local.yaml) | YAML | 13 | 47 | 11 | 71 |
| [config/config.test.yaml](/config/config.test.yaml) | YAML | 11 | 18 | 8 | 37 |
| [config/config.yaml](/config/config.yaml) | YAML | 9 | 18 | 7 | 34 |
| [deploy/alembic/alembic.ini](/deploy/alembic/alembic.ini) | Ini | 122 | 0 | 27 | 149 |
| [deploy/alembic/env.py](/deploy/alembic/env.py) | Python | 56 | 16 | 23 | 95 |
| [deploy/alembic/versions/001\_baseline\_fresh\_schema.py](/deploy/alembic/versions/001_baseline_fresh_schema.py) | Python | 111 | 16 | 27 | 154 |
| [deploy/alembic/versions/002\_add\_trust\_system.py](/deploy/alembic/versions/002_add_trust_system.py) | Python | 109 | 25 | 34 | 168 |
| [deploy/alembic/versions/003\_add\_evaluation\_system.py](/deploy/alembic/versions/003_add_evaluation_system.py) | Python | 162 | 40 | 42 | 244 |
| [deploy/alembic/versions/004\_rename\_topic\_used\_to\_topic\_provided.py](/deploy/alembic/versions/004_rename_topic_used_to_topic_provided.py) | Python | 20 | 1 | 10 | 31 |
| [deploy/alembic/versions/005\_add\_content\_hash.py](/deploy/alembic/versions/005_add_content_hash.py) | Python | 36 | 5 | 13 | 54 |
| [deploy/docker/Dockerfile](/deploy/docker/Dockerfile) | Docker | 23 | 18 | 13 | 54 |
| [deploy/docker/compose/docker-compose.dev.yml](/deploy/docker/compose/docker-compose.dev.yml) | YAML | 73 | 33 | 8 | 114 |
| [deploy/docker/compose/docker-compose.instance.yml](/deploy/docker/compose/docker-compose.instance.yml) | YAML | 131 | 47 | 8 | 186 |
| [deploy/docker/compose/docker-compose.template.yml](/deploy/docker/compose/docker-compose.template.yml) | YAML | 129 | 36 | 8 | 173 |
| [deploy/docker/compose/docker-compose.test.yml](/deploy/docker/compose/docker-compose.test.yml) | YAML | 75 | 51 | 9 | 135 |
| [deploy/docker/init.sql](/deploy/docker/init.sql) | SQLite | 88 | 27 | 13 | 128 |
| [docker-compose.web.yml](/docker-compose.web.yml) | YAML | 24 | 1 | 3 | 28 |
| [frontend/docker-compose.web.yml](/frontend/docker-compose.web.yml) | YAML | 22 | 0 | 3 | 25 |
| [frontend/index.html](/frontend/index.html) | HTML | 13 | 0 | 1 | 14 |
| [frontend/mockup-v2.html](/frontend/mockup-v2.html) | HTML | 2,218 | 35 | 332 | 2,585 |
| [frontend/src/App.tsx](/frontend/src/App.tsx) | TypeScript JSX | 12 | 2 | 6 | 20 |
| [frontend/src/main.tsx](/frontend/src/main.tsx) | TypeScript JSX | 22 | 3 | 5 | 30 |
| [frontend/src/rag/api.ts](/frontend/src/rag/api.ts) | TypeScript | 103 | 11 | 23 | 137 |
| [frontend/src/rag/components/ChatInput.tsx](/frontend/src/rag/components/ChatInput.tsx) | TypeScript JSX | 232 | 17 | 30 | 279 |
| [frontend/src/rag/components/CollectionBrowser.tsx](/frontend/src/rag/components/CollectionBrowser.tsx) | TypeScript JSX | 792 | 40 | 64 | 896 |
| [frontend/src/rag/components/ConversationSidebar.tsx](/frontend/src/rag/components/ConversationSidebar.tsx) | TypeScript JSX | 564 | 36 | 45 | 645 |
| [frontend/src/rag/components/DocumentModal.tsx](/frontend/src/rag/components/DocumentModal.tsx) | TypeScript JSX | 544 | 29 | 21 | 594 |
| [frontend/src/rag/components/KnowledgeGraphView.tsx](/frontend/src/rag/components/KnowledgeGraphView.tsx) | TypeScript JSX | 146 | 5 | 10 | 161 |
| [frontend/src/rag/components/LinkifiedContent.tsx](/frontend/src/rag/components/LinkifiedContent.tsx) | TypeScript JSX | 175 | 46 | 28 | 249 |
| [frontend/src/rag/components/MessageBubble.tsx](/frontend/src/rag/components/MessageBubble.tsx) | TypeScript JSX | 143 | 31 | 16 | 190 |
| [frontend/src/rag/components/MessageList.tsx](/frontend/src/rag/components/MessageList.tsx) | TypeScript JSX | 126 | 12 | 15 | 153 |
| [frontend/src/rag/components/SearchResults.tsx](/frontend/src/rag/components/SearchResults.tsx) | TypeScript JSX | 87 | 7 | 10 | 104 |
| [frontend/src/rag/components/StarterPrompts.tsx](/frontend/src/rag/components/StarterPrompts.tsx) | TypeScript JSX | 86 | 9 | 11 | 106 |
| [frontend/src/rag/components/TemporalTimeline.tsx](/frontend/src/rag/components/TemporalTimeline.tsx) | TypeScript JSX | 63 | 7 | 9 | 79 |
| [frontend/src/rag/components/ToolProposalCard.tsx](/frontend/src/rag/components/ToolProposalCard.tsx) | TypeScript JSX | 272 | 18 | 15 | 305 |
| [frontend/src/rag/components/WebSearchResults.tsx](/frontend/src/rag/components/WebSearchResults.tsx) | TypeScript JSX | 82 | 7 | 9 | 98 |
| [frontend/src/rag/components/dashboard/ActorTypeChart.tsx](/frontend/src/rag/components/dashboard/ActorTypeChart.tsx) | TypeScript JSX | 85 | 6 | 9 | 100 |
| [frontend/src/rag/components/dashboard/CollectionQualityChart.tsx](/frontend/src/rag/components/dashboard/CollectionQualityChart.tsx) | TypeScript JSX | 91 | 5 | 7 | 103 |
| [frontend/src/rag/components/dashboard/CrawlStatsSection.tsx](/frontend/src/rag/components/dashboard/CrawlStatsSection.tsx) | TypeScript JSX | 135 | 6 | 10 | 151 |
| [frontend/src/rag/components/dashboard/DashboardView.tsx](/frontend/src/rag/components/dashboard/DashboardView.tsx) | TypeScript JSX | 244 | 31 | 23 | 298 |
| [frontend/src/rag/components/dashboard/FileTypeChart.tsx](/frontend/src/rag/components/dashboard/FileTypeChart.tsx) | TypeScript JSX | 112 | 6 | 9 | 127 |
| [frontend/src/rag/components/dashboard/IngestMethodChart.tsx](/frontend/src/rag/components/dashboard/IngestMethodChart.tsx) | TypeScript JSX | 102 | 6 | 9 | 117 |
| [frontend/src/rag/components/dashboard/IngestionTimeline.tsx](/frontend/src/rag/components/dashboard/IngestionTimeline.tsx) | TypeScript JSX | 133 | 7 | 8 | 148 |
| [frontend/src/rag/components/dashboard/QualityHistogram.tsx](/frontend/src/rag/components/dashboard/QualityHistogram.tsx) | TypeScript JSX | 58 | 4 | 6 | 68 |
| [frontend/src/rag/components/dashboard/ReviewStatusChart.tsx](/frontend/src/rag/components/dashboard/ReviewStatusChart.tsx) | TypeScript JSX | 88 | 4 | 8 | 100 |
| [frontend/src/rag/components/dashboard/StatsCards.tsx](/frontend/src/rag/components/dashboard/StatsCards.tsx) | TypeScript JSX | 97 | 5 | 7 | 109 |
| [frontend/src/rag/components/dashboard/index.ts](/frontend/src/rag/components/dashboard/index.ts) | TypeScript | 10 | 4 | 3 | 17 |
| [frontend/src/rag/components/layout/AppLayout.tsx](/frontend/src/rag/components/layout/AppLayout.tsx) | TypeScript JSX | 47 | 10 | 8 | 65 |
| [frontend/src/rag/components/layout/LeftNavigation.tsx](/frontend/src/rag/components/layout/LeftNavigation.tsx) | TypeScript JSX | 144 | 17 | 18 | 179 |
| [frontend/src/rag/components/layout/MainContent.tsx](/frontend/src/rag/components/layout/MainContent.tsx) | TypeScript JSX | 61 | 14 | 10 | 85 |
| [frontend/src/rag/components/layout/RightPanel.tsx](/frontend/src/rag/components/layout/RightPanel.tsx) | TypeScript JSX | 3 | 16 | 3 | 22 |
| [frontend/src/rag/components/layout/TopBar.tsx](/frontend/src/rag/components/layout/TopBar.tsx) | TypeScript JSX | 64 | 11 | 5 | 80 |
| [frontend/src/rag/components/modals/ConfirmDeleteModal.tsx](/frontend/src/rag/components/modals/ConfirmDeleteModal.tsx) | TypeScript JSX | 139 | 10 | 13 | 162 |
| [frontend/src/rag/components/modals/IngestionModal.tsx](/frontend/src/rag/components/modals/IngestionModal.tsx) | TypeScript JSX | 1,193 | 116 | 138 | 1,447 |
| [frontend/src/rag/components/modals/LinkToCollectionModal.tsx](/frontend/src/rag/components/modals/LinkToCollectionModal.tsx) | TypeScript JSX | 218 | 17 | 16 | 251 |
| [frontend/src/rag/components/modals/PageRelevanceDisplay.tsx](/frontend/src/rag/components/modals/PageRelevanceDisplay.tsx) | TypeScript JSX | 294 | 14 | 27 | 335 |
| [frontend/src/rag/components/views/DocumentsView.tsx](/frontend/src/rag/components/views/DocumentsView.tsx) | TypeScript JSX | 413 | 38 | 39 | 490 |
| [frontend/src/rag/components/views/SearchView.tsx](/frontend/src/rag/components/views/SearchView.tsx) | TypeScript JSX | 608 | 29 | 48 | 685 |
| [frontend/src/rag/components/visualizations/GraphVisualization.tsx](/frontend/src/rag/components/visualizations/GraphVisualization.tsx) | TypeScript JSX | 254 | 16 | 19 | 289 |
| [frontend/src/rag/components/visualizations/TimelineVisualization.tsx](/frontend/src/rag/components/visualizations/TimelineVisualization.tsx) | TypeScript JSX | 230 | 18 | 18 | 266 |
| [frontend/src/rag/ragApi.ts](/frontend/src/rag/ragApi.ts) | TypeScript | 355 | 68 | 59 | 482 |
| [frontend/src/rag/store.ts](/frontend/src/rag/store.ts) | TypeScript | 742 | 78 | 75 | 895 |
| [frontend/src/rag/styles/global.css](/frontend/src/rag/styles/global.css) | CSS | 283 | 24 | 47 | 354 |
| [frontend/src/rag/theme/lumentor.ts](/frontend/src/rag/theme/lumentor.ts) | TypeScript | 183 | 6 | 15 | 204 |
| [frontend/src/rag/types.ts](/frontend/src/rag/types.ts) | TypeScript | 251 | 55 | 45 | 351 |
| [frontend/src/vite-env.d.ts](/frontend/src/vite-env.d.ts) | TypeScript | 6 | 1 | 3 | 10 |
| [frontend/vite.config.ts](/frontend/vite.config.ts) | TypeScript | 14 | 1 | 2 | 17 |
| [graphiti-patched/Dockerfile](/graphiti-patched/Dockerfile) | Docker | 50 | 15 | 14 | 79 |
| [graphiti-patched/Makefile](/graphiti-patched/Makefile) | Makefile | 18 | 7 | 8 | 33 |
| [graphiti-patched/conftest.py](/graphiti-patched/conftest.py) | Python | 5 | 2 | 4 | 11 |
| [graphiti-patched/docker-compose.test.yml](/graphiti-patched/docker-compose.test.yml) | YAML | 38 | 0 | 2 | 40 |
| [graphiti-patched/docker-compose.yml](/graphiti-patched/docker-compose.yml) | YAML | 90 | 0 | 3 | 93 |
| [graphiti-patched/ellipsis.yaml](/graphiti-patched/ellipsis.yaml) | YAML | 17 | 1 | 2 | 20 |
| [graphiti-patched/examples/azure-openai/azure\_openai\_neo4j.py](/graphiti-patched/examples/azure-openai/azure_openai_neo4j.py) | Python | 135 | 58 | 33 | 226 |
| [graphiti-patched/examples/ecommerce/runner.py](/graphiti-patched/examples/ecommerce/runner.py) | Python | 90 | 5 | 29 | 124 |
| [graphiti-patched/examples/opentelemetry/otel\_stdout\_example.py](/graphiti-patched/examples/opentelemetry/otel_stdout_example.py) | Python | 101 | 0 | 25 | 126 |
| [graphiti-patched/examples/opentelemetry/uv.lock](/graphiti-patched/examples/opentelemetry/uv.lock) | toml | 823 | 0 | 43 | 866 |
| [graphiti-patched/examples/podcast/podcast\_runner.py](/graphiti-patched/examples/podcast/podcast_runner.py) | Python | 95 | 5 | 30 | 130 |
| [graphiti-patched/examples/podcast/transcript\_parser.py](/graphiti-patched/examples/podcast/transcript_parser.py) | Python | 99 | 2 | 24 | 125 |
| [graphiti-patched/examples/quickstart/quickstart\_falkordb.py](/graphiti-patched/examples/quickstart/quickstart_falkordb.py) | Python | 141 | 75 | 35 | 251 |
| [graphiti-patched/examples/quickstart/quickstart\_neo4j.py](/graphiti-patched/examples/quickstart/quickstart_neo4j.py) | Python | 138 | 67 | 35 | 240 |
| [graphiti-patched/examples/quickstart/quickstart\_neptune.py](/graphiti-patched/examples/quickstart/quickstart_neptune.py) | Python | 146 | 67 | 40 | 253 |
| [graphiti-patched/examples/quickstart/requirements.txt](/graphiti-patched/examples/quickstart/requirements.txt) | pip requirements | 2 | 0 | 0 | 2 |
| [graphiti-patched/examples/wizard\_of\_oz/parser.py](/graphiti-patched/examples/wizard_of_oz/parser.py) | Python | 22 | 5 | 10 | 37 |
| [graphiti-patched/examples/wizard\_of\_oz/runner.py](/graphiti-patched/examples/wizard_of_oz/runner.py) | Python | 54 | 18 | 22 | 94 |
| [graphiti-patched/graphiti\_core/\_\_init\_\_.py](/graphiti-patched/graphiti_core/__init__.py) | Python | 2 | 0 | 2 | 4 |
| [graphiti-patched/graphiti\_core/cross\_encoder/\_\_init\_\_.py](/graphiti-patched/graphiti_core/cross_encoder/__init__.py) | Python | 15 | 0 | 6 | 21 |
| [graphiti-patched/graphiti\_core/cross\_encoder/bge\_reranker\_client.py](/graphiti-patched/graphiti_core/cross_encoder/bge_reranker_client.py) | Python | 40 | 1 | 14 | 55 |
| [graphiti-patched/graphiti\_core/cross\_encoder/client.py](/graphiti-patched/graphiti_core/cross_encoder/client.py) | Python | 31 | 0 | 10 | 41 |
| [graphiti-patched/graphiti\_core/cross\_encoder/gemini\_reranker\_client.py](/graphiti-patched/graphiti_core/cross_encoder/gemini_reranker_client.py) | Python | 127 | 8 | 27 | 162 |
| [graphiti-patched/graphiti\_core/cross\_encoder/openai\_reranker\_client.py](/graphiti-patched/graphiti_core/cross_encoder/openai_reranker_client.py) | Python | 107 | 0 | 17 | 124 |
| [graphiti-patched/graphiti\_core/decorators.py](/graphiti-patched/graphiti_core/decorators.py) | Python | 84 | 7 | 20 | 111 |
| [graphiti-patched/graphiti\_core/driver/\_\_init\_\_.py](/graphiti-patched/graphiti_core/driver/__init__.py) | Python | 14 | 0 | 6 | 20 |
| [graphiti-patched/graphiti\_core/driver/driver.py](/graphiti-patched/graphiti_core/driver/driver.py) | Python | 93 | 1 | 31 | 125 |
| [graphiti-patched/graphiti\_core/driver/falkordb\_driver.py](/graphiti-patched/graphiti_core/driver/falkordb_driver.py) | Python | 292 | 22 | 49 | 363 |
| [graphiti-patched/graphiti\_core/driver/graph\_operations/graph\_operations.py](/graphiti-patched/graphiti_core/driver/graph_operations/graph_operations.py) | Python | 145 | 15 | 32 | 192 |
| [graphiti-patched/graphiti\_core/driver/kuzu\_driver.py](/graphiti-patched/graphiti_core/driver/kuzu_driver.py) | Python | 140 | 12 | 31 | 183 |
| [graphiti-patched/graphiti\_core/driver/neo4j\_driver.py](/graphiti-patched/graphiti_core/driver/neo4j_driver.py) | Python | 86 | 6 | 26 | 118 |
| [graphiti-patched/graphiti\_core/driver/neptune\_driver.py](/graphiti-patched/graphiti_core/driver/neptune_driver.py) | Python | 255 | 11 | 40 | 306 |
| [graphiti-patched/graphiti\_core/driver/search\_interface/search\_interface.py](/graphiti-patched/graphiti_core/driver/search_interface/search_interface.py) | Python | 73 | 1 | 16 | 90 |
| [graphiti-patched/graphiti\_core/edges.py](/graphiti-patched/graphiti_core/edges.py) | Python | 532 | 2 | 98 | 632 |
| [graphiti-patched/graphiti\_core/embedder/\_\_init\_\_.py](/graphiti-patched/graphiti_core/embedder/__init__.py) | Python | 7 | 0 | 2 | 9 |
| [graphiti-patched/graphiti\_core/embedder/azure\_openai.py](/graphiti-patched/graphiti_core/embedder/azure_openai.py) | Python | 52 | 3 | 17 | 72 |
| [graphiti-patched/graphiti\_core/embedder/client.py](/graphiti-patched/graphiti_core/embedder/client.py) | Python | 27 | 0 | 12 | 39 |
| [graphiti-patched/graphiti\_core/embedder/gemini.py](/graphiti-patched/graphiti_core/embedder/gemini.py) | Python | 136 | 8 | 40 | 184 |
| [graphiti-patched/graphiti\_core/embedder/openai.py](/graphiti-patched/graphiti_core/embedder/openai.py) | Python | 50 | 0 | 17 | 67 |
| [graphiti-patched/graphiti\_core/embedder/voyage.py](/graphiti-patched/graphiti_core/embedder/voyage.py) | Python | 59 | 0 | 18 | 77 |
| [graphiti-patched/graphiti\_core/errors.py](/graphiti-patched/graphiti_core/errors.py) | Python | 54 | 0 | 30 | 84 |
| [graphiti-patched/graphiti\_core/graph\_queries.py](/graphiti-patched/graphiti_core/graph_queries.py) | Python | 124 | 11 | 28 | 163 |
| [graphiti-patched/graphiti\_core/graphiti.py](/graphiti-patched/graphiti_core/graphiti.py) | Python | 1,062 | 52 | 173 | 1,287 |
| [graphiti-patched/graphiti\_core/graphiti\_types.py](/graphiti-patched/graphiti_core/graphiti_types.py) | Python | 25 | 0 | 9 | 34 |
| [graphiti-patched/graphiti\_core/helpers.py](/graphiti-patched/graphiti_core/helpers.py) | Python | 129 | 8 | 40 | 177 |
| [graphiti-patched/graphiti\_core/llm\_client/\_\_init\_\_.py](/graphiti-patched/graphiti_core/llm_client/__init__.py) | Python | 17 | 0 | 6 | 23 |
| [graphiti-patched/graphiti\_core/llm\_client/anthropic\_client.py](/graphiti-patched/graphiti_core/llm_client/anthropic_client.py) | Python | 330 | 33 | 67 | 430 |
| [graphiti-patched/graphiti\_core/llm\_client/azure\_openai\_client.py](/graphiti-patched/graphiti_core/llm_client/azure_openai_client.py) | Python | 92 | 1 | 23 | 116 |
| [graphiti-patched/graphiti\_core/llm\_client/client.py](/graphiti-patched/graphiti_core/llm_client/client.py) | Python | 189 | 10 | 44 | 243 |
| [graphiti-patched/graphiti\_core/llm\_client/config.py](/graphiti-patched/graphiti_core/llm_client/config.py) | Python | 53 | 0 | 16 | 69 |
| [graphiti-patched/graphiti\_core/llm\_client/errors.py](/graphiti-patched/graphiti_core/llm_client/errors.py) | Python | 27 | 0 | 13 | 40 |
| [graphiti-patched/graphiti\_core/llm\_client/gemini\_client.py](/graphiti-patched/graphiti_core/llm_client/gemini_client.py) | Python | 336 | 37 | 74 | 447 |
| [graphiti-patched/graphiti\_core/llm\_client/groq\_client.py](/graphiti-patched/graphiti_core/llm_client/groq_client.py) | Python | 73 | 0 | 13 | 86 |
| [graphiti-patched/graphiti\_core/llm\_client/openai\_base\_client.py](/graphiti-patched/graphiti_core/llm_client/openai_base_client.py) | Python | 217 | 9 | 36 | 262 |
| [graphiti-patched/graphiti\_core/llm\_client/openai\_client.py](/graphiti-patched/graphiti_core/llm_client/openai_client.py) | Python | 94 | 2 | 20 | 116 |
| [graphiti-patched/graphiti\_core/llm\_client/openai\_generic\_client.py](/graphiti-patched/graphiti_core/llm_client/openai_generic_client.py) | Python | 169 | 11 | 35 | 215 |
| [graphiti-patched/graphiti\_core/llm\_client/utils.py](/graphiti-patched/graphiti_core/llm_client/utils.py) | Python | 23 | 0 | 12 | 35 |
| [graphiti-patched/graphiti\_core/migrations/\_\_init\_\_.py](/graphiti-patched/graphiti_core/migrations/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [graphiti-patched/graphiti\_core/models/\_\_init\_\_.py](/graphiti-patched/graphiti_core/models/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [graphiti-patched/graphiti\_core/models/edges/\_\_init\_\_.py](/graphiti-patched/graphiti_core/models/edges/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [graphiti-patched/graphiti\_core/models/edges/edge\_db\_queries.py](/graphiti-patched/graphiti_core/models/edges/edge_db_queries.py) | Python | 257 | 1 | 23 | 281 |
| [graphiti-patched/graphiti\_core/models/nodes/\_\_init\_\_.py](/graphiti-patched/graphiti_core/models/nodes/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [graphiti-patched/graphiti\_core/models/nodes/node\_db\_queries.py](/graphiti-patched/graphiti_core/models/nodes/node_db_queries.py) | Python | 306 | 1 | 25 | 332 |
| [graphiti-patched/graphiti\_core/nodes.py](/graphiti-patched/graphiti_core/nodes.py) | Python | 682 | 10 | 115 | 807 |
| [graphiti-patched/graphiti\_core/prompts/\_\_init\_\_.py](/graphiti-patched/graphiti_core/prompts/__init__.py) | Python | 3 | 0 | 2 | 5 |
| [graphiti-patched/graphiti\_core/prompts/dedupe\_edges.py](/graphiti-patched/graphiti_core/prompts/dedupe_edges.py) | Python | 134 | 0 | 41 | 175 |
| [graphiti-patched/graphiti\_core/prompts/dedupe\_nodes.py](/graphiti-patched/graphiti_core/prompts/dedupe_nodes.py) | Python | 181 | 0 | 45 | 226 |
| [graphiti-patched/graphiti\_core/prompts/eval.py](/graphiti-patched/graphiti_core/prompts/eval.py) | Python | 128 | 0 | 37 | 165 |
| [graphiti-patched/graphiti\_core/prompts/extract\_edge\_dates.py](/graphiti-patched/graphiti_core/prompts/extract_edge_dates.py) | Python | 71 | 0 | 21 | 92 |
| [graphiti-patched/graphiti\_core/prompts/extract\_edges.py](/graphiti-patched/graphiti_core/prompts/extract_edges.py) | Python | 156 | 3 | 45 | 204 |
| [graphiti-patched/graphiti\_core/prompts/extract\_nodes.py](/graphiti-patched/graphiti_core/prompts/extract_nodes.py) | Python | 245 | 0 | 75 | 320 |
| [graphiti-patched/graphiti\_core/prompts/invalidate\_edges.py](/graphiti-patched/graphiti_core/prompts/invalidate_edges.py) | Python | 73 | 0 | 26 | 99 |
| [graphiti-patched/graphiti\_core/prompts/lib.py](/graphiti-patched/graphiti_core/prompts/lib.py) | Python | 84 | 0 | 19 | 103 |
| [graphiti-patched/graphiti\_core/prompts/models.py](/graphiti-patched/graphiti_core/prompts/models.py) | Python | 21 | 0 | 12 | 33 |
| [graphiti-patched/graphiti\_core/prompts/prompt\_helpers.py](/graphiti-patched/graphiti_core/prompts/prompt_helpers.py) | Python | 30 | 0 | 11 | 41 |
| [graphiti-patched/graphiti\_core/prompts/snippets.py](/graphiti-patched/graphiti_core/prompts/snippets.py) | Python | 24 | 0 | 6 | 30 |
| [graphiti-patched/graphiti\_core/prompts/summarize\_nodes.py](/graphiti-patched/graphiti_core/prompts/summarize_nodes.py) | Python | 100 | 0 | 32 | 132 |
| [graphiti-patched/graphiti\_core/search/\_\_init\_\_.py](/graphiti-patched/graphiti_core/search/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [graphiti-patched/graphiti\_core/search/search.py](/graphiti-patched/graphiti_core/search/search.py) | Python | 451 | 8 | 61 | 520 |
| [graphiti-patched/graphiti\_core/search/search\_config.py](/graphiti-patched/graphiti_core/search/search_config.py) | Python | 120 | 0 | 41 | 161 |
| [graphiti-patched/graphiti\_core/search/search\_config\_recipes.py](/graphiti-patched/graphiti_core/search/search_config_recipes.py) | Python | 187 | 16 | 21 | 224 |
| [graphiti-patched/graphiti\_core/search/search\_filters.py](/graphiti-patched/graphiti_core/search/search_filters.py) | Python | 203 | 0 | 49 | 252 |
| [graphiti-patched/graphiti\_core/search/search\_helpers.py](/graphiti-patched/graphiti_core/search/search_helpers.py) | Python | 60 | 1 | 12 | 73 |
| [graphiti-patched/graphiti\_core/search/search\_utils.py](/graphiti-patched/graphiti_core/search/search_utils.py) | Python | 1,729 | 34 | 233 | 1,996 |
| [graphiti-patched/graphiti\_core/telemetry/\_\_init\_\_.py](/graphiti-patched/graphiti_core/telemetry/__init__.py) | Python | 6 | 0 | 4 | 10 |
| [graphiti-patched/graphiti\_core/telemetry/telemetry.py](/graphiti-patched/graphiti_core/telemetry/telemetry.py) | Python | 73 | 18 | 27 | 118 |
| [graphiti-patched/graphiti\_core/tracer.py](/graphiti-patched/graphiti_core/tracer.py) | Python | 143 | 5 | 46 | 194 |
| [graphiti-patched/graphiti\_core/utils/\_\_init\_\_.py](/graphiti-patched/graphiti_core/utils/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [graphiti-patched/graphiti\_core/utils/bulk\_utils.py](/graphiti-patched/graphiti_core/utils/bulk_utils.py) | Python | 447 | 18 | 84 | 549 |
| [graphiti-patched/graphiti\_core/utils/datetime\_utils.py](/graphiti-patched/graphiti_core/utils/datetime_utils.py) | Python | 41 | 2 | 13 | 56 |
| [graphiti-patched/graphiti\_core/utils/maintenance/\_\_init\_\_.py](/graphiti-patched/graphiti_core/utils/maintenance/__init__.py) | Python | 10 | 0 | 2 | 12 |
| [graphiti-patched/graphiti\_core/utils/maintenance/community\_operations.py](/graphiti-patched/graphiti_core/utils/maintenance/community_operations.py) | Python | 252 | 8 | 72 | 332 |
| [graphiti-patched/graphiti\_core/utils/maintenance/dedup\_helpers.py](/graphiti-patched/graphiti_core/utils/maintenance/dedup_helpers.py) | Python | 202 | 0 | 61 | 263 |
| [graphiti-patched/graphiti\_core/utils/maintenance/edge\_operations.py](/graphiti-patched/graphiti_core/utils/maintenance/edge_operations.py) | Python | 572 | 32 | 108 | 712 |
| [graphiti-patched/graphiti\_core/utils/maintenance/graph\_data\_operations.py](/graphiti-patched/graphiti_core/utils/maintenance/graph_data_operations.py) | Python | 98 | 0 | 23 | 121 |
| [graphiti-patched/graphiti\_core/utils/maintenance/node\_operations.py](/graphiti-patched/graphiti_core/utils/maintenance/node_operations.py) | Python | 491 | 7 | 90 | 588 |
| [graphiti-patched/graphiti\_core/utils/maintenance/temporal\_operations.py](/graphiti-patched/graphiti_core/utils/maintenance/temporal_operations.py) | Python | 85 | 0 | 23 | 108 |
| [graphiti-patched/graphiti\_core/utils/ontology\_utils/entity\_types\_utils.py](/graphiti-patched/graphiti_core/utils/ontology_utils/entity_types_utils.py) | Python | 27 | 0 | 11 | 38 |
| [graphiti-patched/graphiti\_core/utils/text\_utils.py](/graphiti-patched/graphiti_core/utils/text_utils.py) | Python | 34 | 5 | 15 | 54 |
| [graphiti-patched/images/simple\_graph.svg](/graphiti-patched/images/simple_graph.svg) | XML | 130 | 0 | 0 | 130 |
| [graphiti-patched/mcp\_server/config/config-docker-falkordb-combined.yaml](/graphiti-patched/mcp_server/config/config-docker-falkordb-combined.yaml) | YAML | 83 | 3 | 16 | 102 |
| [graphiti-patched/mcp\_server/config/config-docker-falkordb.yaml](/graphiti-patched/mcp_server/config/config-docker-falkordb.yaml) | YAML | 83 | 3 | 15 | 101 |
| [graphiti-patched/mcp\_server/config/config-docker-neo4j.yaml](/graphiti-patched/mcp_server/config/config-docker-neo4j.yaml) | YAML | 85 | 3 | 15 | 103 |
| [graphiti-patched/mcp\_server/config/config.yaml](/graphiti-patched/mcp_server/config/config.yaml) | YAML | 89 | 6 | 16 | 111 |
| [graphiti-patched/mcp\_server/docker/Dockerfile](/graphiti-patched/mcp_server/docker/Dockerfile) | Docker | 84 | 29 | 25 | 138 |
| [graphiti-patched/mcp\_server/docker/build-standalone.sh](/graphiti-patched/mcp_server/docker/build-standalone.sh) | Shell Script | 37 | 7 | 7 | 51 |
| [graphiti-patched/mcp\_server/docker/build-with-version.sh](/graphiti-patched/mcp_server/docker/build-with-version.sh) | Shell Script | 30 | 7 | 7 | 44 |
| [graphiti-patched/mcp\_server/docker/docker-compose-falkordb.yml](/graphiti-patched/mcp_server/docker/docker-compose-falkordb.yml) | YAML | 44 | 5 | 2 | 51 |
| [graphiti-patched/mcp\_server/docker/docker-compose-neo4j.yml](/graphiti-patched/mcp_server/docker/docker-compose-neo4j.yml) | YAML | 48 | 5 | 3 | 56 |
| [graphiti-patched/mcp\_server/docker/docker-compose.yml](/graphiti-patched/mcp_server/docker/docker-compose.yml) | YAML | 41 | 2 | 2 | 45 |
| [graphiti-patched/mcp\_server/docker/github-actions-example.yml](/graphiti-patched/mcp_server/docker/github-actions-example.yml) | YAML | 95 | 6 | 19 | 120 |
| [graphiti-patched/mcp\_server/main.py](/graphiti-patched/mcp_server/main.py) | Python | 15 | 4 | 8 | 27 |
| [graphiti-patched/mcp\_server/pytest.ini](/graphiti-patched/mcp_server/pytest.ini) | Ini | 14 | 0 | 0 | 14 |
| [graphiti-patched/mcp\_server/src/\_\_init\_\_.py](/graphiti-patched/mcp_server/src/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [graphiti-patched/mcp\_server/src/config/\_\_init\_\_.py](/graphiti-patched/mcp_server/src/config/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [graphiti-patched/mcp\_server/src/config/schema.py](/graphiti-patched/mcp_server/src/config/schema.py) | Python | 202 | 13 | 77 | 292 |
| [graphiti-patched/mcp\_server/src/graphiti\_mcp\_server.py](/graphiti-patched/mcp_server/src/graphiti_mcp_server.py) | Python | 691 | 113 | 162 | 966 |
| [graphiti-patched/mcp\_server/src/models/\_\_init\_\_.py](/graphiti-patched/mcp_server/src/models/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [graphiti-patched/mcp\_server/src/models/entity\_types.py](/graphiti-patched/mcp_server/src/models/entity_types.py) | Python | 181 | 0 | 45 | 226 |
| [graphiti-patched/mcp\_server/src/models/response\_types.py](/graphiti-patched/mcp_server/src/models/response_types.py) | Python | 27 | 0 | 17 | 44 |
| [graphiti-patched/mcp\_server/src/services/\_\_init\_\_.py](/graphiti-patched/mcp_server/src/services/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [graphiti-patched/mcp\_server/src/services/factories.py](/graphiti-patched/mcp_server/src/services/factories.py) | Python | 323 | 20 | 95 | 438 |
| [graphiti-patched/mcp\_server/src/services/queue\_service.py](/graphiti-patched/mcp_server/src/services/queue_service.py) | Python | 113 | 12 | 28 | 153 |
| [graphiti-patched/mcp\_server/src/utils/\_\_init\_\_.py](/graphiti-patched/mcp_server/src/utils/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [graphiti-patched/mcp\_server/src/utils/formatting.py](/graphiti-patched/mcp_server/src/utils/formatting.py) | Python | 37 | 1 | 13 | 51 |
| [graphiti-patched/mcp\_server/src/utils/utils.py](/graphiti-patched/mcp_server/src/utils/utils.py) | Python | 21 | 0 | 7 | 28 |
| [graphiti-patched/mcp\_server/tests/\_\_init\_\_.py](/graphiti-patched/mcp_server/tests/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [graphiti-patched/mcp\_server/tests/conftest.py](/graphiti-patched/mcp_server/tests/conftest.py) | Python | 14 | 1 | 7 | 22 |
| [graphiti-patched/mcp\_server/tests/pytest.ini](/graphiti-patched/mcp_server/tests/pytest.ini) | Ini | 32 | 0 | 7 | 39 |
| [graphiti-patched/mcp\_server/tests/run\_tests.py](/graphiti-patched/mcp_server/tests/run_tests.py) | Python | 242 | 33 | 68 | 343 |
| [graphiti-patched/mcp\_server/tests/test\_async\_operations.py](/graphiti-patched/mcp_server/tests/test_async_operations.py) | Python | 360 | 53 | 77 | 490 |
| [graphiti-patched/mcp\_server/tests/test\_comprehensive\_integration.py](/graphiti-patched/mcp_server/tests/test_comprehensive_integration.py) | Python | 516 | 37 | 115 | 668 |
| [graphiti-patched/mcp\_server/tests/test\_configuration.py](/graphiti-patched/mcp_server/tests/test_configuration.py) | Python | 150 | 17 | 41 | 208 |
| [graphiti-patched/mcp\_server/tests/test\_falkordb\_integration.py](/graphiti-patched/mcp_server/tests/test_falkordb_integration.py) | Python | 149 | 9 | 41 | 199 |
| [graphiti-patched/mcp\_server/tests/test\_fixtures.py](/graphiti-patched/mcp_server/tests/test_fixtures.py) | Python | 263 | 7 | 54 | 324 |
| [graphiti-patched/mcp\_server/tests/test\_http\_integration.py](/graphiti-patched/mcp_server/tests/test_http_integration.py) | Python | 189 | 15 | 47 | 251 |
| [graphiti-patched/mcp\_server/tests/test\_integration.py](/graphiti-patched/mcp_server/tests/test_integration.py) | Python | 274 | 21 | 70 | 365 |
| [graphiti-patched/mcp\_server/tests/test\_mcp\_integration.py](/graphiti-patched/mcp_server/tests/test_mcp_integration.py) | Python | 390 | 26 | 88 | 504 |
| [graphiti-patched/mcp\_server/tests/test\_mcp\_transports.py](/graphiti-patched/mcp_server/tests/test_mcp_transports.py) | Python | 208 | 13 | 54 | 275 |
| [graphiti-patched/mcp\_server/tests/test\_stdio\_simple.py](/graphiti-patched/mcp_server/tests/test_stdio_simple.py) | Python | 62 | 7 | 19 | 88 |
| [graphiti-patched/mcp\_server/tests/test\_stress\_load.py](/graphiti-patched/mcp_server/tests/test_stress_load.py) | Python | 407 | 34 | 87 | 528 |
| [graphiti-patched/mcp\_server/uv.lock](/graphiti-patched/mcp_server/uv.lock) | toml | 2,884 | 0 | 141 | 3,025 |
| [graphiti-patched/pytest.ini](/graphiti-patched/pytest.ini) | Ini | 5 | 0 | 1 | 6 |
| [graphiti-patched/server/Makefile](/graphiti-patched/server/Makefile) | Makefile | 18 | 7 | 7 | 32 |
| [graphiti-patched/server/graph\_service/\_\_init\_\_.py](/graphiti-patched/server/graph_service/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [graphiti-patched/server/graph\_service/config.py](/graphiti-patched/server/graph_service/config.py) | Python | 18 | 0 | 9 | 27 |
| [graphiti-patched/server/graph\_service/dto/\_\_init\_\_.py](/graphiti-patched/server/graph_service/dto/__init__.py) | Python | 14 | 0 | 2 | 16 |
| [graphiti-patched/server/graph\_service/dto/common.py](/graphiti-patched/server/graph_service/dto/common.py) | Python | 23 | 0 | 6 | 29 |
| [graphiti-patched/server/graph\_service/dto/ingest.py](/graphiti-patched/server/graph_service/dto/ingest.py) | Python | 10 | 0 | 6 | 16 |
| [graphiti-patched/server/graph\_service/dto/retrieve.py](/graphiti-patched/server/graph_service/dto/retrieve.py) | Python | 32 | 0 | 14 | 46 |
| [graphiti-patched/server/graph\_service/main.py](/graphiti-patched/server/graph_service/main.py) | Python | 17 | 2 | 11 | 30 |
| [graphiti-patched/server/graph\_service/routers/\_\_init\_\_.py](/graphiti-patched/server/graph_service/routers/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [graphiti-patched/server/graph\_service/routers/ingest.py](/graphiti-patched/server/graph_service/routers/ingest.py) | Python | 84 | 0 | 28 | 112 |
| [graphiti-patched/server/graph\_service/routers/retrieve.py](/graphiti-patched/server/graph_service/routers/retrieve.py) | Python | 50 | 0 | 14 | 64 |
| [graphiti-patched/server/graph\_service/zep\_graphiti.py](/graphiti-patched/server/graph_service/zep_graphiti.py) | Python | 90 | 0 | 25 | 115 |
| [graphiti-patched/server/uv.lock](/graphiti-patched/server/uv.lock) | toml | 1,066 | 0 | 59 | 1,125 |
| [graphiti-patched/tests/cross\_encoder/test\_bge\_reranker\_client\_int.py](/graphiti-patched/tests/cross_encoder/test_bge_reranker_client_int.py) | Python | 48 | 7 | 24 | 79 |
| [graphiti-patched/tests/cross\_encoder/test\_gemini\_reranker\_client.py](/graphiti-patched/tests/cross_encoder/test_gemini_reranker_client.py) | Python | 240 | 34 | 80 | 354 |
| [graphiti-patched/tests/driver/\_\_init\_\_.py](/graphiti-patched/tests/driver/__init__.py) | Python | 1 | 0 | 1 | 2 |
| [graphiti-patched/tests/driver/test\_falkordb\_driver.py](/graphiti-patched/tests/driver/test_falkordb_driver.py) | Python | 294 | 9 | 90 | 393 |
| [graphiti-patched/tests/embedder/embedder\_fixtures.py](/graphiti-patched/tests/embedder/embedder_fixtures.py) | Python | 15 | 0 | 6 | 21 |
| [graphiti-patched/tests/embedder/test\_gemini.py](/graphiti-patched/tests/embedder/test_gemini.py) | Python | 278 | 36 | 82 | 396 |
| [graphiti-patched/tests/embedder/test\_openai.py](/graphiti-patched/tests/embedder/test_openai.py) | Python | 90 | 8 | 29 | 127 |
| [graphiti-patched/tests/embedder/test\_voyage.py](/graphiti-patched/tests/embedder/test_voyage.py) | Python | 108 | 8 | 27 | 143 |
| [graphiti-patched/tests/evals/eval\_cli.py](/graphiti-patched/tests/evals/eval_cli.py) | Python | 29 | 2 | 10 | 41 |
| [graphiti-patched/tests/evals/eval\_e2e\_graph\_building.py](/graphiti-patched/tests/evals/eval_e2e_graph_building.py) | Python | 145 | 2 | 34 | 181 |
| [graphiti-patched/tests/evals/pytest.ini](/graphiti-patched/tests/evals/pytest.ini) | Ini | 4 | 0 | 0 | 4 |
| [graphiti-patched/tests/evals/utils.py](/graphiti-patched/tests/evals/utils.py) | Python | 23 | 5 | 12 | 40 |
| [graphiti-patched/tests/helpers\_test.py](/graphiti-patched/tests/helpers_test.py) | Python | 258 | 4 | 52 | 314 |
| [graphiti-patched/tests/llm\_client/test\_anthropic\_client.py](/graphiti-patched/tests/llm_client/test_anthropic_client.py) | Python | 172 | 28 | 56 | 256 |
| [graphiti-patched/tests/llm\_client/test\_anthropic\_client\_int.py](/graphiti-patched/tests/llm_client/test_anthropic_client_int.py) | Python | 56 | 7 | 23 | 86 |
| [graphiti-patched/tests/llm\_client/test\_azure\_openai\_client.py](/graphiti-patched/tests/llm_client/test_azure_openai_client.py) | Python | 85 | 0 | 25 | 110 |
| [graphiti-patched/tests/llm\_client/test\_client.py](/graphiti-patched/tests/llm_client/test_client.py) | Python | 36 | 10 | 12 | 58 |
| [graphiti-patched/tests/llm\_client/test\_errors.py](/graphiti-patched/tests/llm_client/test_errors.py) | Python | 53 | 3 | 21 | 77 |
| [graphiti-patched/tests/llm\_client/test\_gemini\_client.py](/graphiti-patched/tests/llm_client/test_gemini_client.py) | Python | 338 | 58 | 87 | 483 |
| [graphiti-patched/tests/test\_edge\_int.py](/graphiti-patched/tests/test_edge_int.py) | Python | 301 | 39 | 58 | 398 |
| [graphiti-patched/tests/test\_entity\_exclusion\_int.py](/graphiti-patched/tests/test_entity_exclusion_int.py) | Python | 244 | 29 | 79 | 352 |
| [graphiti-patched/tests/test\_graphiti\_int.py](/graphiti-patched/tests/test_graphiti_int.py) | Python | 53 | 5 | 23 | 81 |
| [graphiti-patched/tests/test\_graphiti\_mock.py](/graphiti-patched/tests/test_graphiti_mock.py) | Python | 1,736 | 114 | 219 | 2,069 |
| [graphiti-patched/tests/test\_node\_int.py](/graphiti-patched/tests/test_node_int.py) | Python | 165 | 21 | 44 | 230 |
| [graphiti-patched/tests/test\_text\_utils.py](/graphiti-patched/tests/test_text_utils.py) | Python | 78 | 2 | 27 | 107 |
| [graphiti-patched/tests/utils/maintenance/test\_bulk\_utils.py](/graphiti-patched/tests/utils/maintenance/test_bulk_utils.py) | Python | 245 | 11 | 73 | 329 |
| [graphiti-patched/tests/utils/maintenance/test\_edge\_operations.py](/graphiti-patched/tests/utils/maintenance/test_edge_operations.py) | Python | 544 | 13 | 91 | 648 |
| [graphiti-patched/tests/utils/maintenance/test\_node\_operations.py](/graphiti-patched/tests/utils/maintenance/test_node_operations.py) | Python | 505 | 15 | 132 | 652 |
| [graphiti-patched/tests/utils/maintenance/test\_temporal\_operations\_int.py](/graphiti-patched/tests/utils/maintenance/test_temporal_operations_int.py) | Python | 206 | 11 | 55 | 272 |
| [graphiti-patched/tests/utils/search/search\_utils\_test.py](/graphiti-patched/tests/utils/search/search_utils_test.py) | Python | 121 | 14 | 29 | 164 |
| [graphiti-patched/uv.lock](/graphiti-patched/uv.lock) | toml | 4,053 | 0 | 212 | 4,265 |
| [manage.py](/manage.py) | Python | 576 | 44 | 128 | 748 |
| [mcp-server/src/\_\_init\_\_.py](/mcp-server/src/__init__.py) | Python | 12 | 4 | 5 | 21 |
| [mcp-server/src/cli.py](/mcp-server/src/cli.py) | Python | 75 | 23 | 25 | 123 |
| [mcp-server/src/cli\_commands/\_\_init\_\_.py](/mcp-server/src/cli_commands/__init__.py) | Python | 1 | 0 | 1 | 2 |
| [mcp-server/src/cli\_commands/analyze.py](/mcp-server/src/cli_commands/analyze.py) | Python | 85 | 10 | 27 | 122 |
| [mcp-server/src/cli\_commands/collection.py](/mcp-server/src/cli_commands/collection.py) | Python | 276 | 21 | 73 | 370 |
| [mcp-server/src/cli\_commands/config.py](/mcp-server/src/cli_commands/config.py) | Python | 200 | 25 | 51 | 276 |
| [mcp-server/src/cli\_commands/document.py](/mcp-server/src/cli_commands/document.py) | Python | 270 | 18 | 69 | 357 |
| [mcp-server/src/cli\_commands/graph.py](/mcp-server/src/cli_commands/graph.py) | Python | 272 | 30 | 68 | 370 |
| [mcp-server/src/cli\_commands/ingest.py](/mcp-server/src/cli_commands/ingest.py) | Python | 797 | 79 | 170 | 1,046 |
| [mcp-server/src/cli\_commands/init.py](/mcp-server/src/cli_commands/init.py) | Python | 90 | 14 | 34 | 138 |
| [mcp-server/src/cli\_commands/instance.py](/mcp-server/src/cli_commands/instance.py) | Python | 740 | 58 | 196 | 994 |
| [mcp-server/src/cli\_commands/logs.py](/mcp-server/src/cli_commands/logs.py) | Python | 218 | 27 | 47 | 292 |
| [mcp-server/src/cli\_commands/search.py](/mcp-server/src/cli_commands/search.py) | Python | 100 | 6 | 20 | 126 |
| [mcp-server/src/cli\_commands/service.py](/mcp-server/src/cli_commands/service.py) | Python | 276 | 29 | 94 | 399 |
| [mcp-server/src/cli\_commands/utils/\_\_init\_\_.py](/mcp-server/src/cli_commands/utils/__init__.py) | Python | 1 | 0 | 1 | 2 |
| [mcp-server/src/core/\_\_init\_\_.py](/mcp-server/src/core/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [mcp-server/src/core/chunking.py](/mcp-server/src/core/chunking.py) | Python | 109 | 5 | 31 | 145 |
| [mcp-server/src/core/collections.py](/mcp-server/src/core/collections.py) | Python | 436 | 31 | 89 | 556 |
| [mcp-server/src/core/config\_loader.py](/mcp-server/src/core/config_loader.py) | Python | 420 | 58 | 128 | 606 |
| [mcp-server/src/core/database.py](/mcp-server/src/core/database.py) | Python | 314 | 21 | 60 | 395 |
| [mcp-server/src/core/embeddings.py](/mcp-server/src/core/embeddings.py) | Python | 137 | 5 | 45 | 187 |
| [mcp-server/src/core/first\_run.py](/mcp-server/src/core/first_run.py) | Python | 58 | 7 | 19 | 84 |
| [mcp-server/src/core/instance\_init.py](/mcp-server/src/core/instance_init.py) | Python | 342 | 18 | 101 | 461 |
| [mcp-server/src/core/instance\_registry.py](/mcp-server/src/core/instance_registry.py) | Python | 213 | 8 | 66 | 287 |
| [mcp-server/src/ingestion/\_\_init\_\_.py](/mcp-server/src/ingestion/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [mcp-server/src/ingestion/document\_store.py](/mcp-server/src/ingestion/document_store.py) | Python | 657 | 53 | 109 | 819 |
| [mcp-server/src/ingestion/metadata\_validator.py](/mcp-server/src/ingestion/metadata_validator.py) | Python | 81 | 4 | 25 | 110 |
| [mcp-server/src/ingestion/models.py](/mcp-server/src/ingestion/models.py) | Python | 96 | 0 | 17 | 113 |
| [mcp-server/src/ingestion/web\_crawler.py](/mcp-server/src/ingestion/web_crawler.py) | Python | 520 | 61 | 94 | 675 |
| [mcp-server/src/ingestion/website\_analyzer.py](/mcp-server/src/ingestion/website_analyzer.py) | Python | 337 | 21 | 68 | 426 |
| [mcp-server/src/mcp/\_\_init\_\_.py](/mcp-server/src/mcp/__init__.py) | Python | 6 | 0 | 4 | 10 |
| [mcp-server/src/mcp/audit.py](/mcp-server/src/mcp/audit.py) | Python | 185 | 1 | 26 | 212 |
| [mcp-server/src/mcp/deduplication.py](/mcp-server/src/mcp/deduplication.py) | Python | 159 | 19 | 46 | 224 |
| [mcp-server/src/mcp/evaluation.py](/mcp-server/src/mcp/evaluation.py) | Python | 201 | 13 | 49 | 263 |
| [mcp-server/src/mcp/http\_routes.py](/mcp-server/src/mcp/http_routes.py) | Python | 1,097 | 114 | 149 | 1,360 |
| [mcp-server/src/mcp/server.py](/mcp-server/src/mcp/server.py) | Python | 1,299 | 74 | 287 | 1,660 |
| [mcp-server/src/mcp/tools.py](/mcp-server/src/mcp/tools.py) | Python | 3,636 | 381 | 630 | 4,647 |
| [mcp-server/src/retrieval/\_\_init\_\_.py](/mcp-server/src/retrieval/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [mcp-server/src/retrieval/search.py](/mcp-server/src/retrieval/search.py) | Python | 352 | 24 | 48 | 424 |
| [mcp-server/src/unified/\_\_init\_\_.py](/mcp-server/src/unified/__init__.py) | Python | 11 | 0 | 5 | 16 |
| [mcp-server/src/unified/graph\_store.py](/mcp-server/src/unified/graph_store.py) | Python | 426 | 42 | 88 | 556 |
| [mcp-server/src/unified/mediator.py](/mcp-server/src/unified/mediator.py) | Python | 276 | 41 | 63 | 380 |
| [mcp-server/tests/\_\_init\_\_.py](/mcp-server/tests/__init__.py) | Python | 1 | 0 | 1 | 2 |
| [mcp-server/tests/conftest.py](/mcp-server/tests/conftest.py) | Python | 332 | 62 | 105 | 499 |
| [mcp-server/tests/integration/\_\_init\_\_.py](/mcp-server/tests/integration/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [mcp-server/tests/integration/backend/\_\_init\_\_.py](/mcp-server/tests/integration/backend/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [mcp-server/tests/integration/backend/test\_document\_chunking.py](/mcp-server/tests/integration/backend/test_document_chunking.py) | Python | 345 | 21 | 83 | 449 |
| [mcp-server/tests/integration/backend/test\_rag\_graph.py](/mcp-server/tests/integration/backend/test_rag_graph.py) | Python | 449 | 62 | 112 | 623 |
| [mcp-server/tests/integration/cli/\_\_init\_\_.py](/mcp-server/tests/integration/cli/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [mcp-server/tests/integration/cli/test\_cli\_integration.py](/mcp-server/tests/integration/cli/test_cli_integration.py) | Python | 91 | 17 | 33 | 141 |
| [mcp-server/tests/integration/mcp/\_\_init\_\_.py](/mcp-server/tests/integration/mcp/__init__.py) | Python | 6 | 0 | 3 | 9 |
| [mcp-server/tests/integration/mcp/conftest.py](/mcp-server/tests/integration/mcp/conftest.py) | Python | 170 | 29 | 54 | 253 |
| [mcp-server/tests/integration/mcp/test\_analyze\_website.py](/mcp-server/tests/integration/mcp/test_analyze_website.py) | Python | 124 | 15 | 38 | 177 |
| [mcp-server/tests/integration/mcp/test\_collections.py](/mcp-server/tests/integration/mcp/test_collections.py) | Python | 262 | 45 | 74 | 381 |
| [mcp-server/tests/integration/mcp/test\_document\_crud.py](/mcp-server/tests/integration/mcp/test_document_crud.py) | Python | 158 | 17 | 55 | 230 |
| [mcp-server/tests/integration/mcp/test\_error\_handling.py](/mcp-server/tests/integration/mcp/test_error_handling.py) | Python | 88 | 11 | 30 | 129 |
| [mcp-server/tests/integration/mcp/test\_ingest\_directory.py](/mcp-server/tests/integration/mcp/test_ingest_directory.py) | Python | 195 | 17 | 59 | 271 |
| [mcp-server/tests/integration/mcp/test\_ingest\_file.py](/mcp-server/tests/integration/mcp/test_ingest_file.py) | Python | 175 | 22 | 61 | 258 |
| [mcp-server/tests/integration/mcp/test\_ingest\_url.py](/mcp-server/tests/integration/mcp/test_ingest_url.py) | Python | 216 | 27 | 64 | 307 |
| [mcp-server/tests/integration/mcp/test\_ingestion.py](/mcp-server/tests/integration/mcp/test_ingestion.py) | Python | 76 | 5 | 29 | 110 |
| [mcp-server/tests/integration/mcp/test\_knowledge\_graph.py](/mcp-server/tests/integration/mcp/test_knowledge_graph.py) | Python | 126 | 22 | 43 | 191 |
| [mcp-server/tests/integration/mcp/test\_reingest\_modes.py](/mcp-server/tests/integration/mcp/test_reingest_modes.py) | Python | 843 | 107 | 242 | 1,192 |
| [mcp-server/tests/integration/mcp/test\_search\_documents.py](/mcp-server/tests/integration/mcp/test_search_documents.py) | Python | 338 | 54 | 96 | 488 |
| [mcp-server/tests/integration/mcp/test\_update\_collection\_metadata.py](/mcp-server/tests/integration/mcp/test_update_collection_metadata.py) | Python | 275 | 29 | 57 | 361 |
| [mcp-server/tests/integration/test\_delete\_collection\_graph\_cleanup.py](/mcp-server/tests/integration/test_delete_collection_graph_cleanup.py) | Python | 116 | 9 | 27 | 152 |
| [mcp-server/tests/integration/web/\_\_init\_\_.py](/mcp-server/tests/integration/web/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [mcp-server/tests/integration/web/test\_crawler.py](/mcp-server/tests/integration/web/test_crawler.py) | Python | 69 | 4 | 19 | 92 |
| [mcp-server/tests/integration/web/test\_crawler\_link\_following.py](/mcp-server/tests/integration/web/test_crawler_link_following.py) | Python | 92 | 15 | 28 | 135 |
| [mcp-server/tests/integration/web/test\_recrawl.py](/mcp-server/tests/integration/web/test_recrawl.py) | Python | 299 | 37 | 59 | 395 |
| [mcp-server/tests/integration/web/test\_web\_ingestion.py](/mcp-server/tests/integration/web/test_web_ingestion.py) | Python | 169 | 23 | 37 | 229 |
| [mcp-server/tests/integration/web/test\_web\_link\_following.py](/mcp-server/tests/integration/web/test_web_link_following.py) | Python | 206 | 26 | 43 | 275 |
| [mcp-server/tests/sample\_documents.py](/mcp-server/tests/sample_documents.py) | Python | 124 | 3 | 10 | 137 |
| [mcp-server/tests/test\_configuration.py](/mcp-server/tests/test_configuration.py) | Python | 488 | 15 | 87 | 590 |
| [mcp-server/tests/test\_startup\_validations.py](/mcp-server/tests/test_startup_validations.py) | Python | 117 | 7 | 37 | 161 |
| [mcp-server/tests/unit/\_\_init\_\_.py](/mcp-server/tests/unit/__init__.py) | Python | 0 | 0 | 1 | 1 |
| [mcp-server/tests/unit/cli/\_\_init\_\_.py](/mcp-server/tests/unit/cli/__init__.py) | Python | 1 | 0 | 1 | 2 |
| [mcp-server/tests/unit/cli/test\_cli\_commands.py](/mcp-server/tests/unit/cli/test_cli_commands.py) | Python | 236 | 11 | 61 | 308 |
| [mcp-server/tests/unit/test\_chunking\_comprehensive.py](/mcp-server/tests/unit/test_chunking_comprehensive.py) | Python | 392 | 15 | 167 | 574 |
| [mcp-server/tests/unit/test\_cli\_metadata\_update.py](/mcp-server/tests/unit/test_cli_metadata_update.py) | Python | 111 | 15 | 36 | 162 |
| [mcp-server/tests/unit/test\_collection\_metadata\_schema.py](/mcp-server/tests/unit/test_collection_metadata_schema.py) | Python | 169 | 12 | 35 | 216 |
| [mcp-server/tests/unit/test\_collection\_metadata\_update.py](/mcp-server/tests/unit/test_collection_metadata_update.py) | Python | 205 | 26 | 42 | 273 |
| [mcp-server/tests/unit/test\_database\_health.py](/mcp-server/tests/unit/test_database_health.py) | Python | 608 | 19 | 165 | 792 |
| [mcp-server/tests/unit/test\_embeddings.py](/mcp-server/tests/unit/test_embeddings.py) | Python | 72 | 12 | 36 | 120 |
| [mcp-server/tests/unit/test\_first\_run\_validation.py](/mcp-server/tests/unit/test_first_run_validation.py) | Python | 235 | 17 | 88 | 340 |
| [mcp-server/tests/unit/test\_graph\_store.py](/mcp-server/tests/unit/test_graph_store.py) | Python | 311 | 24 | 97 | 432 |
| [mcp-server/tests/unit/test\_instance\_registry.py](/mcp-server/tests/unit/test_instance_registry.py) | Python | 274 | 4 | 102 | 380 |
| [mcp-server/tests/unit/test\_mcp\_metadata\_update.py](/mcp-server/tests/unit/test_mcp_metadata_update.py) | Python | 105 | 13 | 22 | 140 |
| [mcp-server/tests/unit/test\_metadata\_validator.py](/mcp-server/tests/unit/test_metadata_validator.py) | Python | 465 | 6 | 176 | 647 |
| [mcp-server/tests/unit/test\_website\_analyzer.py](/mcp-server/tests/unit/test_website_analyzer.py) | Python | 308 | 27 | 84 | 419 |
| [migrations/archive/001\_add\_fulltext\_search.sql](/migrations/archive/001_add_fulltext_search.sql) | SQLite | 34 | 11 | 6 | 51 |
| [migrations/archive/002\_require\_collection\_description.sql](/migrations/archive/002_require_collection_description.sql) | SQLite | 15 | 9 | 5 | 29 |
| [scripts/analyze\_mcp\_tokens.py](/scripts/analyze_mcp_tokens.py) | Python | 297 | 38 | 90 | 425 |
| [scripts/build.sh](/scripts/build.sh) | Shell Script | 86 | 16 | 16 | 118 |
| [scripts/check\_database\_data.py](/scripts/check_database_data.py) | Python | 235 | 16 | 59 | 310 |
| [scripts/db\_migrate.py](/scripts/db_migrate.py) | Python | 281 | 34 | 86 | 401 |
| [scripts/deploy\_to\_cloud.py](/scripts/deploy_to_cloud.py) | Python | 1,149 | 86 | 290 | 1,525 |
| [scripts/rag.py](/scripts/rag.py) | Python | 357 | 32 | 91 | 480 |
| [scripts/setup.py](/scripts/setup.py) | Python | 1,375 | 206 | 376 | 1,957 |
| [scripts/teardown.py](/scripts/teardown.py) | Python | 611 | 61 | 188 | 860 |
| [scripts/test\_relevance\_prompts.py](/scripts/test_relevance_prompts.py) | Python | 369 | 24 | 102 | 495 |
| [scripts/update-config.py](/scripts/update-config.py) | Python | 325 | 21 | 107 | 453 |
| [scripts/update\_databases.py](/scripts/update_databases.py) | Python | 444 | 28 | 112 | 584 |
| [scripts/update\_mcp.py](/scripts/update_mcp.py) | Python | 500 | 43 | 146 | 689 |
| [test-data/ground-truth-simple.yaml](/test-data/ground-truth-simple.yaml) | YAML | 73 | 9 | 20 | 102 |
| [test-data/ground-truth.yaml](/test-data/ground-truth.yaml) | YAML | 271 | 10 | 65 | 346 |
| [test-data/test-queries.yaml](/test-data/test-queries.yaml) | YAML | 118 | 9 | 23 | 150 |
| [test\_after\_fix.py](/test_after_fix.py) | Python | 27 | 2 | 6 | 35 |
| [test\_crawl\_debug.py](/test_crawl_debug.py) | Python | 27 | 1 | 5 | 33 |
| [test\_exact\_config.py](/test_exact_config.py) | Python | 45 | 4 | 7 | 56 |
| [test\_isolate\_bug.py](/test_isolate_bug.py) | Python | 28 | 4 | 9 | 41 |
| [uv.lock](/uv.lock) | toml | 6,468 | 0 | 303 | 6,771 |

[Summary](results.md) / Details / [Diff Summary](diff.md) / [Diff Details](diff-details.md)