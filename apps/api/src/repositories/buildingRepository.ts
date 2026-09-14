import buildingsData from "../data/buildings.json" with { type: "json" };

export type Building = {
  building_id: string;
  site_id: string;
  name: string;
  primary_use: string | null;
  square_feet: number | null;
  floor_area: number | null;
  timezone: string | null;
  latitude: number | null;
  longitude: number | null;
  year_built: number | null;
  number_of_floors: number | null;
  occupants: number | null;
  energy_star_score: number | null;
  eui: number | null;
  site_eui: number | null;
  heating_type: string | null;
  leed_level: string | null;
};

const buildings = buildingsData as Building[];

export function getBuildings(): Building[] {
  return buildings;
}

export function getBuildingById(
  buildingId: string,
): Building | undefined {
  return buildings.find(
    (building) => building.building_id === buildingId,
  );
}