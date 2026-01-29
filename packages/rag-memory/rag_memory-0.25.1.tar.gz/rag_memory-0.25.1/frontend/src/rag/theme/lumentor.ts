import { MantineThemeOverride } from '@mantine/core';

/**
 * Lumentor Design System - Illuminated Archive Aesthetic
 *
 * Warm amber/teal palette with charcoal backgrounds, dramatic shadows,
 * and atmospheric effects. Inspired by vintage archives and knowledge vaults.
 */
export const lumentorTheme: MantineThemeOverride = {
  colors: {
    charcoal: [
      '#fafaf9', // cream - lightest
      '#e7e5e4', // cream-dim
      '#a8a29e', // warm-gray
      '#3a342d', // charcoal-lighter
      '#2a2520', // charcoal-light
      '#1a1714', // charcoal (base)
      '#151210',
      '#100e0c',
      '#0b0908',
      '#060504'  // darkest
    ],
    amber: [
      '#fffbeb',
      '#fef3c7',
      '#fde68a',
      '#fcd34d',
      '#fbbf24', // amber-light
      '#f59e0b', // amber (base)
      '#d97706', // amber-dark
      '#b45309',
      '#92400e',
      '#78350f'
    ],
    teal: [
      '#f0fdfa',
      '#ccfbf1',
      '#99f6e4',
      '#5eead4',
      '#2dd4bf',
      '#14b8a6', // teal-light
      '#0f766e', // teal (base)
      '#0d5e57',
      '#0a4940',
      '#073229'
    ],
    sienna: [
      '#fff7ed',
      '#ffedd5',
      '#fed7aa',
      '#fdba74',
      '#fb923c',
      '#f97316',
      '#ea580c', // sienna (base)
      '#c2410c',
      '#9a3412',
      '#7c2d12'
    ]
  },

  primaryColor: 'amber',
  primaryShade: 5,

  defaultRadius: 'md',

  fontFamily: "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  fontFamilyMonospace: "'Fira Code', 'Monaco', 'Courier New', monospace",

  headings: {
    fontFamily: "'Playfair Display', Georgia, serif",
    fontWeight: '700',
    sizes: {
      h1: { fontSize: '3rem', lineHeight: '1.2', fontWeight: '900' },
      h2: { fontSize: '2rem', lineHeight: '1.3', fontWeight: '700' },
      h3: { fontSize: '1.5rem', lineHeight: '1.4', fontWeight: '700' },
      h4: { fontSize: '1.25rem', lineHeight: '1.4', fontWeight: '600' },
      h5: { fontSize: '1.15rem', lineHeight: '1.5', fontWeight: '600' },
      h6: { fontSize: '1rem', lineHeight: '1.5', fontWeight: '600' }
    }
  },

  fontSizes: {
    xs: '0.75rem',
    sm: '0.875rem',
    md: '1rem',
    lg: '1.125rem',
    xl: '1.25rem'
  },

  spacing: {
    xs: '0.5rem',
    sm: '0.75rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem'
  },

  shadows: {
    xs: '0 1px 3px rgba(245, 158, 11, 0.1)',
    sm: '0 2px 8px rgba(245, 158, 11, 0.12)',
    md: '0 4px 16px rgba(245, 158, 11, 0.15)',
    lg: '0 8px 24px rgba(245, 158, 11, 0.2)',
    xl: '0 16px 48px rgba(245, 158, 11, 0.25)'
  },

  components: {
    Button: {
      styles: () => ({
        root: {
          fontWeight: 500,
          transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
          '&:hover': {
            transform: 'translateY(-2px)',
          }
        }
      })
    },

    Card: {
      styles: () => ({
        root: {
          backgroundColor: 'var(--charcoal-light)',
          border: '1px solid rgba(245, 158, 11, 0.15)',
          transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: '0 12px 32px rgba(245, 158, 11, 0.2)',
            borderColor: 'var(--amber-dark)'
          }
        }
      })
    },

    Paper: {
      styles: () => ({
        root: {
          backgroundColor: 'var(--charcoal-light)',
          border: '1px solid rgba(245, 158, 11, 0.1)'
        }
      })
    },

    Modal: {
      styles: () => ({
        modal: {
          backgroundColor: 'var(--charcoal-light)',
          border: '2px solid var(--amber-dark)',
          boxShadow: '0 24px 64px rgba(245, 158, 11, 0.3)'
        },
        header: {
          backgroundColor: 'var(--charcoal)',
          borderBottom: '1px solid var(--amber-dark)',
          paddingBottom: '1rem'
        },
        title: {
          fontFamily: "'Playfair Display', Georgia, serif",
          fontSize: '1.5rem',
          fontWeight: 700,
          background: 'linear-gradient(135deg, var(--amber-light), var(--amber))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text'
        }
      })
    },

    TextInput: {
      styles: () => ({
        input: {
          backgroundColor: 'rgba(42, 37, 32, 0.6)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          color: 'var(--cream)',
          '&:focus': {
            borderColor: 'var(--amber)',
            boxShadow: '0 0 20px rgba(245, 158, 11, 0.2)'
          },
          '&::placeholder': {
            color: 'var(--warm-gray)'
          }
        }
      })
    },

    Textarea: {
      styles: () => ({
        input: {
          backgroundColor: 'rgba(42, 37, 32, 0.6)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          color: 'var(--cream)',
          '&:focus': {
            borderColor: 'var(--amber)',
            boxShadow: '0 0 20px rgba(245, 158, 11, 0.2)'
          },
          '&::placeholder': {
            color: 'var(--warm-gray)'
          }
        }
      })
    }
  }
};
