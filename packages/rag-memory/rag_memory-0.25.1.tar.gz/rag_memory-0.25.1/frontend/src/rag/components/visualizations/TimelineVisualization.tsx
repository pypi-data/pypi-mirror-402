/**
 * TimelineVisualization - Timeline for temporal knowledge evolution
 *
 * Displays how facts and relationships have changed over time
 * Uses vis-timeline for rendering
 */

import { useEffect, useRef } from 'react';
import { Timeline, DataSet } from 'vis-timeline/standalone';
import { Box, Modal, Text, Stack, Badge, Group } from '@mantine/core';

interface TemporalItem {
  fact: string;
  relationship_type: string;
  source_node_id?: string;
  target_node_id?: string;
  source_node_name?: string;  // Entity name for source
  target_node_name?: string;  // Entity name for target
  valid_from: string;
  valid_until: string | null;
  status: 'current' | 'superseded';
  created_at?: string;
  expired_at?: string | null;
}

interface Props {
  items: TemporalItem[];
  opened: boolean;
  onClose: () => void;
}

export function TimelineVisualization({ items, opened, onClose }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<Timeline | null>(null);

  useEffect(() => {
    if (!opened || items.length === 0) {
      return;
    }

    // Wait for container to be available (modal animation)
    const timer = setTimeout(() => {
      if (!containerRef.current) {
        console.error('TimelineVisualization: Container ref still null after delay');
        return;
      }

      // Convert temporal items to timeline items
      const timelineItems = new DataSet(
      items.map((item, idx) => {
        const start = new Date(item.valid_from);
        // For current facts (valid_until is null), extend to present day
        // For superseded facts, use the actual end date
        const end = item.valid_until ? new Date(item.valid_until) : new Date();

        // Build content with entity names if available
        const sourceName = item.source_node_name || (item.source_node_id ? item.source_node_id.substring(0, 15) : '');
        const targetName = item.target_node_name || (item.target_node_id ? item.target_node_id.substring(0, 15) : '');
        const entities = sourceName && targetName ? `<br/><em>${sourceName} → ${targetName}</em>` : '';

        return {
          id: idx,
          content: `<strong>${item.relationship_type}</strong>${entities}<br/>${item.fact.substring(0, 100)}${item.fact.length > 100 ? '...' : ''}`,
          start,
          end, // Always use end date (current date for ongoing facts)
          type: 'range', // Always render as bars, not points
          className: item.status === 'current' ? 'timeline-current' : 'timeline-superseded',
          title: item.fact // Full text on hover
        };
      })
    );

    // Timeline options
    const options = {
      height: '100%',
      margin: {
        item: 20
      },
      orientation: 'top' as const,
      zoomMin: 1000 * 60 * 60 * 24 * 7, // 1 week
      zoomMax: 1000 * 60 * 60 * 24 * 365 * 10, // 10 years
      moveable: true,
      zoomable: true,
      showCurrentTime: true,
      tooltip: {
        followMouse: true,
        overflowMethod: 'cap' as const
      }
    };

    // Create timeline
    const timeline = new Timeline(
      containerRef.current,
      timelineItems,
      options
    );

    timelineRef.current = timeline;

    // Fit all items in view
    timeline.fit();
    }, 100); // 100ms delay for modal to render

    // Cleanup
    return () => {
      clearTimeout(timer);
      if (timelineRef.current) {
        timelineRef.current.destroy();
        timelineRef.current = null;
      }
    };
  }, [items, opened]);

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      size="95%"
      title={
        <Group>
          <Text
            size="xl"
            fw={700}
            style={{
              fontFamily: 'Playfair Display, Georgia, serif',
              background: 'linear-gradient(135deg, var(--sienna), var(--amber-dark))',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}
          >
            Knowledge Evolution Timeline
          </Text>
          <Badge
            color="orange"
            size="lg"
            variant="filled"
            c="dark.9"
            fw={600}
            style={{
              WebkitTextFillColor: 'rgb(20, 20, 20)',
              color: 'rgb(20, 20, 20)'
            }}
          >
            {items.length} events
          </Badge>
        </Group>
      }
      styles={{
        content: {
          background: 'var(--charcoal)',
          border: '2px solid var(--sienna)'
        },
        header: {
          background: 'var(--charcoal-light)',
          borderBottom: '2px solid var(--sienna)'
        },
        title: {
          width: '100%'
        },
        body: {
          padding: 0,
          height: 'calc(90vh - 80px)'
        }
      }}
    >
      <Stack gap={0} style={{ height: '100%' }}>
        {/* Timeline Container */}
        <Box
          ref={containerRef}
          style={{
            width: '100%',
            height: '100%',
            background: 'var(--charcoal-light)',
            border: '1px solid var(--warm-gray)'
          }}
        />

        {/* Legend */}
        <Box
          style={{
            position: 'absolute',
            bottom: 16,
            right: 16,
            background: 'rgba(26, 23, 20, 0.9)',
            border: '1px solid var(--sienna)',
            borderRadius: 8,
            padding: 12
          }}
        >
          <Stack gap="xs">
            <Text size="xs" fw={600} c="cream">Legend</Text>
            <Group gap="xs">
              <Box
                style={{
                  width: 40,
                  height: 12,
                  background: '#14b8a6',
                  borderRadius: 4
                }}
              />
              <Text size="xs" c="cream-dim">Current (active)</Text>
            </Group>
            <Group gap="xs">
              <Box
                style={{
                  width: 40,
                  height: 12,
                  background: '#a8a29e',
                  borderRadius: 4
                }}
              />
              <Text size="xs" c="cream-dim">Superseded (past)</Text>
            </Group>
            <Text size="xs" c="warm-gray" mt="xs">
              Drag to pan timeline<br />
              Scroll to zoom<br />
              Hover for full details
            </Text>
          </Stack>
        </Box>

        {/* Custom CSS for timeline items */}
        <style>{`
          .vis-item.timeline-current {
            background-color: #14b8a6;
            border-color: #0f766e;
            color: #fafaf9;
          }

          .vis-item.timeline-superseded {
            background-color: #a8a29e;
            border-color: #78716c;
            color: #1a1714;
          }

          .vis-item .vis-item-content {
            padding: 8px;
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 12px;
          }

          .vis-time-axis .vis-text {
            color: #fafaf9;
          }

          .vis-panel.vis-background {
            background: #2a2520;
          }

          .vis-panel.vis-center,
          .vis-panel.vis-left,
          .vis-panel.vis-right {
            border-color: #78716c;
          }

          .vis-current-time {
            background-color: #f59e0b;
            width: 2px;
          }
        `}</style>
      </Stack>
    </Modal>
  );
}
