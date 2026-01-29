/**
 * StarterPrompts - Initial prompt suggestions (shows when messages.length === 0)
 *
 * Behavior:
 * - No placeholder: Immediate send (e.g., "What collections do I have?")
 * - Has placeholder: Fill input, user edits (e.g., "Search my knowledge base for [topic]")
 */

import { useEffect, useState } from 'react';
import { Stack, Card, Text, Title, Badge, Group, Loader, Box } from '@mantine/core';
import { IconSparkles } from '@tabler/icons-react';
import { useRagStore } from '../store';
import { getStarterPrompts } from '../ragApi';
import type { StarterPrompt } from '../types';

export default function StarterPrompts() {
  const [prompts, setPrompts] = useState<StarterPrompt[]>([]);
  const [loading, setLoading] = useState(true);
  const { sendMessage, setInputValue } = useRagStore();

  useEffect(() => {
    loadPrompts();
  }, []);

  const loadPrompts = async () => {
    try {
      const data = await getStarterPrompts();
      setPrompts(data);
    } catch (error) {
      console.error('Failed to load starter prompts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePromptClick = (prompt: StarterPrompt) => {
    if (prompt.has_placeholder) {
      // Fill input for user to edit - don't send yet
      setInputValue(prompt.prompt_text);
    } else {
      // Immediate send for prompts without placeholders
      sendMessage(prompt.prompt_text);
    }
  };

  if (loading) {
    return (
      <Box style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <Loader size="lg" />
      </Box>
    );
  }

  return (
    <Stack gap="md" p="md" style={{ flex: 1, justifyContent: 'center' }}>
      <Box ta="center" mb="xl">
        <IconSparkles size={48} style={{ margin: '0 auto', marginBottom: 16 }} />
        <Title order={2}>Welcome to RAG Memory</Title>
        <Text c="dimmed" mt="xs">
          Start by exploring your knowledge base or asking a question
        </Text>
      </Box>

      <Stack gap="sm">
        {prompts.map((prompt) => (
          <Card
            key={prompt.id}
            shadow="sm"
            padding="md"
            radius="md"
            withBorder
            style={{ cursor: 'pointer' }}
            onClick={() => handlePromptClick(prompt)}
            className="starter-prompt-card"
          >
            <Group justify="space-between" mb="xs">
              <Text fw={500}>{prompt.prompt_text}</Text>
              {prompt.category && (
                <Badge variant="light" size="sm">
                  {prompt.category}
                </Badge>
              )}
            </Group>

            {prompt.has_placeholder && (
              <Text size="xs" c="dimmed">
                Click to use this prompt template
              </Text>
            )}
          </Card>
        ))}
      </Stack>

      <style>
        {`
          .starter-prompt-card:hover {
            background-color: var(--mantine-color-dark-5);
            transform: translateY(-2px);
            transition: all 0.2s ease;
          }
        `}
      </style>
    </Stack>
  );
}
