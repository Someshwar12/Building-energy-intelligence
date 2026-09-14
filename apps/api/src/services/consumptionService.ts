import {
  getConsumption,
} from "../repositories/consumptionRepository.js";

export async function getBuildingConsumption(
  buildingId: string,
  from?: string,
  to?: string,
) {
  return getConsumption(
    buildingId,
    from,
    to,
  );
}