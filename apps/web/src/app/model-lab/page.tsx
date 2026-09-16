"use client";

import { useEffect, useMemo, useState } from "react";

import {
  getModelLabRuns,
  getModelLabSummary,
  type ModelLabRun,
  type ModelLabSummary,
  type ModelVersion,
} from "@/lib/api";

type LifecycleStage =
  | "training"
  | "experiment"
  | "evaluation"
  | "registration"
  | "guard"
  | "candidate"
  | "production";

const lifecycleStages: {
  id: LifecycleStage;
  label: string;
  description: string;
}[] = [
  {
    id: "training",
    label: "Training",
    description:
      "Train candidate models against the prepared feature dataset.",
  },
  {
    id: "experiment",
    label: "Experiment",
    description:
      "Track parameters, metrics, configuration and artifacts.",
  },
  {
    id: "evaluation",
    label: "Evaluation",
    description:
      "Evaluate learned models against validation and test metrics.",
  },
  {
    id: "registration",
    label: "Registration",
    description:
      "Register evaluated model artifacts in the MLflow Model Registry.",
  },
  {
    id: "guard",
    label: "Baseline Guard",
    description:
      "Require the learned model to outperform the persistence baseline.",
  },
  {
    id: "candidate",
    label: "Candidate",
    description:
      "A model eligible for promotion after passing evaluation and the baseline guard.",
  },
  {
    id: "production",
    label: "Production",
    description:
      "The model currently selected for serving.",
  },
];

function modelFamilyLabel(
  family: string | null | undefined,
): string {
  switch (family) {
    case "ridge":
      return "Ridge";
    case "random_forest":
      return "Random Forest";
    case "hist_gradient_boosting":
      return "HistGradientBoosting";
    case "pred_persistence":
      return "Persistence";
    case "pred_previous_day":
      return "Previous Day";
    case "pred_previous_week":
      return "Previous Week";
    default:
      return family ?? "Unknown model";
  }
}

export default function ModelLabPage() {
  const [summary, setSummary] =
    useState<ModelLabSummary | null>(null);

  const [runs, setRuns] =
    useState<ModelLabRun[]>([]);

  const [selectedVersion, setSelectedVersion] =
    useState<ModelVersion | null>(null);

  const [selectedStage, setSelectedStage] =
    useState<LifecycleStage>("production");

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const [showParameters, setShowParameters] =
    useState(false);

  useEffect(() => {
    async function loadModelLab() {
      try {
        setLoading(true);
        setError(null);

        const [summaryData, runsData] =
          await Promise.all([
            getModelLabSummary(),
            getModelLabRuns(),
          ]);

        setSummary(summaryData);
        setRuns(runsData.runs);

        if (summaryData.versions.length > 0) {
          setSelectedVersion(
            summaryData.versions[0],
          );
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load Model Lab.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadModelLab();
  }, []);

  const evaluatedVersions = useMemo(() => {
    if (!summary) return [];

    return summary.versions.filter(
      (version) =>
        version.validation_status === "evaluated",
    );
  }, [summary]);

  const rejectedVersions = useMemo(() => {
    if (!summary) return [];

    return summary.versions.filter(
      (version) =>
        version.lifecycle_status === "rejected" ||
        version.baseline_guard === "failed",
    );
  }, [summary]);

  const candidateVersions = useMemo(() => {
    if (!summary) return [];

    return summary.versions.filter(
      (version) =>
        version.aliases.includes("candidate"),
    );
  }, [summary]);

  const registeredCount = summary?.versions.length ?? 0;

  const evaluatedCount =
    evaluatedVersions.length;

  const rejectedCount =
    rejectedVersions.length;

  const baseline = summary?.baseline ?? null;

  const lifecycleInfo = useMemo(() => {
    if (!summary) return null;

    if (selectedStage === "production") {
      return {
        title: "Production",
        value:
          summary.production.model_name,
        detail:
          summary.production.version ===
          "baseline"
            ? "Persistence baseline is currently serving because no learned model currently holds the production alias."
            : `MLflow model version ${summary.production.version} is currently serving.`,
      };
    }

    if (selectedStage === "candidate") {
      return {
        title: "Candidate",
        value:
          summary.candidate
            ? `Version ${summary.candidate.version}`
            : "None",
        detail:
          summary.candidate
            ? `${modelFamilyLabel(summary.candidate.model_family)} is currently marked as a candidate.`
            : "No registered model currently holds the candidate alias.",
      };
    }

    if (selectedStage === "guard") {
      const passedCount =
        summary.versions.filter(
          (version) =>
            version.baseline_guard === "passed",
        ).length;

      const failedCount =
        summary.versions.filter(
          (version) =>
            version.baseline_guard === "failed",
        ).length;

      return {
        title: "Baseline Guard",
        value:
          failedCount > 0
            ? `${failedCount} rejected`
            : passedCount > 0
              ? `${passedCount} passed`
              : "Not triggered",
        detail:
          failedCount > 0
            ? "At least one learned candidate failed the persistence-baseline guard and was rejected."
            : passedCount > 0
              ? "A learned candidate has passed the persistence-baseline guard."
              : "The guard has not recorded a pass or failure.",
      };
    }

    const stage =
      lifecycleStages.find(
        (item) => item.id === selectedStage,
      );

    return {
      title: stage?.label ?? "",
      value:
        selectedStage === "training"
          ? "Feature pipeline"
          : selectedStage === "experiment"
            ? `${runs.length} tracked runs`
            : selectedStage === "evaluation"
              ? `${evaluatedVersions.length} evaluated`
              : `${summary.registered_versions} registered`,
      detail:
        stage?.description ?? "",
    };
  }, [
    summary,
    runs.length,
    selectedStage,
    evaluatedVersions.length,
  ]);

  const comparisonVersions = useMemo(() => {
    if (!summary) return [];

    return [...summary.versions]
      .filter(
        (version) =>
          version.metrics
            .validation_macro_building_nmae !==
          undefined,
      )
      .sort(
        (a, b) =>
          (a.metrics
            .validation_macro_building_nmae ??
            Infinity) -
          (b.metrics
            .validation_macro_building_nmae ??
            Infinity),
      );
  }, [summary]);

  if (loading) {
    return <LoadingState />;
  }

  if (error || !summary) {
    return (
      <main className="min-h-screen bg-[#f7f8fa] px-6 py-8 text-slate-900 md:px-10">
        <div className="mx-auto max-w-7xl">
          <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
              Model Lab
            </p>

            <h1 className="mt-2 text-xl font-semibold">
              Model Lab unavailable
            </h1>

            <p className="mt-2 text-sm text-slate-500">
              {error ??
                "The ML lifecycle service could not be reached."}
            </p>
          </div>
        </div>
      </main>
    );
  }

  const production =
    summary.production;

  return (
    <main className="min-h-screen bg-[#f7f8fa] px-5 py-8 text-slate-900 md:px-8 lg:px-10">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <header className="mb-8">
          <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.16em] text-slate-400">
                Machine learning
              </p>

              <h1 className="mt-2 text-3xl font-semibold tracking-tight">
                Model Lab
              </h1>

              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
                Experimentation, evaluation, registry and
                production lifecycle for the building energy
                forecasting system.
              </p>
            </div>

            <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 shadow-sm">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />

              <span className="text-xs font-medium text-slate-600">
                MLflow connected
              </span>
            </div>
          </div>
        </header>

        {/* Production hero */}
        <section className="grid gap-5 lg:grid-cols-[1.6fr_1fr]">
          <div className="relative overflow-hidden rounded-3xl bg-slate-950 p-7 text-white shadow-sm">
            <div className="absolute -right-20 -top-24 h-64 w-64 rounded-full bg-white/[0.04]" />
            <div className="absolute -bottom-32 right-16 h-72 w-72 rounded-full bg-white/[0.03]" />

            <div className="relative">
              <div className="flex items-start justify-between gap-5">
                <div>
                  <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-slate-400">
                    Production model
                  </p>

                  <h2 className="mt-3 text-3xl font-semibold tracking-tight">
                    {production.model_name}
                  </h2>

                  <p className="mt-2 text-sm text-slate-400">
                    {production.version ===
                    "baseline"
                      ? "Persistence baseline"
                      : `Registered MLflow version ${production.version}`}
                  </p>
                </div>

                <span className="rounded-full border border-white/10 bg-white/[0.06] px-3 py-1.5 text-xs font-medium text-slate-300">
                  {production.serving_mode ===
                  "baseline"
                    ? "Baseline"
                    : "Serving"}
                </span>
              </div>

              <div className="mt-10 grid gap-4 sm:grid-cols-3">
                <DarkStat
                  label="Version"
                  value={production.version}
                />

                <DarkStat
                  label="Alias"
                  value={
                    production.alias ??
                    "none"
                  }
                />

                <DarkStat
                  label="Run"
                  value={
                    production.run_id
                      ? production.run_id.slice(
                          0,
                          10,
                        )
                      : "—"
                  }
                />
              </div>
            </div>
          </div>

          {/* System stats */}
          <div className="grid grid-cols-2 gap-4">
            <MetricCard
              label="Registered"
              value={registeredCount}
              detail="model versions"
            />

            <MetricCard
              label="Evaluated"
              value={evaluatedCount}
              detail="learned models"
            />

            <MetricCard
              label="Rejected"
              value={rejectedCount}
              detail="by lifecycle guard"
            />

            <MetricCard
              label="Candidate"
              value={
                candidateVersions.length > 0
                  ? `v${candidateVersions[0].version}`
                  : "None"
              }
              detail={
                modelFamilyLabel(
                  candidateVersions[0]?.model_family,
                )
              }
            />
          </div>
        </section>

        {/* Persistence baseline */}
        <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-start">
            <div className="max-w-2xl">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                Benchmark baseline
              </p>

              <h2 className="mt-1 text-lg font-semibold">
                {baseline?.display_name ?? "Persistence"}
              </h2>

              <p className="mt-2 text-sm leading-6 text-slate-500">
                {baseline?.strategy ??
                  "Use the latest observed energy value as the next-hour prediction."}
              </p>
            </div>

            <span className="shrink-0 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-500">
              Reference predictor
            </span>
          </div>

          {baseline?.available ? (
            <>
              <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {Object.entries(baseline.metrics).map(
                  ([metric, value]) => (
                    <div
                      key={metric}
                      className="rounded-2xl bg-slate-50 p-4"
                    >
                      <p className="text-[10px] font-medium uppercase tracking-wide text-slate-400">
                        {metric.replaceAll("_", " ")}
                      </p>

                      <p className="mt-2 text-xl font-semibold tracking-tight text-slate-900">
                        {formatMetric(value)}
                      </p>
                    </div>
                  ),
                )}
              </div>

              {baseline.all_baselines.length > 0 && (
                <div className="mt-5">
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                    Baseline benchmark set
                  </p>

                  <div className="mt-3 grid gap-2 sm:grid-cols-3">
                    {baseline.all_baselines.map(
                      (item) => (
                        <div
                          key={item.baseline}
                          className="rounded-xl border border-slate-200 bg-white px-4 py-3"
                        >
                          <p className="truncate text-xs font-medium text-slate-600">
                            {modelFamilyLabel(item.baseline)}
                          </p>

                          <div className="mt-2 space-y-1">
                            {Object.entries(item.metrics).map(
                              ([metric, value]) => (
                                <div
                                  key={metric}
                                  className="flex items-center justify-between gap-3"
                                >
                                  <span className="text-[10px] text-slate-400">
                                    {metric.replaceAll("_", " ")}
                                  </span>

                                  <span className="text-xs font-semibold text-slate-700">
                                    {formatMetric(value)}
                                  </span>
                                </div>
                              ),
                            )}
                          </div>
                        </div>
                      ),
                    )}
                  </div>
                </div>
              )}

              <p className="mt-5 text-xs leading-5 text-slate-400">
                Source: {baseline.source ?? "baseline benchmark report"}.
                These are benchmark results and are kept separate from
                learned-model validation comparisons.
              </p>
            </>
          ) : (
            <div className="mt-6 rounded-2xl border border-dashed border-slate-200 p-6">
              <p className="text-sm font-medium text-slate-700">
                Persistence baseline unavailable
              </p>

              <p className="mt-1 text-xs leading-5 text-slate-400">
                The lifecycle service did not return baseline benchmark
                metrics.
              </p>
            </div>
          )}

          <div className="mt-5 flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-medium text-slate-700">
                Promotion policy
              </p>

              <p className="mt-1 text-xs leading-5 text-slate-500">
                A learned model is not promoted simply because it is the
                strongest learned model. It must also pass the baseline
                guard.
              </p>
            </div>

            <button
              type="button"
              onClick={() =>
                setSelectedStage("guard")
              }
              className="shrink-0 rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-50"
            >
              Inspect guard
            </button>
          </div>
        </section>

        {/* Lifecycle */}
        <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col justify-between gap-3 sm:flex-row">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                Lifecycle
              </p>

              <h2 className="mt-1 text-lg font-semibold">
                From training to serving
              </h2>
            </div>

            <div className="text-xs text-slate-400">
              Click a stage to inspect it
            </div>
          </div>

          <div className="mt-7 overflow-x-auto pb-2">
            <div className="flex min-w-[900px] items-center">
              {lifecycleStages.map(
                (stage, index) => {
                  const active =
                    selectedStage ===
                    stage.id;

                  return (
                    <div
                      key={stage.id}
                      className="flex flex-1 items-center"
                    >
                      <button
                        type="button"
                        onClick={() =>
                          setSelectedStage(
                            stage.id,
                          )
                        }
                        className="group flex min-w-0 flex-1 flex-col items-center text-center"
                      >
                        <div
                          className={`flex h-11 w-11 items-center justify-center rounded-full border text-xs font-semibold transition ${
                            active
                              ? "border-slate-900 bg-slate-900 text-white shadow-lg shadow-slate-900/10"
                              : "border-slate-200 bg-slate-50 text-slate-500 group-hover:border-slate-300 group-hover:bg-white"
                          }`}
                        >
                          {index + 1}
                        </div>

                        <span
                          className={`mt-3 text-xs font-medium ${
                            active
                              ? "text-slate-900"
                              : "text-slate-500"
                          }`}
                        >
                          {stage.label}
                        </span>
                      </button>

                      {index <
                        lifecycleStages.length -
                          1 && (
                        <div className="mx-2 h-px flex-1 bg-slate-200" />
                      )}
                    </div>
                  );
                },
              )}
            </div>
          </div>

          {lifecycleInfo && (
            <div className="mt-6 rounded-2xl bg-slate-50 p-5">
              <div className="flex flex-col justify-between gap-4 sm:flex-row">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                    Selected stage
                  </p>

                  <h3 className="mt-1 text-base font-semibold">
                    {lifecycleInfo.title}
                  </h3>
                </div>

                <div className="text-left sm:text-right">
                  <p className="text-sm font-semibold text-slate-800">
                    {lifecycleInfo.value}
                  </p>

                  <p className="mt-1 max-w-xl text-xs leading-5 text-slate-500">
                    {lifecycleInfo.detail}
                  </p>
                </div>
              </div>
            </div>
          )}
        </section>

        {/* Registry + selected model */}
        <section className="mt-6 grid gap-6 lg:grid-cols-[1fr_1.35fr]">
          {/* Registry */}
          <div className="rounded-3xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 px-6 py-5">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                Model registry
              </p>

              <h2 className="mt-1 text-lg font-semibold">
                Registered versions
              </h2>

              <p className="mt-1 text-xs text-slate-400">
                {registeredCount} registered
                {registeredCount === 1
                  ? " version"
                  : " versions"}
              </p>
            </div>

            <div className="space-y-2 p-3">
              {summary.versions.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-slate-200 p-6 text-center">
                  <p className="text-sm font-medium text-slate-700">
                    No registered versions
                  </p>

                  <p className="mt-1 text-xs text-slate-400">
                    MLflow has not returned any registered
                    forecasting models.
                  </p>
                </div>
              ) : (
                summary.versions.map(
                  (version) => {
                    const selected =
                      selectedVersion?.version ===
                      version.version;

                    const isProduction =
                      production.version ===
                      version.version;

                    const isCandidate =
                      version.aliases.includes(
                        "candidate",
                      );

                    const isRejected =
                      version.lifecycle_status ===
                        "rejected" ||
                      version.baseline_guard ===
                        "failed";

                    return (
                      <button
                        key={version.version}
                        type="button"
                        onClick={() =>
                          setSelectedVersion(
                            version,
                          )
                        }
                        className={`w-full rounded-2xl border p-4 text-left transition ${
                          selected
                            ? "border-slate-300 bg-slate-50 shadow-sm"
                            : "border-transparent hover:border-slate-200 hover:bg-slate-50"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex min-w-0 items-center gap-3">
                            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-xs font-semibold text-white">
                              v{version.version}
                            </div>

                            <div className="min-w-0">
                              <p className="truncate text-sm font-semibold text-slate-800">
                                {modelFamilyLabel(
                                  version.model_family,
                                )}
                              </p>

                              <p className="mt-0.5 truncate text-xs text-slate-400">
                                Run{" "}
                                {version.run_id.slice(
                                  0,
                                  10,
                                )}
                              </p>
                            </div>
                          </div>

                          <div className="flex shrink-0 flex-wrap justify-end gap-1">
                            {isProduction && (
                              <StatusPill>
                                Production
                              </StatusPill>
                            )}

                            {isCandidate && (
                              <StatusPill>
                                Candidate
                              </StatusPill>
                            )}

                            {isRejected && (
                              <StatusPill>
                                Rejected
                              </StatusPill>
                            )}
                          </div>
                        </div>

                        <div className="mt-4 grid grid-cols-2 gap-3">
                          <div>
                            <p className="text-[10px] font-medium uppercase tracking-wide text-slate-400">
                              Validation NMAE
                            </p>

                            <p className="mt-1 text-sm font-semibold text-slate-700">
                              {formatMetric(
                                version.metrics
                                  .validation_macro_building_nmae,
                              )}
                            </p>
                          </div>

                          <div className="text-right">
                            <p className="text-[10px] font-medium uppercase tracking-wide text-slate-400">
                              Lifecycle
                            </p>

                            <p className="mt-1 text-sm font-semibold text-slate-700">
                              {version.lifecycle_status ??
                                version.validation_status ??
                                "Recorded"}
                            </p>
                          </div>
                        </div>
                      </button>
                    );
                  },
                )
              )}
            </div>
          </div>

          {/* Selected model */}
          <div className="rounded-3xl border border-slate-200 bg-white shadow-sm">
            {selectedVersion ? (
              <>
                <div className="border-b border-slate-100 px-6 py-5">
                  <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                        Model version
                      </p>

                      <h2 className="mt-1 text-xl font-semibold tracking-tight">
                        {modelFamilyLabel(
                          selectedVersion.model_family,
                        )}{" "}
                        <span className="text-slate-400">
                          v{selectedVersion.version}
                        </span>
                      </h2>

                      <p className="mt-1 text-xs text-slate-400">
                        MLflow run{" "}
                        {selectedVersion.run_id}
                      </p>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {selectedVersion.validation_status && (
                        <StatusPill>
                          {
                            selectedVersion.validation_status
                          }
                        </StatusPill>
                      )}

                      {selectedVersion.lifecycle_status && (
                        <StatusPill>
                          {
                            selectedVersion.lifecycle_status
                          }
                        </StatusPill>
                      )}
                    </div>
                  </div>
                </div>

                <div className="p-6">
                  <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                    <MiniMetric
                      label="Validation MAE"
                      value={formatMetric(
                        selectedVersion
                          .metrics
                          .validation_mae,
                      )}
                    />

                    <MiniMetric
                      label="Test MAE"
                      value={formatMetric(
                        selectedVersion
                          .metrics.test_mae,
                      )}
                    />

                    <MiniMetric
                      label="Validation NMAE"
                      value={formatMetric(
                        selectedVersion
                          .metrics
                          .validation_macro_building_nmae,
                      )}
                    />

                    <MiniMetric
                      label="Test NMAE"
                      value={formatMetric(
                        selectedVersion
                          .metrics
                          .test_macro_building_nmae,
                      )}
                    />
                  </div>

                  {/* Baseline guard */}
                  <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-5">
                    <div className="flex flex-col justify-between gap-4 sm:flex-row">
                      <div>
                        <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                          Baseline guard
                        </p>

                        <h3 className="mt-1 text-sm font-semibold">
                          {selectedVersion.baseline_guard ===
                          "failed"
                            ? "Learned model rejected"
                            : selectedVersion.baseline_guard ===
                                "passed"
                              ? "Learned model passed"
                              : "Evaluation recorded"}
                        </h3>
                      </div>

                      <div className="text-left sm:text-right">
                        <p className="text-xs text-slate-400">
                          Baseline
                        </p>

                        <p className="mt-1 text-sm font-semibold text-slate-700">
                          {selectedVersion.baseline_model ??
                            "Persistence"}
                        </p>

                        {selectedVersion.baseline_validation_nmae && (
                          <p className="mt-1 text-xs text-slate-400">
                            Recorded baseline NMAE{" "}
                            {selectedVersion.baseline_validation_nmae}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="mt-4 grid gap-3 sm:grid-cols-2">
                      <div className="rounded-xl border border-slate-200 bg-white p-3">
                        <p className="text-[10px] font-medium uppercase tracking-wide text-slate-400">
                          Guard status
                        </p>

                        <p className="mt-1 text-sm font-semibold text-slate-700">
                          {selectedVersion.baseline_guard ??
                            "Not recorded"}
                        </p>
                      </div>

                      <div className="rounded-xl border border-slate-200 bg-white p-3">
                        <p className="text-[10px] font-medium uppercase tracking-wide text-slate-400">
                          Baseline model
                        </p>

                        <p className="mt-1 truncate text-sm font-semibold text-slate-700">
                          {selectedVersion.baseline_model ??
                            "pred_persistence"}
                        </p>
                      </div>
                    </div>

                    {selectedVersion.baseline_guard && (
                      <div className="mt-4 rounded-xl border border-slate-200 bg-white p-3">
                        <p className="text-[10px] font-medium uppercase tracking-wide text-slate-400">
                          Guard metric
                        </p>

                        <p className="mt-1 text-sm font-semibold text-slate-700">
                          {selectedVersion.promotion_metric ??
                            "validation_macro_building_nmae"}
                        </p>

                        <p className="mt-1 text-xs leading-5 text-slate-400">
                          The guard compares the learned model against the
                          persistence baseline using the recorded promotion
                          metric. The benchmark panel above remains a separate
                          baseline report.
                        </p>
                      </div>
                    )}

                    {(selectedVersion.rejection_reason ||
                      selectedVersion.promotion_reason) && (
                      <div className="mt-4 border-t border-slate-200 pt-4 text-xs leading-5 text-slate-500">
                        {selectedVersion.rejection_reason ??
                          selectedVersion.promotion_reason}
                      </div>
                    )}
                  </div>

                  {/* Model lifecycle metadata */}
                  <div className="mt-5 grid gap-3 sm:grid-cols-2">
                    <MiniMetric
                      label="Validation status"
                      value={
                        selectedVersion.validation_status ??
                        "—"
                      }
                    />

                    <MiniMetric
                      label="Lifecycle status"
                      value={
                        selectedVersion.lifecycle_status ??
                        "—"
                      }
                    />

                    <MiniMetric
                      label="Promotion metric"
                      value={
                        selectedVersion.promotion_metric ??
                        "—"
                      }
                    />

                    <MiniMetric
                      label="Baseline guard"
                      value={
                        selectedVersion.baseline_guard ??
                        "—"
                      }
                    />
                  </div>

                  {/* Parameters */}
                  <div className="mt-5">
                    <button
                      type="button"
                      onClick={() =>
                        setShowParameters(
                          (value) => !value,
                        )
                      }
                      className="flex w-full items-center justify-between rounded-xl border border-slate-200 px-4 py-3 text-left transition hover:bg-slate-50"
                    >
                      <span className="text-sm font-medium">
                        Run parameters & tags
                      </span>

                      <span className="text-xs text-slate-400">
                        {showParameters
                          ? "Hide"
                          : "Show"}
                      </span>
                    </button>

                    {showParameters && (
                      <div className="mt-2 grid gap-3 sm:grid-cols-2">
                        <KeyValueList
                          title="Parameters"
                          values={
                            selectedVersion.params
                          }
                        />

                        <KeyValueList
                          title="Tags"
                          values={
                            selectedVersion.tags
                          }
                        />
                      </div>
                    )}
                  </div>
                </div>
              </>
            ) : (
              <div className="flex min-h-[420px] items-center justify-center p-8 text-center">
                <div>
                  <p className="text-sm font-medium">
                    Select a model version
                  </p>

                  <p className="mt-2 text-xs text-slate-400">
                    Choose a registered version to
                    inspect its evaluation and
                    lifecycle information.
                  </p>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Metric comparison */}
        <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col justify-between gap-3 sm:flex-row">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                Evaluation
              </p>

              <h2 className="mt-1 text-lg font-semibold">
                Learned-model validation comparison
              </h2>

              <p className="mt-1 text-xs text-slate-400">
                Validation macro-building NMAE · learned
                models only
              </p>
            </div>

            <p className="text-xs text-slate-400">
              Lower is better
            </p>
          </div>

          {comparisonVersions.length === 0 ? (
            <div className="mt-6 rounded-2xl border border-dashed border-slate-200 p-8 text-center">
              <p className="text-sm font-medium text-slate-700">
                No comparable validation metrics
              </p>

              <p className="mt-1 text-xs text-slate-400">
                Registered models do not currently contain
                validation macro-building NMAE values.
              </p>
            </div>
          ) : (
            <div className="mt-7 space-y-5">
              {comparisonVersions.map(
                (version) => {
                  const value =
                    version.metrics
                      .validation_macro_building_nmae ??
                    0;

                  const max =
                    Math.max(
                      ...comparisonVersions.map(
                        (item) =>
                          item.metrics
                            .validation_macro_building_nmae ??
                          0,
                      ),
                      0.1,
                    );

                  const width = Math.max(
                    5,
                    (value / max) * 100,
                  );

                  const isProduction =
                    version.version ===
                    production.version;

                  const isSelected =
                    version.version ===
                    selectedVersion?.version;

                  return (
                    <button
                      key={version.version}
                      type="button"
                      onClick={() =>
                        setSelectedVersion(
                          version,
                        )
                      }
                      className="group w-full text-left"
                    >
                      <div className="mb-2 flex items-center justify-between gap-4">
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-sm font-medium ${
                              isSelected
                                ? "text-slate-900"
                                : "text-slate-700"
                            }`}
                          >
                            v{version.version}{" "}
                            {modelFamilyLabel(
                              version.model_family,
                            )}
                          </span>

                          {isProduction && (
                            <StatusPill>
                              Production
                            </StatusPill>
                          )}

                          {version.lifecycle_status ===
                            "rejected" && (
                            <StatusPill>
                              Rejected
                            </StatusPill>
                          )}
                        </div>

                        <span className="text-sm font-semibold text-slate-700">
                          {value.toFixed(4)}
                        </span>
                      </div>

                      <div
                        className={`h-3 overflow-hidden rounded-full ${
                          isSelected
                            ? "bg-slate-200"
                            : "bg-slate-100"
                        }`}
                      >
                        <div
                          className="h-full rounded-full bg-slate-900 transition-all duration-500 group-hover:bg-slate-700"
                          style={{
                            width: `${width}%`,
                          }}
                        />
                      </div>
                    </button>
                  );
                },
              )}
            </div>
          )}

          <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-start gap-3">
              <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-white text-xs font-semibold text-slate-500 shadow-sm">
                i
              </div>

              <div>
                <p className="text-xs font-semibold text-slate-700">
                  Baseline comparison is kept separate
                </p>

                <p className="mt-1 text-xs leading-5 text-slate-500">
                  The persistence baseline is shown above as
                  its own benchmark. This chart compares only
                  registered learned-model versions so that
                  different evaluation records are not mixed
                  into one metric visualization.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Evaluation outcome */}
        <section className="mt-6 grid gap-6 lg:grid-cols-2">
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
              Evaluation outcomes
            </p>

            <h2 className="mt-1 text-lg font-semibold">
              Lifecycle decision state
            </h2>

            <div className="mt-6 space-y-3">
              <OutcomeRow
                label="Registered versions"
                value={registeredCount}
              />

              <OutcomeRow
                label="Evaluated learned models"
                value={evaluatedCount}
              />

              <OutcomeRow
                label="Rejected candidates"
                value={rejectedCount}
              />

              <OutcomeRow
                label="Candidate aliases"
                value={candidateVersions.length}
              />

              <OutcomeRow
                label="Production alias"
                value={
                  production.alias
                    ? production.alias
                    : "none"
                }
              />
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-slate-950 p-6 text-white shadow-sm">
            <p className="text-xs font-medium uppercase tracking-[0.16em] text-slate-500">
              Current decision
            </p>

            <h2 className="mt-2 text-xl font-semibold">
              {production.version ===
              "baseline"
                ? "Baseline remains active"
                : `Version ${production.version} is serving`}
            </h2>

            <p className="mt-3 text-sm leading-6 text-slate-400">
              {production.version ===
              "baseline"
                ? "No learned model currently satisfies the complete promotion path, so the serving layer remains on the persistence baseline."
                : `The serving layer currently resolves to MLflow model version ${production.version}.`}
            </p>

            <div className="mt-7 grid gap-3 sm:grid-cols-2">
              <DarkStat
                label="Serving mode"
                value={
                  production.serving_mode
                }
              />

              <DarkStat
                label="Production alias"
                value={
                  production.alias ??
                  "none"
                }
              />
            </div>
          </div>
        </section>

        {/* Experiment history */}
        <section className="mt-6 rounded-3xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-6 py-5">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
              Experiment tracking
            </p>

            <h2 className="mt-1 text-lg font-semibold">
              Experiment history
            </h2>

            <p className="mt-1 text-xs text-slate-400">
              {runs.length} tracked MLflow{" "}
              {runs.length === 1
                ? "run"
                : "runs"}
            </p>
          </div>

          {runs.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-sm font-medium text-slate-700">
                No experiment runs available
              </p>

              <p className="mt-1 text-xs text-slate-400">
                MLflow did not return tracked experiment runs.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {runs.map((run) => (
                <RunRow
                  key={run.run_id}
                  run={run}
                />
              ))}
            </div>
          )}
        </section>

        <footer className="py-8 text-center text-xs text-slate-400">
          Model Lab · MLflow-backed lifecycle observability
        </footer>
      </div>
    </main>
  );
}

function DarkStat({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.05] p-4">
      <p className="text-[10px] font-medium uppercase tracking-wide text-slate-500">
        {label}
      </p>

      <p className="mt-2 truncate text-sm font-semibold text-slate-200">
        {value}
      </p>
    </div>
  );
}

function MetricCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string | number;
  detail: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
        {label}
      </p>

      <p className="mt-3 text-2xl font-semibold tracking-tight">
        {value}
      </p>

      <p className="mt-1 text-xs text-slate-400">
        {detail}
      </p>
    </div>
  );
}

function MiniMetric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl bg-slate-50 p-4">
      <p className="text-[10px] font-medium uppercase tracking-wide text-slate-400">
        {label}
      </p>

      <p className="mt-2 truncate text-base font-semibold text-slate-800">
        {value}
      </p>
    </div>
  );
}

function OutcomeRow({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
      <span className="text-xs text-slate-500">
        {label}
      </span>

      <span className="text-sm font-semibold text-slate-800">
        {value}
      </span>
    </div>
  );
}

function StatusPill({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <span className="rounded-full bg-slate-100 px-2 py-1 text-[10px] font-medium text-slate-500">
      {children}
    </span>
  );
}

function KeyValueList({
  title,
  values,
}: {
  title: string;
  values: Record<string, string>;
}) {
  const entries = Object.entries(values);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <p className="text-xs font-medium text-slate-400">
        {title}
      </p>

      <div className="mt-3 space-y-2">
        {entries.length === 0 ? (
          <p className="text-xs text-slate-400">
            None recorded
          </p>
        ) : (
          entries.map(([key, value]) => (
            <div
              key={key}
              className="flex items-start justify-between gap-4 border-b border-slate-100 pb-2 last:border-0 last:pb-0"
            >
              <span className="break-all text-[11px] text-slate-400">
                {key}
              </span>

              <span className="break-all text-right text-[11px] font-medium text-slate-600">
                {value}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function RunRow({
  run,
}: {
  run: ModelLabRun;
}) {
  const modelFamily =
    run.tags.model_family ??
    run.params.model_family ??
    "Experiment";

  const validation =
    run.metrics
      .validation_macro_building_nmae ??
    run.metrics.validation_nmae;

  const test =
    run.metrics
      .test_macro_building_nmae ??
    run.metrics.test_nmae;

  return (
    <details className="group">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-5 px-6 py-5 transition hover:bg-slate-50">
        <div className="flex min-w-0 items-center gap-4">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-xs font-semibold text-slate-500">
            ML
          </div>

          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-slate-800">
              {modelFamily}
            </p>

            <p className="mt-1 truncate text-xs text-slate-400">
              {run.run_id}
            </p>
          </div>
        </div>

        <div className="hidden items-center gap-8 sm:flex">
          <RunMetric
            label="Validation"
            value={formatMetric(validation)}
          />

          <RunMetric
            label="Test"
            value={formatMetric(test)}
          />

          <span className="text-xs text-slate-400 transition-transform group-open:rotate-180">
            ↓
          </span>
        </div>
      </summary>

      <div className="border-t border-slate-100 bg-slate-50 px-6 py-5">
        <div className="grid gap-4 sm:grid-cols-3">
          <RunMetric
            label="Status"
            value={run.status}
          />

          <RunMetric
            label="Experiment"
            value={run.experiment_id}
          />

          <RunMetric
            label="Run ID"
            value={run.run_id}
          />
        </div>

        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <KeyValueList
            title="Parameters"
            values={run.params}
          />

          <KeyValueList
            title="Tags"
            values={run.tags}
          />
        </div>
      </div>
    </details>
  );
}

function RunMetric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div>
      <p className="text-[10px] font-medium uppercase tracking-wide text-slate-400">
        {label}
      </p>

      <p className="mt-1 truncate text-xs font-semibold text-slate-700">
        {value}
      </p>
    </div>
  );
}

function formatMetric(
  value: number | null | undefined,
) {
  if (
    value === undefined ||
    value === null ||
    Number.isNaN(value)
  ) {
    return "—";
  }

  return value.toFixed(4);
}

function LoadingState() {
  return (
    <main className="min-h-screen bg-[#f7f8fa] px-5 py-8 md:px-8 lg:px-10">
      <div className="mx-auto max-w-7xl animate-pulse">
        <div className="h-3 w-32 rounded bg-slate-200" />

        <div className="mt-3 h-9 w-52 rounded bg-slate-200" />

        <div className="mt-3 h-4 w-96 max-w-full rounded bg-slate-200" />

        <div className="mt-8 grid gap-5 lg:grid-cols-[1.6fr_1fr]">
          <div className="h-52 rounded-3xl bg-slate-200" />

          <div className="grid grid-cols-2 gap-4">
            {[1, 2, 3, 4].map(
              (item) => (
                <div
                  key={item}
                  className="h-24 rounded-2xl bg-white"
                />
              ),
            )}
          </div>
        </div>

        <div className="mt-6 h-52 rounded-3xl bg-white" />

        <div className="mt-6 h-64 rounded-3xl bg-white" />

        <div className="mt-6 h-96 rounded-3xl bg-white" />
      </div>
    </main>
  );
}