const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:4000";

async function request<T>(
  path: string,
): Promise<T> {
  const response = await fetch(
    `${API_URL}${path}`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      `API request failed: ${response.status}`,
    );
  }

  return response.json() as Promise<T>;
}

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

export type ConsumptionPoint = {
  timestamp: string;
  energy_kwh: number | null;
};

export async function getBuildingConsumption(
  buildingId: string,
  from?: string,
  to?: string,
): Promise<{
  building_id: string;
  from: string | null;
  to: string | null;
  points: ConsumptionPoint[];
}> {
  const params = new URLSearchParams();

  if (from) {
    params.set("from", from);
  }

  if (to) {
    params.set("to", to);
  }

  const query = params.toString();

  return request(
    `/api/buildings/${encodeURIComponent(
      buildingId,
    )}/consumption${query ? `?${query}` : ""}`,
  );
}

export type Forecast = {
  building_id: string;
  timestamp: string;
  predicted_energy_kwh: number;
  model_name: string;
  model_version: string;
};

export async function getBuildingForecast(
  buildingId: string,
  timestamp?: string,
): Promise<Forecast> {
  const params = new URLSearchParams();

  if (timestamp) {
    params.set("timestamp", timestamp);
  }

  const query = params.toString();

  return request(
    `/api/buildings/${encodeURIComponent(
      buildingId,
    )}/forecast${query ? `?${query}` : ""}`,
  );
}

export async function getBuildings(): Promise<{
  buildings: Building[];
}> {
  return request("/api/buildings");
}

export async function getBuilding(
  buildingId: string,
): Promise<{
  building: Building;
}> {
  return request(
    `/api/buildings/${encodeURIComponent(buildingId)}`,
  );
}