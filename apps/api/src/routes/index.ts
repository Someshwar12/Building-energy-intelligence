import { Router } from "express";

import { buildingsRouter } from "./buildings.js";
import { consumptionRouter } from "./consumption.js";
import { predictionsRouter } from "./predictions.js";
import { anomaliesRouter } from "./anomalies.js";
import { modelLabRouter } from "./modelLab.js";

export const router = Router();

router.use("/buildings", buildingsRouter);
router.use("/", consumptionRouter);
router.use("/", predictionsRouter);
router.use("/", anomaliesRouter);
router.use("/", modelLabRouter);