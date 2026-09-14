# Data

## Dataset

The project currently uses the BDG2 building energy dataset as its primary
development dataset.

The dataset provides hourly building electricity consumption together with
building metadata and weather observations.

The current Phase 1 working subset contains 12 selected buildings.

## Source Data

The raw BDG2 data used by the project contains three primary data sources:

### Electricity

Hourly building electricity consumption.

The electricity data is used as the primary time-series signal and prediction
target source.

### Building Metadata

Building-level information including:

- building ID
- site ID
- primary space usage
- square footage
- floor area
- timezone

### Weather

Hourly weather observations including:

- air temperature
- dew temperature
- cloud coverage
- precipitation depth
- sea-level pressure
- wind direction
- wind speed

## Raw Data Location

Raw BDG2 files are stored under:

```text
data/raw/bdg2/
````

The current raw files are:

```text
electricity_cleaned.csv
metadata.csv
weather.csv
```

Raw data is kept separate from generated processed datasets.

## Selected Buildings

The current Phase 1 subset contains 12 buildings:

```text
Bear_assembly_Angel
Bear_assembly_Beatrice
Bear_assembly_Danial
Bear_assembly_Diana
Bear_assembly_Genia
Bear_assembly_Harry
Bear_assembly_Jose
Bear_assembly_Roxy
Bear_assembly_Ruby
Bear_education_Alfredo
Bear_education_Alvaro
Bear_education_Arnold
```

The subset provides multiple buildings for evaluating whether a model
generalizes across different buildings rather than only fitting one building.

## Dataset Dimensions

The canonical Phase 1 feature dataset is:

```text
data/processed/phase1_features.parquet
```

It contains:

* 210,528 rows
* 44 columns
* 12 buildings
* 17,544 rows per building

The time range is:

```text
2016-01-01 00:00
        →
2017-12-31 23:00
```

The dataset contains two complete years of hourly observations per selected
building.

## Data Validation

The Phase 1 validation pipeline checks the structural and temporal integrity
of the dataset.

Validation includes:

* duplicate building/timestamp keys
* hourly timestamp continuity
* missing energy observations
* target availability
* lag correctness
* feature consistency

Final validation results:

```text
Duplicate building/timestamp keys: 0
Non-hourly rows:                   0
1h lag mismatches:                 0
2h lag mismatches:                 0
3h lag mismatches:                 0
24h lag mismatches:                0
48h lag mismatches:                0
72h lag mismatches:                0
168h lag mismatches:               0
```

The processed dataset contains:

```text
Missing energy observations: 18,169
Missing target observations: 18,178
```

Missingness is explicitly represented as part of the data-quality state rather
than silently treating missing observations as valid measurements.

## Data Quality Flags

The feature dataset includes quality-related fields used to represent data
quality conditions.

These include:

```text
quality_missing
quality_negative
quality_duplicate
quality_flag
```

Duplicate keys are independently validated as part of the data-quality
pipeline.

## Feature Dataset

The Phase 1 feature dataset contains the following major feature groups.

### Identity and Metadata

```text
building_id
site_id
primary_use
square_feet
floor_area
timezone
```

### Energy

```text
energy_kwh
```

### Weather

```text
air_temperature
dew_temperature
cloud_coverage
wind_speed
wind_direction
sea_level_pressure
precip_depth_1_hr
```

### Calendar

```text
hour
day_of_week
month
day_of_year
is_weekend
```

### Cyclical Time

```text
hour_sin
hour_cos
day_of_year_sin
day_of_year_cos
```

### Historical Energy Lags

```text
energy_lag_1h
energy_lag_2h
energy_lag_3h
energy_lag_24h
energy_lag_48h
energy_lag_72h
energy_lag_168h
```

### Rolling Energy Statistics

```text
energy_roll_mean_3h
energy_roll_mean_6h
energy_roll_mean_24h
energy_roll_max_24h
energy_roll_mean_168h
energy_roll_max_168h
```

### Degree-Day Features

```text
heating_degree_hour
cooling_degree_hour
```

### Prediction Target

```text
target_next_hour_kwh
```

## Feature Construction Pipeline

The current data pipeline is:

```text
Raw BDG2 CSV Files
        ↓
Load Electricity Data
        ↓
Normalize Metadata Columns
        ↓
Normalize Weather Columns
        ↓
Merge Electricity + Metadata
        ↓
Merge Weather by Site + Timestamp
        ↓
Calendar Features
        ↓
Historical Energy Lags
        ↓
Strictly-Past Rolling Features
        ↓
Weather-Derived Features
        ↓
Next-Hour Target
        ↓
Validation
        ↓
phase1_features.parquet
```

## Timestamp Handling

The project treats energy consumption as an hourly time series.

Timestamps are converted to datetime values during processing and the final
dataset is sorted by:

```text
building_id
timestamp
```

The feature pipeline verifies that observations occur at hourly intervals.

## Historical Energy Features

Historical energy features provide the model with information about recent and
seasonal consumption patterns.

The project uses lags at:

```text
1 hour
2 hours
3 hours
24 hours
48 hours
72 hours
168 hours
```

These represent immediate history, daily history, and weekly history.

## Rolling Features

Rolling features summarize recent energy behavior.

The project calculates:

```text
3-hour mean
6-hour mean
24-hour mean
24-hour maximum
168-hour mean
168-hour maximum
```

Rolling calculations use strictly historical observations.

The energy series is shifted by one hour before rolling calculations so that
the current prediction interval cannot contribute information to its own
features.

This is an explicit protection against temporal data leakage.

## Weather Features

Weather observations are joined to building energy observations using:

```text
site_id
timestamp
```

The normalized weather fields are:

```text
air_temperature
dew_temperature
cloud_coverage
wind_speed
wind_direction
sea_level_pressure
precip_depth_1_hr
```

Weather availability is not uniform across all variables.

Temperature-related variables are highly complete, while cloud coverage and
precipitation contain more missing observations.

Missing weather values are preserved rather than fabricated.

## Degree-Day Features

The pipeline derives two temperature-related features:

```text
heating_degree_hour
cooling_degree_hour
```

The degree-day features use a base temperature of 18°C.

Heating degree hour increases when temperature falls below the base temperature.

Cooling degree hour increases when temperature rises above the base temperature.

## Prediction Target

The forecasting target is the next hourly electricity consumption value.

For an observation at time `t`:

```text
target_next_hour_kwh = energy(t + 1)
```

The target is generated using a one-step negative shift within each building.

This makes the task a next-hour forecasting problem.

## Train/Validation/Test Data

The project uses temporal splitting rather than random row-level splitting.

This preserves the chronological nature of the forecasting problem and avoids
allowing future observations to leak into earlier training periods.

The exact split logic is implemented in the project's temporal split utilities
and is tested independently.

## Data and Model Contract

The processed feature dataset is the canonical input to Phase 1 model
training.

The resulting model artifact is:

```text
models/random_forest_phase1.joblib
```

Phase 2 reconstructs the required features from API input and verifies feature
parity against the Phase 1 feature builder.

This establishes a training-to-serving data contract.

## Future Data Work

Later phases may introduce:

* additional buildings
* additional datasets
* automated data ingestion
* stronger schema validation
* automated data-quality reports
* data-quality monitoring
* feature distribution monitoring
* data drift detection
* incremental data pipelines
* production data ingestion

The current BDG2 dataset remains the reproducible development foundation for
the platform.

