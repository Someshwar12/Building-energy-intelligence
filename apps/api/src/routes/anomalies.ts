import { Router } from "express";

import {
  getBuildingAnomalies,
} from "../services/anomalyService.js";

export const anomaliesRouter = Router();

anomaliesRouter.get(
  "/buildings/:buildingId/anomalies",
  async (req, res) => {
    try {
      const { buildingId } = req.params;
      const { from, to } = req.query;

      const result =
        await getBuildingAnomalies(
          buildingId,
          typeof from === "string"
            ? from
            : undefined,
          typeof to === "string"
            ? to
            : undefined,
        );

      res.json(result);
    } catch (error) {
      console.error(
        "Failed to detect anomalies:",
        error,
      );

      res.status(500).json({
        error: {
          code: "ANOMALIES_UNAVAILABLE",
          message:
            "Anomaly detection is currently unavailable.",
        },
      });
    }
  },
);