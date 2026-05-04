import { AppShell } from './shell/AppShell';
import { AuthCallback } from './auth/AuthCallback';

export default function App() {
  if (window.location.pathname === '/auth/callback') {
    return <AuthCallback />;
  }
  
  return <AppShell />;
}
