/**
 * LinkToCollectionModal - Modal for linking a document to an additional collection
 *
 * Features:
 * - Dropdown to select target collection (filters out already-linked collections)
 * - Shows currently linked collections as badges
 * - Loading state during link operation
 * - Error handling with user-friendly messages
 * - Instant operation (no re-embedding or re-graphing)
 */

import { useState, useMemo } from 'react';
import {
  Modal,
  Stack,
  Text,
  Group,
  Button,
  Select,
  Badge,
  Alert,
  Box,
} from '@mantine/core';
import { IconLink, IconInfoCircle } from '@tabler/icons-react';
import type { Collection } from '../../types';
import { manageCollectionLink } from '../../ragApi';

interface LinkToCollectionModalProps {
  opened: boolean;
  onClose: () => void;
  onSuccess: () => void;
  documentId: number;
  documentTitle: string;
  currentCollections: string[];
  availableCollections: Collection[];
}

export function LinkToCollectionModal({
  opened,
  onClose,
  onSuccess,
  documentId,
  documentTitle,
  currentCollections,
  availableCollections,
}: LinkToCollectionModalProps) {
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);
  const [isLinking, setIsLinking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter out collections the document is already in
  const selectOptions = useMemo(() => {
    return availableCollections
      .filter((c) => !currentCollections.includes(c.name))
      .map((c) => ({
        value: c.name,
        label: c.name,
        description: c.description,
      }));
  }, [availableCollections, currentCollections]);

  const hasAvailableCollections = selectOptions.length > 0;
  const isInAllCollections = availableCollections.length > 0 && !hasAvailableCollections;
  const noCollectionsExist = availableCollections.length === 0;

  const handleLink = async () => {
    if (!selectedCollection) return;

    setIsLinking(true);
    setError(null);

    try {
      await manageCollectionLink(documentId, selectedCollection, false);
      setSelectedCollection(null);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to link document');
    } finally {
      setIsLinking(false);
    }
  };

  const handleClose = () => {
    if (isLinking) return;
    setSelectedCollection(null);
    setError(null);
    onClose();
  };

  return (
    <Modal
      opened={opened}
      onClose={handleClose}
      title="Add to Collection"
      size="md"
      centered
      closeOnClickOutside={!isLinking}
      closeOnEscape={!isLinking}
      styles={{
        title: {
          fontFamily: 'Playfair Display, Georgia, serif',
          fontSize: 20,
          color: 'var(--teal-light)',
          fontWeight: 700,
        },
      }}
    >
      <Stack gap="lg">
        {/* Info banner */}
        <Alert
          icon={<IconInfoCircle size={20} />}
          color="teal"
          variant="light"
        >
          <Text size="sm">
            Add this document to another collection. No re-processing required - this is an instant link operation.
          </Text>
        </Alert>

        {/* Document being linked */}
        <Box>
          <Text size="xs" c="dimmed" mb={4}>
            Document
          </Text>
          <Text fw={500} size="sm" style={{ color: 'var(--cream)' }} lineClamp={2}>
            {documentTitle}
          </Text>
        </Box>

        {/* Currently in collections */}
        {currentCollections.length > 0 && (
          <Box>
            <Text size="xs" c="dimmed" mb={4}>
              Currently in
            </Text>
            <Group gap="xs">
              {currentCollections.map((name) => (
                <Badge
                  key={name}
                  variant="light"
                  size="sm"
                  style={{
                    background: 'rgba(20, 184, 166, 0.12)',
                    color: 'var(--teal-light)',
                  }}
                >
                  {name}
                </Badge>
              ))}
            </Group>
          </Box>
        )}

        {/* Collection selector or empty state */}
        {noCollectionsExist ? (
          <Box
            p="md"
            style={{
              background: 'var(--charcoal-light)',
              borderRadius: '8px',
              border: '1px solid var(--warm-gray)',
            }}
          >
            <Text size="sm" c="dimmed" ta="center">
              No collections available. Create a collection first.
            </Text>
          </Box>
        ) : isInAllCollections ? (
          <Box
            p="md"
            style={{
              background: 'var(--charcoal-light)',
              borderRadius: '8px',
              border: '1px solid var(--teal)',
            }}
          >
            <Text size="sm" c="var(--teal-light)" ta="center">
              This document is already in all available collections.
            </Text>
          </Box>
        ) : (
          <Box>
            <Text size="xs" c="dimmed" mb={4}>
              Select Collection
            </Text>
            <Select
              placeholder="Select a collection..."
              data={selectOptions}
              value={selectedCollection}
              onChange={setSelectedCollection}
              disabled={isLinking}
              searchable
              clearable
              styles={{
                input: {
                  background: 'var(--charcoal-light)',
                  border: '1px solid var(--warm-gray)',
                  color: 'var(--cream)',
                  '&:focus': {
                    borderColor: 'var(--teal)',
                  },
                },
                dropdown: {
                  background: 'var(--charcoal-light)',
                  border: '1px solid var(--warm-gray)',
                },
                option: {
                  color: 'var(--cream)',
                  '&[data-selected]': {
                    background: 'var(--teal)',
                  },
                  '&[data-hovered]': {
                    background: 'rgba(20, 184, 166, 0.2)',
                  },
                },
              }}
            />
          </Box>
        )}

        {/* Error display */}
        {error && (
          <Alert color="red" variant="light">
            <Text size="sm">{error}</Text>
          </Alert>
        )}

        {/* Actions */}
        <Group justify="flex-end" mt="md">
          <Button
            variant="light"
            onClick={handleClose}
            disabled={isLinking}
          >
            Cancel
          </Button>
          <Button
            color="teal"
            onClick={handleLink}
            loading={isLinking}
            disabled={isLinking || !selectedCollection || !hasAvailableCollections}
            leftSection={<IconLink size={16} />}
          >
            Link to Collection
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
