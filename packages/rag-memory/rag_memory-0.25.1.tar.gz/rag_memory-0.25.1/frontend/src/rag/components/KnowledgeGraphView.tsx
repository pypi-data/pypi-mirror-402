/**
 * KnowledgeGraphView - Display knowledge graph relationships and temporal timeline
 */

import { Stack, Card, Text, Group, Badge, Table, Timeline } from '@mantine/core';
import {
  IconGraph,
  IconClock,
  IconArrowRight,
  IconCircle,
  IconCircleCheck,
} from '@tabler/icons-react';

interface Relationship {
  id: string;
  relationship_type: string;
  fact: string;
  source_node_id: string;
  target_node_id: string;
  valid_from?: string;
  valid_until?: string;
}

interface TemporalItem {
  fact: string;
  relationship_type: string;
  valid_from: string;
  valid_until: string | null;
  status: 'current' | 'superseded';
  created_at: string;
  expired_at: string | null;
}

interface KnowledgeGraphViewProps {
  relationships?: Relationship[];
  timeline?: TemporalItem[];
}

export default function KnowledgeGraphView({
  relationships,
  timeline,
}: KnowledgeGraphViewProps) {
  // Show relationships view
  if (relationships && relationships.length > 0) {
    return (
      <Card shadow="sm" p="md" radius="md" withBorder mt="md">
        <Stack gap="md">
          <Group gap="xs">
            <IconGraph size={18} />
            <Text fw={500} size="sm">
              Knowledge Graph Relationships ({relationships.length})
            </Text>
          </Group>

          <Table striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Relationship</Table.Th>
                <Table.Th>Type</Table.Th>
                <Table.Th>Valid</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {relationships.map((rel, index) => (
                <Table.Tr key={index}>
                  <Table.Td>
                    <Stack gap="xs">
                      <Group gap="xs">
                        <Text size="xs" fw={500}>
                          {rel.source_node_id}
                        </Text>
                        <IconArrowRight size={14} />
                        <Text size="xs" fw={500}>
                          {rel.target_node_id}
                        </Text>
                      </Group>
                      <Text size="xs" c="dimmed">
                        {rel.fact}
                      </Text>
                    </Stack>
                  </Table.Td>
                  <Table.Td>
                    <Badge variant="light" size="sm">
                      {rel.relationship_type}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Text size="xs" c="dimmed">
                      {rel.valid_from && new Date(rel.valid_from).toLocaleDateString()}
                      {rel.valid_until && ` - ${new Date(rel.valid_until).toLocaleDateString()}`}
                    </Text>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Stack>
      </Card>
    );
  }

  // Show temporal timeline view
  if (timeline && timeline.length > 0) {
    return (
      <Card shadow="sm" p="md" radius="md" withBorder mt="md">
        <Stack gap="md">
          <Group gap="xs">
            <IconClock size={18} />
            <Text fw={500} size="sm">
              Knowledge Evolution Timeline ({timeline.length} events)
            </Text>
          </Group>

          <Timeline active={timeline.length} bulletSize={24} lineWidth={2}>
            {timeline.map((item, index) => (
              <Timeline.Item
                key={index}
                bullet={
                  item.status === 'current' ? (
                    <IconCircleCheck size={16} />
                  ) : (
                    <IconCircle size={16} />
                  )
                }
                title={
                  <Group gap="xs">
                    <Badge
                      variant="light"
                      size="sm"
                      color={item.status === 'current' ? 'blue' : 'gray'}
                    >
                      {item.status}
                    </Badge>
                    <Badge variant="light" size="sm">
                      {item.relationship_type}
                    </Badge>
                  </Group>
                }
              >
                <Text size="sm" mt="xs">
                  {item.fact}
                </Text>
                <Text size="xs" c="dimmed" mt="xs">
                  Valid: {new Date(item.valid_from).toLocaleDateString()}
                  {item.valid_until && ` - ${new Date(item.valid_until).toLocaleDateString()}`}
                </Text>
                <Text size="xs" c="dimmed">
                  Created: {new Date(item.created_at).toLocaleDateString()}
                  {item.expired_at && ` | Expired: ${new Date(item.expired_at).toLocaleDateString()}`}
                </Text>
              </Timeline.Item>
            ))}
          </Timeline>
        </Stack>
      </Card>
    );
  }

  return null;
}
