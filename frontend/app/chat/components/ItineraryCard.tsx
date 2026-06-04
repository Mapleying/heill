"use client";

interface Money {
  amount: number;
  currency: string;
}

interface ItineraryOption {
  id: string;
  label: string;
  total_cost: Money;
  flight?: {
    airline: string;
    origin: string;
    destination: string;
    outbound_date: string;
    return_date?: string;
    price: Money;
  };
  accommodation?: {
    name: string;
    location: string;
    price_per_night: Money;
    url?: string;
  };
  activity: {
    provider_name: string;
    sport: string;
    duration_days?: number;
    skill_levels?: string[];
    price_per_person: Money;
    accommodation_included?: boolean;
    url?: string;
  };
  rationale: string;
  sources: string[];
}

interface RecommendationOutput {
  itineraries: ItineraryOption[];
  caveats?: string[];
  follow_up_questions?: string[];
}

interface Props {
  data: RecommendationOutput;
}

function fmt(money: Money) {
  return `${money.currency} ${money.amount.toLocaleString()}`;
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-1">{label}</p>
      {children}
    </div>
  );
}

function OptionCard({ option }: { option: ItineraryOption }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div className="flex items-center justify-between bg-heill-600 px-4 py-3 text-white">
        <span className="font-semibold text-sm">{option.label}</span>
        <span className="text-lg font-bold">{fmt(option.total_cost)}</span>
      </div>

      <div className="divide-y divide-slate-100">
        <div className="grid grid-cols-1 gap-4 p-4 sm:grid-cols-3">
          {/* Activity */}
          <Section label="Activity">
            <p className="font-medium text-sm">{option.activity.provider_name}</p>
            <p className="text-xs text-slate-500 capitalize">{option.activity.sport}</p>
            {option.activity.duration_days && (
              <p className="text-xs text-slate-500">{option.activity.duration_days} days</p>
            )}
            {option.activity.skill_levels && option.activity.skill_levels.length > 0 && (
              <p className="text-xs text-slate-500">{option.activity.skill_levels.join(", ")}</p>
            )}
            <p className="mt-1 text-sm font-semibold text-heill-700">{fmt(option.activity.price_per_person)}</p>
            {option.activity.accommodation_included && (
              <span className="mt-1 inline-block rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">
                Accommodation included
              </span>
            )}
            {option.activity.url && (
              <a href={option.activity.url} target="_blank" rel="noopener noreferrer"
                className="mt-1 block text-xs text-heill-600 hover:underline truncate">
                View details
              </a>
            )}
          </Section>

          {/* Flight */}
          {option.flight && (
            <Section label="Flight">
              <p className="font-medium text-sm">{option.flight.airline}</p>
              <p className="text-xs text-slate-500">
                {option.flight.origin} → {option.flight.destination}
              </p>
              <p className="text-xs text-slate-500">{option.flight.outbound_date}</p>
              {option.flight.return_date && (
                <p className="text-xs text-slate-500">Return: {option.flight.return_date}</p>
              )}
              <p className="mt-1 text-sm font-semibold text-heill-700">{fmt(option.flight.price)}</p>
            </Section>
          )}

          {/* Accommodation */}
          {option.accommodation && (
            <Section label="Hotel">
              <p className="font-medium text-sm">{option.accommodation.name}</p>
              <p className="text-xs text-slate-500">{option.accommodation.location}</p>
              <p className="mt-1 text-sm font-semibold text-heill-700">
                {fmt(option.accommodation.price_per_night)} / night
              </p>
              {option.accommodation.url && (
                <a href={option.accommodation.url} target="_blank" rel="noopener noreferrer"
                  className="mt-1 block text-xs text-heill-600 hover:underline truncate">
                  View hotel
                </a>
              )}
            </Section>
          )}
        </div>

        {/* Rationale */}
        <div className="px-4 py-3 bg-slate-50">
          <p className="text-xs text-slate-600 italic">{option.rationale}</p>
        </div>

        {/* Sources */}
        {option.sources.length > 0 && (
          <div className="px-4 py-2">
            <p className="text-xs text-slate-400">
              Sources:{" "}
              {option.sources.map((src, i) => (
                <span key={i}>
                  <a href={src} target="_blank" rel="noopener noreferrer"
                    className="text-heill-600 hover:underline">
                    [{i + 1}]
                  </a>{" "}
                </span>
              ))}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export function ItineraryCard({ data }: Props) {
  return (
    <div className="w-full max-w-2xl space-y-4">
      {data.itineraries.map((option) => (
        <OptionCard key={option.id} option={option} />
      ))}

      {data.caveats && data.caveats.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
          {data.caveats.map((c, i) => (
            <p key={i} className="text-xs text-amber-700">{c}</p>
          ))}
        </div>
      )}

      {data.follow_up_questions && data.follow_up_questions.length > 0 && (
        <div className="rounded-lg border border-heill-100 bg-heill-50 px-4 py-3">
          <p className="text-xs font-semibold text-heill-700 mb-1">Follow-up</p>
          {data.follow_up_questions.map((q, i) => (
            <p key={i} className="text-xs text-heill-600">{q}</p>
          ))}
        </div>
      )}
    </div>
  );
}
