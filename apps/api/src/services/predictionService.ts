import { config } from "../config/env.js";
import {
  getPredictionContext,
} from "../repositories/predictionRepository.js";

export type PredictionResult = {
  building_id: string;
  timestamp: string;
  predicted_energy_kwh: number;
  model_name: string;
  model_version: string;
};

export async function predictBuildingEnergy(
  buildingId: string,
  timestamp: string,
): Promise<PredictionResult> {
  const context =
    await getPredictionContext(
      buildingId,
      timestamp,
    );

  const response = await fetch(
    `${config.mlServiceUrl}/predict`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        building_id: buildingId,
        timestamp: context.timestamp,
        site_id: context.site_id,
        primary_use: context.primary_use,
        square_feet: context.square_feet,
        floor_area: context.floor_area,
        timezone: context.timezone,
        air_temperature:
          context.air_temperature,
        dew_temperature:
          context.dew_temperature,
        cloud_coverage:
          context.cloud_coverage,
        wind_speed: context.wind_speed,
        wind_direction:
          context.wind_direction,
        sea_level_pressure:
          context.sea_level_pressure,
        precip_depth_1_hr:
          context.precip_depth_1_hr,
        history: context.history,
      }),
    },
  );

  if (!response.ok) {
    let detail =
      "ML prediction failed.";

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
      // Keep the generic error.
    }

    throw new Error(detail);
  }

  return response.json() as Promise<PredictionResult>;
}