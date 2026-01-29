/**
 * AppLayout - 3-column Lumentor layout
 *
 * Structure: [Left Nav 280px] | [Main Content 1fr] | [Right Panel 360px]
 *
 * This replaces the old 4-column ChatContainer layout with view-based navigation.
 */

import { Box } from '@mantine/core';
import { useState } from 'react';
import { TopBar } from './TopBar';
import { LeftNavigation } from './LeftNavigation';
import { MainContent } from './MainContent';
import { IngestionModal } from '../modals/IngestionModal';
import { useRagStore } from '../../store';

export type View = 'dashboard' | 'collections' | 'documents' | 'search' | 'chat';

export function AppLayout() {
  const [activeView, setActiveView] = useState<View>('dashboard');

  // Agent-triggered ingestion modal state
  const {
    ingestionModalOpen,
    ingestionModalTab,
    ingestionModalParams,
    closeIngestionModal,
    loadCollections,
  } = useRagStore();

  return (
    <Box style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <TopBar />

      <Box
        style={{
          display: 'flex',
          flex: 1,
          overflow: 'hidden'
        }}
      >
        <LeftNavigation activeView={activeView} onViewChange={setActiveView} />
        <Box style={{ flex: 1, overflow: 'hidden' }}>
          <MainContent activeView={activeView} />
        </Box>
      </Box>

      {/* Agent-triggered ingestion modal */}
      <IngestionModal
        opened={ingestionModalOpen}
        onClose={() => {
          closeIngestionModal();
          // Refresh collections after modal closes (user may have ingested content)
          loadCollections();
        }}
        defaultCollection={ingestionModalParams.collection_name}
        defaultTab={ingestionModalTab}
        defaultTopic={ingestionModalParams.topic}
        defaultMode={ingestionModalParams.mode}
        defaultReviewedByHuman={ingestionModalParams.reviewed_by_human}
      />
    </Box>
  );
}
