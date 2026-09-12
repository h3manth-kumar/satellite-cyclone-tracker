/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'void-black': '#0e1012',
        'deep-charcoal': '#15171b',
        'gunmetal': '#1c1f24',
        'graphite': '#23262d',
        'steel': '#333943',
        'pewter': '#444d5a',
        'slate': '#566171',
        'ash': '#8b96aa',
        'fog': '#a0aaba',
        'silver': '#bbc2ce',
        'cloud': '#d5dae2',
        'signal-blue': '#007afc',
        'deep-signal': '#0062ca',
        'map-green': '#228a56',
        'imd-dep': '#3b82f6',
        'imd-dd': '#06b6d4',
        'imd-cs': '#eab308',
        'imd-scs': '#f97316',
        'imd-vscs': '#ef4444',
        'imd-escs': '#dc2626',
        'imd-sucs': '#a855f7'
      },
      borderRadius: {
        'cards': '24px',
        'chips': '12px',
        'badges': '4px',
        'inputs': '6px',
        'buttons': '100px',
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'DM Sans', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
