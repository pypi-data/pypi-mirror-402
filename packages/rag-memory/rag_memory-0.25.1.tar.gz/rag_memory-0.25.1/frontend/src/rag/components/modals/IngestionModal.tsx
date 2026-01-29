/**
 * IngestionModal - Modal for ingesting content via text, URL, or file upload
 *
 * Features:
 * - Three tabs: Text | URL | File
 * - Each tab has collection selector and action button
 * - Progress tracking
 * - Error handling
 */

import { useState, useRef, useEffect } from 'react';
import {
  Modal,
  Tabs,
  Textarea,
  TextInput,
  Select,
  Button,
  Stack,
  Group,
  Checkbox,
  FileInput,
  Text,
  Loader,
  Alert,
  Paper,
  Divider,
  NumberInput,
  Radio,
  SegmentedControl,
  Progress,
  ScrollArea,
} from '@mantine/core';
import { IconUpload, IconWorld, IconFolder, IconAlertCircle, IconAlertTriangle, IconCheck, IconX, IconFile } from '@tabler/icons-react';
import { useRagStore } from '../../store';
import { PageRelevanceDisplay } from './PageRelevanceDisplay';

interface IngestionModalProps {
  opened: boolean;
  onClose: () => void;
  defaultCollection?: string;
  // Agent-provided defaults
  defaultTab?: 'text' | 'url' | 'file' | 'directory';
  defaultTopic?: string;
  defaultMode?: 'ingest' | 'reingest';
  defaultReviewedByHuman?: boolean;
}

export function IngestionModal({
  opened,
  onClose,
  defaultCollection,
  defaultTab = 'text',
  defaultTopic = '',
  defaultMode = 'ingest',
  defaultReviewedByHuman = false,
}: IngestionModalProps) {
  const { collections, loadCollections } = useRagStore();

  // Map 'directory' tab to 'file' tab with folder upload mode
  const initialTab = defaultTab === 'directory' ? 'file' : defaultTab;
  const initialUploadMode = defaultTab === 'directory' ? 'folder' : 'file';

  const [activeTab, setActiveTab] = useState<string>(initialTab);

  // Text ingestion
  const [textContent, setTextContent] = useState('');
  const [textCollection, setTextCollection] = useState(defaultCollection || '');
  const [textTitle, setTextTitle] = useState('');
  const [textMode, setTextMode] = useState<'ingest' | 'reingest'>(defaultMode);
  const [textTopic, setTextTopic] = useState(defaultTopic);
  const [textReviewedByHuman, setTextReviewedByHuman] = useState(defaultReviewedByHuman);
  const [textMetadata, setTextMetadata] = useState(''); // Optional JSON metadata

  // URL ingestion
  const [url, setUrl] = useState('');
  const [followLinks, setFollowLinks] = useState(false);
  const [urlCollection, setUrlCollection] = useState(defaultCollection || '');
  const [previewMode, setPreviewMode] = useState(true); // Default to preview ON
  const [urlPreviewData, setUrlPreviewData] = useState<any>(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [urlMode, setUrlMode] = useState<'ingest' | 'reingest'>(defaultMode);
  const [maxPages, setMaxPages] = useState(10);
  const [urlTopic, setUrlTopic] = useState(defaultTopic);
  const [urlReviewedByHuman, setUrlReviewedByHuman] = useState(defaultReviewedByHuman);
  const [urlMetadata, setUrlMetadata] = useState(''); // Optional JSON metadata

  // File ingestion
  const [file, setFile] = useState<File | null>(null);
  const [fileCollection, setFileCollection] = useState(defaultCollection || '');
  const [fileMode, setFileMode] = useState<'ingest' | 'reingest'>(defaultMode);
  const [fileTopic, setFileTopic] = useState(defaultTopic);
  const [fileReviewedByHuman, setFileReviewedByHuman] = useState(defaultReviewedByHuman);
  const [fileMetadata, setFileMetadata] = useState(''); // Optional JSON metadata

  // Folder ingestion
  const [uploadMode, setUploadMode] = useState<'file' | 'folder'>(initialUploadMode);
  const [folderFiles, setFolderFiles] = useState<File[]>([]);
  const [skippedFiles, setSkippedFiles] = useState<Array<{ name: string; reason: string }>>([]);
  const [folderName, setFolderName] = useState('');
  const folderInputRef = useRef<HTMLInputElement>(null);
  const [folderProgress, setFolderProgress] = useState<{
    current: number;
    total: number;
    currentFile: string;
    results: Array<{
      filename: string;
      status: 'pending' | 'processing' | 'success' | 'error';
      chunks?: number;
      error?: string;
    }>;
  } | null>(null);

  // Status
  const [isIngesting, setIsIngesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Update state when modal opens with new defaults (from agent)
  useEffect(() => {
    if (opened) {
      // Update tab and upload mode
      const newTab = defaultTab === 'directory' ? 'file' : defaultTab;
      const newUploadMode = defaultTab === 'directory' ? 'folder' : 'file';
      setActiveTab(newTab);
      setUploadMode(newUploadMode);

      // Update collection for all tabs
      if (defaultCollection) {
        setTextCollection(defaultCollection);
        setUrlCollection(defaultCollection);
        setFileCollection(defaultCollection);
      }

      // Update topic for all tabs
      setTextTopic(defaultTopic);
      setUrlTopic(defaultTopic);
      setFileTopic(defaultTopic);

      // Update mode for all tabs
      setTextMode(defaultMode);
      setUrlMode(defaultMode);
      setFileMode(defaultMode);

      // Update reviewed_by_human for all tabs
      setTextReviewedByHuman(defaultReviewedByHuman);
      setUrlReviewedByHuman(defaultReviewedByHuman);
      setFileReviewedByHuman(defaultReviewedByHuman);

      // Load collections
      loadCollections();
    }
  }, [opened, defaultTab, defaultCollection, defaultTopic, defaultMode, defaultReviewedByHuman, loadCollections]);

  // Topic warning confirmation
  const [showTopicWarning, setShowTopicWarning] = useState(false);
  const [pendingIngestAction, setPendingIngestAction] = useState<(() => Promise<void>) | null>(null);

  // Helper: Check topic and either proceed or show warning
  const handleIngestWithTopicCheck = (topic: string, ingestFn: () => Promise<void>) => {
    if (!topic.trim()) {
      // No topic provided - show warning dialog
      setPendingIngestAction(() => ingestFn);
      setShowTopicWarning(true);
    } else {
      // Topic provided - proceed directly
      ingestFn();
    }
  };

  // Proceed with ingest after user confirms (dismisses warning)
  const handleConfirmIngestWithoutTopic = () => {
    setShowTopicWarning(false);
    if (pendingIngestAction) {
      pendingIngestAction();
      setPendingIngestAction(null);
    }
  };

  // Cancel ingest and close warning
  const handleCancelIngestWarning = () => {
    setShowTopicWarning(false);
    setPendingIngestAction(null);
  };

  const collectionOptions = collections.map(c => ({ label: c.name, value: c.name }));

  // Blocked file extensions (must match BLOCKED_EXTENSIONS in src/mcp/tools.py)
  // Blocklist approach: block known binary types, allow everything else (text-based)
  const BLOCKED_EXTENSIONS: Record<string, string> = {
    // Images
    '.jpg': 'image file', '.jpeg': 'image file', '.png': 'image file', '.gif': 'image file',
    '.bmp': 'image file', '.svg': 'image file', '.ico': 'image file', '.webp': 'image file',
    '.tiff': 'image file', '.tif': 'image file',
    // Videos
    '.mp4': 'video file', '.mov': 'video file', '.avi': 'video file', '.mkv': 'video file',
    '.wmv': 'video file', '.flv': 'video file', '.webm': 'video file',
    // Audio
    '.mp3': 'audio file', '.wav': 'audio file', '.flac': 'audio file', '.aac': 'audio file',
    '.ogg': 'audio file', '.wma': 'audio file', '.m4a': 'audio file',
    // Archives
    '.zip': 'archive file', '.tar': 'archive file', '.gz': 'archive file', '.rar': 'archive file',
    '.7z': 'archive file', '.bz2': 'archive file', '.xz': 'archive file',
    // Binary/Executables
    '.exe': 'binary file', '.dll': 'binary file', '.so': 'binary file', '.dylib': 'binary file',
    '.bin': 'binary file', '.app': 'binary file', '.msi': 'binary file',
    // Office docs (ZIP-based or binary)
    '.docx': 'Office doc (use PDF)', '.xlsx': 'Office doc (use PDF)', '.pptx': 'Office doc (use PDF)',
    '.doc': 'Office doc (use PDF)', '.xls': 'Office doc (use PDF)', '.ppt': 'Office doc (use PDF)',
    '.odt': 'Office doc (use PDF)', '.ods': 'Office doc (use PDF)', '.odp': 'Office doc (use PDF)',
    // Compiled/bytecode
    '.pyc': 'binary file', '.pyo': 'binary file', '.class': 'binary file',
    '.o': 'binary file', '.obj': 'binary file', '.wasm': 'binary file',
    // Database files
    '.db': 'database file', '.sqlite': 'database file', '.sqlite3': 'database file', '.mdb': 'database file',
    // Other binary
    '.iso': 'binary file', '.dmg': 'binary file', '.pkg': 'binary file', '.deb': 'binary file', '.rpm': 'binary file',
  };

  // Human-readable hint for UI (matches SUPPORTED_FILES_DESCRIPTION in tools.py)
  const SUPPORTED_TYPES_HINT = 'Supports text files, code, and PDFs up to 10 MB';
  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

  // Parse metadata JSON string - returns parsed object or null if empty/invalid
  const parseMetadata = (metadataStr: string): Record<string, any> | null => {
    const trimmed = metadataStr.trim();
    if (!trimmed) return null;
    try {
      const parsed = JSON.parse(trimmed);
      if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
        return null; // Must be a plain object
      }
      return parsed;
    } catch {
      return null;
    }
  };

  // Validate metadata JSON string - returns error message or null if valid
  const validateMetadata = (metadataStr: string): string | null => {
    const trimmed = metadataStr.trim();
    if (!trimmed) return null; // Empty is valid (optional field)
    try {
      const parsed = JSON.parse(trimmed);
      if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
        return 'Must be a JSON object (e.g., {"key": "value"})';
      }
      return null;
    } catch {
      return 'Invalid JSON format';
    }
  };

  // Validate a single file - returns { valid: boolean, reason?: string }
  const validateFile = (file: File): { valid: boolean; reason?: string } => {
    const ext = '.' + (file.name.split('.').pop()?.toLowerCase() || '');

    // Check blocked extensions
    if (BLOCKED_EXTENSIONS[ext]) {
      return { valid: false, reason: BLOCKED_EXTENSIONS[ext] };
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return { valid: false, reason: `exceeds 10 MB (${(file.size / (1024 * 1024)).toFixed(1)} MB)` };
    }

    // Check empty file
    if (file.size === 0) {
      return { valid: false, reason: 'empty file' };
    }

    return { valid: true };
  };

  // Handle folder selection
  const handleFolderSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    // Get folder name from first file's path
    const firstPath = files[0].webkitRelativePath;
    const selectedFolderName = firstPath.split('/')[0];
    setFolderName(selectedFolderName);

    // Categorize files using shared validation logic
    const supported: File[] = [];
    const skipped: Array<{ name: string; reason: string }> = [];

    files.forEach(file => {
      const validation = validateFile(file);

      if (validation.valid) {
        supported.push(file);
      } else {
        skipped.push({ name: file.name, reason: validation.reason || 'unsupported' });
      }
    });

    setFolderFiles(supported);
    setSkippedFiles(skipped);

    // Initialize progress tracking
    if (supported.length > 0) {
      setFolderProgress({
        current: 0,
        total: supported.length,
        currentFile: '',
        results: supported.map(f => ({
          filename: f.name,
          status: 'pending'
        }))
      });
    } else {
      setFolderProgress(null);
    }

    // Reset input so same folder can be re-selected
    e.target.value = '';
  };

  // Handle folder upload (sequential processing)
  const handleIngestFolder = async () => {
    if (folderFiles.length === 0 || !fileCollection) return;

    setIsIngesting(true);
    setError(null);
    setSuccess(null);

    const mcpServerUrl = import.meta.env.VITE_MCP_SERVER_URL;
    if (!mcpServerUrl) {
      setError('MCP server URL not configured. Set VITE_MCP_SERVER_URL in your environment.');
      setIsIngesting(false);
      return;
    }

    let successCount = 0;
    let failCount = 0;
    let totalChunks = 0;

    // Process files sequentially
    for (let i = 0; i < folderFiles.length; i++) {
      const file = folderFiles[i];

      // Update progress: mark current file as processing
      setFolderProgress(prev => prev ? {
        ...prev,
        current: i + 1,
        currentFile: file.name,
        results: prev.results.map((r, idx) =>
          idx === i ? { ...r, status: 'processing' as const } : r
        )
      } : null);

      try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('collection_name', fileCollection);
        formData.append('mode', fileMode);
        if (fileTopic) {
          formData.append('topic', fileTopic);  // Optional topic for relevance scoring
        }
        formData.append('reviewed_by_human', fileReviewedByHuman.toString());
        const parsedFolderMetadata = parseMetadata(fileMetadata);
        if (parsedFolderMetadata) {
          formData.append('metadata', JSON.stringify(parsedFolderMetadata));
        }

        const response = await fetch(`${mcpServerUrl}/api/ingest/file`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.message || errorData.detail || 'Upload failed');
        }

        const data = await response.json();
        successCount++;
        totalChunks += data.num_chunks;

        // Update progress: mark as success
        setFolderProgress(prev => prev ? {
          ...prev,
          results: prev.results.map((r, idx) =>
            idx === i ? { ...r, status: 'success' as const, chunks: data.num_chunks } : r
          )
        } : null);

      } catch (err: any) {
        failCount++;

        // Update progress: mark as error
        setFolderProgress(prev => prev ? {
          ...prev,
          results: prev.results.map((r, idx) =>
            idx === i ? { ...r, status: 'error' as const, error: err.message } : r
          )
        } : null);
      }
    }

    // Final summary
    if (failCount === 0) {
      setSuccess(`Successfully ingested ${successCount} files! Created ${totalChunks} chunks.`);
    } else {
      setSuccess(`Ingested ${successCount} files (${failCount} failed). Created ${totalChunks} chunks.`);
    }

    await loadCollections();
    setIsIngesting(false);
  };

  // Reset file/folder form (preserves settings like topic, collection, mode)
  const handleResetFileForm = () => {
    // Only reset file selection and results - preserve settings for repeated uploads
    setFile(null);
    setFolderFiles([]);
    setSkippedFiles([]);
    setFolderName('');
    setFolderProgress(null);
    setSuccess(null);
    setError(null);
    // Keep: fileMode, fileTopic, fileCollection, fileReviewedByHuman, fileMetadata
  };

  // Helper: Check if ingestion is possible (only block on total HTTP failure)
  const canIngest = (data: any): boolean => {
    if (!data || !data.pages) return false;

    // Can ingest if at least one page doesn't have HTTP errors
    const allFailed = data.pages_failed === data.pages.length && data.pages.length > 0;
    return !allFailed;
  };

  const previewCanIngest = urlPreviewData ? canIngest(urlPreviewData) : true;

  const handleIngestText = async () => {
    if (!textContent.trim() || !textCollection) return;

    setIsIngesting(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('http://localhost:8000/api/rag-memory/ingest/text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: textContent,
          collection_name: textCollection,
          document_title: textTitle || undefined,
          mode: textMode,
          topic: textTopic || undefined,  // Optional topic for relevance scoring
          reviewed_by_human: textReviewedByHuman,
          metadata: parseMetadata(textMetadata) || undefined,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ingestion failed');
      }

      const data = await response.json();

      // Build success message with evaluation if available
      let successMsg = `Successfully ingested! Created ${data.num_chunks} chunks.`;
      if (data.evaluation) {
        const qualityPct = Math.round((data.evaluation.quality_score || 0) * 100);
        successMsg += ` Quality: ${qualityPct}%`;
        if (data.evaluation.topic_relevance_score !== undefined) {
          const relevancePct = Math.round(data.evaluation.topic_relevance_score * 100);
          successMsg += `, Relevance: ${relevancePct}%`;
        }
      }
      setSuccess(successMsg);
      // DON'T clear form - let user see what they just ingested
      // Form will be cleared when modal closes (handleClose)
      await loadCollections();
    } catch (err: any) {
      setError(err.message || 'Failed to ingest text');
    } finally {
      setIsIngesting(false);
    }
  };

  const handlePreviewUrl = async () => {
    if (!url.trim() || !urlCollection) return;

    setIsLoadingPreview(true);
    setError(null);
    setUrlPreviewData(null);

    try {
      const response = await fetch('http://localhost:8000/api/rag-memory/ingest/url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          collection_name: urlCollection,
          mode: urlMode, // Respect user's mode selection (ingest or reingest)
          follow_links: false, // Preview mode: single page only
          max_pages: 1,
          dry_run: true, // Preview mode
          topic: urlTopic || undefined,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'URL preview failed');
      }

      const data = await response.json();

      // Store full preview response (includes status)
      setUrlPreviewData(data);

      // Auto-uncheck preview after completion
      setPreviewMode(false);
    } catch (err: any) {
      // Validation failed - show error without clearing URL
      setError(err.message || 'Failed to preview URL');
      setUrlPreviewData(null);
    } finally {
      setIsLoadingPreview(false);
    }
  };

  const handleIngestUrl = async () => {
    if (!url.trim() || !urlCollection) return;

    // If preview mode is enabled and no preview data yet, do preview first
    if (previewMode && !urlPreviewData) {
      await handlePreviewUrl();
      return;
    }

    // If preview mode enabled and we have preview data, user wants to update preview
    if (previewMode && urlPreviewData) {
      await handlePreviewUrl();
      return;
    }

    // Proceed with actual ingestion
    setIsIngesting(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('http://localhost:8000/api/rag-memory/ingest/url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          collection_name: urlCollection,
          mode: urlMode,
          follow_links: followLinks,
          max_pages: followLinks ? maxPages : 1,
          dry_run: false, // Actual ingestion
          topic: urlTopic || undefined, // Optional topic for relevance scoring
          reviewed_by_human: urlReviewedByHuman,
          metadata: parseMetadata(urlMetadata) || undefined,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'URL ingestion failed');
      }

      const data = await response.json();

      // Check if ingestion actually worked (0 pages = failure)
      const pagesIngested = data.pages_ingested ?? 0;
      const totalChunks = data.total_chunks ?? 0;

      if (pagesIngested === 0) {
        // No pages ingested is a failure
        throw new Error('No content could be extracted from this URL. The page may be empty, blocked, or require JavaScript rendering.');
      }

      // Build success message with evaluation if available
      let successMsg = `Successfully ingested ${pagesIngested} page(s)! Created ${totalChunks} chunks.`;
      if (data.evaluation) {
        const qualityPct = Math.round((data.evaluation.quality_score || 0) * 100);
        successMsg += ` Quality: ${qualityPct}%`;
        if (data.evaluation.topic_relevance_score !== undefined) {
          const relevancePct = Math.round(data.evaluation.topic_relevance_score * 100);
          successMsg += `, Relevance: ${relevancePct}%`;
        }
      }
      setSuccess(successMsg);
      // DON'T clear form - success state will disable everything
      await loadCollections();
    } catch (err: any) {
      setError(err.message || 'Failed to ingest URL');
    } finally {
      setIsIngesting(false);
    }
  };

  // Reset URL form (preserves settings like topic, collection, mode)
  const handleResetUrlForm = () => {
    // Only reset URL and results - preserve settings for repeated ingestion
    setUrl('');
    setUrlPreviewData(null);
    setPreviewMode(true); // Re-enable preview for new URL
    setSuccess(null);
    setError(null);
    // Keep: urlMode, urlTopic, urlCollection, urlReviewedByHuman, urlMetadata, followLinks, maxPages
  };

  const handleIngestFile = async () => {
    if (!file || !fileCollection) return;

    setIsIngesting(true);
    setError(null);
    setSuccess(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('collection_name', fileCollection);
      formData.append('mode', fileMode);
      if (fileTopic) {
        formData.append('topic', fileTopic);  // Optional topic for relevance scoring
      }
      formData.append('reviewed_by_human', fileReviewedByHuman.toString());
      const parsedFileMetadata = parseMetadata(fileMetadata);
      if (parsedFileMetadata) {
        formData.append('metadata', JSON.stringify(parsedFileMetadata));
      }

      // File uploads go directly to MCP server (bypasses backend proxy)
      // Uses in-memory processing, no temp files needed
      // VITE_MCP_SERVER_URL MUST be configured - no hardcoded port default
      const mcpServerUrl = import.meta.env.VITE_MCP_SERVER_URL;
      if (!mcpServerUrl) {
        throw new Error('MCP server URL not configured. Set VITE_MCP_SERVER_URL in your environment.');
      }
      const response = await fetch(`${mcpServerUrl}/api/ingest/file`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || errorData.detail || 'File ingestion failed');
      }

      const data = await response.json();

      // Build success message with evaluation if available
      let successMsg = `Successfully ingested! Created ${data.num_chunks} chunks.`;
      if (data.evaluation) {
        const qualityPct = Math.round((data.evaluation.quality_score || 0) * 100);
        successMsg += ` Quality: ${qualityPct}%`;
        if (data.evaluation.topic_relevance_score !== undefined) {
          const relevancePct = Math.round(data.evaluation.topic_relevance_score * 100);
          successMsg += `, Relevance: ${relevancePct}%`;
        }
      }
      setSuccess(successMsg);
      // DON'T clear form - let user see what they just ingested
      // Form will be cleared when modal closes (handleClose)
      await loadCollections();
    } catch (err: any) {
      setError(err.message || 'Failed to ingest file');
    } finally {
      setIsIngesting(false);
    }
  };

  const handleClose = () => {
    if (isIngesting) return;

    // Reset all form state when closing
    setError(null);
    setSuccess(null);
    setUrl('');
    setFollowLinks(false);
    setUrlPreviewData(null);
    setUrlMode('ingest');
    setMaxPages(10);
    setUrlTopic('');
    setUrlReviewedByHuman(false);
    setUrlMetadata('');
    setTextContent('');
    setTextTitle('');
    setTextMode('ingest');
    setTextTopic('');
    setTextReviewedByHuman(false);
    setTextMetadata('');
    setFile(null);
    setFileMode('ingest');
    setFileTopic('');
    setFileReviewedByHuman(false);
    setFileMetadata('');
    // Reset folder state
    setUploadMode('file');
    setFolderFiles([]);
    setSkippedFiles([]);
    setFolderName('');
    setFolderProgress(null);
    // Reset topic warning state
    setShowTopicWarning(false);
    setPendingIngestAction(null);

    onClose();
  };

  return (
    <Modal
      opened={opened}
      onClose={handleClose}
      title="Ingest Content"
      size="lg"
      styles={{
        title: {
          fontFamily: 'Playfair Display, Georgia, serif',
          fontSize: 24,
          color: 'var(--amber)',
          fontWeight: 700,
        },
      }}
    >
      {error && (
        <Alert
          icon={<IconAlertCircle size={16} />}
          color="red"
          mb="md"
          onClose={() => setError(null)}
          withCloseButton
        >
          {error}
        </Alert>
      )}

      {success && (
        <Alert color="teal" mb="md">
          {success}
        </Alert>
      )}

      <Tabs value={activeTab} onChange={(value) => value && setActiveTab(value)}>
        <Tabs.List mb="md">
          <Tabs.Tab value="text" leftSection={<IconUpload size={16} />}>
            Text
          </Tabs.Tab>
          <Tabs.Tab value="url" leftSection={<IconWorld size={16} />}>
            URL
          </Tabs.Tab>
          <Tabs.Tab value="file" leftSection={<IconFolder size={16} />}>
            File
          </Tabs.Tab>
        </Tabs.List>

        {/* Text Tab */}
        <Tabs.Panel value="text">
          <Stack gap="md">
            <TextInput
              label="Title (optional)"
              placeholder="Document title"
              value={textTitle}
              onChange={(e) => setTextTitle(e.target.value)}
              disabled={isIngesting}
            />

            <Textarea
              label="Content"
              placeholder="Paste or type content here..."
              minRows={8}
              value={textContent}
              onChange={(e) => setTextContent(e.target.value)}
              required
              disabled={isIngesting}
            />

            <Select
              label="Collection"
              placeholder="Select collection"
              data={collectionOptions}
              value={textCollection}
              onChange={(value) => setTextCollection(value || '')}
              required
              disabled={isIngesting}
            />

            <Radio.Group
              label="Ingestion Mode"
              description="Choose 'ingest' for new content or 'reingest' to overwrite existing"
              value={textMode}
              onChange={(value) => setTextMode(value as 'ingest' | 'reingest')}
            >
              <Group mt="xs">
                <Radio value="ingest" label="Ingest (new)" disabled={isIngesting} />
                <Radio value="reingest" label="Reingest (overwrite)" disabled={isIngesting} />
              </Group>
            </Radio.Group>

            <TextInput
              label="Topic (optional)"
              placeholder="e.g., 'API authentication' or 'React hooks'"
              description="Describe the content focus. Used to score relevance."
              value={textTopic}
              onChange={(e) => setTextTopic(e.target.value)}
              disabled={isIngesting}
            />

            <Checkbox
              label="I have reviewed this content"
              description="Check if you've personally reviewed and verified this content is useful"
              checked={textReviewedByHuman}
              onChange={(e) => setTextReviewedByHuman(e.currentTarget.checked)}
              disabled={isIngesting}
            />

            <Textarea
              label="Custom Metadata (optional)"
              placeholder='{"category": "tutorial", "author": "John Doe"}'
              description="JSON object with custom fields for filtering and organization"
              minRows={2}
              maxRows={4}
              value={textMetadata}
              onChange={(e) => setTextMetadata(e.target.value)}
              disabled={isIngesting}
              error={validateMetadata(textMetadata)}
            />

            <Group justify="flex-end" mt="md">
              <Button
                variant="light"
                onClick={handleClose}
                disabled={isIngesting}
              >
                Cancel
              </Button>
              <Button
                onClick={() => handleIngestWithTopicCheck(textTopic, handleIngestText)}
                disabled={!textContent.trim() || !textCollection || isIngesting || !!validateMetadata(textMetadata)}
                loading={isIngesting}
                color="amber"
                style={{
                  background: 'linear-gradient(135deg, var(--amber) 0%, var(--amber-dark) 100%)',
                }}
              >
                Ingest Text
              </Button>

              {/* Validation hints */}
              {!textContent.trim() && (
                <Text size="xs" c="red" mt="xs">
                  ⚠ Content is required
                </Text>
              )}
              {textContent.trim() && !textCollection && (
                <Text size="xs" c="red" mt="xs">
                  ⚠ Collection is required
                </Text>
              )}
            </Group>
          </Stack>
        </Tabs.Panel>

        {/* URL Tab */}
        <Tabs.Panel value="url">
          <Stack gap="md">
            <TextInput
              label="URL"
              placeholder="https://example.com/docs"
              value={url}
              onChange={(e) => {
                setUrl(e.target.value);
                setUrlPreviewData(null); // Reset preview when URL changes
              }}
              required
              disabled={isIngesting || isLoadingPreview || !!success}
            />

            <Radio.Group
              label="Ingestion Mode"
              description="Choose 'ingest' for new content or 'reingest' to overwrite existing"
              value={urlMode}
              onChange={(value) => setUrlMode(value as 'ingest' | 'reingest')}
            >
              <Group mt="xs">
                <Radio value="ingest" label="Ingest (new)" disabled={isIngesting || isLoadingPreview || !!success} />
                <Radio value="reingest" label="Reingest (overwrite)" disabled={isIngesting || isLoadingPreview || !!success} />
              </Group>
            </Radio.Group>

            <Checkbox
              label="Preview before ingesting (recommended)"
              description="Validate URL content before committing to ingestion"
              checked={previewMode}
              onChange={(e) => setPreviewMode(e.target.checked)}
              disabled={isIngesting || isLoadingPreview || !!success}
            />

            <TextInput
              label="Topic (optional)"
              placeholder="e.g., 'API authentication' or 'React hooks'"
              description="Describe the content focus for relevance scoring."
              value={urlTopic}
              onChange={(e) => setUrlTopic(e.target.value)}
              disabled={isIngesting || isLoadingPreview || !!success}
            />

            <Checkbox
              label="Follow links (multi-page crawl)"
              description="Crawl linked pages from this URL"
              checked={followLinks}
              onChange={(e) => setFollowLinks(e.target.checked)}
              disabled={isIngesting || isLoadingPreview || !!success}
            />

            <NumberInput
              label="Max Pages"
              description={followLinks
                ? "Maximum pages to crawl (1-20)"
                : "Only applies when 'Follow links' is enabled"
              }
              value={maxPages}
              onChange={(value) => setMaxPages(value as number)}
              min={1}
              max={20}
              disabled={isIngesting || isLoadingPreview || !!success || !followLinks}
            />

            <Select
              label="Collection"
              placeholder="Select collection"
              data={collectionOptions}
              value={urlCollection}
              onChange={(value) => setUrlCollection(value || '')}
              required
              disabled={isIngesting || isLoadingPreview || !!success}
            />

            <Checkbox
              label="I have reviewed this content"
              description="Check if you've personally reviewed and verified this content is useful"
              checked={urlReviewedByHuman}
              onChange={(e) => setUrlReviewedByHuman(e.currentTarget.checked)}
              disabled={isIngesting || isLoadingPreview || !!success}
            />

            <Textarea
              label="Custom Metadata (optional)"
              placeholder='{"category": "documentation", "version": "2.0"}'
              description="JSON object with custom fields applied to all crawled pages"
              minRows={2}
              maxRows={4}
              value={urlMetadata}
              onChange={(e) => setUrlMetadata(e.target.value)}
              disabled={isIngesting || isLoadingPreview || !!success}
              error={validateMetadata(urlMetadata)}
            />

            {/* Preview Results - Show relevance display (hide in success state) */}
            {!success && urlPreviewData && urlPreviewData.pages && (
              <PageRelevanceDisplay
                pages={urlPreviewData.pages}
                topic={urlTopic}
                pagesRecommended={urlPreviewData.pages_recommended || 0}
                pagesToReview={urlPreviewData.pages_to_review || 0}
                pagesToSkip={urlPreviewData.pages_to_skip || 0}
                pagesFailed={urlPreviewData.pages_failed || 0}
              />
            )}

            {followLinks && !urlPreviewData && (
              <Text size="sm" c="dimmed" style={{ marginTop: -8 }}>
                Note: URL crawling may take several minutes for multiple pages
              </Text>
            )}

            <Group justify="flex-end" mt="md">
              {success ? (
                // Success state: Show "Ingest Another URL" and "Close" buttons
                <>
                  <Button
                    variant="light"
                    onClick={handleClose}
                  >
                    Close
                  </Button>
                  <Button
                    onClick={handleResetUrlForm}
                    color="amber"
                    style={{
                      background: 'linear-gradient(135deg, var(--amber) 0%, var(--amber-dark) 100%)',
                    }}
                  >
                    Ingest Another URL
                  </Button>
                </>
              ) : (
                // Normal state: Show Cancel and action button
                <>
                  <Button
                    variant="light"
                    onClick={handleClose}
                    disabled={isIngesting || isLoadingPreview}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={() => handleIngestWithTopicCheck(urlTopic, handleIngestUrl)}
                    disabled={
                      !url.trim() ||
                      !urlCollection ||
                      isIngesting ||
                      isLoadingPreview ||
                      // ONLY block if preview shows all pages have HTTP errors
                      (urlPreviewData && !previewCanIngest) ||
                      // Block if metadata JSON is invalid
                      !!validateMetadata(urlMetadata)
                    }
                    loading={isIngesting || isLoadingPreview}
                    color="amber"
                    style={{
                      background: 'linear-gradient(135deg, var(--amber) 0%, var(--amber-dark) 100%)',
                    }}
                  >
                    {isLoadingPreview
                      ? 'Validating...'
                      : isIngesting
                      ? 'Ingesting...'
                      : urlPreviewData && !previewCanIngest
                      ? 'Cannot Ingest - All Pages Failed'
                      : !previewMode && urlPreviewData
                      ? urlPreviewData.pages_recommended > 0
                        ? `Ingest ${urlPreviewData.pages_recommended} Page${urlPreviewData.pages_recommended !== 1 ? 's' : ''}`
                        : 'Ingest Anyway (Low Relevance)'
                      : previewMode && urlPreviewData
                      ? 'Update Preview'
                      : previewMode
                      ? 'Preview URL'
                      : 'Ingest URL'}
                  </Button>
                </>
              )}

              {/* Validation hints - ironclad user feedback (hide in success state) */}
              {!success && !url.trim() && (
                <Text size="xs" c="red" mt="xs">
                  ⚠ URL is required
                </Text>
              )}
              {!success && url.trim() && !urlCollection && (
                <Text size="xs" c="red" mt="xs">
                  ⚠ Collection is required
                </Text>
              )}
              {!success && url.trim() && urlCollection && urlPreviewData && !previewCanIngest && (
                <Text size="xs" c="red" mt="xs">
                  ⚠ Cannot ingest - all pages failed with HTTP errors. Please check the URL and try again.
                </Text>
              )}
            </Group>
          </Stack>
        </Tabs.Panel>

        {/* File Tab */}
        <Tabs.Panel value="file">
          <Stack gap="md">
            {/* File/Folder Toggle */}
            <SegmentedControl
              value={uploadMode}
              onChange={(value) => {
                setUploadMode(value as 'file' | 'folder');
                setFile(null);
                setFolderFiles([]);
                setSkippedFiles([]);
                setFolderName('');
                setFolderProgress(null);
                setSuccess(null);
                setError(null);
              }}
              data={[
                { label: 'File', value: 'file' },
                { label: 'Folder', value: 'folder' },
              ]}
              disabled={isIngesting || !!success}
            />

            {/* Hidden folder input */}
            <input
              type="file"
              ref={folderInputRef}
              style={{ display: 'none' }}
              // @ts-ignore - webkitdirectory is non-standard but widely supported
              webkitdirectory=""
              multiple
              onChange={handleFolderSelect}
            />

            {/* Single File Mode */}
            {uploadMode === 'file' && (
              <>
                <FileInput
                  label="Select File"
                  placeholder="Choose a file..."
                  value={file}
                  onChange={(f) => {
                    setFile(f);
                    // Clear any previous validation error when new file selected
                    if (f) {
                      const validation = validateFile(f);
                      if (!validation.valid) {
                        setError(`Cannot upload '${f.name}': ${validation.reason}`);
                        setFile(null);
                      } else {
                        setError(null);
                      }
                    }
                  }}
                  disabled={isIngesting || !!success}
                />

                {/* Supported file types hint (show before file selected) */}
                {!file && (
                  <Text size="xs" c="dimmed">
                    {SUPPORTED_TYPES_HINT}
                  </Text>
                )}

                {file && (
                  <Text size="sm" c="dimmed">
                    Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
                  </Text>
                )}
              </>
            )}

            {/* Folder Mode */}
            {uploadMode === 'folder' && (
              <>
                <Button
                  variant="default"
                  leftSection={<IconFolder size={16} />}
                  onClick={() => folderInputRef.current?.click()}
                  disabled={isIngesting || !!success}
                  fullWidth
                >
                  {folderName ? `Selected: ${folderName}/` : 'Select Folder...'}
                </Button>

                {/* Supported file types hint (show before folder selected) */}
                {!folderName && (
                  <Text size="xs" c="dimmed">
                    {SUPPORTED_TYPES_HINT}
                  </Text>
                )}

                {/* Folder summary */}
                {folderFiles.length > 0 && (
                  <Text size="sm" c="dimmed">
                    Found {folderFiles.length} supported file{folderFiles.length !== 1 ? 's' : ''}
                    {skippedFiles.length > 0 && ` (${skippedFiles.length} skipped)`}
                  </Text>
                )}

                {/* File preview list */}
                {folderProgress && (
                  <Paper withBorder p="sm">
                    {/* Progress bar during upload */}
                    {isIngesting && (
                      <Stack gap="xs" mb="sm">
                        <Group justify="space-between">
                          <Text size="sm" fw={500}>
                            Processing file {folderProgress.current} of {folderProgress.total}
                          </Text>
                          <Text size="sm" c="dimmed">
                            {Math.round((folderProgress.current / folderProgress.total) * 100)}%
                          </Text>
                        </Group>
                        <Progress
                          value={(folderProgress.current / folderProgress.total) * 100}
                          color="amber"
                          size="sm"
                          animated
                        />
                        {folderProgress.currentFile && (
                          <Text size="xs" c="dimmed">
                            Current: {folderProgress.currentFile}
                          </Text>
                        )}
                      </Stack>
                    )}

                    <ScrollArea h={Math.min(200, folderProgress.results.length * 32 + 16)}>
                      <Stack gap="xs">
                        {folderProgress.results.map((result, i) => (
                          <Group key={i} justify="space-between" wrap="nowrap">
                            <Group gap="xs" wrap="nowrap" style={{ minWidth: 0 }}>
                              {result.status === 'success' && <IconCheck size={14} color="var(--mantine-color-teal-6)" />}
                              {result.status === 'error' && <IconX size={14} color="var(--mantine-color-red-6)" />}
                              {result.status === 'processing' && <Loader size={14} color="amber" />}
                              {result.status === 'pending' && <IconFile size={14} color="var(--mantine-color-gray-5)" />}
                              <Text size="sm" truncate style={{ maxWidth: 200 }}>
                                {result.filename}
                              </Text>
                            </Group>
                            <Text size="xs" c="dimmed" style={{ flexShrink: 0 }}>
                              {result.status === 'success' && `${result.chunks} chunks`}
                              {result.status === 'error' && (
                                <Text span c="red" size="xs">{result.error}</Text>
                              )}
                              {result.status === 'pending' && folderFiles[i] && `${(folderFiles[i].size / 1024).toFixed(1)} KB`}
                              {result.status === 'processing' && 'Processing...'}
                            </Text>
                          </Group>
                        ))}
                      </Stack>
                    </ScrollArea>

                    {/* Skipped files section */}
                    {skippedFiles.length > 0 && !isIngesting && !success && (
                      <>
                        <Divider my="sm" label="Skipped files" labelPosition="center" />
                        <ScrollArea h={Math.min(80, skippedFiles.length * 24)}>
                          <Stack gap={4}>
                            {skippedFiles.map((file, i) => (
                              <Group key={i} gap="xs">
                                <IconX size={12} color="var(--mantine-color-gray-5)" />
                                <Text size="xs" c="dimmed">
                                  {file.name} ({file.reason})
                                </Text>
                              </Group>
                            ))}
                          </Stack>
                        </ScrollArea>
                      </>
                    )}
                  </Paper>
                )}

                {/* Empty folder message */}
                {folderName && folderFiles.length === 0 && (
                  <Alert color="yellow" icon={<IconAlertCircle size={16} />}>
                    No supported files found in this folder. Supported types: .txt, .md, .json, .yaml, .py, .js, etc.
                  </Alert>
                )}
              </>
            )}

            <Select
              label="Collection"
              placeholder="Select collection"
              data={collectionOptions}
              value={fileCollection}
              onChange={(value) => setFileCollection(value || '')}
              required
              disabled={isIngesting || !!success}
            />

            <Radio.Group
              label="Ingestion Mode"
              description="Choose 'ingest' for new content or 'reingest' to overwrite existing"
              value={fileMode}
              onChange={(value) => setFileMode(value as 'ingest' | 'reingest')}
            >
              <Group mt="xs">
                <Radio value="ingest" label="Ingest (new)" disabled={isIngesting || !!success} />
                <Radio value="reingest" label="Reingest (overwrite)" disabled={isIngesting || !!success} />
              </Group>
            </Radio.Group>

            <TextInput
              label="Topic (optional)"
              placeholder="e.g., 'API documentation' or 'Machine learning tutorials'"
              description="Describe the content focus. Used to score relevance."
              value={fileTopic}
              onChange={(e) => setFileTopic(e.target.value)}
              disabled={isIngesting || !!success}
            />

            <Checkbox
              label="I have reviewed this content"
              description="Check if you've personally reviewed and verified this content is useful"
              checked={fileReviewedByHuman}
              onChange={(e) => setFileReviewedByHuman(e.currentTarget.checked)}
              disabled={isIngesting || !!success}
            />

            <Textarea
              label="Custom Metadata (optional)"
              placeholder='{"project": "my-project", "type": "config"}'
              description="JSON object with custom fields for filtering and organization"
              minRows={2}
              maxRows={4}
              value={fileMetadata}
              onChange={(e) => setFileMetadata(e.target.value)}
              disabled={isIngesting || !!success}
              error={validateMetadata(fileMetadata)}
            />

            <Group justify="flex-end" mt="md">
              {success ? (
                // Success state: Show "Upload Another" and "Close" buttons
                <>
                  <Button
                    variant="light"
                    onClick={handleClose}
                  >
                    Close
                  </Button>
                  <Button
                    onClick={handleResetFileForm}
                    color="amber"
                    style={{
                      background: 'linear-gradient(135deg, var(--amber) 0%, var(--amber-dark) 100%)',
                    }}
                  >
                    {uploadMode === 'folder' ? 'Upload Another Folder' : 'Upload Another File'}
                  </Button>
                </>
              ) : (
                // Normal state: Show Cancel and action button
                <>
                  <Button
                    variant="light"
                    onClick={handleClose}
                    disabled={isIngesting}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={() => {
                      const ingestFn = uploadMode === 'file' ? handleIngestFile : handleIngestFolder;
                      handleIngestWithTopicCheck(fileTopic, ingestFn);
                    }}
                    disabled={
                      (uploadMode === 'file' && !file) ||
                      (uploadMode === 'folder' && folderFiles.length === 0) ||
                      !fileCollection ||
                      isIngesting ||
                      // Block if metadata JSON is invalid
                      !!validateMetadata(fileMetadata)
                    }
                    loading={isIngesting}
                    color="amber"
                    style={{
                      background: 'linear-gradient(135deg, var(--amber) 0%, var(--amber-dark) 100%)',
                    }}
                  >
                    {isIngesting
                      ? uploadMode === 'folder' && folderProgress
                        ? `Processing ${folderProgress.current}/${folderProgress.total}...`
                        : 'Uploading...'
                      : uploadMode === 'folder' && folderFiles.length > 0
                      ? `Upload ${folderFiles.length} File${folderFiles.length !== 1 ? 's' : ''}`
                      : 'Upload & Ingest'
                    }
                  </Button>
                </>
              )}

              {/* Validation hints */}
              {!success && uploadMode === 'file' && !file && (
                <Text size="xs" c="red" mt="xs">
                  ⚠ File is required
                </Text>
              )}
              {!success && uploadMode === 'folder' && !folderName && (
                <Text size="xs" c="red" mt="xs">
                  ⚠ Folder is required
                </Text>
              )}
              {!success && uploadMode === 'folder' && folderName && folderFiles.length === 0 && (
                <Text size="xs" c="red" mt="xs">
                  ⚠ No supported files in folder
                </Text>
              )}
              {!success && ((uploadMode === 'file' && file) || (uploadMode === 'folder' && folderFiles.length > 0)) && !fileCollection && (
                <Text size="xs" c="red" mt="xs">
                  ⚠ Collection is required
                </Text>
              )}
            </Group>
          </Stack>
        </Tabs.Panel>
      </Tabs>

      {isIngesting && (
        <Group justify="center" mt="lg" mb="sm">
          <Loader size="sm" color="amber" />
          <Text size="sm" c="dimmed">
            Processing... This may take several minutes. Do not close this dialog.
          </Text>
        </Group>
      )}

      {/* Topic Warning Modal */}
      <Modal
        opened={showTopicWarning}
        onClose={handleCancelIngestWarning}
        title={
          <Group gap="xs">
            <IconAlertTriangle size={20} color="var(--mantine-color-yellow-6)" />
            <Text fw={600}>No Topic Provided</Text>
          </Group>
        }
        size="md"
        centered
      >
        <Stack gap="md">
          <Text size="sm">
            You're about to ingest content without specifying a topic. This means:
          </Text>
          <Stack gap="xs" pl="md">
            <Text size="sm" c="dimmed">
              • <strong>No relevance scoring</strong> — You won't know how well this content matches your intended use case
            </Text>
            <Text size="sm" c="dimmed">
              • <strong>Weaker search filtering</strong> — You can't filter by topic relevance when searching
            </Text>
            <Text size="sm" c="dimmed">
              • <strong>Lower quality signals</strong> — Harder to identify and clean up off-topic content later
            </Text>
          </Stack>
          <Text size="sm" fw={500}>
            Adding a brief topic description (e.g., "React hooks" or "API authentication") significantly improves knowledge quality.
          </Text>
          <Group justify="flex-end" mt="md">
            <Button variant="light" onClick={handleCancelIngestWarning}>
              Go Back & Add Topic
            </Button>
            <Button
              color="yellow"
              variant="filled"
              onClick={handleConfirmIngestWithoutTopic}
            >
              Ingest Anyway
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Modal>
  );
}
