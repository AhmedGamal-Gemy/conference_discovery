import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useSettings } from '../hooks/useSettings';
import SettingsEditor from '../components/SettingsEditor';

export default function SettingsPage() {
  const { settings, isLoading, isSaving, saveSettings, error } = useSettings();
  const [successMsg, setSuccessMsg] = useState('');
  const [dismissableError, setDismissableError] = useState<string | null>(null);
  const prevSaving = useRef(isSaving);

  // Show success when save completes without error
  useEffect(() => {
    if (prevSaving.current && !isSaving && !error) {
      setSuccessMsg('Settings saved successfully');
      setDismissableError(null);
      const timer = setTimeout(() => setSuccessMsg(''), 3000);
      return () => clearTimeout(timer);
    }
    if (error) {
      setDismissableError(error);
      setSuccessMsg('');
    }
    prevSaving.current = isSaving;
  }, [isSaving, error]);

  if (isLoading) {
    return (
      <div data-testid="settings-page" className="settings-page">
        <nav className="breadcrumb text-sm text-muted-foreground mb-4">
          <Link to="/" className="hover:underline">Home</Link>
          <span className="mx-2">&gt;</span>
          <span>Settings</span>
        </nav>
        <h2 className="text-lg font-semibold mb-4">Settings</h2>
        <div className="animate-pulse space-y-4" data-testid="skeleton-settings">
          <div className="h-8 bg-muted rounded w-1/3"></div>
          <div className="h-32 bg-muted rounded"></div>
          <div className="h-8 bg-muted rounded w-1/4"></div>
          <div className="h-32 bg-muted rounded"></div>
        </div>
      </div>
    );
  }

  if (error && !settings) {
    return (
      <div data-testid="settings-page" className="settings-page">
        <nav className="breadcrumb text-sm text-muted-foreground mb-4">
          <Link to="/" className="hover:underline">Home</Link>
          <span className="mx-2">&gt;</span>
          <span>Settings</span>
        </nav>
        <h2 className="text-lg font-semibold mb-4">Settings</h2>
        <div className="error-banner" data-testid="error-banner">
          <p>Failed to load settings: {error}</p>
        </div>
      </div>
    );
  }

  if (!settings) {
    return (
      <div data-testid="settings-page" className="settings-page">
        <nav className="breadcrumb text-sm text-muted-foreground mb-4">
          <Link to="/" className="hover:underline">Home</Link>
          <span className="mx-2">&gt;</span>
          <span>Settings</span>
        </nav>
        <h2 className="text-lg font-semibold mb-4">Settings</h2>
        <p className="text-muted-foreground">No settings available.</p>
      </div>
    );
  }

  return (
    <div data-testid="settings-page" className="settings-page">
      <nav className="breadcrumb text-sm text-muted-foreground mb-4">
        <Link to="/" className="hover:underline">Home</Link>
        <span className="mx-2">&gt;</span>
        <span>Settings</span>
      </nav>
      <h2 className="text-lg font-semibold mb-4">Settings</h2>
      {successMsg && (
        <div className="success-banner" data-testid="settings-success">
          <p>{successMsg}</p>
        </div>
      )}
      {dismissableError && (
        <div className="error-banner" data-testid="settings-error">
          <p>{dismissableError}</p>
          <button
            className="ml-auto text-sm underline"
            onClick={() => setDismissableError(null)}
          >
            Dismiss
          </button>
        </div>
      )}
      <SettingsEditor
        settings={settings}
        onSave={saveSettings}
        isSaving={isSaving}
      />
    </div>
  );
}
