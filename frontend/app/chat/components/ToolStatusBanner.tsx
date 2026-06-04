"use client";

import { ToolStatus } from "@/hooks/useHeillChat";

const TOOL_LABELS: Record<string, string> = {
  find_sport_activities: "Searching sport activities",
  search_flights: "Searching flights",
  search_accommodation: "Searching accommodation",
  web_search: "Searching the web",
  browse_page: "Browsing page",
  get_exchange_rate: "Fetching exchange rates",
};

interface Props {
  statuses: ToolStatus[];
}

export function ToolStatusBanner({ statuses }: Props) {
  const active = statuses.filter((s) => s.status === "running");
  if (active.length === 0) return null;

  return (
    <div className="mx-4 mb-2 flex flex-wrap gap-2">
      {active.map((s) => (
        <div
          key={s.id}
          className="flex items-center gap-2 rounded-full bg-heill-50 border border-heill-100 px-3 py-1.5 text-xs text-heill-700"
        >
          <span className="inline-block h-2 w-2 rounded-full bg-heill-500 animate-pulse" />
          {TOOL_LABELS[s.tool] ?? s.tool}…
        </div>
      ))}
    </div>
  );
}
