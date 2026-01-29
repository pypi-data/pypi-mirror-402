/**
 * ConfirmDeleteModal - Reusable confirmation modal for destructive actions
 *
 * Features:
 * - Clear warning with consequences
 * - Shows what will be deleted
 * - Red styling for danger emphasis
 * - Two-step confirmation (click delete → see modal → confirm)
 */

import {
  Modal,
  Stack,
  Text,
  Group,
  Button,
  Alert,
  Loader,
  Box,
} from '@mantine/core';
import { IconAlertTriangle } from '@tabler/icons-react';

export interface DeleteTarget {
  type: 'document' | 'collection';
  name: string;
  /** For collections: number of documents that will be deleted */
  documentCount?: number;
}

interface ConfirmDeleteModalProps {
  opened: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  target: DeleteTarget | null;
  isDeleting?: boolean;
}

export function ConfirmDeleteModal({
  opened,
  onClose,
  onConfirm,
  target,
  isDeleting = false,
}: ConfirmDeleteModalProps) {
  if (!target) return null;

  const isCollection = target.type === 'collection';
  const title = isCollection ? 'Delete Collection' : 'Delete Document';

  const handleConfirm = async () => {
    await onConfirm();
  };

  return (
    <Modal
      opened={opened}
      onClose={isDeleting ? () => {} : onClose}
      title={title}
      size="md"
      centered
      closeOnClickOutside={!isDeleting}
      closeOnEscape={!isDeleting}
      styles={{
        title: {
          fontFamily: 'Playfair Display, Georgia, serif',
          fontSize: 20,
          color: 'var(--mantine-color-red-6)',
          fontWeight: 700,
        },
      }}
    >
      <Stack gap="lg">
        <Alert
          icon={<IconAlertTriangle size={24} />}
          color="red"
          variant="light"
          title="Warning"
        >
          <Text size="sm">
            This action cannot be undone. The data will be permanently removed
            from both the vector store and knowledge graph.
          </Text>
        </Alert>

        <Box>
          <Text size="sm" c="dimmed" mb="xs">
            You are about to delete:
          </Text>
          <Text fw={600} size="md" style={{ color: 'var(--cream)' }}>
            "{target.name}"
          </Text>
        </Box>

        {isCollection && target.documentCount !== undefined && (
          <Box
            p="md"
            style={{
              background: 'var(--charcoal-light)',
              borderRadius: '8px',
              border: '1px solid var(--mantine-color-red-9)',
            }}
          >
            <Text size="sm" mb="xs">
              This will permanently delete:
            </Text>
            <Stack gap={4}>
              <Text size="sm">
                • <strong>{target.documentCount}</strong> document{target.documentCount !== 1 ? 's' : ''} in this collection
              </Text>
              <Text size="sm">• All associated chunks and embeddings</Text>
              <Text size="sm">• All related knowledge graph data</Text>
            </Stack>
          </Box>
        )}

        {!isCollection && (
          <Box
            p="md"
            style={{
              background: 'var(--charcoal-light)',
              borderRadius: '8px',
              border: '1px solid var(--mantine-color-red-9)',
            }}
          >
            <Text size="sm">
              This will permanently delete the document, all its chunks,
              embeddings, and related knowledge graph data.
            </Text>
          </Box>
        )}

        {isDeleting && (
          <Group justify="center" py="md">
            <Loader size="sm" color="red" />
            <Text size="sm" c="dimmed">
              Deleting... Please wait.
            </Text>
          </Group>
        )}

        <Group justify="flex-end" mt="md">
          <Button
            variant="light"
            onClick={onClose}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            color="red"
            onClick={handleConfirm}
            loading={isDeleting}
            disabled={isDeleting}
          >
            {isCollection ? 'Delete Collection' : 'Delete Document'}
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
