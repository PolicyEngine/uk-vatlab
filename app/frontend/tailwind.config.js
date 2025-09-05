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
        'obr-teal': '#00c4a7',
        'obr-teal-dark': '#006b58',
        'obr-blue': '#4299e1',
        'obr-blue-dark': '#2c5282',
      },
      borderRadius: {
        none: '0px',
        sm: '0px',
        DEFAULT: '0px',
        md: '0px',
        lg: '0px',
        xl: '0px',
        '2xl': '0px',
        '3xl': '0px',
        full: '0px',
      },
      fontFamily: {
        'sans': ['var(--font-roboto-serif)', 'Georgia', 'serif'],
        'mono': ['var(--font-roboto-mono)', 'monospace'],
      },
    },
  },
  plugins: [],
}
