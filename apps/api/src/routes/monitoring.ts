import { Router } from "express";

import {
  getMonitoringDrift,
  getMonitoringSummary,
} from "../services/monitoringService.js";

export const monitoringRouter = Router();

monitoringRouter.get("/monitoring/summary", async (_request, response) => {
  try {
    const summary = await getMonitoringSummary();
    response.json(summary);
  } catch (error) {
    const message =
      error instanceof Error
        ? error.message
        : "Monitoring summary unavailable.";

    response.status(502).json({
      error: "MONITORING_UNAVAILABLE",
      message,
    });
  }
});

monitoringRouter.get("/monitoring/drift", async (_request, response) => {
  try {
    const drift = await getMonitoringDrift();
    response.json(drift);
  } catch (error) {
    const message =
      error instanceof Error
        ? error.message
        : "Monitoring drift unavailable.";

    response.status(502).json({
      error: "MONITORING_DRIFT_UNAVAILABLE",
      message,
    });
  }
});