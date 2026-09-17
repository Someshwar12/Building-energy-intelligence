import { config } from "../config/env.js";

export type MonitoringSummary = {
  service: {
    name: string;
    version: string;
    status: string;
    model_name: string;
    model_version: string;
    serving_mode: string;
  };
  monitoring: {
    requests: {
      total: number;
      successful: number;
      failed: number;
    };
    latency_ms: {
      sample_count: number;
      average: number | null;
      p50: number | null;
      p95: number | null;
      p99: number | null;
    };
    model_versions: Record<string, number>;
    serving_modes: Record<string, number>;
    data_quality: Record<string, number>;
    last_prediction_at: string | null;
    last_error_at: string | null;
    last_error: string | null;
  };
};

export type MonitoringDriftFeature = {
  feature: string;
  psi: number | null;
  status: string;
  sample_count: number;
  minimum_sample_count: number;
};

export type MonitoringDrift = {
  status: string;
  sample_count: number;
  minimum_sample_count: number;
  thresholds: {
    warning_psi: number;
    critical_psi: number;
  };
  reference: {
    available: boolean;
    feature_count: number;
    source: string | null;
  };
  features: Record<string, MonitoringDriftFeature>;
};

export async function getMonitoringSummary(): Promise<MonitoringSummary> {
  const response = await fetch(
    `${config.mlServiceUrl}/monitoring/summary`,
  );

  if (!response.ok) {
    let detail = "Monitoring summary request failed.";

    try {
      const body = await response.json();

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

  return response.json() as Promise<MonitoringSummary>;
}

export async function getMonitoringDrift(): Promise<MonitoringDrift> {
  const response = await fetch(
    `${config.mlServiceUrl}/monitoring/drift`,
  );

  if (!response.ok) {
    let detail = "Monitoring drift request failed.";

    try {
      const body = await response.json();

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

  return response.json() as Promise<MonitoringDrift>;
}