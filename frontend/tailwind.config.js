/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
  	extend: {
  		fontFamily: {
  			sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
  			mono: ['SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', 'monospace']
  		},
  		colors: {
  			// Darts-specific color palette
  			'darts-red': {
  				50: '#FEF2F2',
  				100: '#FEE2E2',
  				200: '#FECACA',
  				300: '#FCA5A5',
  				400: '#F87171',
  				500: '#EF4444',
  				600: '#DC2626',
  				700: '#B91C1C',
  				800: '#991B1B',
  				900: '#7F1D1D',
  			},
  			'darts-green': {
  				50: '#F0FDF4',
  				100: '#DCFCE7',
  				200: '#BBF7D0',
  				300: '#86EFAC',
  				400: '#4ADE80',
  				500: '#22C55E',
  				600: '#16A34A',
  				700: '#15803D',
  				800: '#166534',
  				900: '#14532D',
  			},
  			'darts-gold': {
  				50: '#FEFCE8',
  				100: '#FEF9C3',
  				200: '#FEF08A',
  				300: '#FDE047',
  				400: '#FACC15',
  				500: '#FBBF24',
  				600: '#F59E0B',
  				700: '#D97706',
  				800: '#B45309',
  				900: '#92400E',
  			},
  			'darts-dark': {
  				50: '#F9FAFB',
  				100: '#F3F4F6',
  				200: '#E5E7EB',
  				300: '#D1D5DB',
  				400: '#9CA3AF',
  				500: '#6B7280',
  				600: '#4B5563',
  				700: '#374151',
  				800: '#1F2937',
  				900: '#111827',
  			},
  			'darts-bg': {
  				50: '#F8FAFC',
  				100: '#F1F5F9',
  				200: '#E2E8F0',
  				300: '#CBD5E1',
  				400: '#94A3B8',
  				500: '#64748B',
  				600: '#475569',
  				700: '#334155',
  				800: '#1E293B',
  				900: '#0F172A',
  			},
  		},
  		borderRadius: {
  			sm: 'var(--radius-sm)',
  			DEFAULT: 'var(--radius-base)',
  			md: 'var(--radius-md)',
  			lg: 'var(--radius-lg)',
  			xl: 'var(--radius-xl)'
  		},
  		colors: {
  			/* Brand Colors */
  			brand: {
  				primary: {
  					50: 'var(--brand-primary-50)',
  					100: 'var(--brand-primary-100)',
  					200: 'var(--brand-primary-200)',
  					300: 'var(--brand-primary-300)',
  					400: 'var(--brand-primary-400)',
  					500: 'var(--brand-primary-500)',
  					600: 'var(--brand-primary-600)',
  					700: 'var(--brand-primary-700)',
  					800: 'var(--brand-primary-800)',
  					900: 'var(--brand-primary-900)',
  					950: 'var(--brand-primary-950)',
  					DEFAULT: 'var(--brand-primary-600)'
  				},
  				secondary: {
  					50: 'var(--brand-secondary-50)',
  					100: 'var(--brand-secondary-100)',
  					200: 'var(--brand-secondary-200)',
  					300: 'var(--brand-secondary-300)',
  					400: 'var(--brand-secondary-400)',
  					500: 'var(--brand-secondary-500)',
  					600: 'var(--brand-secondary-600)',
  					700: 'var(--brand-secondary-700)',
  					800: 'var(--brand-secondary-800)',
  					900: 'var(--brand-secondary-900)',
  					950: 'var(--brand-secondary-950)',
  					DEFAULT: 'var(--brand-secondary-500)'
  				},
  				accent: {
  					50: 'var(--brand-accent-50)',
  					100: 'var(--brand-accent-100)',
  					200: 'var(--brand-accent-200)',
  					300: 'var(--brand-accent-300)',
  					400: 'var(--brand-accent-400)',
  					500: 'var(--brand-accent-500)',
  					600: 'var(--brand-accent-600)',
  					700: 'var(--brand-accent-700)',
  					800: 'var(--brand-accent-800)',
  					900: 'var(--brand-accent-900)',
  					950: 'var(--brand-accent-950)',
  					DEFAULT: 'var(--brand-accent-500)'
  				},
  				neutral: {
  					50: 'var(--brand-neutral-50)',
  					100: 'var(--brand-neutral-100)',
  					200: 'var(--brand-neutral-200)',
  					300: 'var(--brand-neutral-300)',
  					400: 'var(--brand-neutral-400)',
  					500: 'var(--brand-neutral-500)',
  					600: 'var(--brand-neutral-600)',
  					700: 'var(--brand-neutral-700)',
  					800: 'var(--brand-neutral-800)',
  					900: 'var(--brand-neutral-900)',
  					950: 'var(--brand-neutral-950)',
  					DEFAULT: 'var(--brand-neutral-600)'
  				},
  				success: 'var(--brand-success)',
  				warning: 'var(--brand-warning)', 
  				error: 'var(--brand-error)',
  				info: 'var(--brand-info)'
  			},
  			
  			/* Semantic Colors */
  			background: 'var(--background)',
  			foreground: 'var(--foreground)',
  			card: {
  				DEFAULT: 'var(--card)',
  				foreground: 'var(--card-foreground)'
  			},
  			surface: {
  				DEFAULT: 'var(--surface)',
  				foreground: 'var(--surface-foreground)'
  			},
  			primary: {
  				DEFAULT: 'var(--primary)',
  				foreground: 'var(--primary-foreground)'
  			},
  			secondary: {
  				DEFAULT: 'var(--secondary)',
  				foreground: 'var(--secondary-foreground)'
  			},
  			accent: {
  				DEFAULT: 'var(--accent)',
  				foreground: 'var(--accent-foreground)'
  			},
  			muted: {
  				DEFAULT: 'var(--muted)',
  				foreground: 'var(--muted-foreground)'
  			},
  			border: 'var(--border)',
  			input: 'var(--input)',
  			ring: 'var(--ring)'
  		},
  		keyframes: {
  			'accordion-down': {
  				from: {
  					height: '0'
  				},
  				to: {
  					height: 'var(--radix-accordion-content-height)'
  				}
  			},
  			'accordion-up': {
  				from: {
  					height: 'var(--radix-accordion-content-height)'
  				},
  				to: {
  					height: '0'
  				}
  			},
  			'pulse-slow': {
  				'0%, 100%': { opacity: '1' },
  				'50%': { opacity: '0.7' }
  			},
  			'pulse-fast': {
  				'0%, 100%': { opacity: '1' },
  				'50%': { opacity: '0.5' }
  			},
  			'slide-in': {
  				'0%': { transform: 'translateX(100%)', opacity: '0' },
  				'100%': { transform: 'translateX(0)', opacity: '1' }
  			},
  			'glow': {
  				'0%, 100%': { boxShadow: '0 0 20px rgba(251, 191, 36, 0.5)' },
  				'50%': { boxShadow: '0 0 40px rgba(251, 191, 36, 0.8)' }
  			}
  		},
  		animation: {
  			'accordion-down': 'accordion-down 0.2s ease-out',
  			'accordion-up': 'accordion-up 0.2s ease-out',
  			'pulse-slow': 'pulse-slow 2s ease-in-out infinite',
  			'pulse-fast': 'pulse-fast 1s ease-in-out infinite',
  			'slide-in': 'slide-in 0.3s ease-out',
  			'glow': 'glow 1.5s ease-in-out infinite'
  		}
  	}
  },
  plugins: [require("tailwindcss-animate")],
};