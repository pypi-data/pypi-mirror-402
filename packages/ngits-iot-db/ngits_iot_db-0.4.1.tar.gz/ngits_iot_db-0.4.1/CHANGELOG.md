# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.1] - 2026-01-19

### Added
- **Time dimension table** (`DimTime`) for time-based analytics:
  - `time_id` - Primary key in HHMMSS format (e.g., 143000 for 14:30:00)
  - `time` - Time value (TIME type)
  - `hour`, `minute`, `second` - Time components
  - `hour_of_day` - Hour of day (0-23)
  - `is_business_hours` - Business hours flag (8:00-17:00)
  - `time_period` - Period of day (night, morning, afternoon, evening)
- Added `time_id` foreign key relation to `FactUsage` table (nullable, defaults to NULL)
  - Enables time-based aggregations and BI queries using `dim_time` dimension
  - Added index `idx_usage_time` for query performance
  - Updated model in `iot_db/models/facts/usage.py`
- **Seed script for DimTime** (`iot_db.scripts.populate_dim_time`):
  - Generates 1440 time records (every minute from 00:00 to 23:59)
  - Can be run as module: `python -m iot_db.scripts.populate_dim_time`
  - Can be imported as function: `from iot_db.scripts import populate_dim_time`

### Migration Notes
- Database migration required: run `alembic upgrade head`
- Existing records will have `time_id = NULL`
- Populate `DimTime` table using: `python -m iot_db.scripts.populate_dim_time`

## [0.4.0] - 2026-01-19

### Added
- **Energy type breakdown and phase support** for electricity meters in `FactMeasurement` and `FactUsage`:
  - `FactMeasurement` model extended with electricity-specific fields:
    - `active_forward` / `active_reverse` - Active energy consumption/production (kWh)
    - `reactive_forward` / `reactive_reverse` - Reactive energy consumption/production (kVArh)
    - `phase_number` - Phase identifier (1, 2, 3) or NULL for single-phase/total measurements
    - `measurement_type` - Indicator: 'simple' (water/gas), 'phase' (per-phase), 'total' (sum of phases)
  - `FactUsage` model extended with detailed energy aggregation fields:
    - `active_forward_start/end/consumption` - Active energy consumed during period
    - `active_reverse_start/end/production` - Active energy produced during period
    - `reactive_forward_start/end/consumption` - Reactive energy consumed
    - `reactive_reverse_start/end/production` - Reactive energy produced
    - `net_consumption` - Net active energy (consumption - production)
    - `phase_number` - Phase identifier for multi-phase meters
    - `usage_type` - Indicator: 'simple', 'phase', or 'total'
  - Helper methods in both models:
    - `is_simple()`, `is_electricity()`, `is_phase()`, `is_total()`
    - `get_net_active_energy()`, `calculate_net_consumption()`
    - `get_energy_balance()` for comprehensive energy reporting

### Changed
- **BREAKING**: `FactMeasurement.value` is now nullable (was NOT NULL)
  - Simple meters (water, gas, heat) use `value` field
  - Electricity meters use dedicated energy fields (`active_forward`, etc.)
- **BREAKING**: `FactUsage` consumption fields now nullable:
  - `start_value`, `end_value`, `consumption` - nullable for backward compatibility
  - Electricity meters use dedicated energy breakdown fields
- **BREAKING**: Updated unique constraints to include `phase_number`:
  - `FactMeasurement`: (tenant, device_id, measured_ts, phase_number)
  - `FactUsage`: (tenant, device_id, period_type, start_ts, phase_number)
- Updated indexes for phase-based queries:
  - Added `idx_measurement_phase`, `idx_measurement_type` to `FactMeasurement`
  - Added `idx_usage_phase`, `idx_usage_net` to `FactUsage`

### Migration Notes
- Existing simple meter data (water, gas, heat) remains compatible
- Set `measurement_type = 'simple'` and `phase_number = NULL` for existing records
- New electricity meter data should use dedicated energy fields with appropriate `measurement_type`
- Database migration required: run `alembic upgrade head`

## [0.3.3] - 2026-01-15

### Added
- Added `date_id` foreign key to `FactState` table for consistency with other fact tables
  - Enables date-based aggregations and BI queries using `dim_date` dimension
  - Added index `idx_state_date` for query performance
  - Updated model in `iot_db/models/facts/state.py`

## [0.3.2] - 2026-01-15

### Fixed
- Fixed `FactState.state_data` column type from `JSON` to `JSONB`
  - PostgreSQL GIN indexes require JSONB type, not JSON
  - Updated model in `iot_db/models/facts/state.py`
  - Updated migration `7e65d4230d6b_add_fact_tables.py`
  - Resolves error: "data type json has no default operator class for access method gin"

## [0.3.1] - 2026-01-15

### Fixed
- Added missing database migration `7e65d4230d6b_add_fact_tables.py` for DWH fact tables
  - Creates `fact_measurement` table with indexes for performance
  - Creates `fact_state` table with GIN index for JSON queries
  - Creates `fact_usage` table with composite indexes
  - Adds index on `measurement_raw.is_processed` field
  - Migration ensures proper foreign key relationships with dimension tables

## [0.3.0] - 2026-01-15

### Added
- Data Warehouse (DWH) architecture implementation with Hybrid Star Schema
- New dimension models in `iot_db/models/dimensions/`:
  - `DimDataSource` - Dictionary of IoT data sources (sensorhub, chirpstack, supla)
  - `DimChannelFunction` - Device/channel function types with source mapping
  - `DimDevice` - Universal device registry with denormalization for performance and multi-channel support
  - `DimDate` - Date dimension for time-based analytics
- Multi-channel device support in `DimDevice` model:
  - `device_id` (Text) - Physical device ID shared across channels
  - `device_channel_id` (Text) - Device's channel ID
  - `device_name` (Text) - Physical device name (denormalized for performance)
  - `device_model` (Text) - Physical device model (denormalized for performance)
  - `parent_device_id` (Integer, FK) - Optional parent device for hierarchical organization
  - New indexes: `idx_device_device_id`, `idx_device_device_channel`
- Extended `RawMeasurement` model for DWH staging (replaces separate FactRawData table):
  - Added `processed_ts` - Timestamp when record was processed
  - Added `processing_error` - Error message if processing failed
  - Made `type` field nullable for backward compatibility with new DWH records
  - Added helper methods: `mark_as_processed()`, `mark_as_failed(error)`
  - Serves as unified staging area for both legacy models and DWH fact tables
- New fact models in `iot_db/models/facts/`:
  - `FactMeasurement` - Counter-based measurements for meters (electricity, water, heat, gas)
  - `FactState` - Device state snapshots for sensors and actuators
  - `FactUsage` - Pre-calculated consumption aggregates (hourly, daily, monthly, yearly)
- Migration tracking fields in `RawMeasurement` model:
  - `migrated_to_dwh` (Boolean, indexed) - Flag indicating if record was migrated to DWH
  - `migrated_ts` (DateTime) - Timestamp of migration to DWH
  - `mark_as_migrated()` method - Helper method for marking records as migrated
- Seed scripts for DWH (included in package):
  - `iot_db.scripts.seed_dimension_data` - Populates dimension tables
  - `iot_db.scripts.populate_dim_date` - Generates date dimension with Polish holidays support
  - Scripts can be run as modules: `python -m iot_db.scripts.seed_dimension_data`
  - Scripts can be imported as functions: `from iot_db.scripts import seed_dimension_data`

### Deprecated
- `DimDevice.external_id` is now deprecated in favor of `device_id`
  - Field kept for backward compatibility but should not be used in new code
  - Use `device_id` for device identification and `device_name` for display

## [0.2.6] - 2026-01-06

### Fixed
- Fixed missing `Sources` enum export in package `__init__.py`

## [0.2.5] - 2026-01-06

### Added
- Added `source` field to `RawMeasurement` model for tracking data source origin
- New `Sources` enum in base models with values: sensorhub (1), chirpstack (2), supla (3)
- `source_enum` property for convenient access to Sources enum on RawMeasurement
- Database migration `e0d5bb6c3974_add_source_field_to_rawmeasurement.py` adds source column with default value sensorhub

## [0.2.4] - 2025-08-13

### Added
- Added `Alert` model for storing active and resolved alert instances
- Alert model features:
  - `active_marker` for tracking alert status (NULL for resolved, True for active)
  - `detected_ts` for when alert was first detected
  - `resolved_ts` for when alert was resolved
  - `details` JSON field for flexible alert data storage
  - Unique constraint ensuring one active alert per device/type/level combination
  - Foreign key relationship to `AlertDefinition`
- Removed `device_name` from `AlertBase`, moved to `AlertDefinition` model

### Changed
- Alembic migration files formatted with isort and black for consistent code style

## [0.2.3] - 2025-08-13

### Added
- Added `receivers` field to `AlertDefinition` model for storing alert notification recipients as JSON
- Database migration `314a5d69646a_add_receivers_to_alert_definition.py` adds the receivers column

## [0.2.2] - 2025-08-05

### Changed
- Removed unique constraint on `alert_definition` table for `tenant` and `meter_id` columns
- Database migration `90c1158cc2ba_delete_alert_uniqueness.py` removes the uniqueness constraint

## [0.2.1] - 2025-08-04

### Fixed
- Fixed missing imports: Added `AlertLevels` and `AlertTypes` to package exports

## [0.2.0] - 2025-08-04

### Added
- Alert system models for IoT monitoring
- `AlertDefinition` model for defining alert rules with JSON properties
- `AlertBase` abstract base class with type, level, and device name fields
- New enum types for alert categorization:
  - `AlertTypes`: threshold_high, threshold_low, sudden_change, offline, data_gap, data_delayed, invalid_reading, stuck_value, noise
  - `AlertLevels`: emergency, critical, warning, info
- Database migration `0d7bea8f4d60_create_alerts_models.py` for alert_definition table

## [0.1.2] - 2025-07-31

### Changed
- **BREAKING**: Restructured package layout from `models.*` to `iot_db.models.*`
- Updated import paths: use `from iot_db.models import WaterMeasurement` instead of `from models import WaterMeasurement`
- Updated Alembic configuration to work with new package structure

### Migration Guide
- Change imports from `from models import *` to `from iot_db.models import *`
- All model classes remain the same, only import paths have changed

## [0.1.1] - 2025-07-31

### Fixed
- Fixed package metadata configuration for PyPI compatibility
- Resolved license file inclusion issues

### Changed
- Updated package name to `ngits-iot-db`
- Improved build configuration

## [0.1.0] - 2025-07-30

### Added
- Initial release of IoT Database Models
- SQLAlchemy models for IoT sensor data:
  - ElectricityMeasurement and usage models
  - WaterMeasurement and usage models  
  - HeatMeasurement and usage models
  - TemperatureMeasurement model
  - RawMeasurement model for unprocessed data
- Alembic migrations support with existing migration history
- Multi-tenant support via tenant UUID field
- Type-safe enums for sensor types (electricity, water, heat, temperature)
- Helper functions for model mapping
- Full type annotations with py.typed marker

### Features
- PostgreSQL backend support
- Automatic timestamping (created_ts, updated_ts)  
- Unique constraints to prevent duplicate measurements
- Daily and monthly usage aggregation models
- Raw sensor data storage with JSON fields
- External system integration support via external_id and meter_id

### Migration History Included
- 78371c256762_init_schema.py - Initial database schema
- fc391d505594_add_temperature.py - Temperature sensor support