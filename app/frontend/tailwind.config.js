/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'pe-primary': '#319795',
        'pe-light': '#4db3b1',
        'pe-dark': '#277674',
        'pe-teal': '#319795',
        'pe-gray-50': '#f9fafb',
        'pe-gray-100': '#f3f4f6',
        'pe-gray-200': '#e5e7eb',
        'pe-gray-700': '#374151',
        'pe-gray-900': '#111827',
      },
      borderRadius: {
        sm: '4px',
        DEFAULT: '6px',
        md: '6px',
        lg: '8px',
        xl: '12px',
        '2xl': '16px',
      },
      fontFamily: {
        'sans': ['var(--font-roboto)', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
