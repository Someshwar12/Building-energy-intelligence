import fs from "node:fs";
import path from "node:path";

import {
  parquetMetadata,
  parquetRead,
} from "hyparquet";

type ParquetRow = unknown[];

export type ConsumptionPoint = {
  timestamp: string;
  energy_kwh: number | null;
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

  cachedColumns =
    metadata.schema
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

export async function getConsumption(
  buildingId: string,
  from?: string,
  to?: string,
): Promise<ConsumptionPoint[]> {
  const rows = await loadRows();

  const buildingIdIndex =
    getColumnIndex(BUILDING_ID_COLUMN);

  const timestampIndex =
    getColumnIndex(TIMESTAMP_COLUMN);

  const energyIndex =
    getColumnIndex(ENERGY_COLUMN);

  return rows
    .filter((row) => {
      if (String(row[buildingIdIndex]) !== buildingId) {
        return false;
      }

      const timestamp = new Date(
        String(row[timestampIndex]),
      );

      if (from && timestamp < new Date(from)) {
        return false;
      }

      if (to && timestamp > new Date(to)) {
        return false;
      }

      return true;
    })
    .map((row) => ({
      timestamp: new Date(
        String(row[timestampIndex]),
      ).toISOString(),
      energy_kwh:
        row[energyIndex] == null
          ? null
          : Number(row[energyIndex]),
    }))
    .sort(
      (a, b) =>
        new Date(a.timestamp).getTime() -
        new Date(b.timestamp).getTime(),
    );
}