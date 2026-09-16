import { Router } from "express";

import {
  getModelLabRuns,
  getModelLabSummary,
  getModelLabVersions,
} from "../services/modelLabService.js";

export const modelLabRouter = Router();

modelLabRouter.get(
  "/model-lab/summary",
  async (_req, res) => {
    try {
      const summary =
        await getModelLabSummary();

      res.json(summary);
    } catch (error) {
      console.error(
        "Failed to load Model Lab summary:",
        error,
      );

      res.status(502).json({
        error: {
          code: "MODEL_LAB_UNAVAILABLE",
          message:
            "Model Lab is currently unavailable.",
        },
      });
    }
  },
);

modelLabRouter.get(
  "/model-lab/versions",
  async (_req, res) => {
    try {
      const versions =
        await getModelLabVersions();

      res.json(versions);
    } catch (error) {
      console.error(
        "Failed to load Model Lab versions:",
        error,
      );

      res.status(502).json({
        error: {
          code: "MODEL_LAB_VERSIONS_UNAVAILABLE",
          message:
            "Model Lab versions are currently unavailable.",
        },
      });
    }
  },
);

modelLabRouter.get(
  "/model-lab/runs",
  async (_req, res) => {
    try {
      const runs =
        await getModelLabRuns();

      res.json(runs);
    } catch (error) {
      console.error(
        "Failed to load Model Lab runs:",
        error,
      );

      res.status(502).json({
        error: {
          code: "MODEL_LAB_RUNS_UNAVAILABLE",
          message:
            "Model Lab runs are currently unavailable.",
        },
      });
    }
  },
);