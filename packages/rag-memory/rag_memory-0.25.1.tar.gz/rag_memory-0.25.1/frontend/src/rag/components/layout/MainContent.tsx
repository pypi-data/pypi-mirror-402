/**
 * MainContent - Central content area that displays different views
 *
 * Routes to appropriate view component based on activeView prop:
 * - collections: CollectionBrowser
 * - documents: DocumentViewer/List
 * - search: Search interface with tabs (Semantic, Relationships, Temporal)
 * - chat: MessageList + ChatInput (from old ChatContainer)
 */

import { Box } from '@mantine/core';
import CollectionBrowser from '../CollectionBrowser';
import MessageList from '../MessageList';
import ChatInput from '../ChatInput';
import StarterPrompts from '../StarterPrompts';
import { DocumentsView } from '../views/DocumentsView';
import { SearchView } from '../views/SearchView';
import { DashboardView } from '../dashboard';
import { useRagStore } from '../../store';
import type { View } from './AppLayout';

interface Props {
  activeView: View;
}

export function MainContent({ activeView }: Props) {
  const { messages } = useRagStore();

  return (
    <Box
      style={{
        height: '100%',
        overflowY: 'auto',
        position: 'relative',
        zIndex: 2,
        background: 'var(--charcoal)',
        padding: '24px'
      }}
    >
      {/* Dashboard View */}
      {activeView === 'dashboard' && <DashboardView />}

      {/* Collections View */}
      {activeView === 'collections' && (
        <Box style={{ animation: 'fadeIn 0.4s ease' }}>
          <CollectionBrowser />
        </Box>
      )}

      {/* Documents View */}
      {activeView === 'documents' && <DocumentsView />}

      {/* Search View */}
      {activeView === 'search' && <SearchView />}

      {/* Chat View - Reuse existing components */}
      {activeView === 'chat' && (
        <Box
          style={{
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
            gap: 16,
            animation: 'fadeIn 0.4s ease'
          }}
        >
          {messages.length === 0 ? (
            <Box style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <StarterPrompts />
            </Box>
          ) : (
            <Box style={{ flex: 1, overflowY: 'auto' }}>
              <MessageList />
            </Box>
          )}

          <Box style={{ flexShrink: 0 }}>
            <ChatInput />
          </Box>
        </Box>
      )}
    </Box>
  );
}
