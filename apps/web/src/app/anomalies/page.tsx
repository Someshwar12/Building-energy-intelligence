"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  getBuildings,
  getBuildingAnomalies,
  type Anomaly,
  type Building,
} from "@/lib/api";

type Period = "24h" | "7d" | "30d";

export default function AnomaliesPage() {
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [selectedBuilding, setSelectedBuilding] =
    useState<Building | null>(null);

  const [period, setPeriod] = useState<Period>("7d");

  const [buildingOpen, setBuildingOpen] = useState(false);
  const [buildingSearch, setBuildingSearch] = useState("");

  const [loading, setLoading] = useState(true);
  const [anomalyLoading, setAnomalyLoading] =
    useState(false);
  const [error, setError] = useState<string | null>(null);

  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [pointsAnalyzed, setPointsAnalyzed] = useState(0);
  const [detectionMethod, setDetectionMethod] =
    useState("");

  const buildingSelectorRef =
    useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function loadBuildings() {
      try {
        setLoading(true);
        setError(null);

        const data = await getBuildings();

        setBuildings(data.buildings);

        if (data.buildings.length > 0) {
          setSelectedBuilding(data.buildings[0]);
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load buildings",
        );
      } finally {
        setLoading(false);
      }
    }

    loadBuildings();
  }, []);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        buildingSelectorRef.current &&
        !buildingSelectorRef.current.contains(
          event.target as Node,
        )
      ) {
        setBuildingOpen(false);
      }
    }

    document.addEventListener(
      "mousedown",
      handleClickOutside,
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handleClickOutside,
      );
    };
  }, []);

  useEffect(() => {
    if (!selectedBuilding) {
      return;
    }

    const buildingId =
      selectedBuilding.building_id;

    async function loadAnomalies() {
      try {
        setAnomalyLoading(true);
        setError(null);

        const referenceTime = new Date(
          "2017-12-31T23:00:00Z",
        );

        const periodHours =
          period === "24h"
            ? 24
            : period === "7d"
              ? 24 * 7
              : 24 * 30;

        const from = new Date(
          referenceTime.getTime() -
            periodHours * 60 * 60 * 1000,
        );

        const data =
          await getBuildingAnomalies(
            buildingId,
            from.toISOString(),
            referenceTime.toISOString(),
          );

        setAnomalies(data.anomalies);
        setPointsAnalyzed(
          data.points_analyzed,
        );
        setDetectionMethod(
          data.detection_method,
        );
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load anomaly data",
        );

        setAnomalies([]);
        setPointsAnalyzed(0);
        setDetectionMethod("");
      } finally {
        setAnomalyLoading(false);
      }
    }

    loadAnomalies();
  }, [selectedBuilding, period]);

  const filteredBuildings = useMemo(() => {
    const query = buildingSearch
      .trim()
      .toLowerCase();

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
          value!
            .toLowerCase()
            .includes(query),
        ),
    );
  }, [buildings, buildingSearch]);

  const highCount = anomalies.filter(
    (anomaly) =>
      anomaly.severity === "High",
  ).length;

  const mediumCount = anomalies.filter(
    (anomaly) =>
      anomaly.severity === "Medium",
  ).length;

  const lowCount = anomalies.filter(
    (anomaly) =>
      anomaly.severity === "Low",
  ).length;

  const periodLabel = {
    "24h": "Last 24 hours",
    "7d": "Last 7 days",
    "30d": "Last 30 days",
  }[period];

  return (
    <main className="min-h-screen bg-[#f7f8fa] px-6 py-8 text-slate-900 md:px-10">
      <div className="mx-auto max-w-7xl">

        {/* Header */}
        <div className="mb-8">
          <p className="text-sm font-medium text-slate-500">
            Building Intelligence
          </p>

          <div className="mt-2 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h1 className="text-3xl font-semibold tracking-tight">
                Anomalies
              </h1>

              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
                Detect unusual energy behaviour and
                identify buildings that deviate from
                their expected consumption patterns.
              </p>
            </div>

            <div className="text-sm text-slate-500">
              {loading
                ? "Loading..."
                : `${buildings.length} buildings monitored`}
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="mb-6 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">

          {/* Building selector */}
          <div
            ref={buildingSelectorRef}
            className="relative w-full lg:max-w-md"
          >
            <button
              type="button"
              onClick={() => {
                setBuildingOpen(
                  (open) => !open,
                );
                setBuildingSearch("");
              }}
              className="flex w-full items-center justify-between rounded-xl border border-slate-200 bg-white px-4 py-3 text-left shadow-sm transition hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-slate-100"
            >
              <div className="min-w-0">
                <p className="text-[11px] font-medium uppercase tracking-wide text-slate-400">
                  Building
                </p>

                <p className="mt-1 truncate text-sm font-medium text-slate-800">
                  {selectedBuilding
                    ? selectedBuilding.name ||
                      selectedBuilding.building_id
                    : "Select building"}
                </p>
              </div>

              <span
                className={`ml-4 text-slate-400 transition-transform ${
                  buildingOpen
                    ? "rotate-180"
                    : ""
                }`}
              >
                ▾
              </span>
            </button>

            {buildingOpen && (
              <div className="absolute left-0 right-0 z-50 mt-2 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl">
                <div className="border-b border-slate-100 p-3">
                  <input
                    autoFocus
                    type="search"
                    placeholder="Search buildings, sites or use..."
                    value={buildingSearch}
                    onChange={(event) =>
                      setBuildingSearch(
                        event.target.value,
                      )
                    }
                    onClick={(event) =>
                      event.stopPropagation()
                    }
                    className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition placeholder:text-slate-400 focus:border-slate-300 focus:bg-white"
                  />
                </div>

                <div className="max-h-72 overflow-y-auto p-1.5">
                  {filteredBuildings.length ===
                  0 ? (
                    <div className="px-3 py-6 text-center text-sm text-slate-500">
                      No buildings match your
                      search.
                    </div>
                  ) : (
                    filteredBuildings.map(
                      (building) => {
                        const selected =
                          selectedBuilding?.building_id ===
                          building.building_id;

                        return (
                          <button
                            key={
                              building.building_id
                            }
                            type="button"
                            onClick={() => {
                              setSelectedBuilding(
                                building,
                              );
                              setBuildingOpen(
                                false,
                              );
                              setBuildingSearch(
                                "",
                              );
                            }}
                            className={`flex w-full items-center justify-between rounded-lg px-3 py-3 text-left transition ${
                              selected
                                ? "bg-slate-50"
                                : "hover:bg-slate-50"
                            }`}
                          >
                            <div className="min-w-0">
                              <p className="truncate text-sm font-medium text-slate-800">
                                {building.name ||
                                  building.building_id}
                              </p>

                              <p className="mt-0.5 truncate text-xs text-slate-400">
                                {
                                  building.building_id
                                }{" "}
                                · Site{" "}
                                {
                                  building.site_id
                                }
                              </p>
                            </div>

                            {selected && (
                              <span className="ml-3 text-sm text-slate-700">
                                ✓
                              </span>
                            )}
                          </button>
                        );
                      },
                    )
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Period selector */}
          <div className="flex items-center gap-1 rounded-xl border border-slate-200 bg-white p-1 shadow-sm">
            {(
              ["24h", "7d", "30d"] as Period[]
            ).map((value) => (
              <button
                key={value}
                type="button"
                onClick={() =>
                  setPeriod(value)
                }
                className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
                  period === value
                    ? "bg-slate-900 text-white shadow-sm"
                    : "text-slate-500 hover:bg-slate-50 hover:text-slate-800"
                }`}
              >
                {value}
              </button>
            ))}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 p-5 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* KPI cards */}
        <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
              Anomalies detected
            </p>

            <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">
              {anomalyLoading
                ? "—"
                : anomalies.length}
            </p>

            <p className="mt-2 text-xs text-slate-500">
              {periodLabel}
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
              High severity
            </p>

            <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">
              {anomalyLoading
                ? "—"
                : highCount}
            </p>

            <p className="mt-2 text-xs text-slate-500">
              Requires attention
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
              Medium severity
            </p>

            <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">
              {anomalyLoading
                ? "—"
                : mediumCount}
            </p>

            <p className="mt-2 text-xs text-slate-500">
              Worth investigating
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
              Low severity
            </p>

            <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">
              {anomalyLoading
                ? "—"
                : lowCount}
            </p>

            <p className="mt-2 text-xs text-slate-500">
              Minor deviations
            </p>
          </div>
        </div>

        {/* Detection overview */}
        <div className="mb-6 grid gap-6 lg:grid-cols-[1.7fr_1fr]">

          {/* Timeline */}
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="text-base font-semibold text-slate-900">
                  Anomaly timeline
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Unusual consumption events over
                  the selected period.
                </p>
              </div>

              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-500">
                {periodLabel}
              </span>
            </div>

            {anomalyLoading ? (
              <div className="mt-8 flex min-h-[280px] items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50/50">
                <div className="text-center">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-white text-xl shadow-sm ring-1 ring-slate-200">
                    …
                  </div>

                  <h3 className="mt-4 text-sm font-semibold text-slate-800">
                    Analysing consumption
                  </h3>

                  <p className="mt-2 max-w-sm text-xs leading-5 text-slate-500">
                    Comparing historical energy
                    behaviour against the expected
                    consumption pattern.
                  </p>
                </div>
              </div>
            ) : anomalies.length === 0 ? (
              <div className="mt-8 flex min-h-[280px] items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50/50">
                <div className="max-w-sm text-center">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-white text-xl shadow-sm ring-1 ring-slate-200">
                    ✓
                  </div>

                  <h3 className="mt-4 text-sm font-semibold text-slate-800">
                    No anomalies detected
                  </h3>

                  <p className="mt-2 text-xs leading-5 text-slate-500">
                    No statistically unusual
                    consumption events were detected
                    during the selected period.
                  </p>
                </div>
              </div>
            ) : (
              <div className="mt-8 space-y-3">
                {anomalies
                  .slice(0, 12)
                  .map((anomaly) => (
                    <div
                      key={`${anomaly.timestamp}-${anomaly.score}`}
                      className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 px-4 py-3"
                    >
                      <div>
                        <p className="text-sm font-medium text-slate-800">
                          {new Date(
                            anomaly.timestamp,
                          ).toLocaleString()}
                        </p>

                        <p className="mt-1 text-xs text-slate-500">
                          Observed{" "}
                          {anomaly.energy_kwh.toFixed(
                            2,
                          )}{" "}
                          kWh · Expected{" "}
                          {anomaly.expected_kwh.toFixed(
                            2,
                          )}{" "}
                          kWh
                        </p>
                      </div>

                      <div className="text-right">
                        <p className="text-sm font-semibold text-slate-800">
                          {anomaly.deviation_pct >=
                          0
                            ? "+"
                            : ""}
                          {anomaly.deviation_pct.toFixed(
                            1,
                          )}
                          %
                        </p>

                        <span className="mt-1 inline-block rounded-full bg-white px-2.5 py-1 text-[11px] font-medium text-slate-600 ring-1 ring-slate-200">
                          {anomaly.severity}
                        </span>
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </section>

          {/* Detection method */}
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
              Detection system
            </p>

            <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-900">
              Energy behaviour analysis
            </h2>

            <p className="mt-3 text-sm leading-6 text-slate-500">
              The system compares observed building
              consumption against an expected historical
              pattern and identifies statistically unusual
              deviations.
            </p>

            <div className="mt-6 space-y-3">

              <div className="rounded-xl bg-slate-50 p-4">
                <p className="text-xs font-medium text-slate-400">
                  Input
                </p>

                <p className="mt-1 text-sm font-medium text-slate-700">
                  {pointsAnalyzed > 0
                    ? `${pointsAnalyzed.toLocaleString()} hourly observations`
                    : "Historical hourly consumption"}
                </p>
              </div>

              <div className="rounded-xl bg-slate-50 p-4">
                <p className="text-xs font-medium text-slate-400">
                  Detection
                </p>

                <p className="mt-1 text-sm font-medium leading-5 text-slate-700">
                  {detectionMethod ||
                    "Robust statistical deviation analysis"}
                </p>
              </div>

              <div className="rounded-xl bg-slate-50 p-4">
                <p className="text-xs font-medium text-slate-400">
                  Output
                </p>

                <p className="mt-1 text-sm font-medium text-slate-700">
                  Severity-ranked anomaly events
                </p>
              </div>
            </div>
          </section>
        </div>

        {/* Recent anomalies */}
        <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="flex flex-col gap-2 border-b border-slate-100 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-semibold text-slate-900">
                Recent anomalies
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Detected deviations for{" "}
                {selectedBuilding?.name ||
                  selectedBuilding?.building_id ||
                  "the selected building"}.
              </p>
            </div>

            <span className="text-xs text-slate-400">
              {anomalyLoading
                ? "Analysing..."
                : `${anomalies.length} events`}
            </span>
          </div>

          {anomalyLoading ? (
            <div className="px-6 py-14 text-center">
              <p className="text-sm font-medium text-slate-700">
                Analysing historical consumption...
              </p>

              <p className="mt-2 text-xs text-slate-500">
                This may take a moment while the
                detection service processes the selected
                period.
              </p>
            </div>
          ) : anomalies.length === 0 ? (
            <div className="px-6 py-14 text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-slate-50 text-lg text-slate-400 ring-1 ring-slate-200">
                ✓
              </div>

              <h3 className="mt-4 text-sm font-semibold text-slate-800">
                No detected anomalies
              </h3>

              <p className="mx-auto mt-2 max-w-md text-xs leading-5 text-slate-500">
                No statistically unusual consumption
                events were detected for this building
                during the selected period.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[820px] text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-400">
                    <th className="px-6 py-4 font-medium">
                      Timestamp
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Observed
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Expected
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Deviation
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Score
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Severity
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {anomalies.map(
                    (anomaly) => (
                      <tr
                        key={`${anomaly.timestamp}-${anomaly.score}`}
                        className="border-b border-slate-100 last:border-0"
                      >
                        <td className="px-6 py-4 text-slate-700">
                          {new Date(
                            anomaly.timestamp,
                          ).toLocaleString()}
                        </td>

                        <td className="px-6 py-4 font-medium text-slate-800">
                          {anomaly.energy_kwh.toFixed(
                            2,
                          )}{" "}
                          kWh
                        </td>

                        <td className="px-6 py-4 text-slate-600">
                          {anomaly.expected_kwh.toFixed(
                            2,
                          )}{" "}
                          kWh
                        </td>

                        <td className="px-6 py-4 text-slate-700">
                          {anomaly.deviation_pct >=
                          0
                            ? "+"
                            : ""}
                          {anomaly.deviation_pct.toFixed(
                            1,
                          )}
                          %
                        </td>

                        <td className="px-6 py-4 font-medium text-slate-700">
                          {anomaly.score.toFixed(
                            2,
                          )}
                        </td>

                        <td className="px-6 py-4">
                          <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                            {anomaly.severity}
                          </span>
                        </td>
                      </tr>
                    ),
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}