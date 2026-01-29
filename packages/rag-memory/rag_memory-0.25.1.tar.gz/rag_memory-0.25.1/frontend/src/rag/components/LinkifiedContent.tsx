/**
 * LinkifiedContent - Parses text and makes URLs and document IDs clickable
 *
 * Detects:
 * - URLs (http://, https://) - opens in new tab
 * - Document IDs (id=123, doc_id:123, etc.) - opens DocumentModal
 *
 * NOTE: We intentionally do NOT detect filenames (*.js, *.py, etc.) because
 * it causes false positives like "Node.js", "Next.js", "Vue.js" being treated
 * as clickable documents. The agent uses explicit id=X format instead.
 */

import { useState } from 'react';
import type { ReactElement } from 'react';
import { Text, Anchor } from '@mantine/core';
import DocumentModal from './DocumentModal';
import { getDocument } from '../ragApi';
import type { Document } from '../types';

interface Props {
  content: string;
  color?: string;
  size?: string;
  linkColor?: string;  // Color for URLs and document links
}

// Regex patterns
// URL pattern excludes common sentence punctuation that shouldn't be part of URLs
const URL_PATTERN = /(https?:\/\/[^\s,;!?"'<>]+)/g;

// Document ID patterns - match various formats agents might use:
// - (id: 123) or (id:123) - parentheses with colon
// - [id: 123] or [id:123] - brackets with colon
// - id=123 - equals sign format (common agent output)
// - doc_id:123 or doc_id: 123 - explicit doc_id prefix
const DOCUMENT_ID_PATTERN = /(?:\(id:\s*(\d+)\)|\[id:\s*(\d+)\]|\bid=(\d+)\b|\bdoc_id:\s*(\d+)\b)/g;

// Clean up URL by removing trailing punctuation that's typically not part of URLs
function cleanUrl(url: string): string {
  let cleaned = url;

  // Iteratively remove trailing punctuation that's unlikely to be part of URL
  while (cleaned.length > 0) {
    const lastChar = cleaned[cleaned.length - 1];

    // Strip trailing periods only if followed by nothing or whitespace (end of sentence)
    // This preserves .html, .php, etc.
    if (lastChar === '.') {
      // Check if this looks like a file extension or TLD by checking previous char
      const prevChar = cleaned.length > 1 ? cleaned[cleaned.length - 2] : '';
      if (/[a-zA-Z0-9]/.test(prevChar)) {
        // Likely part of extension/TLD, but remove it if it's a sentence-ending period
        // This is tricky - let's only remove periods if the URL already looks complete
        // For now, keep it - users rarely end sentences with bare domains
        break;
      }
      cleaned = cleaned.slice(0, -1);
      continue;
    }

    // Strip closing parenthesis if unbalanced (not part of URL like Wikipedia links)
    if (lastChar === ')') {
      const openCount = (cleaned.match(/\(/g) || []).length;
      const closeCount = (cleaned.match(/\)/g) || []).length;
      if (closeCount > openCount) {
        // More closing than opening - this ) is probably sentence punctuation
        cleaned = cleaned.slice(0, -1);
        continue;
      }
      // Balanced or more opening - keep it
      break;
    }

    // Strip closing bracket if unbalanced
    if (lastChar === ']') {
      const openCount = (cleaned.match(/\[/g) || []).length;
      const closeCount = (cleaned.match(/\]/g) || []).length;
      if (closeCount > openCount) {
        cleaned = cleaned.slice(0, -1);
        continue;
      }
      break;
    }

    // No more trimming needed
    break;
  }

  return cleaned;
}

export default function LinkifiedContent({ content, color = 'var(--cream)', size = 'sm', linkColor }: Props) {
  const [modalOpen, setModalOpen] = useState(false);
  const [viewingDoc, setViewingDoc] = useState<Document | null>(null);
  const [loading, setLoading] = useState(false);

  const handleDocumentIdClick = async (documentId: number) => {
    setLoading(true);
    try {
      // Direct fetch by ID - no search needed
      const doc = await getDocument(documentId);
      if (doc) {
        setViewingDoc(doc);
        setModalOpen(true);
      } else {
        alert(`Document with ID ${documentId} not found`);
      }
    } catch (error) {
      console.error('Failed to load document:', error);
      alert('Failed to load document');
    } finally {
      setLoading(false);
    }
  };

  const handleUrlClick = (url: string) => {
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  // Parse content and identify links
  const renderContent = () => {
    const parts: ReactElement[] = [];
    let lastIndex = 0;
    let key = 0;

    // Find all matches (URLs and document IDs only)
    const matches: Array<{ type: 'url' | 'docId'; text: string; index: number; docId?: number; endIndex: number }> = [];

    // Find URLs first - they take priority
    let match;
    while ((match = URL_PATTERN.exec(content)) !== null) {
      const rawUrl = match[0];
      const cleanedUrl = cleanUrl(rawUrl);
      matches.push({
        type: 'url',
        text: cleanedUrl,
        index: match.index,
        endIndex: match.index + cleanedUrl.length
      });
    }

    // Helper to check if position is inside a URL
    const isInsideUrl = (index: number): boolean => {
      return matches.some(m => m.type === 'url' && index >= m.index && index < m.endIndex);
    };

    // Find document IDs in various formats - but skip if inside URL
    // Pattern has 4 capture groups: (id: X), [id: X], id=X, doc_id:X
    // Only one group will have a value depending on which format matched
    DOCUMENT_ID_PATTERN.lastIndex = 0; // Reset regex
    while ((match = DOCUMENT_ID_PATTERN.exec(content)) !== null) {
      if (!isInsideUrl(match.index)) {
        // Find which capture group matched (1-4)
        const docIdStr = match[1] || match[2] || match[3] || match[4];
        if (docIdStr) {
          matches.push({
            type: 'docId',
            text: match[0],
            index: match.index,
            docId: parseInt(docIdStr, 10),
            endIndex: match.index + match[0].length
          });
        }
      }
    }

    // Sort matches by position
    matches.sort((a, b) => a.index - b.index);

    // Render text with links
    matches.forEach((m) => {
      // Add text before match
      if (m.index > lastIndex) {
        parts.push(
          <Text key={key++} span style={{ color }}>
            {content.substring(lastIndex, m.index)}
          </Text>
        );
      }

      // Add link
      if (m.type === 'url') {
        parts.push(
          <Anchor
            key={key++}
            onClick={() => handleUrlClick(m.text)}
            style={{ cursor: 'pointer', color: linkColor || 'var(--amber)', textDecoration: 'underline' }}
          >
            {m.text}
          </Anchor>
        );
      } else if (m.type === 'docId' && m.docId !== undefined) {
        // Document ID link - direct fetch by ID
        parts.push(
          <Anchor
            key={key++}
            onClick={() => handleDocumentIdClick(m.docId!)}
            style={{
              cursor: loading ? 'wait' : 'pointer',
              color: linkColor || 'var(--teal-light)',
              textDecoration: 'underline',
              fontWeight: 500
            }}
          >
            {m.text}
          </Anchor>
        );
      }

      lastIndex = m.index + m.text.length;
    });

    // Add remaining text
    if (lastIndex < content.length) {
      parts.push(
        <Text key={key++} span style={{ color }}>
          {content.substring(lastIndex)}
        </Text>
      );
    }

    return parts.length > 0 ? parts : <Text span style={{ color }}>{content}</Text>;
  };

  return (
    <>
      <Text
        size={size}
        style={{
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {renderContent()}
      </Text>

      <DocumentModal
        document={viewingDoc}
        opened={modalOpen}
        onClose={() => {
          setModalOpen(false);
          setViewingDoc(null);
        }}
        onDocumentUpdate={(updated) => setViewingDoc(updated)}
      />
    </>
  );
}
