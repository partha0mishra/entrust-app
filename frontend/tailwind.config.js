/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'encora-green': '#00B74F',
        'encora-dark': '#1a1a1a',
        // Oxford Blue palette
        'oxford': {
          50: '#f1f3f9',
          100: '#d2dbee',
          200: '#b5c3e3',
          300: '#6a88c8',
          400: '#4c70bd',
          500: '#3d5da4',
          600: '#2c4477',
          700: '#213459',
          800: '#182541',
          900: '#0a111e',
        },
        // Encora Yellow
        'encora-yellow': {
          50: '#fafedf',
          100: '#f5febf',
          200: '#effd90',
          300: '#e8fd61',
          400: '#ddfc13',
          500: '#bfda11',
          600: '#85970c',
          700: '#677508',
          800: '#3a4305',
          900: '#2c3203',
        },
        // Encora Red
        'encora-red': {
          50: '#fff0ef',
          100: '#ffd7ce',
          200: '#ffafa0',
          300: '#ff9380',
          400: '#ff7960',
          500: '#ff5031',
          600: '#d7442a',
          700: '#b03822',
          800: '#752517',
          900: '#4e1910',
        },
        // Taupe
        'taupe': {
          50: '#eeece6',
          100: '#e6e1d7',
          200: '#d8d1c1',
          300: '#d0c7b4',
          400: '#c8bda7',
          500: '#a99f8d',
          600: '#8b8274',
          700: '#6b6559',
          800: '#4c4840',
          900: '#2d2b26',
        },
      },
      fontFamily: {
        'schibsted': ['Schibsted Grotesk', 'sans-serif'],
      },
    },
  },
  plugins: [],
}