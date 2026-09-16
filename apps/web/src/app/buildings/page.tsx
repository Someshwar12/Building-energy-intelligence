"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { getBuildings, type Building } from "@/lib/api";

export default function BuildingsPage() {
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadBuildings() {
      try {
        setLoading(true);
        setError(null);

        const data = await getBuildings();
        setBuildings(data.buildings);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load buildings",
        );
      } finally {
        setLoading(false);
      }
    }

    loadBuildings();
  }, []);

  const filteredBuildings = useMemo(() => {
    const query = search.trim().toLowerCase();

    if (!query) {
      return buildings;
    }

    return buildings.filter((building) =>
      [
        building.name,
        building.building_id,
        building.site_id,
        building.primary_use,
      ]
        .filter(Boolean)
        .some((value) => value!.toLowerCase().includes(query)),
    );
  }, [buildings, search]);

  return (
    <main className="min-h-screen bg-[#f7f8fa] px-6 py-8 text-slate-900 md:px-10">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <p className="text-sm font-medium text-slate-500">
            Building Intelligence
          </p>

          <div className="mt-2 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <h1 className="text-3xl font-semibold tracking-tight">
                Buildings
              </h1>

              <p className="mt-2 text-sm text-slate-500">
                Browse monitored buildings and inspect their energy behaviour.
              </p>
            </div>

            <div className="text-sm text-slate-500">
              {loading ? "Loading..." : `${buildings.length} buildings`}
            </div>
          </div>
        </div>

        <div className="mb-6">
          <input
            type="search"
            placeholder="Search buildings, sites or use..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition placeholder:text-slate-400 focus:border-slate-400 focus:ring-2 focus:ring-slate-100"
          />
        </div>

        {loading && (
          <div className="rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-500">
            Loading buildings...
          </div>
        )}

        {error && (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
            {error}
          </div>
        )}

        {!loading && !error && filteredBuildings.length === 0 && (
          <div className="rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-500">
            No buildings match your search.
          </div>
        )}

        {!loading && !error && filteredBuildings.length > 0 && (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {filteredBuildings.map((building) => (
              <Link
                key={building.building_id}
                href={`/buildings/${encodeURIComponent(building.building_id)}`}
                aria-label={`Open ${building.name || building.building_id}`}
                className="group block cursor-pointer rounded-2xl border border-slate-200 bg-white p-5 transition duration-200 hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-slate-300 focus:ring-offset-2"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <h2 className="truncate font-semibold text-slate-900">
                      {building.name || building.building_id}
                    </h2>

                    <p className="mt-1 text-xs text-slate-500">
                      {building.building_id}
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      Site {building.site_id}
                    </p>
                  </div>

                  <span className="shrink-0 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
                    Monitored
                  </span>
                </div>

                <div className="mt-6 grid grid-cols-2 gap-4 border-t border-slate-100 pt-4">
                  <div>
                    <p className="text-xs text-slate-400">Primary use</p>

                    <p className="mt-1 text-sm font-medium text-slate-700">
                      {building.primary_use ?? "—"}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs text-slate-400">Floor area</p>

                    <p className="mt-1 text-sm font-medium text-slate-700">
                      {(
                        building.square_feet ??
                        building.floor_area
                      )?.toLocaleString() ?? "—"}
                    </p>
                  </div>
                </div>

                <div className="mt-5 flex items-center justify-between text-sm font-medium text-slate-700">
                  <span className="transition group-hover:text-slate-950">
                    Open building
                  </span>

                  <span className="translate-x-0 transition-transform duration-200 group-hover:translate-x-1">
                    →
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}