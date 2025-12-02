// Darts Fantasy Auction - Theme Configuration
// PDC-inspired color palette and design tokens

export const colors = {
  // Primary: Dartboard red
  primary: {
    50: '#FEF2F2',
    100: '#FEE2E2',
    200: '#FECACA',
    300: '#FCA5A5',
    400: '#F87171',
    500: '#EF4444',
    600: '#DC2626', // Main red
    700: '#B91C1C',
    800: '#991B1B',
    900: '#7F1D1D',
  },
  
  // Secondary: Dartboard green
  secondary: {
    50: '#F0FDF4',
    100: '#DCFCE7',
    200: '#BBF7D0',
    300: '#86EFAC',
    400: '#4ADE80',
    500: '#22C55E',
    600: '#16A34A', // Main green
    700: '#15803D',
    800: '#166534',
    900: '#14532D',
  },
  
  // Accent: Gold (for winners, treble 20 vibe)
  accent: {
    50: '#FEFCE8',
    100: '#FEF9C3',
    200: '#FEF08A',
    300: '#FDE047',
    400: '#FACC15',
    500: '#FBBF24', // Main gold
    600: '#F59E0B',
    700: '#D97706',
    800: '#B45309',
    900: '#92400E',
  },
  
  // Dark: Charcoal/oche mat feel
  dark: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    200: '#E5E7EB',
    300: '#D1D5DB',
    400: '#9CA3AF',
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
    800: '#1F2937', // Main dark
    900: '#111827',
  },
  
  // Background: Deep slate (TV broadcast)
  background: {
    50: '#F8FAFC',
    100: '#F1F5F9',
    200: '#E2E8F0',
    300: '#CBD5E1',
    400: '#94A3B8',
    500: '#64748B',
    600: '#475569',
    700: '#334155',
    800: '#1E293B',
    900: '#0F172A', // Main background
  },
};

export const typography = {
  fonts: {
    heading: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    body: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    mono: '"SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, monospace',
  },
  
  sizes: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem', // 36px
    '5xl': '3rem',    // 48px
    '6xl': '3.75rem', // 60px
    '7xl': '4.5rem',  // 72px
  },
  
  weights: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    extrabold: 800,
  },
};

export const spacing = {
  xs: '0.5rem',   // 8px
  sm: '0.75rem',  // 12px
  md: '1rem',     // 16px
  lg: '1.5rem',   // 24px
  xl: '2rem',     // 32px
  '2xl': '3rem',  // 48px
  '3xl': '4rem',  // 64px
};

export const borderRadius = {
  none: '0',
  sm: '0.125rem',   // 2px
  md: '0.375rem',   // 6px
  lg: '0.5rem',     // 8px
  xl: '0.75rem',    // 12px
  '2xl': '1rem',    // 16px
  full: '9999px',
};

export const shadows = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  glow: '0 0 20px rgba(251, 191, 36, 0.5)', // Gold glow
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
};

export const animations = {
  pulse: {
    keyframes: {
      '0%, 100%': { opacity: 1 },
      '50%': { opacity: 0.5 },
    },
    duration: '2s',
    iterationCount: 'infinite',
  },
  
  slideIn: {
    keyframes: {
      from: { transform: 'translateX(100%)', opacity: 0 },
      to: { transform: 'translateX(0)', opacity: 1 },
    },
    duration: '0.3s',
    easing: 'ease-out',
  },
  
  scaleIn: {
    keyframes: {
      from: { transform: 'scale(0.95)', opacity: 0 },
      to: { transform: 'scale(1)', opacity: 1 },
    },
    duration: '0.2s',
    easing: 'ease-out',
  },
  
  glow: {
    keyframes: {
      '0%, 100%': { boxShadow: '0 0 20px rgba(251, 191, 36, 0.5)' },
      '50%': { boxShadow: '0 0 40px rgba(251, 191, 36, 0.8)' },
    },
    duration: '1.5s',
    iterationCount: 'infinite',
  },
};

// Timer urgency states
export const timerStates = {
  calm: {
    range: [20, 30],
    borderColor: colors.secondary[600],
    bgColor: colors.secondary[50],
    textColor: colors.secondary[900],
    animation: null,
  },
  warning: {
    range: [10, 20],
    borderColor: colors.accent[500],
    bgColor: colors.accent[50],
    textColor: colors.accent[900],
    animation: 'pulse-slow',
  },
  urgent: {
    range: [0, 10],
    borderColor: colors.primary[600],
    bgColor: colors.primary[50],
    textColor: colors.primary[900],
    animation: 'pulse-fast',
  },
};

export default {
  colors,
  typography,
  spacing,
  borderRadius,
  shadows,
  animations,
  timerStates,
};
