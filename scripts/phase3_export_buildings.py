from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

METADATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "bdg2"
    / "metadata.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "apps"
    / "api"
    / "src"
    / "data"
    / "buildings.json"
)

BUILDING_IDS = [
    "Bear_assembly_Angel",
    "Bear_assembly_Beatrice",
    "Bear_assembly_Danial",
    "Bear_assembly_Diana",
    "Bear_assembly_Genia",
    "Bear_assembly_Harry",
    "Bear_assembly_Jose",
    "Bear_assembly_Roxy",
    "Bear_assembly_Ruby",
    "Bear_education_Alfredo",
    "Bear_education_Alvaro",
    "Bear_education_Arnold",
]


def display_name(building_id: str) -> str:
    return building_id.replace("_", " ").title()


def clean_value(value):
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        return value.item()

    return value


def main() -> None:
    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"Metadata file not found: {METADATA_PATH}"
        )

    metadata = pd.read_csv(METADATA_PATH)

    if "building_id" not in metadata.columns:
        raise ValueError(
            "metadata.csv does not contain building_id."
        )

    metadata["building_id"] = metadata["building_id"].astype(str)

    selected = metadata[
        metadata["building_id"].isin(BUILDING_IDS)
    ].copy()

    missing_ids = sorted(
        set(BUILDING_IDS) - set(selected["building_id"])
    )

    if missing_ids:
        raise ValueError(
            "The following selected buildings were not found: "
            + ", ".join(missing_ids)
        )

    selected = selected.set_index("building_id").loc[BUILDING_IDS]

    records = []

    for building_id, row in selected.iterrows():
        records.append(
            {
                "building_id": building_id,
                "site_id": clean_value(row["site_id"]),
                "name": display_name(building_id),
                "primary_use": clean_value(
                    row["primaryspaceusage"]
                ),
                "square_feet": clean_value(row["sqft"]),
                "floor_area": clean_value(row["sqm"]),
                "timezone": clean_value(row["timezone"]),
                "latitude": clean_value(row["lat"]),
                "longitude": clean_value(row["lng"]),
                "year_built": clean_value(row["yearbuilt"]),
                "number_of_floors": clean_value(
                    row["numberoffloors"]
                ),
                "occupants": clean_value(row["occupants"]),
                "energy_star_score": clean_value(
                    row["energystarscore"]
                ),
                "eui": clean_value(row["eui"]),
                "site_eui": clean_value(row["site_eui"]),
                "heating_type": clean_value(
                    row["heatingtype"]
                ),
                "leed_level": clean_value(row["leed_level"]),
            }
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            records,
            indent=2,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        f"Exported {len(records)} buildings to "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()