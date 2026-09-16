"use client";

import { useEffect, useMemo, useState } from "react";
import {
  getBuildings,
  getBuildingAnomalies,
  getBuildingConsumption,
  type AnomalyAnalysis,
  type Building,
} from "@/lib/api";

type PortfolioPoint = {
  hour: string;
  label: string;
  energy: number;
};

type BuildingEnergy = {
  building: Building;
  energy: number;
  anomalies: number;
};

function formatNumber(
  value: number,
  digits = 0,
): string {
  return value.toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  });
}

function formatCompact(
  value: number,
): string {
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}M`;
  }

  if (value >= 1_000) {
    return `${(value / 1_000).toFixed(1)}k`;
  }

  return formatNumber(value);
}

function shortBuildingName(
  building: Building,
): string {
  const name =
    building.name || building.building_id;

  return name.length > 22
    ? `${name.slice(0, 22)}…`
    : name;
}

export default function OverviewPage() {
  const [buildings, setBuildings] = useState<
    Building[]
  >([]);

  const [buildingEnergy, setBuildingEnergy] =
    useState<BuildingEnergy[]>([]);

  const [portfolioTrend, setPortfolioTrend] =
    useState<PortfolioPoint[]>([]);

  const [totalAnomalies, setTotalAnomalies] =
    useState(0);

  const [highAnomalies, setHighAnomalies] =
    useState(0);

  const [pointsAnalyzed, setPointsAnalyzed] =
    useState(0);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const referenceTime = useMemo(
    () => new Date("2017-12-31T23:00:00Z"),
    [],
  );

  useEffect(() => {
    async function loadPortfolio() {
      try {
        setLoading(true);
        setError(null);

        const buildingData =
          await getBuildings();

        const loadedBuildings =
          buildingData.buildings;

        setBuildings(loadedBuildings);

        /*
         * The dataset currently ends around the end
         * of 2017, so the portfolio snapshot uses the
         * same reference period as the Forecast and
         * Anomalies pages.
         */
        const to =
          referenceTime.toISOString();

        const from = new Date(
          referenceTime.getTime() -
            24 * 60 * 60 * 1000,
        ).toISOString();

        const results =
          await Promise.allSettled(
            loadedBuildings.map(
              async (building) => {
                const [
                  consumption,
                  anomalies,
                ] =
                  await Promise.all([
                    getBuildingConsumption(
                      building.building_id,
                      from,
                      to,
                    ),
                    getBuildingAnomalies(
                      building.building_id,
                      from,
                      to,
                    ),
                  ]);

                return {
                  building,
                  consumption,
                  anomalies,
                };
              },
            ),
          );

        const successfulResults =
          results
            .filter(
              (
                result,
              ): result is PromiseFulfilledResult<{
                building: Building;
                consumption: {
                  building_id: string;
                  from: string | null;
                  to: string | null;
                  points: {
                    timestamp: string;
                    energy_kwh: number | null;
                  }[];
                };
                anomalies: AnomalyAnalysis;
              }> =>
                result.status ===
                "fulfilled",
            )
            .map(
              (result) =>
                result.value,
            );

        let anomalyTotal = 0;
        let highTotal = 0;
        let analyzedTotal = 0;

        const energyByBuilding: BuildingEnergy[] =
          [];

        const hourlyTotals = new Map<
          string,
          number
        >();

        for (const result of successfulResults) {
          const validPoints =
            result.consumption.points.filter(
              (
                point,
              ): point is {
                timestamp: string;
                energy_kwh: number;
              } =>
                point.energy_kwh !== null &&
                Number.isFinite(
                  point.energy_kwh,
                ),
            );

          const buildingTotal =
            validPoints.reduce(
              (sum, point) =>
                sum + point.energy_kwh,
              0,
            );

          energyByBuilding.push({
            building:
              result.building,
            energy: buildingTotal,
            anomalies:
              result.anomalies
                .anomalies_detected,
          });

          anomalyTotal +=
            result.anomalies
              .anomalies_detected;

          highTotal +=
            result.anomalies
              .high_severity;

          analyzedTotal +=
            result.anomalies
              .points_analyzed;

          for (const point of validPoints) {
            const hour = new Date(
              point.timestamp,
            )
              .toISOString()
              .slice(0, 13);

            hourlyTotals.set(
              hour,
              (hourlyTotals.get(hour) ??
                0) +
                point.energy_kwh,
            );
          }
        }

        const sortedHours = [
          ...hourlyTotals.entries(),
        ]
          .sort(([a], [b]) =>
            a.localeCompare(b),
          )
          .slice(-24);

        const trend: PortfolioPoint[] =
          sortedHours.map(
            ([hour, energy]) => {
              const date = new Date(
                `${hour}:00:00Z`,
              );

              return {
                hour,
                label: date.toLocaleTimeString(
                  undefined,
                  {
                    hour: "numeric",
                    hour12: true,
                  },
                ),
                energy,
              };
            },
          );

        setBuildingEnergy(
          energyByBuilding.sort(
            (a, b) =>
              b.energy - a.energy,
          ),
        );

        setPortfolioTrend(trend);
        setTotalAnomalies(anomalyTotal);
        setHighAnomalies(highTotal);
        setPointsAnalyzed(
          analyzedTotal,
        );
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load portfolio data",
        );
      } finally {
        setLoading(false);
      }
    }

    loadPortfolio();
  }, [referenceTime]);

  const totalEnergy = buildingEnergy.reduce(
    (sum, item) =>
      sum + item.energy,
    0,
  );

  const averageHourlyEnergy =
    portfolioTrend.length > 0
      ? portfolioTrend.reduce(
          (sum, point) =>
            sum + point.energy,
          0,
        ) / portfolioTrend.length
      : 0;

  const activeBuildings =
    buildingEnergy.filter(
      (item) => item.energy > 0,
    ).length;

  const buildingWithMostEnergy =
    buildingEnergy[0];

  const anomalyRate =
    pointsAnalyzed > 0
      ? (totalAnomalies /
          pointsAnalyzed) *
        100
      : 0;

  const maxTrendEnergy = Math.max(
    ...portfolioTrend.map(
      (point) => point.energy,
    ),
    1,
  );

  const maxBuildingEnergy = Math.max(
    ...buildingEnergy
      .slice(0, 6)
      .map((item) => item.energy),
    1,
  );

  return (
    <main className="min-h-screen bg-[#f6f8fb] text-slate-950">
      <div className="mx-auto max-w-[1500px] px-6 py-7 md:px-10 lg:px-12">

        {/* =========================================================
            HEADER
        ========================================================= */}
        <header className="mb-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm font-medium tracking-wide text-slate-500">
                Energy operations
              </p>

              <h1 className="mt-1 text-4xl font-semibold tracking-[-0.035em] text-slate-950 md:text-5xl">
                Portfolio overview
              </h1>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500 md:text-base">
                A live analytical view of energy behaviour,
                anomalies, and operational signals across
                the monitored building portfolio.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <div className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-500 shadow-sm">
                Portfolio · BDG2
              </div>

              <div className="flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-xs font-semibold text-slate-600 shadow-sm">
                OP
              </div>
            </div>
          </div>
        </header>

        {error && (
          <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* =========================================================
            HERO PORTFOLIO SNAPSHOT
        ========================================================= */}
        <section className="relative mb-6 overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-[0_10px_40px_rgba(15,23,42,0.04)]">

          <div className="grid lg:grid-cols-[1.1fr_0.9fr]">

            {/* Main metric */}
            <div className="relative overflow-hidden p-7 md:p-9">

              <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-slate-100/80 blur-3xl" />

              <div className="relative">
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-emerald-500" />

                  <span className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
                    Portfolio energy snapshot
                  </span>
                </div>

                <div className="mt-7 flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
                  <div>
                    <p className="text-sm text-slate-500">
                      Consumption · last 24 hours
                    </p>

                    <div className="mt-2 flex items-baseline gap-2">
                      <span className="text-5xl font-semibold tracking-[-0.045em] text-slate-950 md:text-6xl">
                        {loading
                          ? "—"
                          : formatCompact(
                              totalEnergy,
                            )}
                      </span>

                      <span className="text-sm font-medium text-slate-400">
                        kWh
                      </span>
                    </div>

                    <p className="mt-3 text-sm text-slate-500">
                      {loading
                        ? "Calculating portfolio activity..."
                        : `${activeBuildings} of ${buildings.length} buildings reporting energy`}
                    </p>
                  </div>

                  {/* Energy illustration */}
                  <div className="relative hidden h-32 w-52 shrink-0 sm:block">
                    <svg
                      viewBox="0 0 220 130"
                      className="h-full w-full"
                      fill="none"
                      aria-hidden="true"
                    >
                      <path
                        d="M8 96 C 40 94, 45 67, 73 71 C 102 75, 103 103, 130 91 C 158 78, 162 43, 192 47 C 204 49, 211 40, 216 31"
                        stroke="currentColor"
                        strokeWidth="2"
                        className="text-slate-200"
                      />

                      <path
                        d="M8 96 C 40 94, 45 67, 73 71 C 102 75, 103 103, 130 91 C 158 78, 162 43, 192 47 C 204 49, 211 40, 216 31"
                        stroke="currentColor"
                        strokeWidth="3"
                        strokeLinecap="round"
                        className="text-slate-900"
                      />

                      <circle
                        cx="8"
                        cy="96"
                        r="5"
                        className="fill-slate-900"
                      />

                      <circle
                        cx="73"
                        cy="71"
                        r="5"
                        className="fill-slate-900"
                      />

                      <circle
                        cx="130"
                        cy="91"
                        r="5"
                        className="fill-slate-900"
                      />

                      <circle
                        cx="192"
                        cy="47"
                        r="5"
                        className="fill-slate-900"
                      />

                      <path
                        d="M190 22 L190 48 L176 48 L201 76 L198 51 L214 51 Z"
                        className="fill-slate-900"
                      />
                    </svg>
                  </div>
                </div>
              </div>
            </div>

            {/* Snapshot metrics */}
            <div className="grid grid-cols-2 border-t border-slate-100 lg:border-l lg:border-t-0">
              <div className="border-b border-r border-slate-100 p-6 md:p-8">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                  Avg. hourly load
                </p>

                <p className="mt-4 text-3xl font-semibold tracking-tight">
                  {loading
                    ? "—"
                    : formatNumber(
                        averageHourlyEnergy,
                        1,
                      )}
                </p>

                <p className="mt-2 text-xs text-slate-500">
                  kWh / hour
                </p>
              </div>

              <div className="border-b border-slate-100 p-6 md:p-8">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                  Anomalies
                </p>

                <p className="mt-4 text-3xl font-semibold tracking-tight">
                  {loading
                    ? "—"
                    : totalAnomalies}
                </p>

                <p className="mt-2 text-xs text-slate-500">
                  detected in 24h
                </p>
              </div>

              <div className="border-r border-slate-100 p-6 md:p-8">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                  High severity
                </p>

                <p className="mt-4 text-3xl font-semibold tracking-tight">
                  {loading
                    ? "—"
                    : highAnomalies}
                </p>

                <p className="mt-2 text-xs text-slate-500">
                  priority signals
                </p>
              </div>

              <div className="p-6 md:p-8">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                  Data coverage
                </p>

                <p className="mt-4 text-3xl font-semibold tracking-tight">
                  {loading
                    ? "—"
                    : `${formatNumber(
                        (activeBuildings /
                          Math.max(
                            buildings.length,
                            1,
                          )) *
                          100,
                      )}%`}
                </p>

                <p className="mt-2 text-xs text-slate-500">
                  buildings reporting
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* =========================================================
            ANALYTICAL GRID
        ========================================================= */}
        <div className="grid gap-6 xl:grid-cols-[1.65fr_1fr]">

          {/* =======================================================
              PORTFOLIO CONSUMPTION CHART
          ======================================================= */}
          <section className="rounded-[24px] border border-slate-200 bg-white p-6 shadow-[0_8px_30px_rgba(15,23,42,0.035)] md:p-7">

            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">
                  Portfolio signal
                </p>

                <h2 className="mt-2 text-xl font-semibold tracking-tight">
                  Energy consumption
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Combined hourly consumption across monitored buildings.
                </p>
              </div>

              <div className="rounded-full bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-500">
                Last 24 hours
              </div>
            </div>

            <div className="mt-8">
              {loading ? (
                <div className="flex h-[280px] items-center justify-center rounded-2xl bg-slate-50">
                  <span className="text-sm text-slate-400">
                    Loading portfolio signal...
                  </span>
                </div>
              ) : portfolioTrend.length === 0 ? (
                <div className="flex h-[280px] items-center justify-center rounded-2xl bg-slate-50">
                  <span className="text-sm text-slate-400">
                    No consumption data available.
                  </span>
                </div>
              ) : (
                <div className="relative h-[280px]">

                  {/* Grid */}
                  <div className="pointer-events-none absolute inset-0 flex flex-col justify-between">
                    {[0, 1, 2, 3].map(
                      (line) => (
                        <div
                          key={line}
                          className="border-t border-dashed border-slate-100"
                        />
                      ),
                    )}
                  </div>

                  {/* Bars */}
                  <div className="absolute inset-x-0 bottom-8 top-4 flex items-end gap-[3px] px-1">
                    {portfolioTrend.map(
                      (point, index) => {
                        const height =
                          Math.max(
                            (point.energy /
                              maxTrendEnergy) *
                              100,
                            3,
                          );

                        const isPeak =
                          point.energy ===
                          maxTrendEnergy;

                        return (
                          <div
                            key={point.hour}
                            className="group relative flex h-full flex-1 items-end"
                          >
                            <div
                              className={`w-full rounded-t-md transition-all duration-300 ${
                                isPeak
                                  ? "bg-slate-900"
                                  : "bg-slate-200 group-hover:bg-slate-400"
                              }`}
                              style={{
                                height: `${height}%`,
                              }}
                            />

                            <div className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-2 hidden -translate-x-1/2 whitespace-nowrap rounded-lg bg-slate-950 px-3 py-2 text-xs text-white shadow-lg group-hover:block">
                              {point.label}
                              <br />
                              <span className="text-slate-300">
                                {formatNumber(
                                  point.energy,
                                  1,
                                )}{" "}
                                kWh
                              </span>
                            </div>

                            {index %
                              Math.max(
                                Math.ceil(
                                  portfolioTrend.length /
                                    6,
                                ),
                                1,
                              ) ===
                              0 && (
                              <span className="absolute left-1/2 top-full mt-3 -translate-x-1/2 whitespace-nowrap text-[10px] text-slate-400">
                                {point.label}
                              </span>
                            )}
                          </div>
                        );
                      },
                    )}
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* =======================================================
              PORTFOLIO STATUS ILLUSTRATION
          ======================================================= */}
          <section className="relative overflow-hidden rounded-[24px] border border-slate-200 bg-slate-950 p-7 text-white shadow-[0_12px_40px_rgba(15,23,42,0.08)]">

            <div className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-white/[0.05] blur-3xl" />

            <div className="relative">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">
                Operational picture
              </p>

              <h2 className="mt-2 text-2xl font-semibold tracking-tight">
                Portfolio health
              </h2>

              <p className="mt-2 text-sm leading-6 text-slate-400">
                A compact view of the signals currently coming
                from the energy intelligence layer.
              </p>

              {/* Illustration */}
              <div className="mt-7 flex h-36 items-center justify-center">
                <svg
                  viewBox="0 0 360 150"
                  className="h-full w-full"
                  fill="none"
                  aria-hidden="true"
                >
                  <path
                    d="M20 118 H340"
                    stroke="currentColor"
                    strokeWidth="1"
                    className="text-white/10"
                  />

                  <path
                    d="M42 108 V79 H82 V108"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="text-white/50"
                  />

                  <path
                    d="M92 108 V52 H137 V108"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="text-white/70"
                  />

                  <path
                    d="M147 108 V67 H191 V108"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="text-white/50"
                  />

                  <path
                    d="M202 108 V36 H250 V108"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="text-white/80"
                  />

                  <path
                    d="M262 108 V76 H310 V108"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="text-white/50"
                  />

                  <path
                    d="M20 36 C 72 26, 91 48, 134 33 C 174 18, 190 44, 224 27 C 262 8, 284 36, 340 17"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    className="text-white"
                  />

                  <circle
                    cx="340"
                    cy="17"
                    r="5"
                    className="fill-white"
                  />
                </svg>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-2xl border border-white/10 bg-white/[0.06] p-4">
                  <p className="text-xs text-slate-400">
                    Reporting
                  </p>

                  <p className="mt-2 text-xl font-semibold">
                    {loading
                      ? "—"
                      : `${activeBuildings}/${buildings.length}`}
                  </p>

                  <p className="mt-1 text-[11px] text-slate-500">
                    buildings
                  </p>
                </div>

                <div className="rounded-2xl border border-white/10 bg-white/[0.06] p-4">
                  <p className="text-xs text-slate-400">
                    Anomaly rate
                  </p>

                  <p className="mt-2 text-xl font-semibold">
                    {loading
                      ? "—"
                      : `${anomalyRate.toFixed(1)}%`}
                  </p>

                  <p className="mt-1 text-[11px] text-slate-500">
                    of analysed observations
                  </p>
                </div>
              </div>
            </div>
          </section>
        </div>

        {/* =========================================================
            LOWER ANALYTICAL ROW
        ========================================================= */}
        <div className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">

          {/* Building energy distribution */}
          <section className="rounded-[24px] border border-slate-200 bg-white p-6 shadow-[0_8px_30px_rgba(15,23,42,0.035)] md:p-7">

            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">
                  Portfolio composition
                </p>

                <h2 className="mt-2 text-xl font-semibold tracking-tight">
                  Energy by building
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Relative contribution to the current 24-hour load.
                </p>
              </div>

              {buildingWithMostEnergy && (
                <div className="hidden rounded-full bg-slate-50 px-3 py-1.5 text-xs text-slate-500 sm:block">
                  Highest contributor
                </div>
              )}
            </div>

            <div className="mt-7 space-y-5">
              {loading ? (
                <div className="py-10 text-center text-sm text-slate-400">
                  Loading building distribution...
                </div>
              ) : buildingEnergy.length === 0 ? (
                <div className="py-10 text-center text-sm text-slate-400">
                  No building energy data available.
                </div>
              ) : (
                buildingEnergy
                  .slice(0, 6)
                  .map((item) => {
                    const share =
                      totalEnergy > 0
                        ? (item.energy /
                            totalEnergy) *
                          100
                        : 0;

                    const width =
                      (item.energy /
                        maxBuildingEnergy) *
                      100;

                    return (
                      <div
                        key={
                          item.building
                            .building_id
                        }
                      >
                        <div className="mb-2 flex items-center justify-between gap-4">
                          <div className="min-w-0">
                            <p className="truncate text-sm font-medium text-slate-800">
                              {shortBuildingName(
                                item.building,
                              )}
                            </p>

                            <p className="mt-0.5 text-[11px] text-slate-400">
                              {
                                item.building
                                  .primary_use
                              }
                            </p>
                          </div>

                          <div className="shrink-0 text-right">
                            <p className="text-sm font-semibold text-slate-800">
                              {formatNumber(
                                item.energy,
                                1,
                              )}{" "}
                              kWh
                            </p>

                            <p className="text-[11px] text-slate-400">
                              {share.toFixed(
                                1,
                              )}
                              %
                            </p>
                          </div>
                        </div>

                        <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                          <div
                            className="h-full rounded-full bg-slate-900 transition-all duration-700"
                            style={{
                              width: `${width}%`,
                            }}
                          />
                        </div>
                      </div>
                    );
                  })
              )}
            </div>
          </section>

          {/* Intelligence summary */}
          <section className="rounded-[24px] border border-slate-200 bg-white p-6 shadow-[0_8px_30px_rgba(15,23,42,0.035)] md:p-7">

            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">
              Intelligence layer
            </p>

            <h2 className="mt-2 text-xl font-semibold tracking-tight">
              What the system is watching
            </h2>

            <div className="mt-7 space-y-3">

              <div className="flex gap-4 rounded-2xl bg-slate-50 p-4">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-sm font-semibold text-slate-800 shadow-sm ring-1 ring-slate-200">
                  01
                </div>

                <div>
                  <p className="text-sm font-semibold text-slate-800">
                    Consumption behaviour
                  </p>

                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    Tracks hourly energy demand across the
                    portfolio and individual buildings.
                  </p>
                </div>
              </div>

              <div className="flex gap-4 rounded-2xl bg-slate-50 p-4">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-sm font-semibold text-slate-800 shadow-sm ring-1 ring-slate-200">
                  02
                </div>

                <div>
                  <p className="text-sm font-semibold text-slate-800">
                    Forecast behaviour
                  </p>

                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    Uses the production inference pipeline to
                    estimate upcoming energy demand.
                  </p>
                </div>
              </div>

              <div className="flex gap-4 rounded-2xl bg-slate-50 p-4">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-sm font-semibold text-slate-800 shadow-sm ring-1 ring-slate-200">
                  03
                </div>

                <div>
                  <p className="text-sm font-semibold text-slate-800">
                    Anomaly detection
                  </p>

                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    Identifies consumption behaviour that
                    deviates significantly from historical patterns.
                  </p>
                </div>
              </div>

              <div className="flex gap-4 rounded-2xl bg-slate-50 p-4">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-sm font-semibold text-slate-800 shadow-sm ring-1 ring-slate-200">
                  04
                </div>

                <div>
                  <p className="text-sm font-semibold text-slate-800">
                    Data quality
                  </p>

                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    Measures how much usable consumption data is
                    available for analytical workflows.
                  </p>
                </div>
              </div>
            </div>
          </section>
        </div>

        {/* =========================================================
            FOOTER STATUS STRIP
        ========================================================= */}
        <section className="mt-6 flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white px-6 py-5 shadow-sm sm:flex-row sm:items-center sm:justify-between">

          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-50">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
            </span>

            <div>
              <p className="text-sm font-semibold text-slate-800">
                Data layer operational
              </p>

              <p className="mt-0.5 text-xs text-slate-500">
                Portfolio analytics are connected to the application data layer.
              </p>
            </div>
          </div>

          <div className="text-xs text-slate-400">
            Snapshot · January 1, 2018 · 4:30 AM UTC
          </div>
        </section>
      </div>
    </main>
  );
}