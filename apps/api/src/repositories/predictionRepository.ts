import fs from "node:fs";
import path from "node:path";

import {
  parquetMetadata,
  parquetRead,
} from "hyparquet";

type ParquetRow = unknown[];

export type PredictionContext = {
  timestamp: string;
  site_id: string;
  primary_use: string;
  square_feet: number;
  floor_area: number;
  timezone: string;
  air_temperature: number | null;
  dew_temperature: number | null;
  cloud_coverage: number | null;
  wind_speed: number | null;
  wind_direction: number | null;
  sea_level_pressure: number | null;
  precip_depth_1_hr: number | null;
  history: {
    timestamp: string;
    energy_kwh: number;
  }[];
};

const PROJECT_ROOT = path.resolve(
  import.meta.dirname,
  "../../../..",
);

const DATASET_PATH = path.join(
  PROJECT_ROOT,
  "data",
  "processed",
  "phase1_features.parquet",
);

const BUILDING_ID_COLUMN = "building_id";
const TIMESTAMP_COLUMN = "timestamp";
const ENERGY_COLUMN = "energy_kwh";
const SITE_ID_COLUMN = "site_id";
const PRIMARY_USE_COLUMN = "primary_use";
const SQUARE_FEET_COLUMN = "square_feet";
const FLOOR_AREA_COLUMN = "floor_area";
const TIMEZONE_COLUMN = "timezone";
const AIR_TEMPERATURE_COLUMN = "air_temperature";
const DEW_TEMPERATURE_COLUMN = "dew_temperature";
const CLOUD_COVERAGE_COLUMN = "cloud_coverage";
const WIND_SPEED_COLUMN = "wind_speed";
const WIND_DIRECTION_COLUMN = "wind_direction";
const SEA_LEVEL_PRESSURE_COLUMN = "sea_level_pressure";
const PRECIP_DEPTH_COLUMN = "precip_depth_1_hr";

let cachedRows: ParquetRow[] | null = null;
let cachedColumns: string[] | null = null;

async function loadRows(): Promise<ParquetRow[]> {
  if (cachedRows) {
    return cachedRows;
  }

  if (!fs.existsSync(DATASET_PATH)) {
    throw new Error(
      `Historical dataset not found: ${DATASET_PATH}`,
    );
  }

  const buffer = await fs.promises.readFile(DATASET_PATH);

  const file = buffer.buffer.slice(
    buffer.byteOffset,
    buffer.byteOffset + buffer.byteLength,
  );

  const metadata = parquetMetadata(file);

  cachedColumns = metadata.schema
    .filter(
      (column) =>
        column.name !== "schema" &&
        column.name !== undefined,
    )
    .map((column) => column.name);

  await new Promise<void>((resolve, reject) => {
    try {
      parquetRead({
        file,
        onComplete: (rows) => {
          cachedRows = rows as ParquetRow[];
          resolve();
        },
      });
    } catch (error) {
      reject(error);
    }
  });

  if (!cachedRows || !cachedColumns) {
    throw new Error(
      "Parquet dataset could not be loaded.",
    );
  }

  return cachedRows;
}

function getColumnIndex(columnName: string): number {
  if (!cachedColumns) {
    throw new Error(
      "Parquet columns are not initialized.",
    );
  }

  const index = cachedColumns.indexOf(columnName);

  if (index === -1) {
    throw new Error(
      `Required Parquet column not found: ${columnName}`,
    );
  }

  return index;
}

function value(
  row: ParquetRow,
  columnName: string,
): unknown {
  return row[getColumnIndex(columnName)];
}

function numberValue(
  row: ParquetRow,
  columnName: string,
): number | null {
  const raw = value(row, columnName);

  if (raw == null) {
    return null;
  }

  const number = Number(raw);

  return Number.isFinite(number) ? number : null;
}

function stringValue(
  row: ParquetRow,
  columnName: string,
): string {
  return String(value(row, columnName));
}

function findRow(
  rows: ParquetRow[],
  buildingId: string,
  timestamp: Date,
): ParquetRow | undefined {
  return rows.find((row) => {
    if (
      stringValue(row, BUILDING_ID_COLUMN) !==
      buildingId
    ) {
      return false;
    }

    const rowTimestamp = new Date(
      stringValue(row, TIMESTAMP_COLUMN),
    );

    return (
      rowTimestamp.getTime() === timestamp.getTime()
    );
  });
}

export async function getPredictionContext(
  buildingId: string,
  predictionTimestamp: string,
): Promise<PredictionContext> {
  const rows = await loadRows();

  const timestamp = new Date(predictionTimestamp);

  if (Number.isNaN(timestamp.getTime())) {
    throw new Error(
      "Prediction timestamp is invalid.",
    );
  }

  const targetRow = findRow(
    rows,
    buildingId,
    timestamp,
  );

  if (!targetRow) {
    throw new Error(
      "Prediction timestamp is unavailable for this building.",
    );
  }

  const historyStart = new Date(
    timestamp.getTime() -
      168 * 60 * 60 * 1000,
  );

  const history = rows
    .filter((row) => {
      if (
        stringValue(row, BUILDING_ID_COLUMN) !==
        buildingId
      ) {
        return false;
      }

      const rowTimestamp = new Date(
        stringValue(row, TIMESTAMP_COLUMN),
      );

      return (
        rowTimestamp >= historyStart &&
        rowTimestamp < timestamp
      );
    })
    .sort(
      (a, b) =>
        new Date(
          stringValue(a, TIMESTAMP_COLUMN),
        ).getTime() -
        new Date(
          stringValue(b, TIMESTAMP_COLUMN),
        ).getTime(),
    );

  if (history.length !== 168) {
    throw new Error(
      `Expected 168 historical observations, found ${history.length}.`,
    );
  }

  const expectedStart = historyStart.getTime();

  for (let index = 0; index < history.length; index += 1) {
    const expectedTimestamp =
      expectedStart +
      index * 60 * 60 * 1000;

    const actualTimestamp = new Date(
      stringValue(
        history[index],
        TIMESTAMP_COLUMN,
      ),
    ).getTime();

    if (actualTimestamp !== expectedTimestamp) {
      throw new Error(
        "Historical observations are not consecutive hourly records.",
      );
    }
  }

  return {
    timestamp: timestamp.toISOString(),

    site_id: stringValue(
      targetRow,
      SITE_ID_COLUMN,
    ),

    primary_use: stringValue(
      targetRow,
      PRIMARY_USE_COLUMN,
    ),

    square_feet:
      numberValue(
        targetRow,
        SQUARE_FEET_COLUMN,
      ) ?? 0,

    floor_area:
      numberValue(
        targetRow,
        FLOOR_AREA_COLUMN,
      ) ?? 0,

    timezone: stringValue(
      targetRow,
      TIMEZONE_COLUMN,
    ),

    air_temperature: numberValue(
      targetRow,
      AIR_TEMPERATURE_COLUMN,
    ),

    dew_temperature: numberValue(
      targetRow,
      DEW_TEMPERATURE_COLUMN,
    ),

    cloud_coverage: numberValue(
      targetRow,
      CLOUD_COVERAGE_COLUMN,
    ),

    wind_speed: numberValue(
      targetRow,
      WIND_SPEED_COLUMN,
    ),

    wind_direction: numberValue(
      targetRow,
      WIND_DIRECTION_COLUMN,
    ),

    sea_level_pressure: numberValue(
      targetRow,
      SEA_LEVEL_PRESSURE_COLUMN,
    ),

    precip_depth_1_hr: numberValue(
      targetRow,
      PRECIP_DEPTH_COLUMN,
    ),

    history: history.map((row) => ({
      timestamp: new Date(
        stringValue(row, TIMESTAMP_COLUMN),
      ).toISOString(),

      energy_kwh:
        numberValue(
          row,
          ENERGY_COLUMN,
        ) ?? 0,
    })),
  };
}