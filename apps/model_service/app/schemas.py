from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class EnergyObservation(BaseModel):
    timestamp: datetime
    energy_kwh: float = Field(ge=0)


class PredictionRequest(BaseModel):
    building_id: str = Field(min_length=1)
    timestamp: datetime

    site_id: str = Field(min_length=1)
    primary_use: str = Field(min_length=1)
    square_feet: float = Field(gt=0)
    floor_area: float = Field(gt=0)
    timezone: str = Field(min_length=1)

    air_temperature: float | None = None
    dew_temperature: float | None = None
    cloud_coverage: float | None = Field(default=None, ge=0)
    wind_speed: float | None = Field(default=None, ge=0)
    wind_direction: float | None = Field(default=None, ge=0, le=360)
    sea_level_pressure: float | None = Field(default=None, ge=0)
    precip_depth_1_hr: float | None = Field(default=None, ge=0)

    history: list[EnergyObservation] = Field(min_length=168)

    @field_validator("history")
    @classmethod
    def validate_history(cls, history: list[EnergyObservation]) -> list[EnergyObservation]:
        timestamps = [item.timestamp for item in history]

        if len(set(timestamps)) != len(timestamps):
            raise ValueError("history contains duplicate timestamps")

        if timestamps != sorted(timestamps):
            raise ValueError("history must be sorted chronologically")

        return history


class PredictionResponse(BaseModel):
    building_id: str
    timestamp: datetime
    predicted_energy_kwh: float
    model_name: str
    model_version: str