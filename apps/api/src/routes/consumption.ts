import { Router } from "express";

import {
  getBuildingConsumption,
} from "../services/consumptionService.js";

export const consumptionRouter = Router();

consumptionRouter.get(
  "/buildings/:buildingId/consumption",
  async (req, res) => {
    try {
      const { buildingId } = req.params;
      const { from, to } = req.query;

      const points = await getBuildingConsumption(
        buildingId,
        typeof from === "string" ? from : undefined,
        typeof to === "string" ? to : undefined,
      );

      res.json({
        building_id: buildingId,
        from: from ?? null,
        to: to ?? null,
        points,
      });
    } catch (error) {
      console.error(
        "Failed to retrieve consumption:",
        error,
      );

      res.status(500).json({
        error: {
          code: "CONSUMPTION_UNAVAILABLE",
          message:
            "Historical consumption is currently unavailable.",
        },
      });
    }
  },
);