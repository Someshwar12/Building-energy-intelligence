import {
  getBuildingById,
  getBuildings,
} from "../repositories/buildingRepository.js";

export function listBuildings() {
  return getBuildings();
}

export function findBuilding(buildingId: string) {
  return getBuildingById(buildingId);
}