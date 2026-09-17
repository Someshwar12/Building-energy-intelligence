const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:4000";

async function request<T>(
  path: string,
): Promise<T> {
  const response = await fetch(
    `${API_URL}${path}`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      `API request failed: ${response.status}`,
    );
  }

  return response.json() as Promise<T>;
}

export type Building = {
  building_id: string;
  site_id: string;
  name: string;
  primary_use: string | null;
  square_feet: number | null;
  floor_area: number | null;
  timezone: string | null;
  latitude: number | null;
  longitude: number | null;
  year_built: number | null;
  number_of_floors: number | null;
  occupants: number | null;
  energy_star_score: number | null;
  eui: number | null;
  site_eui: number | null;
  heating_type: string | null;
  leed_level: string | null;
};

export type ConsumptionPoint = {
  timestamp: string;
  energy_kwh: number | null;
};

export async function getBuildingConsumption(
  buildingId: string,
  from?: string,
  to?: string,
): Promise<{
  building_id: string;
  from: string | null;
  to: string | null;
  points: ConsumptionPoint[];
}> {
  const params = new URLSearchParams();

  if (from) {
    params.set("from", from);
  }

  if (to) {
    params.set("to", to);
  }

  const query = params.toString();

  return request(
    `/api/buildings/${encodeURIComponent(
      buildingId,
    )}/consumption${query ? `?${query}` : ""}`,
  );
}

export type Forecast = {
  building_id: string;
  timestamp: string;
  predicted_energy_kwh: number;
  model_name: string;
  model_version: string;
};

export async function getBuildingForecast(
  buildingId: string,
  timestamp?: string,
): Promise<Forecast> {
  const params = new URLSearchParams();

  if (timestamp) {
    params.set("timestamp", timestamp);
  }

  const query = params.toString();

  return request(
    `/api/buildings/${encodeURIComponent(
      buildingId,
    )}/forecast${query ? `?${query}` : ""}`,
  );
}

export async function getBuildings(): Promise<{
  buildings: Building[];
}> {
  return request("/api/buildings");
}

export async function getBuilding(
  buildingId: string,
): Promise<{
  building: Building;
}> {
  return request(
    `/api/buildings/${encodeURIComponent(buildingId)}`,
  );
}

export type Anomaly = {
  timestamp: string;
  energy_kwh: number;
  expected_kwh: number;
  deviation_pct: number;
  score: number;
  severity: "High" | "Medium" | "Low";
};

export type AnomalyAnalysis = {
  building_id: string;
  from: string | null;
  to: string | null;
  detection_method: string;
  points_analyzed: number;
  anomalies_detected: number;
  high_severity: number;
  medium_severity: number;
  low_severity: number;
  anomalies: Anomaly[];
};

export async function getBuildingAnomalies(
  buildingId: string,
  from?: string,
  to?: string,
): Promise<AnomalyAnalysis> {
  const params = new URLSearchParams();

  if (from) {
    params.set("from", from);
  }

  if (to) {
    params.set("to", to);
  }

  const query = params.toString();

  return request(
    `/api/buildings/${encodeURIComponent(
      buildingId,
    )}/anomalies${query ? `?${query}` : ""}`,
  );
}

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
  baseline: ModelLabBaseline;
  registered_versions: number;
  evaluated_versions: number;
  rejected_versions: number;
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

export async function getModelLabSummary(): Promise<ModelLabSummary> {
  return request<ModelLabSummary>(
    "/api/model-lab/summary",
  );
}

export async function getModelLabVersions(): Promise<{
  model_name: string;
  versions: ModelVersion[];
}> {
  return request<{
    model_name: string;
    versions: ModelVersion[];
  }>("/api/model-lab/versions");
}

export async function getModelLabRuns(): Promise<{
  model_name: string;
  runs: ModelLabRun[];
}> {
  return request<{
    model_name: string;
    runs: ModelLabRun[];
  }>("/api/model-lab/runs");
}

export type MonitoringSummaryData = {
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

export async function getMonitoringSummary(): Promise<MonitoringSummaryData> {
  return request<MonitoringSummaryData>(
    "/api/monitoring/summary",
  );
}

export async function getMonitoringDrift(): Promise<MonitoringDrift> {
  return request<MonitoringDrift>(
    "/api/monitoring/drift",
  );
}