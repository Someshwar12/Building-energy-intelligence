"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

type Building = {
  building_id: string;
  site_id: string;
  name: string;
  primary_use: string | null;
  square_feet: number | null;
  floor_area: number | null;
  timezone: string | null;
  latitude: number | null;
  longitude: number | null;
  year_built: number | null;
  number_of_floors: number | null;
  occupants: number | null;
  energy_star_score: number | null;
  eui: number | null;
  site_eui: number | null;
  heating_type: string | null;
  leed_level: string | null;
};

export default function Home() {
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    async function loadBuildings() {
      try {
        const response = await fetch(
          "http://127.0.0.1:4000/api/buildings",
        );

        if (!response.ok) {
          throw new Error("Failed to load buildings");
        }

        const data = await response.json();
        setBuildings(data.buildings);
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    }

    loadBuildings();
  }, []);

  return (
    <main className="min-h-screen bg-[#f7f8fa] text-slate-950">
      <div className="flex min-h-screen">
        <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white lg:flex lg:flex-col">
          <div className="flex h-20 items-center border-b border-slate-100 px-7">
            <div>
              <div className="text-sm font-semibold tracking-tight">
                Building Intelligence
              </div>
              <div className="mt-0.5 text-xs text-slate-400">
                Energy operations
              </div>
            </div>
          </div>

          <nav className="flex-1 px-4 py-6">
            <div className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
              Workspace
            </div>

            <div className="rounded-xl bg-slate-950 px-3 py-2.5 text-sm font-medium text-white">
              Overview
            </div>

            <Link
              href="/#buildings"
              className="mt-1 block rounded-xl px-3 py-2.5 text-sm text-slate-500 transition hover:bg-slate-50 hover:text-slate-950"
            >
              Buildings
            </Link>

            <div className="mt-1 rounded-xl px-3 py-2.5 text-sm text-slate-500">
              Consumption
            </div>

            <div className="mt-1 rounded-xl px-3 py-2.5 text-sm text-slate-500">
              Forecasts
            </div>

            <div className="mt-1 rounded-xl px-3 py-2.5 text-sm text-slate-500">
              Anomalies
            </div>
          </nav>

          <div className="border-t border-slate-100 p-5">
            <div className="text-xs text-slate-400">Dataset</div>
            <div className="mt-1 text-sm font-medium text-slate-700">
              BDG2
            </div>
            <div className="mt-0.5 text-xs text-slate-400">
              {loading
                ? "Loading buildings..."
                : `${buildings.length} monitored buildings`}
            </div>
          </div>
        </aside>

        <section className="min-w-0 flex-1">
          <header className="flex h-20 items-center justify-between border-b border-slate-200 bg-white px-5 sm:px-8">
            <div>
              <div className="text-xs font-medium text-slate-400">
                Energy operations
              </div>
              <h1 className="mt-1 text-xl font-semibold tracking-tight">
                Overview
              </h1>
            </div>

            <div className="hidden items-center gap-3 sm:flex">
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-500">
                BDG2 · 2016–2017
              </div>

              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600">
                OP
              </div>
            </div>
          </header>

          <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
            <div>
              <p className="text-sm text-slate-500">
                Portfolio overview
              </p>

              <h2 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">
                Understand what is happening across your buildings.
              </h2>
            </div>

            <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <MetricCard
                label="Monitored buildings"
                value={loading ? "—" : String(buildings.length)}
                detail="Connected to the application"
              />

              <MetricCard
                label="Energy forecast"
                value="—"
                detail="Awaiting live model data"
              />

              <MetricCard
                label="Buildings above expected"
                value="—"
                detail="Awaiting analytical data"
              />

              <MetricCard
                label="Data status"
                value={error ? "Error" : loading ? "Loading" : "Ready"}
                detail="Application data layer"
              />
            </div>

            <section
              id="buildings"
              className="mt-8 rounded-2xl border border-slate-200 bg-white"
            >
              <div className="border-b border-slate-100 px-6 py-5">
                <h3 className="text-sm font-semibold">
                  Monitored buildings
                </h3>

                <p className="mt-1 text-xs text-slate-400">
                  Select a building to investigate its energy behavior.
                </p>
              </div>

              {error ? (
                <div className="px-6 py-12 text-center">
                  <div className="text-sm font-medium text-slate-700">
                    Buildings unavailable
                  </div>

                  <p className="mt-1 text-xs text-slate-400">
                    The application could not retrieve building data.
                  </p>
                </div>
              ) : loading ? (
                <div className="divide-y divide-slate-100">
                  {[1, 2, 3, 4].map((item) => (
                    <div
                      key={item}
                      className="flex animate-pulse items-center justify-between px-6 py-5"
                    >
                      <div>
                        <div className="h-4 w-48 rounded bg-slate-100" />
                        <div className="mt-2 h-3 w-24 rounded bg-slate-100" />
                      </div>

                      <div className="h-4 w-20 rounded bg-slate-100" />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {buildings.map((building) => (
                    <div
                      key={building.building_id}
                      className="flex flex-col gap-4 px-6 py-5 transition hover:bg-slate-50 sm:flex-row sm:items-center sm:justify-between"
                    >
                      <div>
                        <div className="text-sm font-medium">
                          {building.name}
                        </div>

                        <div className="mt-1 text-xs text-slate-400">
                          {building.primary_use ?? "Unknown use"} ·{" "}
                          {building.site_id}
                        </div>
                      </div>

                      <div className="flex items-center gap-6">
                        <div className="text-right">
                          <div className="text-[11px] text-slate-400">
                            Building ID
                          </div>

                          <div className="mt-1 text-xs font-medium text-slate-600">
                            {building.building_id}
                          </div>
                        </div>

                        <Link
                          href={`/buildings/${encodeURIComponent(
                            building.building_id,
                          )}`}
                          className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-950"
                        >
                          Open
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        </section>
      </div>
    </main>
  );
}

function MetricCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="text-xs font-medium text-slate-400">{label}</div>

      <div className="mt-3 text-2xl font-semibold tracking-tight">
        {value}
      </div>

      <div className="mt-1 text-xs text-slate-400">{detail}</div>
    </div>
  );
}