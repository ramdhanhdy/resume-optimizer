/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#0274BD',
        'soft-neutral': '#E9E6DD',
        'dark-neutral': '#C4AD9D',
        'text-main': '#1c1c1e',
        accent: '#F57251',
        'background-main': '#FAFAF9',
        'surface-light': '#FFFFFF',
        'surface-dark': '#F5F5F5',
        'border-subtle': '#E5E5E5',
        warning: '#FF9500',
      },
      borderRadius: {
        lg: '8px',
      },
      boxShadow: {
        subtle: '0 1px 3px rgba(0,0,0,0.08)',
      },
      transitionTimingFunction: {
        swift: 'cubic-bezier(0.4, 0.0, 0.2, 1)',
      },
      animation: {
        'pulse-slow': 'pulse-slow 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        'pulse-slow': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' },
        },
      },
    },
  },
  plugins: [],
}
