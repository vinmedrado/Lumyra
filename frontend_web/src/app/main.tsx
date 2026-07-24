import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import { AuthProvider } from '../hooks/useAuth';
import { ThemeProvider } from '../components/providers/ThemeProvider';
import '../styles/global.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider>
      <AuthProvider><App /></AuthProvider>
    </ThemeProvider>
  </React.StrictMode>
);
