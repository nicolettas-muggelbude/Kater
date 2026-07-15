// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

// TODO: sobald DNS für kater-adressen.app auf GitHub Pages zeigt und die
// Domain unter Settings > Pages als aktiv bestätigt ist: base entfernen,
// neu bauen und pushen (Custom-Domain-Root braucht keinen base-Pfad mehr).
export default defineConfig({
  site: 'https://nicolettas-muggelbude.github.io/Kater',
  base: '/Kater',
  vite: {
    plugins: [tailwindcss()]
  }
});
