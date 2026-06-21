import { useState, useEffect, useCallback } from 'react';
import { getSettings, updateSettings } from '../api/client';
import type { Settings } from '../types/settings';

interface UseSettingsReturn {
  settings: Settings | null;
  isLoading: boolean;
  isSaving: boolean;
  saveSettings: (partial: Partial<Settings>) => Promise<void>;
  error: string | null;
}

export function useSettings(): UseSettingsReturn {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSettings()
      .then(setSettings)
      .catch(err => setError(err.message))
      .finally(() => setIsLoading(false));
  }, []);

  const saveSettings = useCallback(async (partial: Partial<Settings>) => {
    setIsSaving(true);
    setError(null);
    try {
      const updated = await updateSettings(partial);
      setSettings(updated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save settings');
    } finally {
      setIsSaving(false);
    }
  }, []);

  return { settings, isLoading, isSaving, saveSettings, error };
}
