import { Outlet, Link } from 'react-router-dom';
import { useTheme } from './ThemeProvider';
import { Button } from '@/components/ui/button';

export default function Layout() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="app-layout" data-testid="app-layout">
      <header className="app-header">
        <div className="header-left flex items-center gap-4">
          <Link to="/" className="app-title" data-testid="app-title">
            Conference Discovery
          </Link>
          <nav className="flex gap-2 text-sm">
            <Link to="/" className="hover:underline text-muted-foreground">Pipeline</Link>
            <Link to="/discovery" className="hover:underline text-muted-foreground">Discovery</Link>
          </nav>
        </div>
        <div className="header-actions">
          <Link to="/settings" data-testid="settings-link">
            <Button variant="ghost" size="sm">Settings</Button>
          </Link>
          <Button variant="outline" size="sm" onClick={toggleTheme} data-testid="theme-toggle">
            {theme === 'dark' ? 'Light' : 'Dark'}
          </Button>
        </div>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
      <footer className="app-footer">
        <small>Powered by Google ADK + Mistral AI</small>
      </footer>
    </div>
  );
}
