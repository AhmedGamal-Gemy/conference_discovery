import type { Conference } from '../types/conference';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { cn } from '@/lib/utils';

// ── Props ──────────────────────────────────────────────────────────

interface ConferenceCardProps {
  conference: Conference | null;
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

function CardWithData({ conference }: { conference: Conference }) {
  const speakerList = conference.speakers ?? [];
  const visibleSpeakers = speakerList.slice(0, 10);
  const remainingCount = speakerList.length - 10;

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
            <h4 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <svg
                className="size-3.5"
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
              <span data-testid="speaker-count">
                {speakerList.length} speaker
                {speakerList.length !== 1 ? 's' : ''} confirmed
              </span>
            </h4>
            <ul className="space-y-1.5">
              {visibleSpeakers.map((speaker, idx) => (
                <li key={idx} className="text-sm leading-snug">
                  <span className="font-medium text-foreground">
                    {speaker.name}
                  </span>
                  {(speaker.title || speaker.affiliation) && (
                    <span className="text-muted-foreground">
                      {' — '}
                      {[speaker.title, speaker.affiliation]
                        .filter(Boolean)
                        .join(', ')}
                    </span>
                  )}
                </li>
              ))}
            </ul>
            {remainingCount > 0 && (
              <p className="text-sm text-muted-foreground">
                and {remainingCount} more
              </p>
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
            value={conference.non_local_count}
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
      </CardContent>
    </Card>
  );
}

// ── Main component ─────────────────────────────────────────────────

export default function ConferenceCard({
  conference,
  isLoading,
}: ConferenceCardProps) {
  if (isLoading) return <CardSkeleton />;
  if (!conference) return <CardEmpty />;
  return <CardWithData conference={conference} />;
}
