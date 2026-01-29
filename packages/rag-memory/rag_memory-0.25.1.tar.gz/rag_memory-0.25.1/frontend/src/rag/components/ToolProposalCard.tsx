/**
 * ToolProposalCard - Displays pending tool calls for user approval
 *
 * Shows:
 * - Tool name(s) being proposed
 * - All parameters with values
 * - Approve/Reject buttons
 * - Optional edit mode for revising parameters
 */

import { useState } from 'react';
import {
  Paper,
  Text,
  Group,
  Stack,
  Button,
  Badge,
  Code,
  Collapse,
  TextInput,
  Textarea,
  Box,
  Divider,
  ActionIcon,
} from '@mantine/core';
import { IconCheck, IconX, IconEdit, IconChevronDown, IconChevronUp } from '@tabler/icons-react';
import type { PendingToolCall } from '../types';

interface Props {
  tools: PendingToolCall[];
  onApprove: () => void;
  onReject: (reason?: string) => void;
  onRevise: (revisedTools: PendingToolCall[]) => void;
}

// Format tool names for display
const formatToolName = (name: string): string => {
  const names: Record<string, string> = {
    'search_documents': 'Search Documents',
    'list_documents': 'List Documents',
    'list_collections': 'List Collections',
    'get_collection_info': 'Get Collection Info',
    'get_document_by_id': 'Get Document',
    'web_search': 'Web Search',
    'query_relationships': 'Query Knowledge Graph',
    'query_temporal': 'Query Timeline',
    'create_collection': 'Create Collection',
    'delete_collection': 'Delete Collection',
    'update_document': 'Update Document',
    'delete_document': 'Delete Document',
    'ingest_url': 'Ingest Web Page',
    'ingest_text': 'Ingest Text',
    'ingest_file': 'Ingest File',
    'ingest_directory': 'Ingest Directory',
    'analyze_website': 'Analyze Website',
    'validate_url': 'Validate URL',
    'fetch_url': 'Fetch URL',
  };
  return names[name] || name;
};

// Color for tool category
const getToolColor = (name: string): string => {
  if (name.startsWith('ingest') || name === 'create_collection') return 'teal';
  if (name.startsWith('delete')) return 'red';
  if (name.startsWith('search') || name.startsWith('query') || name.startsWith('list') || name.startsWith('get')) return 'blue';
  return 'gray';
};

export default function ToolProposalCard({ tools, onApprove, onReject, onRevise }: Props) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedTools, setEditedTools] = useState<PendingToolCall[]>(tools);
  const [expandedTools, setExpandedTools] = useState<Set<string>>(new Set(tools.map(t => t.id)));
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectInput, setShowRejectInput] = useState(false);

  const toggleExpand = (toolId: string) => {
    setExpandedTools(prev => {
      const next = new Set(prev);
      if (next.has(toolId)) {
        next.delete(toolId);
      } else {
        next.add(toolId);
      }
      return next;
    });
  };

  const handleArgChange = (toolId: string, argKey: string, value: string) => {
    setEditedTools(prev =>
      prev.map(t =>
        t.id === toolId
          ? { ...t, args: { ...t.args, [argKey]: value } }
          : t
      )
    );
  };

  const handleApprove = () => {
    if (isEditing) {
      // Submit revised tools
      onRevise(editedTools);
    } else {
      onApprove();
    }
  };

  const handleReject = () => {
    if (showRejectInput && rejectReason) {
      onReject(rejectReason);
    } else if (showRejectInput) {
      onReject();
    } else {
      setShowRejectInput(true);
    }
  };

  return (
    <Paper
      p="md"
      radius="md"
      style={{
        background: 'linear-gradient(135deg, var(--charcoal-light) 0%, #2d2923 100%)',
        border: '2px solid var(--amber)',
        maxWidth: '90%',
        margin: '0 auto',
      }}
    >
      {/* Header */}
      <Group justify="space-between" mb="md">
        <Group gap="xs">
          <Badge color="amber" variant="filled" size="lg">
            Tool Approval Required
          </Badge>
          <Text size="sm" c="dimmed">
            {tools.length} tool{tools.length > 1 ? 's' : ''} pending
          </Text>
        </Group>
        <ActionIcon
          variant="subtle"
          color="gray"
          onClick={() => {
            setIsEditing(!isEditing);
            if (!isEditing) {
              setEditedTools(tools); // Reset to original when entering edit mode
            }
          }}
          title={isEditing ? 'Cancel editing' : 'Edit parameters'}
        >
          <IconEdit size={18} />
        </ActionIcon>
      </Group>

      {/* Tool List */}
      <Stack gap="sm">
        {(isEditing ? editedTools : tools).map((tool) => (
          <Paper
            key={tool.id}
            p="sm"
            radius="sm"
            style={{
              background: 'var(--charcoal)',
              border: '1px solid var(--warm-gray)',
            }}
          >
            {/* Tool Header */}
            <Group
              justify="space-between"
              onClick={() => toggleExpand(tool.id)}
              style={{ cursor: 'pointer' }}
            >
              <Group gap="xs">
                <Badge color={getToolColor(tool.name)} variant="light">
                  {formatToolName(tool.name)}
                </Badge>
                <Text size="xs" c="dimmed">
                  {Object.keys(tool.args).length} parameter{Object.keys(tool.args).length !== 1 ? 's' : ''}
                </Text>
              </Group>
              {expandedTools.has(tool.id) ? (
                <IconChevronUp size={16} color="var(--warm-gray)" />
              ) : (
                <IconChevronDown size={16} color="var(--warm-gray)" />
              )}
            </Group>

            {/* Tool Parameters */}
            <Collapse in={expandedTools.has(tool.id)}>
              <Divider my="xs" color="var(--warm-gray)" />
              <Stack gap="xs">
                {Object.entries(tool.args).map(([key, value]) => (
                  <Box key={key}>
                    <Text size="xs" c="dimmed" mb={4}>
                      {key}
                    </Text>
                    {isEditing ? (
                      typeof value === 'string' && value.length > 50 ? (
                        <Textarea
                          size="xs"
                          value={String(value)}
                          onChange={(e) => handleArgChange(tool.id, key, e.target.value)}
                          autosize
                          minRows={2}
                          maxRows={6}
                          styles={{
                            input: {
                              background: 'var(--charcoal-light)',
                              color: 'var(--cream)',
                              border: '1px solid var(--warm-gray)',
                              fontFamily: 'var(--mantine-font-family-monospace)',
                              fontSize: '12px',
                            },
                          }}
                        />
                      ) : (
                        <TextInput
                          size="xs"
                          value={String(value)}
                          onChange={(e) => handleArgChange(tool.id, key, e.target.value)}
                          styles={{
                            input: {
                              background: 'var(--charcoal-light)',
                              color: 'var(--cream)',
                              border: '1px solid var(--warm-gray)',
                              fontFamily: 'var(--mantine-font-family-monospace)',
                              fontSize: '12px',
                            },
                          }}
                        />
                      )
                    ) : (
                      <Code
                        block
                        style={{
                          background: 'var(--charcoal-light)',
                          color: 'var(--cream)',
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word',
                          fontSize: '12px',
                        }}
                      >
                        {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                      </Code>
                    )}
                  </Box>
                ))}
              </Stack>
            </Collapse>
          </Paper>
        ))}
      </Stack>

      {/* Reject Reason Input */}
      <Collapse in={showRejectInput}>
        <TextInput
          mt="md"
          placeholder="Reason for rejection (optional)"
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
          styles={{
            input: {
              background: 'var(--charcoal)',
              color: 'var(--cream)',
              border: '1px solid var(--warm-gray)',
            },
          }}
        />
      </Collapse>

      {/* Action Buttons */}
      <Group justify="flex-end" mt="md" gap="sm">
        {showRejectInput && (
          <Button
            variant="subtle"
            color="gray"
            size="sm"
            onClick={() => setShowRejectInput(false)}
          >
            Cancel
          </Button>
        )}
        <Button
          variant="light"
          color="red"
          size="sm"
          leftSection={<IconX size={16} />}
          onClick={handleReject}
        >
          {showRejectInput ? 'Confirm Reject' : 'Reject'}
        </Button>
        <Button
          variant="filled"
          color="teal"
          size="sm"
          leftSection={<IconCheck size={16} />}
          onClick={handleApprove}
        >
          {isEditing ? 'Apply & Execute' : 'Approve'}
        </Button>
      </Group>
    </Paper>
  );
}
