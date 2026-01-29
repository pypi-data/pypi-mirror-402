/**
 * ChatInput - User message input with file/folder picker support
 *
 * Files attached here are read client-side and their preview is sent to the agent
 * so it can suggest intelligent ingestion parameters (collection, topic, etc.)
 */

import { useState, useCallback } from 'react';
import { Textarea, ActionIcon, Group, Box, Badge, CloseButton, Text, Paper } from '@mantine/core';
import { IconSend, IconPaperclip, IconFolder, IconFile, IconFolderFilled } from '@tabler/icons-react';
import { useRagStore } from '../store';

// Preview limit per file (characters)
const PREVIEW_CHAR_LIMIT = 3000;

// File size formatting
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// Attached file with preview content
interface AttachedFile {
  name: string;
  size: number;
  type: string;
  preview: string;
  fullContent: string;
  isTruncated: boolean;
  relativePath?: string; // For folder uploads
}

export default function ChatInput() {
  const { inputValue, setInputValue, sendMessage, isStreaming } = useRagStore();
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [isReadingFiles, setIsReadingFiles] = useState(false);

  // Read file contents using FileReader
  const readFileContent = useCallback((file: File, relativePath?: string): Promise<AttachedFile> => {
    return new Promise((resolve) => {
      const reader = new FileReader();

      reader.onload = (e) => {
        const content = e.target?.result as string || '';
        const isTruncated = content.length > PREVIEW_CHAR_LIMIT;
        const preview = isTruncated ? content.slice(0, PREVIEW_CHAR_LIMIT) + '\n... [truncated]' : content;

        resolve({
          name: file.name,
          size: file.size,
          type: file.type || 'text/plain',
          preview,
          fullContent: content,
          isTruncated,
          relativePath,
        });
      };

      reader.onerror = () => {
        resolve({
          name: file.name,
          size: file.size,
          type: file.type || 'unknown',
          preview: '[Unable to read file content]',
          fullContent: '',
          isTruncated: false,
          relativePath,
        });
      };

      // Read as text - works for most text-based files
      reader.readAsText(file);
    });
  }, []);

  const handleSend = async () => {
    if ((!inputValue.trim() && attachedFiles.length === 0) || isStreaming) return;

    // Build message with file previews
    let messageContent = inputValue.trim();

    if (attachedFiles.length > 0) {
      const fileSection = attachedFiles.map((f) => {
        const path = f.relativePath ? `${f.relativePath}` : f.name;
        return `### File: ${path} (${formatFileSize(f.size)})${f.isTruncated ? ' [preview]' : ''}
\`\`\`
${f.preview}
\`\`\``;
      }).join('\n\n');

      if (messageContent) {
        messageContent = `${messageContent}\n\n---\n**Attached Files (${attachedFiles.length}):**\n\n${fileSection}`;
      } else {
        messageContent = `**Attached Files (${attachedFiles.length}):**\n\n${fileSection}\n\nPlease help me ingest these files.`;
      }
    }

    await sendMessage(messageContent);
    setInputValue('');
    setAttachedFiles([]);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileClick = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    // Accept common text-based files
    input.accept = '.txt,.md,.json,.yaml,.yml,.xml,.html,.css,.js,.ts,.jsx,.tsx,.py,.rb,.go,.rs,.java,.c,.cpp,.h,.hpp,.sh,.bash,.sql,.csv,.log,.ini,.cfg,.conf,.env.example,.gitignore,.dockerfile,Dockerfile,.toml,.lock';

    input.onchange = async (e: any) => {
      const files = Array.from(e.target.files) as File[];
      if (files.length > 0) {
        setIsReadingFiles(true);
        try {
          const readFiles = await Promise.all(files.map((f) => readFileContent(f)));
          setAttachedFiles((prev) => [...prev, ...readFiles]);
        } finally {
          setIsReadingFiles(false);
        }
      }
    };
    input.click();
  };

  const handleFolderClick = () => {
    const input = document.createElement('input');
    input.type = 'file';
    // @ts-ignore - webkitdirectory is not in types
    input.webkitdirectory = true;

    input.onchange = async (e: any) => {
      const files = Array.from(e.target.files) as File[];
      if (files.length > 0) {
        setIsReadingFiles(true);
        try {
          // Filter to text-based files and limit count
          const textExtensions = ['.txt', '.md', '.json', '.yaml', '.yml', '.xml', '.html', '.css', '.js', '.ts', '.jsx', '.tsx', '.py', '.rb', '.go', '.rs', '.java', '.c', '.cpp', '.h', '.hpp', '.sh', '.sql', '.csv', '.log', '.ini', '.cfg', '.conf', '.toml'];
          const textFiles = files.filter((f) => {
            const ext = '.' + f.name.split('.').pop()?.toLowerCase();
            return textExtensions.includes(ext);
          }).slice(0, 20); // Limit to 20 files

          const readFiles = await Promise.all(
            textFiles.map((f) => readFileContent(f, f.webkitRelativePath))
          );
          setAttachedFiles((prev) => [...prev, ...readFiles]);

          // Warn if files were skipped
          if (files.length > textFiles.length) {
            const skipped = files.length - textFiles.length;
            console.log(`Skipped ${skipped} non-text files from folder upload`);
          }
        } finally {
          setIsReadingFiles(false);
        }
      }
    };
    input.click();
  };

  const removeFile = (index: number) => {
    setAttachedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const clearAllFiles = () => {
    setAttachedFiles([]);
  };

  return (
    <Box mt="md">
      {/* Attached files display */}
      {attachedFiles.length > 0 && (
        <Paper
          p="xs"
          mb="xs"
          withBorder
          style={{
            backgroundColor: 'var(--mantine-color-dark-7)',
            borderColor: 'var(--mantine-color-dark-5)',
          }}
        >
          <Group justify="space-between" mb="xs">
            <Text size="xs" c="dimmed">
              {attachedFiles.length} file{attachedFiles.length > 1 ? 's' : ''} attached
              {attachedFiles.some(f => f.relativePath) && ' (from folder)'}
            </Text>
            <CloseButton size="xs" onClick={clearAllFiles} title="Remove all" />
          </Group>
          <Group gap="xs" wrap="wrap">
            {attachedFiles.map((file, index) => (
              <Badge
                key={`${file.name}-${index}`}
                variant="light"
                color="gray"
                size="lg"
                leftSection={file.relativePath ? <IconFolderFilled size={14} /> : <IconFile size={14} />}
                rightSection={
                  <CloseButton
                    size="xs"
                    onClick={() => removeFile(index)}
                    style={{ marginLeft: 4 }}
                  />
                }
                style={{ paddingRight: 4 }}
              >
                {file.relativePath ? file.relativePath.split('/').slice(-1)[0] : file.name}
                <Text span size="xs" c="dimmed" ml={4}>
                  ({formatFileSize(file.size)})
                </Text>
              </Badge>
            ))}
          </Group>
        </Paper>
      )}

      <Group align="flex-end" gap="xs">
        <Textarea
          placeholder={attachedFiles.length > 0
            ? "Add a message or just send to have the agent analyze these files..."
            : "Ask me anything about your knowledge base..."
          }
          value={inputValue}
          onChange={(e) => setInputValue(e.currentTarget.value)}
          onKeyDown={handleKeyPress}
          minRows={2}
          maxRows={6}
          autosize
          disabled={isStreaming || isReadingFiles}
          style={{ flex: 1 }}
        />

        <Group gap="xs">
          <ActionIcon
            variant="light"
            color="gray"
            size="lg"
            onClick={handleFileClick}
            disabled={isStreaming || isReadingFiles}
            loading={isReadingFiles}
            title="Attach files"
          >
            <IconPaperclip size={20} />
          </ActionIcon>

          <ActionIcon
            variant="light"
            color="gray"
            size="lg"
            onClick={handleFolderClick}
            disabled={isStreaming || isReadingFiles}
            title="Attach folder"
          >
            <IconFolder size={20} />
          </ActionIcon>

          <ActionIcon
            variant="filled"
            color="blue"
            size="lg"
            onClick={handleSend}
            disabled={(!inputValue.trim() && attachedFiles.length === 0) || isStreaming || isReadingFiles}
            loading={isStreaming}
          >
            <IconSend size={20} />
          </ActionIcon>
        </Group>
      </Group>
    </Box>
  );
}
