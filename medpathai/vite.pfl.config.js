import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath, URL } from 'node:url'

const projectRoot = fileURLToPath(new URL('.', import.meta.url))
const officerRoot = fileURLToPath(new URL('./officer', import.meta.url))

export default defineConfig({
  root: officerRoot,
  envDir: projectRoot,
  plugins: [react(), tailwindcss()],
  server: {
    port: 5174,
    fs: {
      allow: [projectRoot],
    },
  },
  preview: {
    port: 4174,
  },
  build: {
    outDir: '../dist-pfl',
    emptyOutDir: true,
  },
})
