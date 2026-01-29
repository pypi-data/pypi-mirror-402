/**
 * GraphVisualization - Network diagram for knowledge graph relationships
 *
 * Displays nodes (entities) and edges (relationships) as interactive network graph
 * Uses vis-network for rendering
 */

import { useEffect, useRef } from 'react';
import { Network, DataSet } from 'vis-network/standalone';
import { Box, Modal, Text, Stack, Badge, Group } from '@mantine/core';

interface Relationship {
  id: string;
  relationship_type: string;
  fact: string;
  source_node_id: string;
  target_node_id: string;
  source_node_name?: string;  // Entity name for source
  target_node_name?: string;  // Entity name for target
  valid_from?: string;
  valid_until?: string;
}

interface Props {
  relationships: Relationship[];
  opened: boolean;
  onClose: () => void;
}

export function GraphVisualization({ relationships, opened, onClose }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);

  useEffect(() => {
    if (!opened || relationships.length === 0) {
      console.log('GraphVisualization: Not rendering', { opened, hasContainer: !!containerRef.current, relationshipCount: relationships.length });
      return;
    }

    // Wait for container to be available (modal animation)
    const timer = setTimeout(() => {
      if (!containerRef.current) {
        console.error('GraphVisualization: Container ref still null after delay');
        return;
      }

      console.log('GraphVisualization: Rendering graph with relationships:', relationships);

    // Extract unique nodes from relationships with their names
    const nodeMap = new Map<string, string>();
    relationships.forEach(rel => {
      // Use entity name if available, otherwise use truncated UUID
      if (rel.source_node_id) {
        const name = rel.source_node_name || rel.source_node_id.substring(0, 20);
        nodeMap.set(rel.source_node_id, name);
      }
      if (rel.target_node_id) {
        const name = rel.target_node_name || rel.target_node_id.substring(0, 20);
        nodeMap.set(rel.target_node_id, name);
      }
    });

    console.log('GraphVisualization: Unique nodes:', Array.from(nodeMap.entries()));

    // Create nodes dataset with entity names
    const nodes = new DataSet(
      Array.from(nodeMap.entries()).map(([id, name]) => ({
        id,
        label: name, // Use entity name instead of UUID
        shape: 'dot',
        size: 20,
        color: {
          background: '#14b8a6', // teal
          border: '#0f766e',     // teal-dark
          highlight: {
            background: '#f59e0b', // amber
            border: '#d97706'
          }
        },
        font: {
          color: '#fafaf9',      // cream
          size: 14
        }
      }))
    );

    // Create edges dataset
    const edges = new DataSet(
      relationships.map(rel => ({
        id: rel.id,
        from: rel.source_node_id,
        to: rel.target_node_id,
        label: rel.relationship_type,
        arrows: 'to',
        color: {
          color: '#f59e0b',      // amber
          highlight: '#fbbf24'   // amber-light
        },
        font: {
          color: '#fafaf9',
          size: 12,
          strokeWidth: 0
        },
        title: rel.fact,         // Tooltip
        smooth: {
          enabled: true,
          type: 'curvedCW',
          roundness: 0.2
        }
      }))
    );

    // Network options
    const options = {
      nodes: {
        font: {
          color: '#fafaf9'
        }
      },
      edges: {
        font: {
          align: 'middle'
        }
      },
      physics: {
        enabled: true,
        stabilization: {
          iterations: 200
        },
        barnesHut: {
          gravitationalConstant: -8000,
          springLength: 150,
          springConstant: 0.04
        }
      },
      interaction: {
        hover: true,
        tooltipDelay: 200,
        zoomView: true,
        dragView: true
      },
      layout: {
        improvedLayout: true,
        hierarchical: {
          enabled: false
        }
      }
    };

    console.log('GraphVisualization: Creating network with', nodes.length, 'nodes and', edges.length, 'edges');
    console.log('GraphVisualization: Container dimensions:', containerRef.current.offsetWidth, 'x', containerRef.current.offsetHeight);

    // Create network
    try {
      const network = new Network(
        containerRef.current,
        { nodes, edges },
        options
      );

      networkRef.current = network;
      console.log('GraphVisualization: Network created successfully');
    } catch (error) {
      console.error('GraphVisualization: Failed to create network:', error);
    }
    }, 100); // 100ms delay for modal to render

    // Cleanup
    return () => {
      clearTimeout(timer);
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [relationships, opened]);

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
              background: 'linear-gradient(135deg, var(--teal-light), var(--teal))',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}
          >
            Knowledge Graph Visualization
          </Text>
          <Badge
            color="teal"
            size="lg"
            variant="filled"
            c="dark.9"
            fw={600}
            style={{
              WebkitTextFillColor: 'rgb(20, 20, 20)',
              color: 'rgb(20, 20, 20)'
            }}
          >
            {relationships.length} relationships
          </Badge>
        </Group>
      }
      styles={{
        content: {
          background: 'var(--charcoal)',
          border: '2px solid var(--teal)'
        },
        header: {
          background: 'var(--charcoal-light)',
          borderBottom: '2px solid var(--teal)'
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
        {/* Graph Container */}
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
            border: '1px solid var(--teal)',
            borderRadius: 8,
            padding: 12
          }}
        >
          <Stack gap="xs">
            <Text size="xs" fw={600} c="cream">Legend</Text>
            <Group gap="xs">
              <Box
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  background: '#14b8a6'
                }}
              />
              <Text size="xs" c="cream-dim">Entity</Text>
            </Group>
            <Group gap="xs">
              <Box
                style={{
                  width: 20,
                  height: 2,
                  background: '#f59e0b'
                }}
              />
              <Text size="xs" c="cream-dim">Relationship</Text>
            </Group>
            <Text size="xs" c="warm-gray" mt="xs">
              Hover over edges for details<br />
              Drag nodes to rearrange<br />
              Scroll to zoom
            </Text>
          </Stack>
        </Box>
      </Stack>
    </Modal>
  );
}
