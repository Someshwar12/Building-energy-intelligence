"use client";

import { useEffect, useMemo, useState } from "react";

import {
  getMonitoringDrift,
  getMonitoringSummary,
  type MonitoringDrift,
  type MonitoringSummaryData,
} from "@/lib/api";

function formatMetric(
  value: number | null,
  digits = 1,
): string {
  if (value === null || !Number.isFinite(value)) {
    return "—";
  }

  return value.toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  });
}

function formatTimestamp(
  value: string | null,
): string {
  if (!value) {
    return "No prediction recorded";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function statusLabel(
  status: string,
): string {
  switch (status.toLowerCase()) {
    case "healthy":
      return "Healthy";
    case "warning":
      return "Warning";
    case "critical":
      return "Critical";
    case "insufficient_data":
      return "Awaiting data";
    default:
      return status.replaceAll("_", " ");
  }
}

function statusClasses(
  status: string,
): string {
  switch (status.toLowerCase()) {
    case "healthy":
      return "bg-emerald-50 text-emerald-700 border-emerald-200";
    case "warning":
      return "bg-amber-50 text-amber-700 border-amber-200";
    case "critical":
      return "bg-red-50 text-red-700 border-red-200";
    default:
      return "bg-slate-50 text-slate-600 border-slate-200";
  }
}

function featureLabel(
  feature: string,
): string {
  return feature
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase(),
    );
}

export default function MonitoringPage() {
  const [summary, setSummary] =
    useState<MonitoringSummaryData | null>(null);

  const [drift, setDrift] =
    useState<MonitoringDrift | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    async function loadMonitoring() {
      try {
        setLoading(true);
        setError(null);

        const [summaryData, driftData] =
          await Promise.all([
            getMonitoringSummary(),
            getMonitoringDrift(),
          ]);

        setSummary(summaryData);
        setDrift(driftData);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load monitoring data.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadMonitoring();
  }, []);

  const successRate = useMemo(() => {
    if (!summary) {
      return null;
    }

    const {
      total,
      successful,
    } = summary.monitoring.requests;

    if (total === 0) {
      return null;
    }

    return (successful / total) * 100;
  }, [summary]);

  const driftFeatures = useMemo(() => {
    if (!drift) {
      return [];
    }

    return Object.values(drift.features).sort(
      (a, b) =>
        (b.psi ?? -1) -
        (a.psi ?? -1),
    );
  }, [drift]);

  const driftCounts = useMemo(() => {
    let healthy = 0;
    let warning = 0;
    let critical = 0;

    for (const feature of driftFeatures) {
      switch (feature.status.toLowerCase()) {
        case "healthy":
          healthy += 1;
          break;
        case "warning":
          warning += 1;
          break;
        case "critical":
          critical += 1;
          break;
      }
    }

    return {
      healthy,
      warning,
      critical,
    };
  }, [driftFeatures]);

  return (
    <main className="min-h-screen bg-[#f6f8fb] text-slate-950">
      <div className="mx-auto max-w-[1500px] px-6 py-7 md:px-10 lg:px-12">

        {/* HEADER */}
        <header className="mb-8">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm font-medium tracking-wide text-slate-500">
                ML operations
              </p>

              <h1 className="mt-1 text-4xl font-semibold tracking-[-0.035em] md:text-5xl">
                Monitoring
              </h1>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500 md:text-base">
                Operational health, prediction activity,
                data quality, and feature drift across
                the inference service.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <div
                className={`rounded-full border px-4 py-2 text-sm font-medium ${
                  summary
                    ? statusClasses(
                        summary.service.status,
                      )
                    : "border-slate-200 bg-white text-slate-500"
                }`}
              >
                {summary
                  ? statusLabel(
                      summary.service.status,
                    )
                  : loading
                    ? "Loading"
                    : "Unavailable"}
              </div>

              <div className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-500 shadow-sm">
                Runtime observability
              </div>
            </div>
          </div>
        </header>

        {error && (
          <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* SERVICE + RELIABILITY */}
        <section className="mb-6 grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">

          <div className="rounded-[28px] border border-slate-200 bg-white p-7 shadow-[0_10px_40px_rgba(15,23,42,0.04)] md:p-8">
            <div className="flex items-start justify-between gap-5">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
                  Serving environment
                </p>

                <h2 className="mt-2 text-2xl font-semibold tracking-tight">
                  {summary?.service.name ??
                    "Model service"}
                </h2>
              </div>

              <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600">
                v{summary?.service.version ?? "—"}
              </span>
            </div>

            <div className="mt-8 grid gap-5 sm:grid-cols-3">
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-400">
                  Model
                </p>

                <p className="mt-2 text-lg font-semibold">
                  {summary?.service.model_name ??
                    "—"}
                </p>
              </div>

              <div>
                <p className="text-xs uppercase tracking-wide text-slate-400">
                  Version
                </p>

                <p className="mt-2 text-lg font-semibold">
                  {summary?.service.model_version ??
                    "—"}
                </p>
              </div>

              <div>
                <p className="text-xs uppercase tracking-wide text-slate-400">
                  Serving mode
                </p>

                <p className="mt-2 text-lg font-semibold capitalize">
                  {summary?.service.serving_mode ??
                    "—"}
                </p>
              </div>
            </div>

            <div className="mt-8 border-t border-slate-100 pt-5">
              <p className="text-xs uppercase tracking-wide text-slate-400">
                Last successful inference
              </p>

              <p className="mt-2 text-sm font-medium text-slate-700">
                {formatTimestamp(
                  summary?.monitoring
                    .last_prediction_at ??
                    null,
                )}
              </p>
            </div>
          </div>

          <div className="rounded-[28px] border border-slate-200 bg-slate-950 p-7 text-white shadow-[0_10px_40px_rgba(15,23,42,0.08)] md:p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
              Request reliability
            </p>

            <div className="mt-5 flex items-end justify-between gap-4">
              <div>
                <p className="text-5xl font-semibold tracking-[-0.045em]">
                  {successRate === null
                    ? "—"
                    : `${formatMetric(
                        successRate,
                        1,
                      )}%`}
                </p>

                <p className="mt-2 text-sm text-slate-400">
                  successful requests
                </p>
              </div>

              <div className="text-right">
                <p className="text-2xl font-semibold">
                  {summary?.monitoring
                    .requests.total ?? "—"}
                </p>

                <p className="mt-1 text-xs text-slate-400">
                  total requests
                </p>
              </div>
            </div>

            <div className="mt-8 grid grid-cols-2 gap-3">
              <div className="rounded-2xl bg-white/5 p-4">
                <p className="text-xs text-slate-400">
                  Successful
                </p>

                <p className="mt-2 text-xl font-semibold">
                  {summary?.monitoring
                    .requests.successful ?? "—"}
                </p>
              </div>

              <div className="rounded-2xl bg-white/5 p-4">
                <p className="text-xs text-slate-400">
                  Failed
                </p>

                <p className="mt-2 text-xl font-semibold">
                  {summary?.monitoring
                    .requests.failed ?? "—"}
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* LATENCY */}
        <section className="mb-6 rounded-[28px] border border-slate-200 bg-white shadow-[0_10px_40px_rgba(15,23,42,0.04)]">
          <div className="border-b border-slate-100 p-7 md:p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
              Service performance
            </p>

            <h2 className="mt-2 text-2xl font-semibold tracking-tight">
              Prediction latency
            </h2>
          </div>

          <div className="grid grid-cols-2 divide-x divide-y divide-slate-100 md:grid-cols-4 md:divide-y-0">
            {[
              [
                "p50",
                summary?.monitoring.latency_ms.p50,
              ],
              [
                "p95",
                summary?.monitoring.latency_ms.p95,
              ],
              [
                "p99",
                summary?.monitoring.latency_ms.p99,
              ],
              [
                "Average",
                summary?.monitoring.latency_ms.average,
              ],
            ].map(([label, value]) => (
              <div
                key={label}
                className="p-6 md:p-7"
              >
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                  {label}
                </p>

                <p className="mt-4 text-3xl font-semibold tracking-tight">
                  {loading
                    ? "—"
                    : formatMetric(
                        value as number | null,
                        2,
                      )}
                </p>

                <p className="mt-2 text-xs text-slate-500">
                  milliseconds
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* DRIFT */}
        <section className="mb-6 rounded-[28px] border border-slate-200 bg-white shadow-[0_10px_40px_rgba(15,23,42,0.04)]">
          <div className="flex flex-col gap-5 border-b border-slate-100 p-7 md:p-8 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
                Distribution monitoring
              </p>

              <h2 className="mt-2 text-2xl font-semibold tracking-tight">
                Feature drift
              </h2>

              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
                Population Stability Index compares recent
                inference observations against the reference
                feature distributions.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`rounded-full border px-3 py-1.5 text-xs font-medium ${statusClasses(
                  drift?.status ?? "unknown",
                )}`}
              >
                {drift
                  ? statusLabel(drift.status)
                  : "No data"}
              </span>

              <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-500">
                {drift?.sample_count ?? 0} observations
              </span>
            </div>
          </div>

          <div className="grid gap-0 border-b border-slate-100 md:grid-cols-3 md:divide-x">
            <div className="p-6 md:p-7">
              <p className="text-xs uppercase tracking-wide text-slate-400">
                Healthy features
              </p>

              <p className="mt-3 text-3xl font-semibold">
                {driftCounts.healthy}
              </p>
            </div>

            <div className="border-t border-slate-100 p-6 md:border-t-0 md:p-7">
              <p className="text-xs uppercase tracking-wide text-slate-400">
                Warning
              </p>

              <p className="mt-3 text-3xl font-semibold">
                {driftCounts.warning}
              </p>
            </div>

            <div className="border-t border-slate-100 p-6 md:border-t-0 md:p-7">
              <p className="text-xs uppercase tracking-wide text-slate-400">
                Critical
              </p>

              <p className="mt-3 text-3xl font-semibold">
                {driftCounts.critical}
              </p>
            </div>
          </div>

          <div className="divide-y divide-slate-100">
            {driftFeatures.length === 0 ? (
              <div className="p-8 text-sm text-slate-500">
                No drift observations are available yet.
              </div>
            ) : (
              driftFeatures.map((feature) => {
                const psi =
                  feature.psi ?? 0;

                const maximum = Math.max(
                  drift?.thresholds.critical_psi ??
                    0.25,
                  psi,
                );

                const width = Math.min(
                  100,
                  (psi / maximum) * 100,
                );

                return (
                  <div
                    key={feature.feature}
                    className="grid gap-5 p-6 md:grid-cols-[1.4fr_1fr_auto] md:items-center md:p-7"
                  >
                    <div>
                      <p className="text-sm font-semibold text-slate-800">
                        {featureLabel(
                          feature.feature,
                        )}
                      </p>

                      <p className="mt-1 text-xs text-slate-400">
                        {feature.sample_count} current
                        observations
                      </p>
                    </div>

                    <div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">
                          PSI
                        </span>

                        <span className="font-semibold text-slate-700">
                          {formatMetric(
                            feature.psi,
                            3,
                          )}
                        </span>
                      </div>

                      <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full bg-slate-900 transition-all duration-500"
                          style={{
                            width: `${width}%`,
                          }}
                        />
                      </div>
                    </div>

                    <span
                      className={`w-fit rounded-full border px-3 py-1.5 text-xs font-medium ${statusClasses(
                        feature.status,
                      )}`}
                    >
                      {statusLabel(
                        feature.status,
                      )}
                    </span>
                  </div>
                );
              })
            )}
          </div>

          <div className="flex flex-col gap-2 border-t border-slate-100 bg-slate-50/60 px-7 py-5 text-xs text-slate-500 md:flex-row md:items-center md:justify-between">
            <span>
              Warning ≥{" "}
              {drift?.thresholds.warning_psi ??
                0.1}{" "}
              PSI
            </span>

            <span>
              Critical ≥{" "}
              {drift?.thresholds.critical_psi ??
                0.25}{" "}
              PSI
            </span>

            <span>
              Minimum sample size:{" "}
              {drift?.minimum_sample_count ??
                30}
            </span>
          </div>
        </section>

        {/* DATA QUALITY + DIAGNOSTICS */}
        <section className="grid gap-5 lg:grid-cols-2">

          <div className="rounded-[28px] border border-slate-200 bg-white p-7 shadow-[0_10px_40px_rgba(15,23,42,0.04)] md:p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
              Input integrity
            </p>

            <h2 className="mt-2 text-2xl font-semibold tracking-tight">
              Data quality
            </h2>

            {summary &&
            Object.keys(
              summary.monitoring.data_quality,
            ).length > 0 ? (
              <div className="mt-6 space-y-3">
                {Object.entries(
                  summary.monitoring.data_quality,
                ).map(
                  ([check, value]) => (
                    <div
                      key={check}
                      className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3"
                    >
                      <span className="text-sm font-medium text-slate-700">
                        {featureLabel(check)}
                      </span>

                      <span className="text-xs text-slate-500">
                        {value}
                      </span>
                    </div>
                  ),
                )}
              </div>
            ) : (
              <div className="mt-6 rounded-2xl bg-slate-50 p-5 text-sm text-slate-500">
                No data-quality checks have been
                recorded yet.
              </div>
            )}
          </div>

          <div className="rounded-[28px] border border-slate-200 bg-white p-7 shadow-[0_10px_40px_rgba(15,23,42,0.04)] md:p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
              Service diagnostics
            </p>

            <h2 className="mt-2 text-2xl font-semibold tracking-tight">
              Latest error
            </h2>

            {summary?.monitoring.last_error ? (
              <>
                <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-5">
                  <p className="text-sm font-medium leading-6 text-red-800">
                    {summary.monitoring.last_error}
                  </p>
                </div>

                <p className="mt-4 text-xs text-slate-400">
                  {formatTimestamp(
                    summary.monitoring.last_error_at,
                  )}
                </p>
              </>
            ) : (
              <div className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
                <p className="text-sm font-medium text-emerald-800">
                  No errors have been recorded.
                </p>

                <p className="mt-1 text-xs text-emerald-700">
                  The inference service has no recent
                  recorded failures.
                </p>
              </div>
            )}
          </div>
        </section>

        <footer className="mt-8 pb-4 text-xs text-slate-400">
          Reference profile:{" "}
          {drift?.reference.source ??
            "not available"}
        </footer>
      </div>
    </main>
  );
}