import { config } from "../config/env.js";

export type ModelVersion = {
  version: string;
  model_name: string;
  run_id: string;
  status: string;
  aliases: string[];
  description: string | null;
  created_at: number | null;
  updated_at: number | null;
  model_family: string | null;
  validation_status: string | null;
  lifecycle_status: string | null;
  promotion_metric: string | null;
  promotion_reason: string | null;
  baseline_guard: string | null;
  baseline_model: string | null;
  baseline_validation_nmae: string | null;
  rejection_reason: string | null;
  metrics: Record<string, number>;
  params: Record<string, string>;
  tags: Record<string, string>;
};

export type BaselineResult = {
  baseline: string;
  metrics: Record<string, number>;
};

export type ModelLabBaseline = {
  available: boolean;
  name: string;
  display_name: string;
  strategy: string;
  metrics: Record<string, number>;
  all_baselines: BaselineResult[];
  source: string | null;
};

export type ModelLabSummary = {
  model_name: string;

  production: {
    model_name: string;
    version: string;
    alias: string | null;
    run_id: string | null;
    serving_mode: string;
  };

  candidate: {
    version: string;
    model_family: string | null;
  } | null;

  registered_versions: number;
  evaluated_versions: number;
  rejected_versions: number;

  baseline: ModelLabBaseline;

  versions: ModelVersion[];
};

export type ModelLabRun = {
  run_id: string;
  experiment_id: string;
  status: string;
  start_time: number | null;
  end_time: number | null;
  params: Record<string, string>;
  metrics: Record<string, number>;
  tags: Record<string, string>;
};

async function request<T>(
  path: string,
): Promise<T> {
  const response = await fetch(
    `${config.mlServiceUrl}${path}`,
  );

  if (!response.ok) {
    let detail =
      "Model Lab request failed.";

    try {
      const body =
        await response.json();

      if (
        body &&
        typeof body === "object" &&
        "detail" in body
      ) {
        detail = String(body.detail);
      }
    } catch {
      // Keep generic error.
    }

    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

export async function getModelLabSummary() {
  return request<ModelLabSummary>(
    "/model-lab/summary",
  );
}

export async function getModelLabVersions() {
  return request<{
    model_name: string;
    versions: ModelVersion[];
  }>("/model-lab/versions");
}

export async function getModelLabRuns() {
  return request<{
    model_name: string;
    runs: ModelLabRun[];
  }>("/model-lab/runs");
}