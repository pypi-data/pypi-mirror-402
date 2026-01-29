import React from 'react';
import ReactDOM from 'react-dom/client';
import { MantineProvider } from '@mantine/core';
import App from './App';

// Mantine core styles
import '@mantine/core/styles.css';

// Lumentor fonts
import '@fontsource/playfair-display/600.css';
import '@fontsource/playfair-display/700.css';
import '@fontsource/playfair-display/900.css';
import '@fontsource/ibm-plex-sans/400.css';
import '@fontsource/ibm-plex-sans/500.css';
import '@fontsource/ibm-plex-sans/600.css';
import '@fontsource/fira-code/400.css';
import '@fontsource/fira-code/500.css';

// Lumentor design system
import { lumentorTheme } from './rag/theme/lumentor';
import './rag/styles/global.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <MantineProvider theme={lumentorTheme} defaultColorScheme="dark">
      <App />
    </MantineProvider>
  </React.StrictMode>
);
