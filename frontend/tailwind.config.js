/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f6ff',
          100: '#e0edff',
          200: '#c2dbff',
          300: '#94bdff',
          400: '#5c97ff',
          500: '#1c69d4', // Map brand 500 to BMW corporate blue / m-blue-dark
          600: '#0066b1', // Map brand 600 to M-blue-light
          700: '#0653b6', // electric-blue
          800: '#172cb5',
          900: '#192a8f',
          950: '#141c57',
        },
        slateDark: {
          bg: '#000000',       // Pure black canvas
          card: '#1a1a1a',     // Surface card
          cardHover: '#262626',// Surface elevated
          border: '#3c3c3c',   // Hairline border
          text: '#bbbbbb',     // Default body text
          muted: '#7e7e7e',    // Muted/Secondary
        },
        bmw: {
          blueLight: '#0066b1',
          blueDark: '#1c69d4',
          red: '#e22718',
          electric: '#0653b6',
          carbon: '#2b2b2b',
          soft: '#0d0d0d'
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      letterSpacing: {
        'bmw-machined': '1.5px',
        'bmw-display': '-0.5px'
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer': 'shimmer 2s infinite linear',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        }
      }
    },
  },
  plugins: [],
}
