/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#3b82f6', // blue-500
          dark: '#1d4ed8',    // blue-700
        },
        secondary: {
          DEFAULT: '#6b7280', // gray-500
          dark: '#374151',    // gray-700
        },
        success: {
          DEFAULT: '#10b981', // emerald-500
          dark: '#047857',    // emerald-700
        },
        danger: {
          DEFAULT: '#ef4444', // red-500
          dark: '#b91c1c',    // red-700
        },
        warning: {
          DEFAULT: '#f59e0b', // amber-500
          dark: '#b45309',    // amber-700
        },
        neutral: {
          DEFAULT: '#6b7280', // gray-500
          dark: '#374151',    // gray-700
        },
      },
    },
  },
  plugins: [],
}