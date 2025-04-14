import type { Config } from 'tailwindcss';
import typography from '@tailwindcss/typography';
import forms from '@tailwindcss/forms';

export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],

	theme: {
		extend: {
			colors: {
				primary: {
					light: '#60a5fa', // blue-400
					DEFAULT: '#3b82f6', // blue-500
					dark: '#2563eb'  // blue-600
				},
				secondary: {
					light: '#f3f4f6', // gray-100
					DEFAULT: '#e5e7eb', // gray-200
					dark: '#d1d5db'  // gray-300
				},
				accent: {
					DEFAULT: '#10b981', // emerald-500
					dark: '#059669' // emerald-600
				},
				// Define specific dark mode colors if needed
				'dark-bg': '#1f2937', // gray-800
				'dark-surface': '#374151', // gray-700
				'dark-text': '#f9fafb', // gray-50
				'dark-text-secondary': '#9ca3af' // gray-400
			}
		}
	},

	plugins: [
		typography,
		forms
	]
} as Config;
