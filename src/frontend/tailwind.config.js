/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        nare: {
          bg: '#f7f0e1',
          panel: '#ffffff',
          ink: '#111827',
          soft: '#64748b',
          line: '#dbe4f2',
          accent: '#2563eb',
        },
      },
      boxShadow: {
        panel: '0 8px 24px rgba(15, 23, 42, 0.08)',
      },
    },
  },
  plugins: [],
}
