/**
 * LeftNavigation - Left sidebar with view navigation
 *
 * Features:
 * - View navigation items (Collections, Documents, Search, Chat) - ALWAYS VISIBLE
 * - Shows ConversationSidebar BELOW navigation when in chat mode
 * - Collapsible sidebar
 * - Resizable width via drag handle
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { Box, NavLink, ActionIcon } from '@mantine/core';
import { IconDashboard, IconStack, IconFiles, IconSearch, IconMessage, IconChevronLeft, IconChevronRight } from '@tabler/icons-react';
import ConversationSidebar from '../ConversationSidebar';
import type { View } from './AppLayout';

interface Props {
  activeView: View;
  onViewChange: (view: View) => void;
}

const MIN_WIDTH = 200;
const MAX_WIDTH = 500;
const DEFAULT_WIDTH = 280;
const COLLAPSED_WIDTH = 60;

export function LeftNavigation({ activeView, onViewChange }: Props) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [width, setWidth] = useState(DEFAULT_WIDTH);
  const [isResizing, setIsResizing] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const navItems: Array<{ view: View; icon: typeof IconStack; label: string }> = [
    { view: 'dashboard', icon: IconDashboard, label: 'Dashboard' },
    { view: 'collections', icon: IconStack, label: 'Collections' },
    { view: 'documents', icon: IconFiles, label: 'Documents' },
    { view: 'search', icon: IconSearch, label: 'Search' },
    { view: 'chat', icon: IconMessage, label: 'Agent Chat' }
  ];

  // Handle mouse move during resize
  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isResizing) return;

    const newWidth = e.clientX;
    if (newWidth >= MIN_WIDTH && newWidth <= MAX_WIDTH) {
      setWidth(newWidth);
    }
  }, [isResizing]);

  // Handle mouse up to stop resizing
  const handleMouseUp = useCallback(() => {
    setIsResizing(false);
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  }, []);

  // Add/remove event listeners for resize
  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, handleMouseMove, handleMouseUp]);

  // Start resizing
  const startResize = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  const currentWidth = isCollapsed ? COLLAPSED_WIDTH : width;

  return (
    <Box
      ref={containerRef}
      style={{
        width: `${currentWidth}px`,
        flex: `0 0 ${currentWidth}px`,
        height: '100%',
        background: 'linear-gradient(180deg, var(--charcoal-light) 0%, var(--charcoal) 100%)',
        borderRight: '2px solid var(--amber-dark)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        animation: 'slideIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) 0.2s both',
        position: 'relative',
        transition: isResizing ? 'none' : 'width 0.2s ease, flex-basis 0.2s ease',
      }}
    >
      {/* Navigation Items - ALWAYS VISIBLE */}
      <Box style={{ padding: isCollapsed ? '24px 8px' : '24px 16px', borderBottom: activeView === 'chat' && !isCollapsed ? '1px solid var(--charcoal-lighter)' : 'none' }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.view}
              label={isCollapsed ? '' : item.label}
              leftSection={<Icon size={20} />}
              active={activeView === item.view}
              onClick={() => onViewChange(item.view)}
              style={{
                borderRadius: 8,
                marginBottom: 8,
                color: activeView === item.view ? 'var(--cream)' : 'var(--cream-dim)',
                backgroundColor: activeView === item.view ? 'rgba(245, 158, 11, 0.12)' : 'transparent',
                transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
                position: 'relative',
                justifyContent: isCollapsed ? 'center' : 'flex-start',
                padding: isCollapsed ? '12px' : undefined,
              }}
              title={isCollapsed ? item.label : undefined}
            />
          );
        })}

        {/* Collapse/Expand button */}
        <Box style={{ marginTop: 16, display: 'flex', justifyContent: isCollapsed ? 'center' : 'flex-end' }}>
          <ActionIcon
            onClick={toggleCollapse}
            variant="subtle"
            size="md"
            color="gray"
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? <IconChevronRight size={18} /> : <IconChevronLeft size={18} />}
          </ActionIcon>
        </Box>
      </Box>

      {/* Show ConversationSidebar content when in chat view and not collapsed */}
      {activeView === 'chat' && !isCollapsed && (
        <Box style={{ flex: 1, overflow: 'hidden' }}>
          <ConversationSidebar />
        </Box>
      )}

      {/* Resize handle - only when not collapsed */}
      {!isCollapsed && (
        <Box
          onMouseDown={startResize}
          style={{
            position: 'absolute',
            top: 0,
            right: 0,
            width: '6px',
            height: '100%',
            cursor: 'col-resize',
            backgroundColor: isResizing ? 'var(--amber)' : 'transparent',
            transition: 'background-color 0.2s ease',
            zIndex: 10,
          }}
          onMouseEnter={(e) => {
            if (!isResizing) {
              e.currentTarget.style.backgroundColor = 'rgba(245, 158, 11, 0.3)';
            }
          }}
          onMouseLeave={(e) => {
            if (!isResizing) {
              e.currentTarget.style.backgroundColor = 'transparent';
            }
          }}
        />
      )}
    </Box>
  );
}
