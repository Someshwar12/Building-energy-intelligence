import { Router } from "express";

import { buildingsRouter } from "./buildings.js";
import { consumptionRouter } from "./consumption.js";
import { predictionsRouter } from "./predictions.js";

export const router = Router();

router.use(
  "/buildings",
  buildingsRouter,
);

router.use(
  "/",
  consumptionRouter,
);

router.use(
  "/",
  predictionsRouter,
);