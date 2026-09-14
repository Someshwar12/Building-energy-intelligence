import { Router } from "express";

import {
  findBuilding,
  listBuildings,
} from "../services/buildingService.js";

export const buildingsRouter = Router();

buildingsRouter.get("/", (_req, res) => {
  res.json({
    buildings: listBuildings(),
  });
});

buildingsRouter.get("/:buildingId", (req, res) => {
  const building = findBuilding(req.params.buildingId);

  if (!building) {
    res.status(404).json({
      error: {
        code: "BUILDING_NOT_FOUND",
        message: "Building not found.",
      },
    });

    return;
  }

  res.json({
    building,
  });
});