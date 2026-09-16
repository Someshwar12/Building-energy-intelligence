"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import ConsumptionChart from "@/components/ConsumptionChart";
import {
  getBuilding,
  getBuildingConsumption,
  getBuildingForecast,
  getBuildings,
  type Building,
  type ConsumptionPoint,
  type Forecast,
} from "@/lib/api";

type Period = "24h" | "7d" | "30d";

const REFERENCE_TIME = new Date(
  "2017-12-31T23:00:00Z",
);

const PERIOD_CONFIG: Record<
  Period,
  {
    label: string;
    subtitle: string;
    hours: number;
  }
> = {
  "24h": {
    label: "Past 24 hours",
    subtitle:
      "Hourly electricity consumption · Last 24 hours",
    hours: 24,
  },
  "7d": {
    label: "Past 7 days",
    subtitle:
      "Hourly electricity consumption · Last 7 days",
    hours: 24 * 7,
  },
  "30d": {
    label: "Past 30 days",
    subtitle:
      "Hourly electricity consumption · December 2017",
    hours: 24 * 30,
  },
};

export default function BuildingDetailsPage() {
  const params = useParams<{
    buildingId: string;
  }>();

  const router = useRouter();

  const [building, setBuilding] =
    useState<Building | null>(null);

  const [buildings, setBuildings] =
    useState<Building[]>([]);

  const [consumption, setConsumption] =
    useState<ConsumptionPoint[]>([]);

  const [forecast, setForecast] =
    useState<Forecast | null>(null);

  const [period, setPeriod] =
    useState<Period>("30d");

  const [loading, setLoading] =
    useState(true);

  const [buildingsLoading, setBuildingsLoading] =
    useState(true);

  const [consumptionLoading, setConsumptionLoading] =
    useState(true);

  const [forecastLoading, setForecastLoading] =
    useState(true);

  const [error, setError] =
    useState(false);

  const [consumptionError, setConsumptionError] =
    useState(false);

  const [forecastError, setForecastError] =
    useState(false);

  useEffect(() => {
    async function loadBuilding() {
      try {
        const data = await getBuilding(
          params.buildingId,
        );

        setBuilding(data.building);
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    }

    loadBuilding();
  }, [params.buildingId]);

  useEffect(() => {
    async function loadBuildings() {
      try {
        const data = await getBuildings();

        setBuildings(data.buildings);
      } catch {
        // Building navigation is an enhancement.
        // The page itself should remain usable if
        // the building list cannot be retrieved.
        setBuildings([]);
      } finally {
        setBuildingsLoading(false);
      }
    }

    loadBuildings();
  }, []);

  useEffect(() => {
    async function loadConsumption() {
      setConsumptionLoading(true);
      setConsumptionError(false);

      try {
        const periodHours =
          PERIOD_CONFIG[period].hours;

        // The API range is inclusive, so subtract
        // one hour to return exactly 24 / 168 / 720
        // hourly observations.
        const from = new Date(
          REFERENCE_TIME.getTime() -
            (periodHours - 1) *
              60 *
              60 *
              1000,
        );

        const data =
          await getBuildingConsumption(
            params.buildingId,
            from.toISOString(),
            REFERENCE_TIME.toISOString(),
          );

        setConsumption(data.points);
      } catch {
        setConsumptionError(true);
      } finally {
        setConsumptionLoading(false);
      }
    }

    loadConsumption();
  }, [params.buildingId, period]);

  useEffect(() => {
    async function loadForecast() {
      setForecastLoading(true);
      setForecastError(false);

      try {
        const data =
          await getBuildingForecast(
            params.buildingId,
            "2017-12-31T23:00:00Z",
          );

        setForecast(data);
      } catch {
        setForecastError(true);
      } finally {
        setForecastLoading(false);
      }
    }

    loadForecast();
  }, [params.buildingId]);

  if (loading) {
    return (
      <main className="min-h-screen bg-[#f7f8fa] p-8">
        <div className="mx-auto max-w-7xl">
          <div className="animate-pulse">
            <div className="h-4 w-32 rounded bg-slate-200" />

            <div className="mt-4 h-8 w-72 rounded bg-slate-200" />

            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[1, 2, 3, 4].map(
                (item) => (
                  <div
                    key={item}
                    className="h-32 rounded-2xl border border-slate-200 bg-white"
                  />
                ),
              )}
            </div>
          </div>
        </div>
      </main>
    );
  }

  if (error || !building) {
    return (
      <main className="min-h-screen bg-[#f7f8fa] p-8">
        <div className="mx-auto max-w-3xl">
          <div className="rounded-2xl border border-slate-200 bg-white p-8">
            <h1 className="text-lg font-semibold">
              Building unavailable
            </h1>

            <p className="mt-2 text-sm text-slate-500">
              We could not retrieve this building.
            </p>

            <Link
              href="/"
              className="mt-6 inline-flex rounded-lg bg-slate-950 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800"
            >
              Return to overview
            </Link>
          </div>
        </div>
      </main>
    );
  }

  const selectedPeriod =
    PERIOD_CONFIG[period];

  const currentIndex =
    buildings.findIndex(
      (item) =>
        item.building_id ===
        building.building_id,
    );

  const hasNavigation =
    !buildingsLoading &&
    currentIndex >= 0 &&
    buildings.length > 1;

  const previousBuilding =
    hasNavigation && currentIndex > 0
      ? buildings[currentIndex - 1]
      : null;

  const nextBuilding =
    hasNavigation &&
    currentIndex < buildings.length - 1
      ? buildings[currentIndex + 1]
      : null;

  function navigateToBuilding(
    target: Building | null,
  ) {
    if (!target) {
      return;
    }

    router.push(
      `/buildings/${encodeURIComponent(
        target.building_id,
      )}`,
    );
  }

  return (
    <main className="min-h-screen bg-[#f7f8fa] text-slate-950">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-5 py-5 sm:px-8">
          <div className="flex items-center justify-between gap-4">
            <Link
              href="/"
              className="text-xs font-medium text-slate-400 transition hover:text-slate-950"
            >
              ← Overview
            </Link>

            {hasNavigation && (
              <div className="text-xs font-medium text-slate-400">
                {currentIndex + 1} /{" "}
                {buildings.length}
              </div>
            )}
          </div>

          <div className="mt-6 flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
            <div>
              <div className="text-xs font-medium text-slate-400">
                Building
              </div>

              <h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">
                {building.name}
              </h1>

              <p className="mt-2 text-sm text-slate-500">
                {building.primary_use ??
                  "Unknown use"}{" "}
                · {building.site_id}
              </p>
            </div>

            <div className="flex items-center gap-2">
              {hasNavigation && (
                <>
                  <button
                    type="button"
                    disabled={!previousBuilding}
                    onClick={() =>
                      navigateToBuilding(
                        previousBuilding,
                      )
                    }
                    className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900 disabled:cursor-not-allowed disabled:opacity-35"
                  >
                    ‹ Previous
                  </button>

                  <button
                    type="button"
                    disabled={!nextBuilding}
                    onClick={() =>
                      navigateToBuilding(
                        nextBuilding,
                      )
                    }
                    className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900 disabled:cursor-not-allowed disabled:opacity-35"
                  >
                    Next ›
                  </button>
                </>
              )}

              <div className="ml-1 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-500">
                {building.building_id}
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <InfoCard
            label="Floor area"
            value={
              building.floor_area !=
              null
                ? `${building.floor_area.toLocaleString()} m²`
                : "Unavailable"
            }
          />

          <InfoCard
            label="Floor area (sq ft)"
            value={
              building.square_feet !=
              null
                ? `${building.square_feet.toLocaleString()} ft²`
                : "Unavailable"
            }
          />

          <InfoCard
            label="Timezone"
            value={
              building.timezone ??
              "Unavailable"
            }
          />

          <InfoCard
            label="Primary use"
            value={
              building.primary_use ??
              "Unavailable"
            }
          />
        </section>

        <section className="mt-8 grid gap-6 lg:grid-cols-[1.5fr_1fr]">
          <div className="rounded-2xl border border-slate-200 bg-white">
            <div className="border-b border-slate-100 px-6 py-5">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <h2 className="text-sm font-semibold">
                    Consumption
                  </h2>

                  <p className="mt-1 text-xs text-slate-400">
                    {selectedPeriod.subtitle}
                  </p>
                </div>

                <div className="flex items-center gap-1 rounded-xl border border-slate-200 bg-slate-50 p-1">
                  {(
                    [
                      "24h",
                      "7d",
                      "30d",
                    ] as Period[]
                  ).map((value) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() =>
                        setPeriod(value)
                      }
                      className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                        period === value
                          ? "bg-slate-900 text-white shadow-sm"
                          : "text-slate-500 hover:bg-white hover:text-slate-800"
                      }`}
                    >
                      {value}
                    </button>
                  ))}
                </div>

                {!consumptionLoading &&
                  !consumptionError &&
                  consumption.length >
                    0 && (
                    <div className="text-xs font-medium text-slate-400">
                      {consumption.length.toLocaleString()}{" "}
                      observations
                    </div>
                  )}
              </div>
            </div>

            <div className="px-6 py-6">
              {consumptionLoading && (
                <div className="h-72 animate-pulse rounded-xl bg-slate-50" />
              )}

              {!consumptionLoading &&
                consumptionError && (
                  <div className="flex h-72 items-center justify-center">
                    <div className="max-w-sm text-center">
                      <div className="text-sm font-medium text-slate-700">
                        Consumption unavailable
                      </div>

                      <p className="mt-2 text-xs leading-5 text-slate-400">
                        Historical consumption
                        could not be retrieved
                        for this building.
                      </p>
                    </div>
                  </div>
                )}

              {!consumptionLoading &&
                !consumptionError &&
                consumption.length ===
                  0 && (
                  <div className="flex h-72 items-center justify-center">
                    <div className="max-w-sm text-center">
                      <div className="text-sm font-medium text-slate-700">
                        No consumption data
                      </div>

                      <p className="mt-2 text-xs leading-5 text-slate-400">
                        No historical
                        observations are
                        available for the
                        selected period.
                      </p>
                    </div>
                  </div>
                )}

              {!consumptionLoading &&
                !consumptionError &&
                consumption.length >
                  0 && (
                  <ConsumptionChart
                    points={consumption}
                  />
                )}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white">
            <div className="border-b border-slate-100 px-6 py-5">
              <h2 className="text-sm font-semibold">
                Next-hour forecast
              </h2>

              <p className="mt-1 text-xs text-slate-400">
                Model prediction generated from
                the building&apos;s historical
                context.
              </p>
            </div>

            <div className="px-6 py-6">
              {forecastLoading && (
                <div className="animate-pulse rounded-xl bg-slate-50 px-5 py-6">
                  <div className="h-3 w-28 rounded bg-slate-200" />

                  <div className="mt-3 h-9 w-40 rounded bg-slate-200" />
                </div>
              )}

              {!forecastLoading &&
                forecastError && (
                  <div className="rounded-xl bg-slate-50 px-5 py-6">
                    <div className="text-sm font-medium text-slate-700">
                      Forecast unavailable
                    </div>

                    <p className="mt-2 text-xs leading-5 text-slate-400">
                      The application could
                      not obtain a prediction
                      from the ML service.
                    </p>
                  </div>
                )}

              {!forecastLoading &&
                !forecastError &&
                forecast && (
                  <div>
                    <div className="text-xs font-medium text-slate-400">
                      Predicted consumption
                    </div>

                    <div className="mt-2 text-4xl font-semibold tracking-tight">
                      {forecast.predicted_energy_kwh.toLocaleString(
                        undefined,
                        {
                          maximumFractionDigits: 1,
                        },
                      )}{" "}
                      <span className="text-lg font-medium text-slate-400">
                        kWh
                      </span>
                    </div>

                    <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                      <div className="text-[11px] font-medium uppercase tracking-wide text-slate-400">
                        Model
                      </div>

                      <div className="mt-1 text-sm font-medium text-slate-700">
                        {forecast.model_name}
                      </div>

                      <div className="mt-1 text-xs text-slate-400">
                        {forecast.model_version}
                      </div>

                      <div className="mt-3 text-xs text-slate-400">
                        {new Date(
                          forecast.timestamp,
                        ).toLocaleString()}
                      </div>
                    </div>
                  </div>
                )}
            </div>
          </div>
        </section>

        <section className="mt-6 rounded-2xl border border-slate-200 bg-white">
          <div className="border-b border-slate-100 px-6 py-5">
            <h2 className="text-sm font-semibold">
              Building profile
            </h2>

            <p className="mt-1 text-xs text-slate-400">
              Reference information from the
              building metadata.
            </p>
          </div>

          <div className="grid divide-y divide-slate-100 sm:grid-cols-2 sm:divide-y-0">
            <div className="sm:border-r sm:border-slate-100">
              <DetailRow
                label="Year built"
                value={
                  building.year_built?.toString() ??
                  "Unavailable"
                }
              />

              <DetailRow
                label="Floors"
                value={
                  building.number_of_floors?.toString() ??
                  "Unavailable"
                }
              />

              <DetailRow
                label="Occupants"
                value={
                  building.occupants?.toLocaleString() ??
                  "Unavailable"
                }
              />
            </div>

            <div>
              <DetailRow
                label="Heating"
                value={
                  building.heating_type ??
                  "Unavailable"
                }
              />

              <DetailRow
                label="LEED"
                value={
                  building.leed_level ??
                  "Unavailable"
                }
              />

              <DetailRow
                label="Site EUI"
                value={
                  building.site_eui !=
                  null
                    ? `${building.site_eui.toLocaleString()}`
                    : "Unavailable"
                }
              />
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

function InfoCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="text-xs font-medium text-slate-400">
        {label}
      </div>

      <div className="mt-3 text-sm font-semibold">
        {value}
      </div>
    </div>
  );
}

function DetailRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between gap-6 px-6 py-4">
      <span className="text-xs text-slate-400">
        {label}
      </span>

      <span className="text-right text-xs font-medium text-slate-700">
        {value}
      </span>
    </div>
  );
}