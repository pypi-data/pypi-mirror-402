/**
 * MessageList - Displays chat messages with streaming support and rich content
 */

import { useEffect, useRef, useState } from 'react';
import { Stack, ScrollArea } from '@mantine/core';
import { useRagStore } from '../store';
import MessageBubble from './MessageBubble';
import SearchResults from './SearchResults';
import WebSearchResults from './WebSearchResults';
import KnowledgeGraphView from './KnowledgeGraphView';
import TemporalTimeline from './TemporalTimeline';
import DocumentModal from './DocumentModal';
import ToolProposalCard from './ToolProposalCard';
import { getDocument } from '../ragApi';
import type { Document } from '../types';

export default function MessageList() {
  const {
    messages,
    streamingContent,
    isStreaming,
    currentSearchResults,
    currentWebSearchResults,
    currentKnowledgeGraph,
    currentTemporalData,
    currentToolExecutions,
    pendingToolCalls,
    approvePendingTools,
    rejectPendingTools,
    revisePendingTools,
    sendMessage,
  } = useRagStore();
  const viewport = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Document modal state
  const [isDocModalOpen, setIsDocModalOpen] = useState(false);
  const [viewingDocument, setViewingDocument] = useState<Document | null>(null);

  // Handle opening document in modal
  const handleViewDocument = async (documentId: number) => {
    try {
      const doc = await getDocument(documentId);
      setViewingDocument(doc);
      setIsDocModalOpen(true);
    } catch (error) {
      console.error('Failed to load document:', error);
    }
  };

  // Auto-scroll to bottom when new messages arrive or rich content appears
  // Using Lumentor pattern: bottomRef + scrollIntoView + requestAnimationFrame
  useEffect(() => {
    requestAnimationFrame(() => {
      if (bottomRef.current) {
        bottomRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    });
  }, [
    messages,
    streamingContent,
    isStreaming,
    currentSearchResults,
    currentWebSearchResults,
    currentKnowledgeGraph,
    currentTemporalData,
    currentToolExecutions,
    pendingToolCalls,
  ]);

  return (
    <ScrollArea
      h="100%"
      viewportRef={viewport}
      style={{ flex: 1 }}
      offsetScrollbars
    >
      <Stack gap="md" p="md">
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            currentToolExecutions={currentToolExecutions}
          />
        ))}

        {/* Streaming message (assistant's in-progress response) */}
        {isStreaming && (
          <MessageBubble
            message={{
              id: -1,
              role: 'assistant',
              content: streamingContent || '',
              created_at: new Date().toISOString(),
            }}
            isStreaming
            currentToolExecutions={currentToolExecutions}
          />
        )}

        {/* Tool Proposal Card - show when agent wants to execute tools */}
        {pendingToolCalls.length > 0 && (
          <ToolProposalCard
            tools={pendingToolCalls}
            onApprove={approvePendingTools}
            onReject={rejectPendingTools}
            onRevise={revisePendingTools}
          />
        )}

        {/* Rich content components - only show AFTER streaming completes */}
        {!isStreaming && currentSearchResults.length > 0 && (
          <SearchResults
            results={currentSearchResults}
            onDocumentClick={handleViewDocument}
          />
        )}

        {!isStreaming && currentWebSearchResults.length > 0 && (
          <WebSearchResults
            results={currentWebSearchResults}
            onValidateUrl={(url) => sendMessage(`Validate this URL: ${url}`)}
            onIngestUrl={(url) => sendMessage(`Ingest this URL: ${url}`)}
          />
        )}

        {!isStreaming && currentKnowledgeGraph.length > 0 && (
          <KnowledgeGraphView relationships={currentKnowledgeGraph} />
        )}

        {!isStreaming && currentTemporalData.length > 0 && (
          <TemporalTimeline timeline={currentTemporalData} />
        )}

        {/* Invisible element at bottom for auto-scroll (Lumentor pattern) */}
        <div ref={bottomRef} />
      </Stack>

      {/* Document Modal */}
      <DocumentModal
        document={viewingDocument}
        opened={isDocModalOpen}
        onClose={() => {
          setIsDocModalOpen(false);
          setViewingDocument(null);
        }}
        onDocumentUpdate={(updated) => setViewingDocument(updated)}
      />
    </ScrollArea>
  );
}
