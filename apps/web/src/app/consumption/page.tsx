"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  getBuildings,
  getBuildingConsumption,
  type Building,
  type ConsumptionPoint,
} from "@/lib/api";

const PERIODS = [
  { label: "24 hours", hours: 24 },
  { label: "7 days", hours: 168 },
  { label: "30 days", hours: 720 },
];

function formatEnergy(value: number) {
  return `${value.toLocaleString(undefined, {
    maximumFractionDigits: 1,
  })} kWh`;
}

function formatTimestamp(timestamp: string) {
  return new Date(timestamp).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function ConsumptionPage() {
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [selectedBuilding, setSelectedBuilding] = useState("");
  const [period, setPeriod] = useState(168);
  const [points, setPoints] = useState<ConsumptionPoint[]>([]);
  const [loadingBuildings, setLoadingBuildings] = useState(true);
  const [loadingConsumption, setLoadingConsumption] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [buildingSelectorOpen, setBuildingSelectorOpen] =
    useState(false);
  const [buildingSearch, setBuildingSearch] = useState("");

  const selectorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function loadBuildings() {
      try {
        setLoadingBuildings(true);
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
            : "Failed to load building data.",
        );
      } finally {
        setLoadingBuildings(false);
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

    async function loadConsumption() {
      try {
        setLoadingConsumption(true);
        setError(null);

        const to = new Date("2017-12-31T23:00:00Z");
        const from = new Date(
          to.getTime() - period * 60 * 60 * 1000,
        );

        const response = await getBuildingConsumption(
          selectedBuilding,
          from.toISOString(),
          to.toISOString(),
        );

        setPoints(response.points);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load consumption data.",
        );
        setPoints([]);
      } finally {
        setLoadingConsumption(false);
      }
    }

    loadConsumption();
  }, [selectedBuilding, period]);

  const validPoints = useMemo(
    () =>
      points.filter(
        (point) => point.energy_kwh !== null,
      ),
    [points],
  );

  const stats = useMemo(() => {
    const values = validPoints.map(
      (point) => point.energy_kwh as number,
    );

    if (values.length === 0) {
      return {
        total: 0,
        average: 0,
        peak: 0,
        peakTimestamp: null as string | null,
      };
    }

    const total = values.reduce(
      (sum, value) => sum + value,
      0,
    );

    const peak = Math.max(...values);
    const peakIndex = values.indexOf(peak);

    return {
      total,
      average: total / values.length,
      peak,
      peakTimestamp:
        validPoints[peakIndex]?.timestamp ?? null,
    };
  }, [validPoints]);

  const chartData = useMemo(
    () =>
      validPoints.map((point) => ({
        timestamp: point.timestamp,
        energy: point.energy_kwh,
      })),
    [validPoints],
  );

  const selected = buildings.find(
    (building) =>
      building.building_id === selectedBuilding,
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
      <div className="min-h-screen">
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
                      <path d="M4 18V9m5 9V5m6 13v-7m5 7V3" />
                    </svg>
                  </span>

                  <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
                    Energy analytics
                  </span>
                </div>

                <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
                  Consumption
                </h1>

                <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
                  Explore historical electricity consumption and
                  identify the patterns shaping building demand.
                </p>
              </div>

              <div className="flex flex-col gap-2 sm:flex-row">
                {/* Searchable building selector */}
                <div
                  ref={selectorRef}
                  className="relative min-w-64"
                >
                  <button
                    type="button"
                    disabled={loadingBuildings}
                    onClick={() => {
                      setBuildingSelectorOpen(
                        (open) => !open,
                      );
                      setBuildingSearch("");
                    }}
                    className="flex w-full items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white px-4 py-3 text-left text-sm font-medium text-slate-700 outline-none transition hover:border-slate-300 focus:border-slate-400 focus:ring-2 focus:ring-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <span className="truncate">
                      {loadingBuildings
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
                          filteredBuildings.map(
                            (building) => {
                              const isSelected =
                                building.building_id ===
                                selectedBuilding;

                              return (
                                <button
                                  key={
                                    building.building_id
                                  }
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
                            },
                          )
                        )}
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex rounded-xl border border-slate-200 bg-slate-50 p-1">
                  {PERIODS.map((option) => (
                    <button
                      key={option.hours}
                      onClick={() =>
                        setPeriod(option.hours)
                      }
                      className={`rounded-lg px-3 py-2 text-xs font-medium transition ${
                        period === option.hours
                          ? "bg-white text-slate-950 shadow-sm"
                          : "text-slate-500 hover:text-slate-900"
                      }`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </header>

        <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
          {selected && (
            <section className="mb-6 overflow-hidden rounded-2xl border border-slate-200 bg-white">
              <div className="relative px-6 py-6 sm:px-7">
                <div className="absolute right-0 top-0 h-32 w-32 rounded-full bg-slate-100 blur-3xl" />

                <div className="relative flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="text-xs font-medium uppercase tracking-[0.14em] text-slate-400">
                      Selected building
                    </div>

                    <h2 className="mt-1 text-xl font-semibold tracking-tight">
                      {selected.name ||
                        selected.building_id}
                    </h2>

                    <p className="mt-1 text-sm text-slate-500">
                      {selected.primary_use ??
                        "Unknown use"}{" "}
                      · Site {selected.site_id}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                    Historical data available
                  </div>
                </div>
              </div>
            </section>
          )}

          {error && (
            <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
              {error}
            </div>
          )}

          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label="Total consumption"
              value={
                loadingConsumption
                  ? "..."
                  : formatEnergy(stats.total)
              }
              detail={`${validPoints.length.toLocaleString()} observations`}
              icon="bolt"
            />

            <StatCard
              label="Average / hour"
              value={
                loadingConsumption
                  ? "..."
                  : formatEnergy(stats.average)
              }
              detail="Across selected period"
              icon="average"
            />

            <StatCard
              label="Peak demand"
              value={
                loadingConsumption
                  ? "..."
                  : formatEnergy(stats.peak)
              }
              detail={
                stats.peakTimestamp
                  ? formatTimestamp(stats.peakTimestamp)
                  : "No peak available"
              }
              icon="peak"
            />

            <StatCard
              label="Data coverage"
              value={
                loadingConsumption
                  ? "..."
                  : `${validPoints.length.toLocaleString()}`
              }
              detail="Valid hourly points"
              icon="data"
            />
          </section>

          <section className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white">
            <div className="flex flex-col gap-3 border-b border-slate-100 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="text-sm font-semibold">
                  Electricity consumption
                </h2>

                <p className="mt-1 text-xs text-slate-400">
                  Hourly energy demand over the selected period
                </p>
              </div>

              <div className="flex items-center gap-2 text-xs text-slate-400">
                <span className="h-2 w-2 rounded-full bg-slate-900" />
                Energy
              </div>
            </div>

            <div className="h-[420px] px-2 pb-5 pt-6 sm:px-5">
              {loadingConsumption ? (
                <div className="flex h-full items-center justify-center">
                  <div className="text-sm text-slate-400">
                    Loading consumption data...
                  </div>
                </div>
              ) : chartData.length === 0 ? (
                <div className="flex h-full items-center justify-center">
                  <div className="text-center">
                    <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100 text-slate-400">
                      No data
                    </div>

                    <p className="mt-3 text-sm font-medium text-slate-600">
                      No consumption observations found
                    </p>
                  </div>
                </div>
              ) : (
                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >
                  <AreaChart
                    data={chartData}
                    margin={{
                      top: 8,
                      right: 18,
                      left: 0,
                      bottom: 4,
                    }}
                  >
                    <defs>
                      <linearGradient
                        id="consumptionFill"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="0%"
                          stopColor="#0f172a"
                          stopOpacity={0.16}
                        />

                        <stop
                          offset="100%"
                          stopColor="#0f172a"
                          stopOpacity={0}
                        />
                      </linearGradient>
                    </defs>

                    <CartesianGrid
                      vertical={false}
                      stroke="#e5e7eb"
                      strokeDasharray="3 3"
                    />

                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) =>
                        new Date(
                          value,
                        ).toLocaleDateString(
                          undefined,
                          {
                            month: "short",
                            day: "numeric",
                          },
                        )
                      }
                      tick={{
                        fontSize: 11,
                        fill: "#94a3b8",
                      }}
                      axisLine={false}
                      tickLine={false}
                      minTickGap={45}
                    />

                    <YAxis
                      tick={{
                        fontSize: 11,
                        fill: "#94a3b8",
                      }}
                      axisLine={false}
                      tickLine={false}
                      width={55}
                    />

                    <Tooltip
                      labelFormatter={(value) =>
                        formatTimestamp(
                          String(value),
                        )
                      }
                      formatter={(value) => [
                        `${Number(
                          value,
                        ).toLocaleString(undefined, {
                          maximumFractionDigits: 2,
                        })} kWh`,
                        "Consumption",
                      ]}
                      contentStyle={{
                        borderRadius: 12,
                        border: "1px solid #e2e8f0",
                        boxShadow:
                          "0 10px 30px rgba(15, 23, 42, 0.08)",
                      }}
                    />

                    <Area
                      type="monotone"
                      dataKey="energy"
                      stroke="#0f172a"
                      strokeWidth={2}
                      fill="url(#consumptionFill)"
                      dot={false}
                      activeDot={{ r: 4 }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </section>

          <section className="mt-6 grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
            <div className="rounded-2xl border border-slate-200 bg-white p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold">
                    Period summary
                  </h3>

                  <p className="mt-1 text-xs text-slate-400">
                    Current analytical window
                  </p>
                </div>

                <div className="rounded-xl bg-slate-50 px-3 py-2 text-xs font-medium text-slate-500">
                  {
                    PERIODS.find(
                      (item) => item.hours === period,
                    )?.label
                  }
                </div>
              </div>

              <div className="mt-6 grid grid-cols-2 gap-4">
                <SummaryItem
                  label="Lowest observation"
                  value={
                    validPoints.length
                      ? formatEnergy(
                          Math.min(
                            ...validPoints.map(
                              (point) =>
                                point.energy_kwh as number,
                            ),
                          ),
                        )
                      : "—"
                  }
                />

                <SummaryItem
                  label="Highest observation"
                  value={
                    stats.peak
                      ? formatEnergy(stats.peak)
                      : "—"
                  }
                />

                <SummaryItem
                  label="Building ID"
                  value={selectedBuilding || "—"}
                />

                <SummaryItem
                  label="Time resolution"
                  value="Hourly"
                />
              </div>
            </div>

            <div className="relative overflow-hidden rounded-2xl bg-slate-950 p-6 text-white">
              <div className="absolute -right-8 -top-8 h-32 w-32 rounded-full border border-white/10" />
              <div className="absolute -right-2 -top-2 h-20 w-20 rounded-full border border-white/10" />

              <div className="relative">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/10">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    className="h-5 w-5"
                    stroke="currentColor"
                    strokeWidth="1.6"
                  >
                    <path d="M12 3v18M3 12h18M5.5 5.5l13 13M18.5 5.5l-13 13" />
                  </svg>
                </div>

                <h3 className="mt-5 text-lg font-semibold">
                  Consumption intelligence
                </h3>

                <p className="mt-2 text-sm leading-6 text-slate-400">
                  Historical consumption is the foundation for
                  forecasting, anomaly detection, and
                  building-level performance analysis.
                </p>

                <div className="mt-6 flex items-center gap-2 text-xs text-slate-400">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                  Connected to BDG2 historical data
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}

function StatCard({
  label,
  value,
  detail,
  icon,
}: {
  label: string;
  value: string;
  detail: string;
  icon: "bolt" | "average" | "peak" | "data";
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex items-start justify-between">
        <div className="text-xs font-medium text-slate-400">
          {label}
        </div>

        <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-slate-50 text-slate-500">
          {icon === "bolt" && "⚡"}
          {icon === "average" && "∿"}
          {icon === "peak" && "↗"}
          {icon === "data" && "◫"}
        </div>
      </div>

      <div className="mt-4 text-2xl font-semibold tracking-tight">
        {value}
      </div>

      <div className="mt-1 truncate text-xs text-slate-400">
        {detail}
      </div>
    </div>
  );
}

function SummaryItem({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl bg-slate-50 p-4">
      <div className="text-xs text-slate-400">
        {label}
      </div>

      <div className="mt-2 truncate text-sm font-semibold text-slate-700">
        {value}
      </div>
    </div>
  );
}