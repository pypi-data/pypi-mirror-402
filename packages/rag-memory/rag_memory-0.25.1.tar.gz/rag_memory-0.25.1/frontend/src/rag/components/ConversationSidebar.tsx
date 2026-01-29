/**
 * ConversationSidebar - Modern conversation history with full feature set
 *
 * Features:
 * - Collapsible sidebar with toggle button
 * - Search conversations
 * - Pinned conversations section
 * - Date-based grouping
 * - Rename conversations (inline edit)
 * - Pin/unpin conversations
 * - Multi-select mode for bulk operations
 * - Bulk delete selected
 * - Delete all conversations
 */

import { useState, useEffect } from 'react';
import {
  Stack,
  TextInput,
  ScrollArea,
  UnstyledButton,
  Text,
  Group,
  ActionIcon,
  Box,
  Divider,
  Menu,
  Checkbox,
  Button,
  Modal,
} from '@mantine/core';
import {
  IconSearch,
  IconPlus,
  IconMessage,
  IconDots,
  IconTrash,
  IconEdit,
  IconPin,
  IconPinFilled,
  IconChecks,
  IconChevronLeft,
  IconChevronRight,
} from '@tabler/icons-react';
import { useRagStore } from '../store';
import type { Conversation } from '../types';

interface ConversationSidebarProps {
  onClose?: () => void;
}

export default function ConversationSidebar({ onClose }: ConversationSidebarProps) {
  const {
    conversations,
    activeConversationId,
    loadConversations,
    selectConversation,
    deleteConversation,
    updateConversation,
    bulkDeleteConversations,
    deleteAllConversations,
    startNewConversation,
  } = useRagStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [hoveredId, setHoveredId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [isMultiSelectMode, setIsMultiSelectMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [deleteAllModalOpen, setDeleteAllModalOpen] = useState(false);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // Filter conversations by search query
  const filteredConversations = conversations.filter((conv) =>
    (conv.title || 'Untitled').toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Separate pinned and unpinned conversations
  const pinnedConversations = filteredConversations.filter((c) => c.is_pinned);
  const unpinnedConversations = filteredConversations.filter((c) => !c.is_pinned);

  // Group unpinned conversations by date
  const groupedConversations = groupConversationsByDate(unpinnedConversations);

  const handleSelectConversation = (conversationId: number) => {
    if (isMultiSelectMode) {
      // Toggle selection
      setSelectedIds((prev) =>
        prev.includes(conversationId)
          ? prev.filter((id) => id !== conversationId)
          : [...prev, conversationId]
      );
    } else {
      selectConversation(conversationId);
      onClose?.();
    }
  };

  const handleNewConversation = () => {
    startNewConversation();
    onClose?.();
  };

  const handleTogglePin = async (conversationId: number, isPinned: boolean) => {
    await updateConversation(conversationId, { is_pinned: !isPinned });
  };

  const handleStartRename = (conv: Conversation) => {
    setEditingId(conv.id);
    setEditingTitle(conv.title || '');
  };

  const handleSaveRename = async (conversationId: number) => {
    if (editingTitle.trim()) {
      await updateConversation(conversationId, { title: editingTitle.trim() });
    }
    setEditingId(null);
  };

  const handleCancelRename = () => {
    setEditingId(null);
    setEditingTitle('');
  };

  const handleToggleMultiSelect = () => {
    setIsMultiSelectMode(!isMultiSelectMode);
    setSelectedIds([]);
  };

  const handleBulkDelete = async () => {
    if (selectedIds.length > 0) {
      if (confirm(`Delete ${selectedIds.length} conversation(s)?`)) {
        await bulkDeleteConversations(selectedIds);
        setSelectedIds([]);
        setIsMultiSelectMode(false);
      }
    }
  };

  const handleDeleteAll = async () => {
    setDeleteAllModalOpen(false);
    await deleteAllConversations();
  };

  // Collapsed view - just toggle button
  if (isCollapsed) {
    return (
      <Box
        style={{
          width: '48px',
          height: '100%',
          backgroundColor: 'var(--mantine-color-dark-8)',
          borderRight: '1px solid var(--mantine-color-dark-6)',
          display: 'flex',
          alignItems: 'flex-start',
          padding: '12px',
        }}
      >
        <ActionIcon
          onClick={() => setIsCollapsed(false)}
          variant="subtle"
          size="lg"
          color="gray"
        >
          <IconChevronRight size={18} />
        </ActionIcon>
      </Box>
    );
  }

  return (
    <Stack
      gap={0}
      h="100%"
      style={{
        backgroundColor: 'var(--mantine-color-dark-8)',
        borderRight: '1px solid var(--mantine-color-dark-6)',
      }}
    >
      {/* Header with New Chat and Collapse buttons */}
      <Box p="md" style={{ borderBottom: '1px solid var(--mantine-color-dark-6)' }}>
        <Group gap="xs" wrap="nowrap">
          <UnstyledButton
            onClick={handleNewConversation}
            style={{
              flex: 1,
              padding: '12px 16px',
              borderRadius: '8px',
              backgroundColor: 'var(--mantine-color-dark-7)',
              border: '1px solid var(--mantine-color-dark-5)',
              transition: 'all 150ms ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--mantine-color-dark-6)';
              e.currentTarget.style.borderColor = 'var(--mantine-color-dark-4)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--mantine-color-dark-7)';
              e.currentTarget.style.borderColor = 'var(--mantine-color-dark-5)';
            }}
          >
            <Group gap="sm" wrap="nowrap">
              <IconPlus size={18} stroke={1.5} />
              <Text size="sm" fw={500}>
                New
              </Text>
            </Group>
          </UnstyledButton>

          <ActionIcon
            onClick={() => setIsCollapsed(true)}
            variant="subtle"
            size="lg"
            color="gray"
          >
            <IconChevronLeft size={18} />
          </ActionIcon>
        </Group>
      </Box>

      {/* Search */}
      <Box p="md" pb="xs">
        <TextInput
          placeholder="Search conversations..."
          leftSection={<IconSearch size={16} />}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.currentTarget.value)}
          styles={{
            input: {
              backgroundColor: 'var(--mantine-color-dark-7)',
              border: '1px solid var(--mantine-color-dark-6)',
              '&:focus': {
                borderColor: 'var(--mantine-color-blue-6)',
              },
            },
          }}
        />
      </Box>

      {/* Action buttons: Multi-select, Delete All */}
      <Box px="md" pb="xs">
        <Group gap="xs">
          <Button
            size="compact-sm"
            variant={isMultiSelectMode ? 'filled' : 'subtle'}
            color="gray"
            leftSection={<IconChecks size={14} />}
            onClick={handleToggleMultiSelect}
            fullWidth={!isMultiSelectMode}
          >
            {isMultiSelectMode ? 'Cancel' : 'Select'}
          </Button>

          {isMultiSelectMode && selectedIds.length > 0 && (
            <Button
              size="compact-sm"
              variant="filled"
              color="red"
              leftSection={<IconTrash size={14} />}
              onClick={handleBulkDelete}
              fullWidth
            >
              Delete {selectedIds.length}
            </Button>
          )}

          {!isMultiSelectMode && conversations.length > 0 && (
            <Button
              size="compact-sm"
              variant="subtle"
              color="red"
              leftSection={<IconTrash size={14} />}
              onClick={() => setDeleteAllModalOpen(true)}
            >
              Delete All
            </Button>
          )}
        </Group>
      </Box>

      {/* Conversation List */}
      <ScrollArea flex={1} offsetScrollbars>
        <Stack gap="xs" p="xs">
          {/* Pinned Section */}
          {pinnedConversations.length > 0 && (
            <Box>
              <Text
                size="xs"
                fw={600}
                c="dimmed"
                tt="uppercase"
                px="md"
                py="xs"
                style={{ letterSpacing: '0.5px' }}
              >
                Pinned
              </Text>

              <Stack gap={2}>
                {pinnedConversations.map((conversation) => (
                  <ConversationItem
                    key={conversation.id}
                    conversation={conversation}
                    isActive={conversation.id === activeConversationId}
                    isHovered={conversation.id === hoveredId}
                    isEditing={conversation.id === editingId}
                    editingTitle={editingTitle}
                    isMultiSelectMode={isMultiSelectMode}
                    isSelected={selectedIds.includes(conversation.id)}
                    onSelect={() => handleSelectConversation(conversation.id)}
                    onDelete={() => deleteConversation(conversation.id)}
                    onTogglePin={() => handleTogglePin(conversation.id, conversation.is_pinned)}
                    onStartRename={() => handleStartRename(conversation)}
                    onSaveRename={() => handleSaveRename(conversation.id)}
                    onCancelRename={handleCancelRename}
                    onEditingTitleChange={setEditingTitle}
                    onMouseEnter={() => setHoveredId(conversation.id)}
                    onMouseLeave={() => setHoveredId(null)}
                  />
                ))}
              </Stack>

              <Divider my="xs" color="dark.6" />
            </Box>
          )}

          {/* Grouped Conversations */}
          {Object.entries(groupedConversations).map(([dateLabel, convs]) => (
            <Box key={dateLabel}>
              <Text
                size="xs"
                fw={600}
                c="dimmed"
                tt="uppercase"
                px="md"
                py="xs"
                style={{ letterSpacing: '0.5px' }}
              >
                {dateLabel}
              </Text>

              <Stack gap={2}>
                {convs.map((conversation) => (
                  <ConversationItem
                    key={conversation.id}
                    conversation={conversation}
                    isActive={conversation.id === activeConversationId}
                    isHovered={conversation.id === hoveredId}
                    isEditing={conversation.id === editingId}
                    editingTitle={editingTitle}
                    isMultiSelectMode={isMultiSelectMode}
                    isSelected={selectedIds.includes(conversation.id)}
                    onSelect={() => handleSelectConversation(conversation.id)}
                    onDelete={() => deleteConversation(conversation.id)}
                    onTogglePin={() => handleTogglePin(conversation.id, conversation.is_pinned)}
                    onStartRename={() => handleStartRename(conversation)}
                    onSaveRename={() => handleSaveRename(conversation.id)}
                    onCancelRename={handleCancelRename}
                    onEditingTitleChange={setEditingTitle}
                    onMouseEnter={() => setHoveredId(conversation.id)}
                    onMouseLeave={() => setHoveredId(null)}
                  />
                ))}
              </Stack>

              <Divider my="xs" color="dark.6" />
            </Box>
          ))}

          {filteredConversations.length === 0 && (
            <Box p="xl" style={{ textAlign: 'center' }}>
              <Text size="sm" c="dimmed">
                {searchQuery ? 'No conversations found' : 'No conversations yet'}
              </Text>
            </Box>
          )}
        </Stack>
      </ScrollArea>

      {/* Delete All Confirmation Modal */}
      <Modal
        opened={deleteAllModalOpen}
        onClose={() => setDeleteAllModalOpen(false)}
        title="Delete All Conversations"
        centered
      >
        <Text size="sm" mb="md">
          Are you sure you want to delete ALL {conversations.length} conversation(s)? This action
          cannot be undone.
        </Text>
        <Group justify="flex-end">
          <Button variant="subtle" onClick={() => setDeleteAllModalOpen(false)}>
            Cancel
          </Button>
          <Button color="red" onClick={handleDeleteAll}>
            Delete All
          </Button>
        </Group>
      </Modal>
    </Stack>
  );
}

/**
 * Individual conversation item with all features
 */
interface ConversationItemProps {
  conversation: Conversation;
  isActive: boolean;
  isHovered: boolean;
  isEditing: boolean;
  editingTitle: string;
  isMultiSelectMode: boolean;
  isSelected: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onTogglePin: () => void;
  onStartRename: () => void;
  onSaveRename: () => void;
  onCancelRename: () => void;
  onEditingTitleChange: (title: string) => void;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
}

function ConversationItem({
  conversation,
  isActive,
  isHovered,
  isEditing,
  editingTitle,
  isMultiSelectMode,
  isSelected,
  onSelect,
  onDelete,
  onTogglePin,
  onStartRename,
  onSaveRename,
  onCancelRename,
  onEditingTitleChange,
  onMouseEnter,
  onMouseLeave,
}: ConversationItemProps) {
  return (
    <Box
      onClick={onSelect}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      style={{
        width: '100%',
        padding: '10px 12px',
        borderRadius: '6px',
        backgroundColor: isActive
          ? 'var(--mantine-color-dark-6)'
          : isHovered || isSelected
          ? 'var(--mantine-color-dark-7)'
          : 'transparent',
        border: isActive
          ? '1px solid var(--mantine-color-dark-5)'
          : '1px solid transparent',
        transition: 'all 120ms ease',
        position: 'relative',
        cursor: 'pointer',
      }}
    >
      <Group gap="sm" wrap="nowrap" justify="space-between">
        {/* Checkbox (multi-select mode) */}
        {isMultiSelectMode && (
          <Checkbox
            checked={isSelected}
            onChange={(e) => {
              e.stopPropagation();
              onSelect();
            }}
            onClick={(e) => {
              e.stopPropagation();
            }}
            size="xs"
            styles={{ input: { cursor: 'pointer' } }}
          />
        )}

        {/* Content */}
        <Group gap="sm" wrap="nowrap" style={{ flex: 1, minWidth: 0 }}>
          {!isMultiSelectMode && (
            <IconMessage
              size={16}
              stroke={1.5}
              style={{
                color: isActive ? 'var(--mantine-color-blue-5)' : 'var(--mantine-color-gray-6)',
                flexShrink: 0,
              }}
            />
          )}

          {isEditing ? (
            <TextInput
              value={editingTitle}
              onChange={(e) => onEditingTitleChange(e.currentTarget.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  onSaveRename();
                } else if (e.key === 'Escape') {
                  onCancelRename();
                }
              }}
              onBlur={onSaveRename}
              onClick={(e) => e.stopPropagation()}
              autoFocus
              size="xs"
              styles={{
                input: {
                  backgroundColor: 'var(--mantine-color-dark-7)',
                  border: '1px solid var(--mantine-color-blue-6)',
                },
              }}
              style={{ flex: 1 }}
            />
          ) : (
            <Text
              size="sm"
              fw={isActive ? 500 : 400}
              c={isActive ? 'white' : 'gray.3'}
              style={{
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {conversation.title || 'Untitled Conversation'}
            </Text>
          )}
        </Group>

        {/* Actions menu (show on hover, hide in multi-select mode) */}
        {isHovered && !isMultiSelectMode && !isEditing && (
          <Menu position="right-start" offset={4}>
            <Menu.Target>
              <ActionIcon
                size="sm"
                variant="subtle"
                color="gray"
                onClick={(e) => {
                  e.stopPropagation();
                }}
                style={{ flexShrink: 0 }}
              >
                <IconDots size={16} />
              </ActionIcon>
            </Menu.Target>

            <Menu.Dropdown>
              <Menu.Item
                leftSection={<IconEdit size={16} />}
                onClick={(e) => {
                  e.stopPropagation();
                  onStartRename();
                }}
              >
                Rename
              </Menu.Item>
              <Menu.Item
                leftSection={
                  conversation.is_pinned ? <IconPinFilled size={16} /> : <IconPin size={16} />
                }
                onClick={(e) => {
                  e.stopPropagation();
                  onTogglePin();
                }}
              >
                {conversation.is_pinned ? 'Unpin' : 'Pin'}
              </Menu.Item>
              <Menu.Divider />
              <Menu.Item
                leftSection={<IconTrash size={16} />}
                color="red"
                onClick={(e) => {
                  e.stopPropagation();
                  if (confirm('Delete this conversation?')) {
                    onDelete();
                  }
                }}
              >
                Delete
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>
        )}
      </Group>
    </Box>
  );
}

/**
 * Group conversations by date (Today, Yesterday, Last 7 Days, Last 30 Days, Older)
 */
function groupConversationsByDate(conversations: Conversation[]): Record<string, Conversation[]> {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const lastWeek = new Date(today);
  lastWeek.setDate(lastWeek.getDate() - 7);
  const lastMonth = new Date(today);
  lastMonth.setDate(lastMonth.getDate() - 30);

  const groups: Record<string, Conversation[]> = {
    'Today': [],
    'Yesterday': [],
    'Last 7 Days': [],
    'Last 30 Days': [],
    'Older': [],
  };

  conversations.forEach((conv) => {
    const convDate = new Date(conv.created_at);
    const convDateOnly = new Date(convDate.getFullYear(), convDate.getMonth(), convDate.getDate());

    if (convDateOnly.getTime() === today.getTime()) {
      groups['Today'].push(conv);
    } else if (convDateOnly.getTime() === yesterday.getTime()) {
      groups['Yesterday'].push(conv);
    } else if (convDate >= lastWeek) {
      groups['Last 7 Days'].push(conv);
    } else if (convDate >= lastMonth) {
      groups['Last 30 Days'].push(conv);
    } else {
      groups['Older'].push(conv);
    }
  });

  // Remove empty groups
  Object.keys(groups).forEach((key) => {
    if (groups[key].length === 0) {
      delete groups[key];
    }
  });

  return groups;
}
