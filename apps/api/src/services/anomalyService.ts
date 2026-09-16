import {
  getConsumption,
  type ConsumptionPoint,
} from "../repositories/consumptionRepository.js";

export type AnomalySeverity =
  | "High"
  | "Medium"
  | "Low";

export type Anomaly = {
  timestamp: string;
  energy_kwh: number;
  expected_kwh: number;
  deviation_pct: number;
  score: number;
  severity: AnomalySeverity;
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

const DEFAULT_WINDOW = 24;

function median(values: number[]): number {
  if (values.length === 0) {
    return 0;
  }

  const sorted = [...values].sort(
    (a, b) => a - b,
  );

  const middle = Math.floor(sorted.length / 2);

  if (sorted.length % 2 === 0) {
    return (
      (sorted[middle - 1] + sorted[middle]) / 2
    );
  }

  return sorted[middle];
}

function calculateMad(
  values: number[],
  center: number,
): number {
  return median(
    values.map((value) =>
      Math.abs(value - center),
    ),
  );
}

function classifySeverity(
  score: number,
): AnomalySeverity {
  if (score >= 6) {
    return "High";
  }

  if (score >= 4.5) {
    return "Medium";
  }

  return "Low";
}

function detectAnomalies(
  points: ConsumptionPoint[],
): Anomaly[] {
  const validPoints = points.filter(
    (
      point,
    ): point is ConsumptionPoint & {
      energy_kwh: number;
    } =>
      point.energy_kwh !== null &&
      Number.isFinite(point.energy_kwh) &&
      point.energy_kwh >= 0,
  );

  const anomalies: Anomaly[] = [];

  for (
    let index = DEFAULT_WINDOW;
    index < validPoints.length;
    index += 1
  ) {
    const current = validPoints[index];

    const windowStart =
      Math.max(0, index - DEFAULT_WINDOW);

    const historicalValues = validPoints
      .slice(windowStart, index)
      .map((point) => point.energy_kwh);

    if (historicalValues.length < 12) {
      continue;
    }

    const expected = median(
      historicalValues,
    );

    const mad = calculateMad(
      historicalValues,
      expected,
    );

    /*
     * The small epsilon prevents division by zero
     * when historical consumption is nearly constant.
     */
    const robustScale = Math.max(
      mad * 1.4826,
      Math.max(expected * 0.05, 0.1),
    );

    const deviation =
      current.energy_kwh - expected;

    const score =
      Math.abs(deviation) / robustScale;

    /*
     * A score below 3 is treated as normal.
     */
    if (score < 3) {
      continue;
    }

    const deviationPct =
      expected === 0
        ? current.energy_kwh === 0
          ? 0
          : 100
        : (deviation / expected) * 100;

    anomalies.push({
      timestamp: current.timestamp,
      energy_kwh: current.energy_kwh,
      expected_kwh: expected,
      deviation_pct: deviationPct,
      score,
      severity: classifySeverity(score),
    });
  }

  return anomalies;
}

export async function getBuildingAnomalies(
  buildingId: string,
  from?: string,
  to?: string,
): Promise<AnomalyAnalysis> {
  const points = await getConsumption(
    buildingId,
    from,
    to,
  );

  const anomalies = detectAnomalies(points);

  return {
    building_id: buildingId,
    from: from ?? null,
    to: to ?? null,
    detection_method:
      "24-hour rolling median with MAD-based robust deviation scoring",
    points_analyzed: points.filter(
      (point) =>
        point.energy_kwh !== null &&
        Number.isFinite(point.energy_kwh),
    ).length,
    anomalies_detected: anomalies.length,
    high_severity: anomalies.filter(
      (anomaly) =>
        anomaly.severity === "High",
    ).length,
    medium_severity: anomalies.filter(
      (anomaly) =>
        anomaly.severity === "Medium",
    ).length,
    low_severity: anomalies.filter(
      (anomaly) =>
        anomaly.severity === "Low",
    ).length,
    anomalies,
  };
}