import { useState } from 'react';
import type { Conference } from '../types/conference';
import type { ValidationResult } from '../types/pipeline';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { cn } from '@/lib/utils';

// ── Props ──────────────────────────────────────────────────────────

interface ConferenceCardProps {
  conference: Conference | null;
  validation: ValidationResult | null;
  isLoading: boolean;
}

// ── Helpers ────────────────────────────────────────────────────────

/**
 * Formats an ISO date string (e.g. "2026-03-15") to a human-readable
 * form like "March 15". Returns "—" for null/undefined/invalid.
 */
function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '—';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return '—';
    return d.toLocaleDateString('en-US', { month: 'long', day: 'numeric' });
  } catch {
    return '—';
  }
}

/**
 * Formats a date range showing the month once when both dates are in
 * the same month, e.g. "March 15–17, 2026".
 */
function formatDateRange(
  start: string | null | undefined,
  end: string | null | undefined,
): string {
  if (!start && !end) return 'TBA';

  try {
    const s = start ? new Date(start) : null;
    const e = end ? new Date(end) : null;

    if (s && isNaN(s.getTime())) return 'TBA';
    if (e && isNaN(e.getTime())) return formatDate(start);
    if (!s && e) return formatDate(end);

    if (s && !e) return formatDate(start);

    // Both exist and are valid
    const sMonth = s!.toLocaleDateString('en-US', { month: 'long' });
    const eMonth = e!.toLocaleDateString('en-US', { month: 'long' });
    const sDay = s!.getDate();
    const eDay = e!.getDate();
    const eYear = e!.getFullYear();

    if (sMonth === eMonth) {
      return `${sMonth} ${sDay}–${eDay}, ${eYear}`;
    }

    return `${sMonth} ${sDay} – ${eMonth} ${eDay}, ${eYear}`;
  } catch {
    return 'TBA';
  }
}

// ── Skeleton loader ────────────────────────────────────────────────

function SkeletonBar({ className }: { className?: string }) {
  return (
    <div
      className={cn('animate-pulse rounded-md bg-muted', className)}
    />
  );
}

function CardSkeleton() {
  return (
    <Card data-testid="conference-card" className="w-full">
      <CardContent className="space-y-5 p-6">
        {/* Title + badges row */}
        <div className="flex items-center gap-3">
          <SkeletonBar className="h-6 w-56" />
          <SkeletonBar className="h-5 w-16 rounded-full" />
          <SkeletonBar className="h-5 w-20 rounded-full" />
        </div>

        {/* Details row */}
        <div className="flex flex-wrap gap-3">
          <SkeletonBar className="h-5 w-40" />
          <SkeletonBar className="h-5 w-24" />
          <SkeletonBar className="h-5 w-32" />
        </div>

        {/* Venue section */}
        <div className="space-y-2">
          <SkeletonBar className="h-4 w-12" />
          <SkeletonBar className="h-5 w-64" />
          <SkeletonBar className="h-4 w-48" />
        </div>

        {/* Speakers section */}
        <div className="space-y-2">
          <SkeletonBar className="h-4 w-36" />
          <SkeletonBar className="h-4 w-full" />
          <SkeletonBar className="h-4 w-full" />
          <SkeletonBar className="h-4 w-3/4" />
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-3">
          <SkeletonBar className="h-16 rounded-lg" />
          <SkeletonBar className="h-16 rounded-lg" />
          <SkeletonBar className="h-16 rounded-lg" />
        </div>

        {/* Register + link */}
        <SkeletonBar className="h-4 w-48" />
        <SkeletonBar className="h-4 w-64" />
      </CardContent>
    </Card>
  );
}

// ── Sub-components for data state ──────────────────────────────────

function CardEmpty() {
  return (
    <Card data-testid="conference-card" className="w-full">
      <CardContent className="flex flex-col items-center justify-center py-16">
        <svg
          className="mb-4 size-12 text-muted-foreground/40"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M6 6h15M6 12h15M6 18h15M3 6h.01M3 12h.01M3 18h.01"
          />
        </svg>
        <p className="text-center text-sm text-muted-foreground">
          Run a pipeline to see conference data
        </p>
      </CardContent>
    </Card>
  );
}

// ── Sub-components for data state ──────────────────────────────────

function StatCard({
  label,
  value,
}: {
  label: string;
  value: number | string;
}) {
  return (
    <div className="flex flex-col items-center gap-0.5 rounded-lg border bg-muted/30 px-3 py-2.5">
      <span className="text-xl font-bold tabular-nums leading-none text-foreground">
        {value}
      </span>
      <span className="text-xs text-muted-foreground">{label}</span>
    </div>
  );
}

// ── Data card ──────────────────────────────────────────────────────

function CardWithData({ conference, validation }: { conference: Conference; validation?: ValidationResult }) {
  const speakerList = conference.speakers ?? [];
  const [speakersExpanded, setSpeakersExpanded] = useState(false);

  return (
    <Card data-testid="conference-card" className="w-full">
      <CardHeader>
        {/* ── Header row: name + badges ── */}
        <div className="flex flex-wrap items-center gap-2">
          <h2
            data-testid="conference-name"
            className="text-xl font-bold leading-tight tracking-tight text-foreground"
          >
            {conference.conference_name || 'Untitled Conference'}
          </h2>

  {conference.conference_acronym && (
    <Badge variant="secondary" className="shrink-0 text-xs">
      {conference.conference_acronym}
    </Badge>
  )}

  {conference.conference_format && (
    <Badge variant="outline" className="shrink-0 text-xs">
      {conference.conference_format}
    </Badge>
  )}

  {/* ── Sector tags ── */}
  {conference.sector_tags && conference.sector_tags.length > 0 && (
    <div className="flex flex-wrap gap-1">
      {conference.sector_tags.slice(0, 5).map((tag) => (
        <Badge key={tag} variant="secondary" className="text-xs">
          {tag}
        </Badge>
      ))}
    </div>
  )}
        </div>
      </CardHeader>

      <CardContent className="space-y-5">
        {/* ── Details grid ── */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-sm text-muted-foreground">
          <span className="inline-flex items-center gap-1.5">
            <svg
              className="size-3.5 shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
              <line x1="16" y1="2" x2="16" y2="6" />
              <line x1="8" y1="2" x2="8" y2="6" />
              <line x1="3" y1="10" x2="21" y2="10" />
            </svg>
            {formatDateRange(conference.date_start, conference.date_end)}
          </span>

          {conference.industry && (
            <span className="inline-flex items-center gap-1.5">
              <svg
                className="size-3.5 shrink-0"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A2 2 0 013 12V7a4 4 0 014-4z"
                />
              </svg>
              {conference.industry}
            </span>
          )}

          {conference.organizer && (
            <span className="inline-flex items-center gap-1.5">
              <svg
                className="size-3.5 shrink-0"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                />
              </svg>
              {conference.organizer}
            </span>
          )}

          {conference.submission_deadline && (
            <span className="inline-flex items-center gap-1.5">
              <svg
                className="size-3.5 shrink-0"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              Submission:{' '}
              {formatDate(conference.submission_deadline)}
            </span>
          )}
        </div>

        {/* ── Venue section ── */}
        {(conference.venue_name ||
          conference.venue_address ||
          conference.venue_city ||
          conference.venue_country) && (
          <div className="space-y-1.5">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Venue
            </h4>
            <div className="flex items-start gap-2">
              <svg
                className="mt-0.5 size-4 shrink-0 text-muted-foreground"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              <div className="min-w-0 flex-1 text-sm">
                {conference.venue_name && (
                  <p className="font-medium text-foreground">
                    {conference.venue_name}
                  </p>
                )}
                {(conference.venue_address ||
                  conference.venue_city ||
                  conference.venue_country) && (
                  <p className="text-muted-foreground">
                    {[conference.venue_address, conference.venue_city, conference.venue_country]
                      .filter(Boolean)
                      .join(', ')}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── Speakers section ── */}
        {speakerList.length > 0 && (
          <div className="space-y-2">
            {/* ── Collapsible header ── */}
            <button
              type="button"
              onClick={() => setSpeakersExpanded(!speakersExpanded)}
              className="flex w-full items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground hover:text-foreground transition-colors"
            >
              <svg
                className="size-3.5 shrink-0"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
              <span data-testid="speaker-count" className="flex-1 text-left">
                {speakerList.length} speaker
                {speakerList.length !== 1 ? 's' : ''} confirmed
              </span>
              <svg
                className={cn(
                  'size-4 transition-transform',
                  speakersExpanded && 'rotate-180',
                )}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {/* ── Summary line (collapsed) ── */}
            {!speakersExpanded && (
              <p className="text-sm text-muted-foreground leading-relaxed">
                {speakerList.slice(0, 5).map((s) => s.name).join(', ')}
                {speakerList.length > 5 && `, and ${speakerList.length - 5} more`}
              </p>
            )}

            {/* ── Full list (expanded) ── */}
            {speakersExpanded && (
              <div className="max-h-80 overflow-y-auto rounded-lg border bg-muted/20">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-muted/80 backdrop-blur">
                    <tr className="text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      <th className="px-3 py-2">Name</th>
                      <th className="px-3 py-2 hidden sm:table-cell">Title / Affiliation</th>
                      <th className="px-3 py-2 w-20">Origin</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {speakerList.map((speaker, idx) => (
                      <tr key={idx} className="hover:bg-muted/40">
                        <td className="px-3 py-2 font-medium text-foreground">
                          {speaker.name}
                        </td>
                        <td className="px-3 py-2 text-muted-foreground hidden sm:table-cell">
                          {[speaker.title, speaker.affiliation].filter(Boolean).join(', ') || '—'}
                        </td>
                        <td className="px-3 py-2">
                          {speaker.country === 'USA' && (
                            <Badge variant="outline" className="text-[10px] px-1.5 py-0">US</Badge>
                          )}
                          {speaker.country && speaker.country !== 'USA' && (
                            <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                              {speaker.country}
                            </Badge>
                          )}
                          {!speaker.country && (
                            <span className="text-xs text-muted-foreground">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ── Stats row ── */}
        <div className="grid grid-cols-3 gap-3">
          <StatCard
            label="Total speakers"
            value={conference.total_speakers}
          />
          <StatCard
            label="Non-local"
            value={speakerList.some((s) => s.is_local != null) ? conference.non_local_count : '—'}
          />
          <StatCard
            label="Non-USA"
            value={conference.non_usa_count}
          />
        </div>

{/* ── Registration ── */}
<div className="flex flex-col gap-1.5 text-sm">
  <div className="flex items-center gap-2">
    <svg
      className="size-4 shrink-0 text-muted-foreground"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
    <span className="text-muted-foreground">Covers accommodation:</span>
    <span
      className={cn(
        'font-medium',
        conference.covers_accommodation
          ? 'text-green-600 dark:text-green-400'
          : 'text-muted-foreground',
      )}
    >
      {conference.covers_accommodation ? 'Yes' : 'No'}
    </span>
  </div>

  {conference.fee_range_usd && (
    <div className="flex items-center gap-2 text-muted-foreground">
      <svg
        className="size-4 shrink-0"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <span>Fees: {conference.fee_range_usd}</span>
    </div>
  )}

  {conference.early_bird_deadline && (
    <div className="flex items-center gap-2 text-muted-foreground">
      <svg
        className="size-4 shrink-0"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <span>Early bird: {formatDate(conference.early_bird_deadline)}</span>
    </div>
  )}
</div>

        {/* ── Website link ── */}
        {conference.website_url && (
          <div className="flex items-center gap-2 text-sm">
            <svg
              className="size-4 shrink-0 text-muted-foreground"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
              />
            </svg>
            <a
              data-testid="website-url"
              href={conference.website_url}
              target="_blank"
              rel="noopener noreferrer"
              className="truncate text-blue-600 underline-offset-2 hover:underline dark:text-blue-400"
            >
              {conference.website_url}
            </a>
          </div>
        )}

         {/* ── Validation result ── */}
         {validation && (
           <ValidationResults validation={validation} />
         )}
      </CardContent>
    </Card>
  );
}

// ── Validation rules definition ────────────────────────────────────

const VALIDATION_RULES = [
  { id: 1, name: 'Speakers confirmed for this edition' },
  { id: 2, name: 'At least one speaker found' },
  { id: 3, name: 'At least 5 scientific speakers' },
  { id: 4, name: 'Venue name exists' },
  { id: 5, name: 'Venue address exists' },
  { id: 6, name: 'Venue is not a hotel' },
  { id: 7, name: 'Conference does not cover accommodation' },
  { id: 8, name: 'Conference date found' },
  { id: 9, name: 'Date is not too soon (≥30 days away)' },
  { id: 10, name: 'Enough non-USA speakers' },
  { id: 11, name: 'Enough non-local speakers' },
  { id: 12, name: 'Not sent before (deduplication)' },
] as const;

type RuleState = 'passed' | 'failed' | 'not_checked';

function getRuleStates(validation: ValidationResult): RuleState[] {
  if (validation.passed) {
    return VALIDATION_RULES.map(() => 'passed');
  }
  const failedAt = validation.failed_condition ?? 0;
  return VALIDATION_RULES.map((rule) => {
    if (rule.id < failedAt) return 'passed';
    if (rule.id === failedAt) return 'failed';
    return 'not_checked';
  });
}

function getDateBucketLabel(bucket: ValidationResult['date_bucket']) {
  switch (bucket) {
    case 'now':   return 'Within 90 days';
    case 'future': return 'Beyond 90 days';
    case 'reject': return 'Rejected';
  }
}

function getDateBucketIcon(bucket: ValidationResult['date_bucket']) {
  switch (bucket) {
    case 'now':
      return (
        <svg className="size-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    case 'future':
      return (
        <svg className="size-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      );
    case 'reject':
      return (
        <svg className="size-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      );
  }
}

// ── Rule state icon ──────────────────────────────────────────────

function RuleIcon({ state }: { state: RuleState }) {
  if (state === 'passed') {
    return (
      <svg viewBox="0 0 16 16" className="size-4 shrink-0 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="3 8 7 12 13 4" />
      </svg>
    );
  }
  if (state === 'failed') {
    return (
      <svg viewBox="0 0 16 16" className="size-4 shrink-0 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="8" cy="8" r="6" />
        <line x1="5.5" y1="5.5" x2="10.5" y2="10.5" />
        <line x1="10.5" y1="5.5" x2="5.5" y2="10.5" />
      </svg>
    );
  }
  // not_checked
  return (
    <svg viewBox="0 0 16 16" className="size-4 shrink-0 text-muted-foreground/40" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="8" cy="8" r="6" />
      <line x1="8" y1="5" x2="8" y2="11" strokeDasharray="2 2" />
    </svg>
  );
}

// ── Validation results (replaces ValidationBadge) ────────────────

export function ValidationResults({ validation }: { validation: ValidationResult }) {
  const [expanded, setExpanded] = useState(false);
  const states = getRuleStates(validation);
  const passedCount = states.filter((s) => s === 'passed').length;
  const totalRules = VALIDATION_RULES.length;
  const failedAt = validation.failed_condition;

  // Summary text
  const summaryText = validation.passed
    ? 'Passed all 12 rules'
    : `Failed rule ${failedAt} of ${totalRules}`;

  // Date bucket styling
  const bucketVariant: 'secondary' | 'outline' | 'destructive' =
    validation.date_bucket === 'reject' ? 'destructive'
    : validation.date_bucket === 'now' ? 'secondary'
    : 'outline';

  return (
    <div
      className={cn(
        'rounded-lg border overflow-hidden',
        validation.passed
          ? 'border-green-500/30 bg-green-50/50 dark:bg-green-950/20'
          : 'border-red-500/30 bg-red-50/50 dark:bg-red-950/20',
      )}
      data-testid="validation-results"
    >
      {/* ── Summary header (always visible) ── */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className={cn(
          'flex w-full items-center gap-2.5 px-3 py-2.5 text-sm transition-colors',
          'hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
          validation.passed
            ? 'text-green-700 dark:text-green-400'
            : 'text-red-700 dark:text-red-400',
        )}
        aria-expanded={expanded}
        aria-controls="validation-rules-table"
      >
        {/* Status icon */}
        {validation.passed ? (
          <svg viewBox="0 0 16 16" className="size-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="3 8 7 12 13 4" />
          </svg>
        ) : (
          <svg viewBox="0 0 16 16" className="size-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="8" cy="8" r="6" />
            <line x1="5.5" y1="5.5" x2="10.5" y2="10.5" />
            <line x1="10.5" y1="5.5" x2="5.5" y2="10.5" />
          </svg>
        )}

        {/* Summary text */}
        <span className="font-semibold flex-1 text-left">{summaryText}</span>

        {/* Count badge */}
        <Badge
          variant={validation.passed ? 'secondary' : 'outline'}
          className={cn(
            'text-[10px] px-1.5 py-0 font-mono tabular-nums shrink-0',
            validation.passed
              ? 'border-green-500/40 text-green-700 dark:text-green-400'
              : 'border-red-500/40 text-red-700 dark:text-red-400',
          )}
        >
          {passedCount}/{totalRules}
        </Badge>

        {/* Date bucket */}
        <Badge variant={bucketVariant} className="text-[10px] px-1.5 py-0 shrink-0 inline-flex items-center gap-1">
          {getDateBucketIcon(validation.date_bucket)}
          {getDateBucketLabel(validation.date_bucket)}
        </Badge>

        {/* Expand chevron */}
        <svg
          className={cn(
            'size-4 shrink-0 transition-transform duration-200 text-muted-foreground',
            expanded && 'rotate-180',
          )}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* ── Collapsible rules table ── */}
      <div
        id="validation-rules-table"
        className={cn(
          'grid transition-all duration-300 ease-in-out',
          expanded ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0',
        )}
      >
        <div className="overflow-hidden">
          <div className="border-t border-border/50">
            <table className="w-full text-sm" role="table" aria-label="Validation rule details">
              <tbody className="divide-y divide-border/30">
                {VALIDATION_RULES.map((rule, idx) => {
                  const state = states[idx];
                  const isFailedRule = state === 'failed';

                  return (
                    <tr
                      key={rule.id}
                      className={cn(
                        'transition-colors',
                        isFailedRule
                          ? 'bg-red-50/60 dark:bg-red-950/30'
                          : state === 'not_checked'
                            ? 'bg-muted/20 opacity-50'
                            : 'hover:bg-muted/30',
                      )}
                    >
                      {/* Rule number */}
                      <td className="px-3 py-1.5 w-10">
                        <Badge variant="outline" className="text-[10px] px-1.5 py-0 font-mono tabular-nums">
                          {rule.id}
                        </Badge>
                      </td>

                      {/* Rule name */}
                      <td className={cn(
                        'px-3 py-1.5 font-medium',
                        state === 'not_checked'
                          ? 'text-muted-foreground/60'
                          : 'text-foreground',
                      )}>
                        {rule.name}
                      </td>

                      {/* State icon + label */}
                      <td className="px-3 py-1.5 w-28">
                        <span className="inline-flex items-center gap-1.5">
                          <RuleIcon state={state} />
                          <span className={cn(
                            'text-xs font-medium',
                            state === 'passed' && 'text-green-600 dark:text-green-400',
                            state === 'failed' && 'text-red-600 dark:text-red-400',
                            state === 'not_checked' && 'text-muted-foreground/60',
                          )}>
                            {state === 'passed' ? 'Passed' : state === 'failed' ? 'Failed' : 'Not checked'}
                          </span>
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {/* ── Rejection reason ── */}
            {!validation.passed && validation.rejection_reason && (
              <div className="px-3 py-2.5 border-t border-border/30 bg-red-50/40 dark:bg-red-950/20">
                <div className="flex items-start gap-2 text-sm">
                  <svg className="mt-0.5 size-4 shrink-0 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                  <p className="text-red-700 dark:text-red-300 leading-relaxed">
                    {validation.rejection_reason}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────

export default function ConferenceCard({
  conference,
  validation,
  isLoading,
}: ConferenceCardProps) {
  if (isLoading) return <CardSkeleton />;
  if (!conference) return <CardEmpty />;
  return <CardWithData conference={conference} validation={validation ?? undefined} />;
}
