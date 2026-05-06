import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        palermo: {
          pink: '#eb3b81',
          dark: '#0f0f13',
          card: '#18181b',
          bg: '#e5e7eb',
          gray: '#27272a',
        },
        como: {
          blue: '#0047AB',
          white: '#FFFFFF',
          dark: '#0B132B',
        },
        slate: {
          950: '#0a0f1f',
        },
        emerald: {
          950: '#022c22',
        },
      },
      fontFamily: {
        heading: ['var(--font-oswald)', 'sans-serif'],
        body: ['var(--font-inter)', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'grid-pattern': "url('/grid.svg')",
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('tailwindcss-animate'),
  ],
}

export default config
