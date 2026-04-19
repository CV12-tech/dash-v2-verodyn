import type { Config } from 'tailwindcss';

export default {
  content: ['./src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        bg:              'hsl(var(--bg) / <alpha-value>)',
        surface:         'hsl(var(--surface) / <alpha-value>)',
        'surface-muted': 'hsl(var(--surface-muted) / <alpha-value>)',
        'surface-sunken':'hsl(var(--surface-sunken) / <alpha-value>)',
        ink:             'hsl(var(--ink) / <alpha-value>)',
        'ink-muted':     'hsl(var(--ink-muted) / <alpha-value>)',
        'ink-subtle':    'hsl(var(--ink-subtle) / <alpha-value>)',
        border:          'hsl(var(--border) / <alpha-value>)',
        'border-strong': 'hsl(var(--border-strong) / <alpha-value>)',
        primary: {
          DEFAULT: 'hsl(var(--primary) / <alpha-value>)',
          fg:      'hsl(var(--primary-fg) / <alpha-value>)',
          soft:    'hsl(var(--primary-soft) / <alpha-value>)',
        },
        success: {
          DEFAULT: 'hsl(var(--success) / <alpha-value>)',
          soft:    'hsl(var(--success-soft) / <alpha-value>)',
        },
        warning: {
          DEFAULT: 'hsl(var(--warning) / <alpha-value>)',
          soft:    'hsl(var(--warning-soft) / <alpha-value>)',
        },
        info: {
          DEFAULT: 'hsl(var(--info) / <alpha-value>)',
          soft:    'hsl(var(--info-soft) / <alpha-value>)',
        },
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'Plus Jakarta Sans', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        sm: '6px',
        DEFAULT: '8px',
        md: '10px',
        lg: '12px',
        xl: '16px',
      },
      spacing: {
        '18': '4.5rem',
      },
    },
  },
  plugins: [],
} satisfies Config;
