/** Type definitions matching backend Pydantic models from web/schemas.py */

export interface SubPages {
  speakers?: string | null;
  venue?: string | null;
  registration?: string | null;
}

export interface HomepageData {
  conference_name: string;
  conference_acronym?: string | null;
  date_start?: string | null;
  date_end?: string | null;
  industry?: string | null;
  sector_tags: string[];
  conference_format?: string | null;
  organizer?: string | null;
  submission_deadline?: string | null;
  venue_city?: string | null;
  venue_country?: string | null;
  sub_pages: SubPages;
}

export interface Speaker {
  name: string;
  title?: string | null;
  affiliation?: string | null;
  country?: string | null;
  is_scientific: boolean;
  travel_hours?: number | null;
  is_local?: boolean | null;
  is_usa?: boolean | null;
}

export interface VenueData {
  venue_name?: string | null;
  venue_address?: string | null;
  city?: string | null;
  country?: string | null;
  is_hotel: boolean;
}

export interface RegistrationData {
  covers_accommodation: boolean;
  fee_range_usd?: string | null;
  early_bird_deadline?: string | null;
}

/**
 * Flattened conference model matching ConferenceResponse from web/schemas.py.
 * All optional fields are nullable — missing/null pipeline data produces null
 * in JSON, never validation errors.
 */
export interface Conference {
  conference_id: string;
  conference_name: string;
  conference_acronym?: string | null;
  date_start?: string | null;
  date_end?: string | null;
  industry?: string | null;
  sector_tags: string[];
  conference_format?: string | null;
  organizer?: string | null;
  submission_deadline?: string | null;
  venue_city?: string | null;
  venue_country?: string | null;
  sub_pages?: SubPages | null;
  venue_name?: string | null;
  venue_address?: string | null;
  venue_country_detail?: string | null;
  covers_accommodation: boolean;
  fee_range_usd?: string | null;
  early_bird_deadline?: string | null;
  speakers: Speaker[];
  total_speakers: number;
  non_local_count: number;
  non_usa_count: number;
  website_url?: string | null;
  speakers_page_url?: string | null;
}
