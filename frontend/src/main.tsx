import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './estilos.css'; // del skill ui-ux-experto (assets/estilos.css)

// El único `!` aceptado: #root existe siempre en index.html.
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
