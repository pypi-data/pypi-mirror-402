/**
 * MessageBubble - Individual chat message with rich content support
 *
 * Supports:
 * - Plain text messages
 * - Code blocks
 * - Tool execution status
 * - Search results
 * - Knowledge graph relationships
 * - Web search results
 * - File attachments (displayed as minimal indicator)
 */

import { Paper, Text, Box, Badge, Loader, Stack, Group } from '@mantine/core';
import { IconCheck, IconX, IconPaperclip } from '@tabler/icons-react';
import LinkifiedContent from './LinkifiedContent';
import type { ChatMessage, ToolExecution } from '../types';

// Markers that separate user's message from attached file content
const FILE_ATTACHMENT_MARKER = '\n\n---\n**Attached Files';
const FILE_ATTACHMENT_START = '**Attached Files';

/**
 * Parse user message to separate the text from file attachments.
 * File content is sent to the agent but shouldn't clutter the UI.
 * Handles two cases:
 * 1. User text + files: "message\n\n---\n**Attached Files..."
 * 2. Files only: "**Attached Files..."
 */
function parseUserMessage(content: string): { displayContent: string; fileCount: number } {
  // Case 1: Message with separator before files
  const markerIndex = content.indexOf(FILE_ATTACHMENT_MARKER);
  if (markerIndex !== -1) {
    const displayContent = content.substring(0, markerIndex).trim();
    const afterMarker = content.substring(markerIndex);
    const countMatch = afterMarker.match(/\*\*Attached Files \((\d+)\):\*\*/);
    const fileCount = countMatch ? parseInt(countMatch[1], 10) : 1;
    return { displayContent, fileCount };
  }

  // Case 2: Files only (no user text, starts with **Attached Files)
  if (content.startsWith(FILE_ATTACHMENT_START)) {
    const countMatch = content.match(/\*\*Attached Files \((\d+)\):\*\*/);
    const fileCount = countMatch ? parseInt(countMatch[1], 10) : 1;
    return { displayContent: '', fileCount };
  }

  // No attachments
  return { displayContent: content, fileCount: 0 };
}

interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
  currentToolExecutions?: ToolExecution[];
}

// Helper function to format tool names for display
const formatToolName = (name: string) => {
  const names: Record<string, string> = {
    'search_documents': 'Searching documents',
    'list_documents': 'Listing documents',
    'list_collections': 'Listing collections',
    'get_collection_info': 'Getting collection info',
    'get_document_by_id': 'Getting document',
    'web_search': 'Searching web',
    'query_relationships': 'Querying knowledge graph',
    'query_temporal': 'Analyzing timeline',
    'create_collection': 'Creating collection',
    'update_document': 'Updating document',
    'delete_document': 'Deleting document',
    'ingest_url': 'Ingesting web page',
    'ingest_text': 'Ingesting text',
    'ingest_file': 'Ingesting file',
    'ingest_directory': 'Ingesting directory',
    'analyze_website': 'Analyzing website',
    'validate_url': 'Validating URL',
    'fetch_url': 'Fetching URL',
  };
  return names[name] || 'Working...';  // Generic fallback instead of tool name
};

export default function MessageBubble({ message, isStreaming, currentToolExecutions }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  // For user messages, parse out file attachments to display minimal indicator
  const { displayContent, fileCount } = isUser
    ? parseUserMessage(message.content)
    : { displayContent: message.content, fileCount: 0 };

  return (
    <Box
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        animation: 'fadeIn 0.4s ease',
      }}
    >
      <Paper
        p="md"
        radius="md"
        style={{
          maxWidth: '80%',
          position: 'relative',
          background: isUser
            ? 'linear-gradient(135deg, var(--amber) 0%, var(--amber-dark) 100%)'
            : 'var(--charcoal-light)',
          border: isUser
            ? 'none'
            : '2px solid var(--warm-gray)',
          color: isUser ? 'var(--charcoal)' : 'var(--cream)',
        }}
      >
        {/* Role badge */}
        <Badge
          size="xs"
          variant={isUser ? 'filled' : 'light'}
          color={isUser ? 'dark' : 'teal'}
          mb="xs"
        >
          {isUser ? 'You' : 'Assistant'}
        </Badge>

        {/* File attachment indicator (for user messages with attachments) */}
        {isUser && fileCount > 0 && (
          <Group gap="xs" mb="xs">
            <Badge
              size="sm"
              variant="light"
              color="dark"
              leftSection={<IconPaperclip size={12} />}
            >
              {fileCount} file{fileCount > 1 ? 's' : ''} attached
            </Badge>
          </Group>
        )}

        {/* Message content with clickable links */}
        <LinkifiedContent
          content={displayContent || (fileCount > 0 ? 'Please help me ingest these files.' : '')}
          color={isUser ? 'var(--charcoal)' : 'var(--cream)'}
          linkColor={isUser ? 'var(--charcoal)' : undefined}  // Dark links on amber background, default (amber) on dark background
          size="sm"
        />

        {/* Streaming indicator */}
        {isStreaming && (
          <Box mt="xs">
            <Loader size="xs" color={isUser ? 'dark' : 'amber'} />
          </Box>
        )}

        {/* Tool execution indicators - only show for assistant messages */}
        {!isUser && currentToolExecutions && currentToolExecutions.length > 0 && (
          <Stack gap="xs" mt="xs">
            {currentToolExecutions.map((tool) => (
              <Group key={tool.id} gap="xs">
                {tool.status === 'running' && <Loader size="xs" color="amber" />}
                {tool.status === 'completed' && <IconCheck size={16} color="var(--teal)" />}
                {tool.status === 'failed' && <IconX size={16} color="var(--sienna)" />}
                <Text
                  size="sm"
                  style={{
                    color: 'var(--warm-gray)'
                  }}
                >
                  {tool.status === 'running' && `${formatToolName(tool.name)}...`}
                  {tool.status === 'completed' && `✓ ${formatToolName(tool.name)}`}
                  {tool.status === 'failed' && `✗ ${formatToolName(tool.name)}`}
                </Text>
              </Group>
            ))}
          </Stack>
        )}

        {/* Timestamp */}
        <Text
          size="xs"
          mt="xs"
          style={{
            color: isUser ? 'var(--charcoal-lighter)' : 'var(--warm-gray)'
          }}
        >
          {new Date(message.created_at).toLocaleTimeString()}
        </Text>
      </Paper>
    </Box>
  );
}
