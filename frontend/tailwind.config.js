/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef4ff',
          100: '#dbe6ff',
          200: '#b8cdff',
          300: '#8babff',
          400: '#5c82ff',
          500: '#3861f5',
          600: '#2846d6',
          700: '#2138ab',
          800: '#1f3187',
          900: '#1e2d6b',
        },
      },
    },
  },
  plugins: [],
}
