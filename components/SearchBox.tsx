'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';

interface SearchResult {
  type: 'company' | 'job' | 'location';
  slug: string;
  display_name: string;
  sub?: string;
}

export default function SearchBox({
  placeholder = 'Search companies, job titles, or cities...',
  size = 'lg',
}: {
  placeholder?: string;
  size?: 'sm' | 'lg';
}) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [highlighted, setHighlighted] = useState(-1);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);

  const search = useCallback(async (q: string) => {
    if (!q.trim()) {
      setResults([]);
      setOpen(false);
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(
        `/api/search?q=${encodeURIComponent(q)}`
      );
      const data = await res.json();
      setResults(data.results || []);
      setOpen(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => search(query), 300);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [query, search]);

  function navigate(result: SearchResult) {
    setOpen(false);
    setQuery('');
    switch (result.type) {
      case 'company':
        router.push(`/company/${result.slug}`);
        break;
      case 'job':
        router.push(`/job/${result.slug}`);
        break;
      case 'location':
        router.push(`/location/${result.slug}`);
        break;
    }
  }

  function handleKey(e: React.KeyboardEvent) {
    if (!open || !results.length) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlighted((h) => Math.min(h + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlighted((h) => Math.max(h - 1, 0));
    } else if (e.key === 'Enter' && highlighted >= 0) {
      navigate(results[highlighted]);
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  }

  const typeLabel: Record<SearchResult['type'], string> = {
    company: 'Company',
    job: 'Job Title',
    location: 'City',
  };

  const typeColor: Record<SearchResult['type'], string> = {
    company: 'bg-blue-100 text-blue-700',
    job: 'bg-green-100 text-green-700',
    location: 'bg-purple-100 text-purple-700',
  };

  const inputClass =
    size === 'lg'
      ? 'w-full px-5 py-4 text-base border-2 border-gray-200 rounded-xl focus:outline-none focus:border-blue-500 shadow-sm'
      : 'w-full px-4 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-blue-500';

  return (
    <div className="relative w-full">
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKey}
          onFocus={() => results.length && setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          placeholder={placeholder}
          className={inputClass}
          aria-label="Search"
          autoComplete="off"
        />
        {loading && (
          <div className="absolute right-4 top-1/2 -translate-y-1/2">
            <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>

      {open && results.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-xl shadow-xl max-h-72 overflow-y-auto">
          {results.map((r, i) => (
            <button
              key={`${r.type}-${r.slug}`}
              className={`w-full px-4 py-3 text-left flex items-center gap-3 hover:bg-gray-50 transition-colors ${
                i === highlighted ? 'bg-blue-50' : ''
              }`}
              onMouseDown={() => navigate(r)}
              onMouseEnter={() => setHighlighted(i)}
            >
              <span
                className={`text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap ${typeColor[r.type]}`}
              >
                {typeLabel[r.type]}
              </span>
              <span className="text-gray-900 font-medium">{r.display_name}</span>
              {r.sub && (
                <span className="text-gray-400 text-sm ml-auto">{r.sub}</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
