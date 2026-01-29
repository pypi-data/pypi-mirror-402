/**
 * TopBar - Dramatic header with Lumentor branding
 *
 * Features:
 * - Animated logo with glow effect
 * - Gradient text branding
 * - Settings button
 */

import { Box, ActionIcon } from '@mantine/core';
import { IconSettings } from '@tabler/icons-react';

export function TopBar() {
  return (
    <Box
      style={{
        height: 80,
        background: 'linear-gradient(135deg, var(--charcoal) 0%, var(--charcoal-light) 100%)',
        borderBottom: '3px solid var(--amber-dark)',
        boxShadow: '0 4px 20px rgba(245, 158, 11, 0.15)',
        display: 'flex',
        alignItems: 'center',
        padding: '0 40px',
        gap: 30,
        position: 'relative',
        zIndex: 100,
        animation: 'slideDown 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)'
      }}
    >
      {/* Logo */}
      <Box style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <Box
          style={{
            fontSize: 42,
            color: 'var(--amber)',
            filter: 'drop-shadow(0 0 12px rgba(245, 158, 11, 0.5))',
            animation: 'glow 3s ease-in-out infinite'
          }}
        >
          ✦
        </Box>
        <Box>
          <Box
            style={{
              fontFamily: 'Playfair Display, Georgia, serif',
              fontSize: 32,
              fontWeight: 700,
              lineHeight: 1,
              background: 'linear-gradient(135deg, var(--amber-light), var(--amber))',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}
          >
            Lumentor
          </Box>
          <Box
            style={{
              fontSize: 12,
              fontStyle: 'italic',
              color: 'var(--warm-gray)',
              marginTop: 4
            }}
          >
            Knowledge Illuminated
          </Box>
        </Box>
      </Box>

      {/* Spacer */}
      <Box style={{ flex: 1 }} />

      {/* Settings */}
      <ActionIcon size="lg" variant="subtle" color="amber">
        <IconSettings size={24} />
      </ActionIcon>
    </Box>
  );
}
