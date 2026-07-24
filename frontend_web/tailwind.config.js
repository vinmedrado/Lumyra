export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#F6F1FF', 100: '#F1ECFF', 200: '#DDD0FF', 300: '#BCA7FF',
          500: '#8B5CF6', 600: '#6D28D9', 700: '#5B21B6', 800: '#4B1D95', 900: '#2B1458'
        },
        gold: { 50: '#FFF8E8', 100: '#F8E7B1', 300: '#E7C978', 500: '#B88937', 600: '#9B6E24' },
        ink: '#181210',
        ice: '#F7F8FB'
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['Playfair Display', 'Georgia', 'serif']
      },
      boxShadow: {
        soft: '0 18px 60px rgba(24, 18, 16, 0.10)',
        glow: '0 0 44px rgba(139, 92, 246, 0.22)',
        gold: '0 18px 50px rgba(184, 137, 55, 0.16)'
      },
      keyframes: {
        fadeUp: { '0%': { opacity: '0', transform: 'translateY(12px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        pulseLive: { '0%, 100%': { opacity: '.65', transform: 'scale(.95)' }, '50%': { opacity: '1', transform: 'scale(1.08)' } }
      },
      animation: { fadeUp: 'fadeUp .5s ease both', pulseLive: 'pulseLive 1.5s ease-in-out infinite' }
    }
  },
  plugins: []
};
