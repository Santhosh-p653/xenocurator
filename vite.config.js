import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  root: 'app',
  plugins: [react()],
  build: {
    outDir: '../dist', // Outputs the build to project root /dist folder
    emptyOutDir: true
  }
});
