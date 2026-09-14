import { Router } from "express";

import {
  predictBuildingEnergy,
} from "../services/predictionService.js";

export const predictionsRouter = Router();

predictionsRouter.get(
  "/buildings/:buildingId/forecast",
  async (req, res) => {
    const { buildingId } = req.params;

    const timestamp =
      typeof req.query.timestamp === "string"
        ? req.query.timestamp
        : "2017-12-31T23:00:00Z";

    try {
      const prediction =
        await predictBuildingEnergy(
          buildingId,
          timestamp,
        );

      res.json(prediction);
    } catch (error) {
      console.error(
        "Failed to generate building forecast:",
        error,
      );

      res.status(502).json({
        error: {
          code: "FORECAST_UNAVAILABLE",
          message:
            "The building forecast is currently unavailable.",
        },
      });
    }
  },
);