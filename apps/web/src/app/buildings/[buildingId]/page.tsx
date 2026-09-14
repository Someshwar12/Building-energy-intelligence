"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import ConsumptionChart from "@/components/ConsumptionChart";
import {
  getBuilding,
  getBuildingConsumption,
  getBuildingForecast,
  type Building,
  type ConsumptionPoint,
  type Forecast,
} from "@/lib/api";

export default function BuildingDetailsPage() {
  const params = useParams<{ buildingId: string }>();

  const [building, setBuilding] =
    useState<Building | null>(null);

  const [consumption, setConsumption] =
    useState<ConsumptionPoint[]>([]);

  const [forecast, setForecast] =
    useState<Forecast | null>(null);

  const [loading, setLoading] = useState(true);
  const [consumptionLoading, setConsumptionLoading] =
    useState(true);
  const [forecastLoading, setForecastLoading] =
    useState(true);

  const [error, setError] = useState(false);
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
    async function loadConsumption() {
      setConsumptionLoading(true);
      setConsumptionError(false);

      try {
        const data = await getBuildingConsumption(
          params.buildingId,
          "2017-12-02T00:00:00Z",
          "2017-12-31T23:00:00Z",
        );

        setConsumption(data.points);
      } catch {
        setConsumptionError(true);
      } finally {
        setConsumptionLoading(false);
      }
    }

    loadConsumption();
  }, [params.buildingId]);

  useEffect(() => {
    async function loadForecast() {
      setForecastLoading(true);
      setForecastError(false);

      try {
        const data = await getBuildingForecast(
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
              {[1, 2, 3, 4].map((item) => (
                <div
                  key={item}
                  className="h-32 rounded-2xl border border-slate-200 bg-white"
                />
              ))}
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

  return (
    <main className="min-h-screen bg-[#f7f8fa] text-slate-950">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-5 py-5 sm:px-8">
          <Link
            href="/"
            className="text-xs font-medium text-slate-400 transition hover:text-slate-950"
          >
            ← Overview
          </Link>

          <div className="mt-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
            <div>
              <div className="text-xs font-medium text-slate-400">
                Building
              </div>

              <h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">
                {building.name}
              </h1>

              <p className="mt-2 text-sm text-slate-500">
                {building.primary_use ?? "Unknown use"} ·{" "}
                {building.site_id}
              </p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-500">
              {building.building_id}
            </div>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <InfoCard
            label="Floor area"
            value={
              building.floor_area != null
                ? `${building.floor_area.toLocaleString()} m²`
                : "Unavailable"
            }
          />

          <InfoCard
            label="Floor area (sq ft)"
            value={
              building.square_feet != null
                ? `${building.square_feet.toLocaleString()} ft²`
                : "Unavailable"
            }
          />

          <InfoCard
            label="Timezone"
            value={building.timezone ?? "Unavailable"}
          />

          <InfoCard
            label="Primary use"
            value={building.primary_use ?? "Unavailable"}
          />
        </section>

        <section className="mt-8 grid gap-6 lg:grid-cols-[1.5fr_1fr]">
          <div className="rounded-2xl border border-slate-200 bg-white">
            <div className="border-b border-slate-100 px-6 py-5">
              <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-end">
                <div>
                  <h2 className="text-sm font-semibold">
                    Consumption
                  </h2>

                  <p className="mt-1 text-xs text-slate-400">
                    Hourly electricity consumption · December
                    2017
                  </p>
                </div>

                {!consumptionLoading &&
                  !consumptionError &&
                  consumption.length > 0 && (
                    <div className="text-xs font-medium text-slate-400">
                      {consumption.length.toLocaleString()} observations
                    </div>
                  )}
              </div>
            </div>

            <div className="px-6 py-6">
              {consumptionLoading && (
                <div className="h-72 animate-pulse rounded-xl bg-slate-50" />
              )}

              {!consumptionLoading && consumptionError && (
                <div className="flex h-72 items-center justify-center">
                  <div className="max-w-sm text-center">
                    <div className="text-sm font-medium text-slate-700">
                      Consumption unavailable
                    </div>

                    <p className="mt-2 text-xs leading-5 text-slate-400">
                      Historical consumption could not be
                      retrieved for this building.
                    </p>
                  </div>
                </div>
              )}

              {!consumptionLoading &&
                !consumptionError &&
                consumption.length === 0 && (
                  <div className="flex h-72 items-center justify-center">
                    <div className="max-w-sm text-center">
                      <div className="text-sm font-medium text-slate-700">
                        No consumption data
                      </div>

                      <p className="mt-2 text-xs leading-5 text-slate-400">
                        No historical observations are available
                        for the selected period.
                      </p>
                    </div>
                  </div>
                )}

              {!consumptionLoading &&
                !consumptionError &&
                consumption.length > 0 && (
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
                Model prediction generated from the building&apos;s
                historical context.
              </p>
            </div>

            <div className="px-6 py-6">
              {forecastLoading && (
                <div className="animate-pulse rounded-xl bg-slate-50 px-5 py-6">
                  <div className="h-3 w-28 rounded bg-slate-200" />

                  <div className="mt-3 h-9 w-40 rounded bg-slate-200" />
                </div>
              )}

              {!forecastLoading && forecastError && (
                <div className="rounded-xl bg-slate-50 px-5 py-6">
                  <div className="text-sm font-medium text-slate-700">
                    Forecast unavailable
                  </div>

                  <p className="mt-2 text-xs leading-5 text-slate-400">
                    The application could not obtain a prediction
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
              Reference information from the building metadata.
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
                  building.site_eui != null
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