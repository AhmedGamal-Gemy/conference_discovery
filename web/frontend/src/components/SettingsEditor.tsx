import { useState, useCallback } from 'react';
import type { Settings } from '../types/settings';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';
import { ChevronDown, Plus, X } from 'lucide-react';

// ── Props ──────────────────────────────────────────────────────────

interface SettingsEditorProps {
  settings: Settings;
  onSave: (partial: Partial<Settings>) => void;
  isSaving: boolean;
}

// ── Helpers ────────────────────────────────────────────────────────

function computeDiff(original: Settings, current: Settings): Partial<Settings> {
  const diff: Partial<Settings> = {};
  const keys = Object.keys(original) as (keyof Settings)[];
  for (const key of keys) {
    if (JSON.stringify(original[key]) !== JSON.stringify(current[key])) {
      (diff as Record<string, unknown>)[key] = (current as unknown as Record<string, unknown>)[key];
    }
  }
  return diff;
}

function setNestedValue(obj: Settings, path: string, value: unknown): Settings {
  const copy: Record<string, unknown> = JSON.parse(JSON.stringify(obj));
  const parts = path.split('.');
  let target = copy;
  for (let i = 0; i < parts.length - 1; i++) {
    target = target[parts[i]] as Record<string, unknown>;
  }
  target[parts[parts.length - 1]] = value;
  return copy as unknown as Settings;
}

// ── Section component ──────────────────────────────────────────────

function Section({
  id,
  label,
  isExpanded,
  onToggle,
  children,
}: {
  id: string;
  label: string;
  isExpanded: boolean;
  onToggle: (id: string) => void;
  children: React.ReactNode;
}) {
  return (
    <div
      data-testid={`section-${id}`}
      className="rounded-lg border border-border bg-card"
    >
      <button
        type="button"
        onClick={() => onToggle(id)}
        className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-semibold text-card-foreground transition-colors hover:bg-muted/50"
      >
        {label}
        <ChevronDown
          className={cn(
            'size-4 text-muted-foreground transition-transform duration-200',
            isExpanded && 'rotate-180',
          )}
        />
      </button>
      {isExpanded && <div className="space-y-3 border-t border-border px-4 py-3">{children}</div>}
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────

export default function SettingsEditor({ settings, onSave, isSaving }: SettingsEditorProps) {
  const [form, setForm] = useState<Settings>(() => JSON.parse(JSON.stringify(settings)));

  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    () => new Set(['discovery']),
  );

  const handleFieldChange = useCallback((path: string, value: unknown) => {
    setForm((prev) => setNestedValue(prev, path, value));
  }, []);

  const toggleSection = useCallback((id: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const [topicRows, setTopicRows] = useState<
    Array<{ id: string; slug: string; displayName: string }>
  >(
    () =>
      Object.entries(settings.topics).map(([slug, displayName], i) => ({
        id: `tr-${i}`,
        slug,
        displayName,
      })),
  );

  const updateTopicRow = useCallback(
    (rowId: string, field: 'slug' | 'displayName', value: string) => {
      setTopicRows((prev) => {
        const next = prev.map((r) => (r.id === rowId ? { ...r, [field]: value } : r));
        const record: Record<string, string> = {};
        for (const r of next) {
          if (r.slug) record[r.slug] = r.displayName;
        }
        handleFieldChange('topics', record);
        return next;
      });
    },
    [handleFieldChange],
  );

  const removeTopicRow = useCallback(
    (rowId: string) => {
      setTopicRows((prev) => {
        const next = prev.filter((r) => r.id !== rowId);
        const record: Record<string, string> = {};
        for (const r of next) {
          if (r.slug) record[r.slug] = r.displayName;
        }
        handleFieldChange('topics', record);
        return next;
      });
    },
    [handleFieldChange],
  );

  const addTopicRow = useCallback(() => {
    const id = `tr-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
    setTopicRows((prev) => [...prev, { id, slug: '', displayName: '' }]);
  }, []);

  const handleSave = useCallback(() => {
    const changed = computeDiff(settings, form);
    if (Object.keys(changed).length > 0) {
      onSave(changed);
    }
  }, [settings, form, onSave]);

  // ── Field renderers ──────────────────────────────────────────────

  const renderInputField = (
    label: string,
    testId: string,
    value: string | number,
    onChange: (value: string) => void,
    inputType: 'text' | 'number' = 'text',
    extra?: { min?: number; max?: number; step?: number },
  ) => (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={testId}>{label}</Label>
      <Input
        id={testId}
        data-testid={testId}
        type={inputType}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        {...extra}
      />
    </div>
  );

  const renderSwitchField = (
    label: string,
    testId: string,
    checked: boolean,
    onChange: (checked: boolean) => void,
  ) => (
    <div className="flex items-center justify-between">
      <Label htmlFor={testId}>{label}</Label>
      <Switch
        id={testId}
        data-testid={testId}
        checked={checked}
        onCheckedChange={onChange}
      />
    </div>
  );

  const numberOnChange = (setter: (v: number) => void) => (raw: string) => {
    const parsed = Number(raw);
    if (!Number.isNaN(parsed)) setter(parsed);
  };

  // ── Render ───────────────────────────────────────────────────────

  return (
    <div data-testid="settings-editor" className="space-y-4">
      {/* Discovery */}
      <Section
        id="discovery"
        label="Discovery"
        isExpanded={expandedSections.has('discovery')}
        onToggle={toggleSection}
      >
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="input-discovery-topic">Topic</Label>
          <select
            id="input-discovery-topic"
            data-testid="input-discovery-topic"
            value={form.discovery.topic}
            onChange={(e) => handleFieldChange('discovery.topic', e.target.value)}
            className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
          >
            {!settings.topics[form.discovery.topic] && (
              <option value={form.discovery.topic} disabled>
                Custom: {form.discovery.topic}
              </option>
            )}
            {Object.entries(settings.topics).map(([slug, label]) => (
              <option key={slug} value={slug}>
                {label}
              </option>
            ))}
          </select>
        </div>
        {renderSwitchField('Use Exa search', 'input-discovery-sources-exa', form.discovery.sources.exa, (v) =>
          handleFieldChange('discovery.sources.exa', v),
        )}
        {renderSwitchField('Use directories', 'input-discovery-sources-directories', form.discovery.sources.directories, (v) =>
          handleFieldChange('discovery.sources.directories', v),
        )}
        {renderSwitchField('Use org websites', 'input-discovery-sources-org_websites', form.discovery.sources.org_websites, (v) =>
          handleFieldChange('discovery.sources.org_websites', v),
        )}
        {renderInputField('Months ahead', 'input-discovery-months_ahead', form.discovery.months_ahead, numberOnChange((v) => handleFieldChange('discovery.months_ahead', v)), 'number')}
      </Section>

      {/* Topics */}
      <Section
        id="topics"
        label="Topics"
        isExpanded={expandedSections.has('topics')}
        onToggle={toggleSection}
      >
        <div className="space-y-2">
          {topicRows.map((row) => {
            const allSlugs = topicRows.map((r) => r.slug);
            const dupCount = allSlugs.filter((s) => s === row.slug).length;
            let slugError: string | null = null;
            if (row.slug) {
              if (row.slug !== row.slug.toLowerCase()) slugError = 'Must be lowercase';
              else if (!/^[a-z0-9_]+$/.test(row.slug))
                slugError = 'Only letters, numbers, and underscores allowed';
              else if (dupCount > 1) slugError = 'Duplicate slug';
            }
            return (
              <div key={row.id} className="flex items-start gap-2">
                <div className="flex-1">
                  <Input
                    value={row.slug}
                    onChange={(e) => updateTopicRow(row.id, 'slug', e.target.value)}
                    placeholder="slug"
                    className="font-mono"
                  />
                  {slugError && (
                    <p className="mt-0.5 text-xs text-red-500">{slugError}</p>
                  )}
                </div>
                <div className="flex-1">
                  <Input
                    value={row.displayName}
                    onChange={(e) => updateTopicRow(row.id, 'displayName', e.target.value)}
                    placeholder="Display name"
                  />
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => removeTopicRow(row.id)}
                  className="mt-0 shrink-0"
                  aria-label={`Remove ${row.displayName || 'topic'}`}
                >
                  <X className="size-4" />
                </Button>
              </div>
            );
          })}
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={addTopicRow}
          disabled={topicRows.filter((r) => !r.slug && !r.displayName).length >= 3}
          className="mt-2"
        >
          <Plus className="mr-1 size-4" /> Add Topic
        </Button>
      </Section>

      {/* Exa */}
      <Section
        id="exa"
        label="Exa"
        isExpanded={expandedSections.has('exa')}
        onToggle={toggleSection}
      >
        {renderInputField('Num results', 'input-exa-num_results', form.exa.num_results, numberOnChange((v) => handleFieldChange('exa.num_results', v)), 'number')}
        {renderInputField('Pages per query', 'input-exa-pages_per_query', form.exa.pages_per_query, numberOnChange((v) => handleFieldChange('exa.pages_per_query', v)), 'number')}
      </Section>

      {/* Validation */}
      <Section
        id="validation"
        label="Validation"
        isExpanded={expandedSections.has('validation')}
        onToggle={toggleSection}
      >
        {renderInputField('Min speakers', 'input-validation-min_speakers', form.validation.min_speakers, numberOnChange((v) => handleFieldChange('validation.min_speakers', v)), 'number')}
        {renderInputField('Min non-local', 'input-validation-min_non_local', form.validation.min_non_local, numberOnChange((v) => handleFieldChange('validation.min_non_local', v)), 'number')}
        {renderInputField('Min travel hours', 'input-validation-min_travel_hours', form.validation.min_travel_hours, numberOnChange((v) => handleFieldChange('validation.min_travel_hours', v)), 'number')}
        {renderInputField('Date window (min days)', 'input-validation-date_window-min_days', form.validation.date_window.min_days, numberOnChange((v) => handleFieldChange('validation.date_window.min_days', v)), 'number')}
        {renderInputField('Date window (max days)', 'input-validation-date_window-max_days', form.validation.date_window.max_days, numberOnChange((v) => handleFieldChange('validation.date_window.max_days', v)), 'number')}
      </Section>

      {/* Output */}
      <Section
        id="output"
        label="Output"
        isExpanded={expandedSections.has('output')}
        onToggle={toggleSection}
      >
        {renderInputField('Excel path', 'input-output-excel_path', form.output.excel_path, (v) =>
          handleFieldChange('output.excel_path', v),
        )}
        {renderInputField('Notify email', 'input-output-notify_email', form.output.notify_email, (v) =>
          handleFieldChange('output.notify_email', v),
        )}
      </Section>

      {/* LLM */}
      <Section
        id="llm"
        label="LLM"
        isExpanded={expandedSections.has('llm')}
        onToggle={toggleSection}
      >
        <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          Orchestrator
        </div>
        {renderInputField('Model', 'input-llm-orchestrator-model', form.llm.orchestrator.model, (v) =>
          handleFieldChange('llm.orchestrator.model', v),
        )}
        {renderInputField('Temperature', 'input-llm-orchestrator-temperature', form.llm.orchestrator.temperature, numberOnChange((v) => handleFieldChange('llm.orchestrator.temperature', v)), 'number', { min: 0, max: 1, step: 0.1 })}

        <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          Extraction
        </div>
        {renderInputField('Model', 'input-llm-extraction-model', form.llm.extraction.model, (v) =>
          handleFieldChange('llm.extraction.model', v),
        )}
        {renderInputField('Temperature', 'input-llm-extraction-temperature', form.llm.extraction.temperature, numberOnChange((v) => handleFieldChange('llm.extraction.temperature', v)), 'number', { min: 0, max: 1, step: 0.1 })}

        <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          Discovery
        </div>
        {renderInputField('Model', 'input-llm-discovery-model', form.llm.discovery.model, (v) =>
          handleFieldChange('llm.discovery.model', v),
        )}
      </Section>

      {/* Infrastructure */}
      <Section
        id="infrastructure"
        label="Infrastructure"
        isExpanded={expandedSections.has('infrastructure')}
        onToggle={toggleSection}
      >
        {renderInputField('Scrapling MCP URL', 'input-infrastructure-scrapling_mcp_url', form.scrapling_mcp_url, (v) =>
          handleFieldChange('scrapling_mcp_url', v),
        )}
        {renderSwitchField('Debug', 'input-infrastructure-debug', form.debug, (v) =>
          handleFieldChange('debug', v),
        )}
      </Section>

      {/* Save */}
      <Button
        data-testid="settings-save"
        onClick={handleSave}
        disabled={isSaving}
        className="w-full"
      >
        {isSaving ? 'Saving...' : 'Save Settings'}
      </Button>
    </div>
  );
}
