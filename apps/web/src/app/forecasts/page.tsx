"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  getBuildings,
  getBuildingForecast,
  type Building,
  type Forecast,
} from "@/lib/api";

export default function ForecastsPage() {
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [selectedBuilding, setSelectedBuilding] = useState("");
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingForecast, setLoadingForecast] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [buildingSelectorOpen, setBuildingSelectorOpen] =
    useState(false);
  const [buildingSearch, setBuildingSearch] = useState("");

  const selectorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function loadBuildings() {
      try {
        setLoading(true);
        setError(null);

        const response = await getBuildings();
        setBuildings(response.buildings);

        if (response.buildings.length > 0) {
          setSelectedBuilding(response.buildings[0].building_id);
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load buildings.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadBuildings();
  }, []);

  useEffect(() => {
    function handleOutsideClick(event: MouseEvent) {
      if (
        selectorRef.current &&
        !selectorRef.current.contains(event.target as Node)
      ) {
        setBuildingSelectorOpen(false);
      }
    }

    document.addEventListener("mousedown", handleOutsideClick);

    return () => {
      document.removeEventListener(
        "mousedown",
        handleOutsideClick,
      );
    };
  }, []);

  useEffect(() => {
    if (!selectedBuilding) return;

    async function loadForecast() {
      try {
        setLoadingForecast(true);
        setError(null);

        const result = await getBuildingForecast(
          selectedBuilding,
          "2017-12-31T23:00:00Z",
        );

        setForecast(result);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load forecast.",
        );
        setForecast(null);
      } finally {
        setLoadingForecast(false);
      }
    }

    loadForecast();
  }, [selectedBuilding]);

  const selected = buildings.find(
    (building) => building.building_id === selectedBuilding,
  );

  const filteredBuildings = useMemo(() => {
    const query = buildingSearch.trim().toLowerCase();

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
        .some((value) =>
          value!.toLowerCase().includes(query),
        ),
    );
  }, [buildings, buildingSearch]);

  return (
    <main className="min-h-screen bg-[#f7f8fa] text-slate-950">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-5 py-7 sm:px-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="mb-3 flex items-center gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-slate-950 text-white">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    className="h-4 w-4"
                    stroke="currentColor"
                    strokeWidth="1.8"
                  >
                    <path d="M4 16l5-5 4 3 7-8" />
                    <path d="M15 6h5v5" />
                  </svg>
                </span>

                <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
                  Predictive analytics
                </span>
              </div>

              <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
                Forecasts
              </h1>

              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
                View the energy forecast produced by the
                platform&apos;s production inference pipeline.
              </p>
            </div>

            {/* Searchable building selector */}
            <div
              ref={selectorRef}
              className="relative min-w-64"
            >
              <button
                type="button"
                disabled={loading}
                onClick={() => {
                  setBuildingSelectorOpen(
                    (open) => !open,
                  );
                  setBuildingSearch("");
                }}
                className="flex w-full items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white px-4 py-3 text-left text-sm font-medium text-slate-700 outline-none transition hover:border-slate-300 focus:border-slate-400 focus:ring-2 focus:ring-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <span className="truncate">
                  {loading
                    ? "Loading buildings..."
                    : selected?.name ||
                      selected?.building_id ||
                      "Select building"}
                </span>

                <svg
                  viewBox="0 0 20 20"
                  fill="none"
                  className={`h-4 w-4 shrink-0 text-slate-400 transition-transform ${
                    buildingSelectorOpen
                      ? "rotate-180"
                      : ""
                  }`}
                  stroke="currentColor"
                  strokeWidth="1.7"
                >
                  <path
                    d="m5 7.5 5 5 5-5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </button>

              {buildingSelectorOpen && (
                <div className="absolute right-0 top-[calc(100%+8px)] z-30 w-full min-w-[280px] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl shadow-slate-950/10">
                  <div className="border-b border-slate-100 p-2">
                    <div className="relative">
                      <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                        stroke="currentColor"
                        strokeWidth="1.8"
                      >
                        <circle
                          cx="11"
                          cy="11"
                          r="6.5"
                        />
                        <path d="m16 16 4 4" />
                      </svg>

                      <input
                        autoFocus
                        type="search"
                        value={buildingSearch}
                        onChange={(event) =>
                          setBuildingSearch(
                            event.target.value,
                          )
                        }
                        placeholder="Search buildings..."
                        className="w-full rounded-xl bg-slate-50 py-2.5 pl-9 pr-3 text-sm text-slate-700 outline-none placeholder:text-slate-400 focus:bg-slate-100"
                      />
                    </div>
                  </div>

                  <div className="max-h-72 overflow-y-auto p-1.5">
                    {filteredBuildings.length === 0 ? (
                      <div className="px-3 py-8 text-center">
                        <div className="text-sm font-medium text-slate-600">
                          No buildings found
                        </div>

                        <p className="mt-1 text-xs text-slate-400">
                          Try a different building name,
                          site, or ID.
                        </p>
                      </div>
                    ) : (
                      filteredBuildings.map((building) => {
                        const isSelected =
                          building.building_id ===
                          selectedBuilding;

                        return (
                          <button
                            key={building.building_id}
                            type="button"
                            onClick={() => {
                              setSelectedBuilding(
                                building.building_id,
                              );
                              setBuildingSelectorOpen(
                                false,
                              );
                              setBuildingSearch("");
                            }}
                            className={`flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left transition ${
                              isSelected
                                ? "bg-slate-50"
                                : "hover:bg-slate-50"
                            }`}
                          >
                            <div className="min-w-0">
                              <div className="truncate text-sm font-medium text-slate-800">
                                {building.name ||
                                  building.building_id}
                              </div>

                              <div className="mt-0.5 truncate text-xs text-slate-400">
                                {building.site_id}
                                {" · "}
                                {building.primary_use ??
                                  "Unknown use"}
                              </div>
                            </div>

                            {isSelected && (
                              <svg
                                viewBox="0 0 20 20"
                                fill="none"
                                className="ml-3 h-4 w-4 shrink-0 text-slate-950"
                                stroke="currentColor"
                                strokeWidth="2"
                              >
                                <path
                                  d="m5 10 3 3 7-7"
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                />
                              </svg>
                            )}
                          </button>
                        );
                      })
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
        {error && (
          <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {selected && (
          <section className="relative mb-6 overflow-hidden rounded-2xl border border-slate-200 bg-white">
            <div className="absolute -right-20 -top-20 h-56 w-56 rounded-full bg-slate-100 blur-3xl" />

            <div className="relative flex flex-col gap-5 px-6 py-6 sm:px-7 md:flex-row md:items-center md:justify-between">
              <div>
                <div className="text-xs font-medium uppercase tracking-[0.14em] text-slate-400">
                  Selected building
                </div>

                <h2 className="mt-1 text-xl font-semibold tracking-tight">
                  {selected.name || selected.building_id}
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  {selected.primary_use ?? "Unknown use"} · Site{" "}
                  {selected.site_id}
                </p>
              </div>

              <div className="flex items-center gap-2 rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                Inference service connected
              </div>
            </div>
          </section>
        )}

        <section className="grid gap-4 md:grid-cols-3">
          <div className="relative overflow-hidden rounded-2xl bg-slate-950 p-6 text-white md:col-span-2">
            <div className="absolute right-[-35px] top-[-35px] h-40 w-40 rounded-full border border-white/10" />
            <div className="absolute right-[-5px] top-[-5px] h-24 w-24 rounded-full border border-white/10" />

            <div className="relative">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs font-medium uppercase tracking-[0.14em] text-slate-400">
                    Predicted energy
                  </div>

                  <div className="mt-4">
                    {loadingForecast ? (
                      <div className="h-12 w-56 animate-pulse rounded-lg bg-white/10" />
                    ) : (
                      <div className="text-4xl font-semibold tracking-tight sm:text-5xl">
                        {forecast
                          ? forecast.predicted_energy_kwh.toLocaleString(
                              undefined,
                              {
                                maximumFractionDigits: 1,
                              },
                            )
                          : "—"}

                        <span className="ml-2 text-base font-medium text-slate-400">
                          kWh
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="hidden h-16 w-16 items-center justify-center rounded-2xl bg-white/10 sm:flex">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    className="h-8 w-8"
                    stroke="currentColor"
                    strokeWidth="1.5"
                  >
                    <path d="M4 17l5-6 4 3 7-8" />
                    <path d="M16 6h4v4" />
                  </svg>
                </div>
              </div>

              <div className="mt-8 border-t border-white/10 pt-5">
                <div className="text-xs text-slate-500">
                  Forecast timestamp
                </div>

                <div className="mt-1 text-sm font-medium text-slate-300">
                  {forecast
                    ? new Date(
                        forecast.timestamp,
                      ).toLocaleString()
                    : "—"}
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6">
            <div className="text-xs font-medium uppercase tracking-[0.14em] text-slate-400">
              Model
            </div>

            <div className="mt-5">
              <div className="text-lg font-semibold">
                {loadingForecast
                  ? "Loading..."
                  : forecast?.model_name || "—"}
              </div>

              <div className="mt-2 inline-flex rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                Version {forecast?.model_version || "—"}
              </div>
            </div>

            <div className="mt-8 border-t border-slate-100 pt-5">
              <div className="text-xs text-slate-400">
                Serving pipeline
              </div>

              <div className="mt-2 flex items-center gap-2 text-sm font-medium text-slate-700">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                FastAPI inference
              </div>
            </div>
          </div>
        </section>

        <section className="mt-6 grid gap-6 lg:grid-cols-[1fr_0.8fr]">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-7">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-sm font-semibold">
                  Forecast context
                </h2>

                <p className="mt-1 text-xs leading-5 text-slate-400">
                  Prediction generated from the building&apos;s
                  historical context and the deployed inference
                  service.
                </p>
              </div>

              <span className="rounded-xl bg-slate-50 px-3 py-2 text-xs font-medium text-slate-500">
                168h context
              </span>
            </div>

            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              <ContextCard
                label="Building"
                value={
                  selected?.name ||
                  selectedBuilding ||
                  "—"
                }
              />

              <ContextCard
                label="Primary use"
                value={
                  selected?.primary_use || "Unknown"
                }
              />

              <ContextCard
                label="Site"
                value={selected?.site_id || "—"}
              />

              <ContextCard
                label="Prediction unit"
                value="kWh"
              />
            </div>
          </div>

          <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-6 sm:p-7">
            <div className="absolute bottom-0 right-0 h-32 w-32 rounded-full bg-slate-100 blur-3xl" />

            <div className="relative">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-600">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  className="h-5 w-5"
                  stroke="currentColor"
                  strokeWidth="1.6"
                >
                  <path d="M12 3v18M3 12h18" />
                  <circle cx="12" cy="12" r="8" />
                </svg>
              </div>

              <h3 className="mt-5 text-lg font-semibold">
                Production inference
              </h3>

              <p className="mt-2 text-sm leading-6 text-slate-500">
                This forecast is requested through the application
                API and served by the containerized model service.
              </p>

              <div className="mt-6 space-y-3 text-xs">
                <PipelineStep
                  label="Application API"
                  active
                />
                <PipelineStep
                  label="FastAPI model service"
                  active
                />
                <PipelineStep
                  label="Production model alias"
                  active
                />
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

function ContextCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl bg-slate-50 p-4">
      <div className="text-xs text-slate-400">{label}</div>

      <div className="mt-2 truncate text-sm font-semibold text-slate-700">
        {value}
      </div>
    </div>
  );
}

function PipelineStep({
  label,
  active,
}: {
  label: string;
  active: boolean;
}) {
  return (
    <div className="flex items-center gap-3">
      <span
        className={`h-2 w-2 rounded-full ${
          active ? "bg-emerald-500" : "bg-slate-300"
        }`}
      />

      <span className="font-medium text-slate-600">
        {label}
      </span>
    </div>
  );
}