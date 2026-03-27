import { NextRequest, NextResponse } from 'next/server';
import { getAllEmployers, getAllJobs, getAllLocations } from '@/lib/db';

let _cache: null | {
  employers: { slug: string; display_name: string; total_h1b_count: number }[];
  jobs: { slug: string; display_name: string; total_count: number }[];
  locations: { slug: string; city: string; state: string; total_count: number }[];
} = null;

function getSearchData() {
  if (!_cache) {
    _cache = {
      employers: getAllEmployers().map((e) => ({
        slug: e.slug,
        display_name: e.display_name,
        total_h1b_count: e.total_h1b_count,
      })),
      jobs: getAllJobs().map((j) => ({
        slug: j.slug,
        display_name: j.display_name,
        total_count: j.total_count,
      })),
      locations: getAllLocations().map((l) => ({
        slug: l.slug,
        city: l.city,
        state: l.state,
        total_count: l.total_count,
      })),
    };
  }
  return _cache;
}

export function GET(req: NextRequest) {
  const q = req.nextUrl.searchParams.get('q')?.toLowerCase().trim() ?? '';
  if (!q || q.length < 2) {
    return NextResponse.json({ results: [] });
  }

  const data = getSearchData();
  const results: {
    type: 'company' | 'job' | 'location';
    slug: string;
    display_name: string;
    sub?: string;
  }[] = [];

  for (const e of data.employers) {
    if (e.display_name.toLowerCase().includes(q)) {
      results.push({
        type: 'company',
        slug: e.slug,
        display_name: e.display_name,
        sub: `${e.total_h1b_count.toLocaleString()} applications`,
      });
    }
    if (results.filter((r) => r.type === 'company').length >= 5) break;
  }

  for (const j of data.jobs) {
    if (j.display_name.toLowerCase().includes(q)) {
      results.push({
        type: 'job',
        slug: j.slug,
        display_name: j.display_name,
        sub: `${j.total_count.toLocaleString()} records`,
      });
    }
    if (results.filter((r) => r.type === 'job').length >= 5) break;
  }

  for (const l of data.locations) {
    if (
      l.city.toLowerCase().includes(q) ||
      l.state.toLowerCase().includes(q)
    ) {
      results.push({
        type: 'location',
        slug: l.slug,
        display_name: `${l.city}, ${l.state}`,
        sub: `${l.total_count.toLocaleString()} records`,
      });
    }
    if (results.filter((r) => r.type === 'location').length >= 5) break;
  }

  return NextResponse.json({ results: results.slice(0, 12) });
}
