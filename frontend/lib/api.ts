const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API}${path}`, { ...init, headers: { 'Content-Type': 'application/json', ...(init.headers || {}) }, cache: 'no-store' });
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.detail || 'Something went wrong. Please try again.'); }
  return response.json();
}
export type Season = { id?: number; season: string; start_month: number; end_month: number; price_per_person: number; basis?: string; gst_note?: string };
export type Package = { id: number; code: string; slug: string; title: string; destination: string; duration_days: number; summary: string; hero_image: string; itinerary: {day:number;title:string;description:string}[]; inclusions: string[]; hotel_category: string; status: string; published_version?: number; seasons: Season[] };
