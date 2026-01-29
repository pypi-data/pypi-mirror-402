#!/usr/bin/env python3
"""Seed data for dimension tables.

This script populates the dimension tables with initial reference data:
- dim_data_source: IoT data sources (SensorHub, ChirpStack, Supla)
- dim_channel_function: Device/channel function types

Usage:
    python -m iot_db.scripts.seed_dimension_data
"""

import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from iot_db.models import DimChannelFunction, DimDataSource


def seed_data_sources(session: Session):
    """Seed dim_data_source table with IoT data sources."""
    print("Seeding dim_data_source...")

    data_sources = [
        {
            "id": 1,
            "name": "sensorhub",
            "description": "Custom scripts and sensors",
        },
        {
            "id": 2,
            "name": "chirpstack",
            "description": "ChirpStack LoRaWAN network server",
        },
        {
            "id": 3,
            "name": "supla",
            "description": "Supla IoT platform",
        },
    ]

    for data in data_sources:
        # Check if exists
        existing = session.query(DimDataSource).filter_by(id=data["id"]).first()
        if existing:
            print(f"  - {data['name']} already exists, skipping")
            continue

        source = DimDataSource(**data)
        session.add(source)
        print(f"  + Added {data['name']}")

    session.commit()
    print("dim_data_source seeded successfully\n")


def seed_channel_functions(session: Session):
    """Seed dim_channel_function table with device function types."""
    print("Seeding dim_channel_function...")

    # Generic functions (source_id = NULL)
    generic_functions = [
        {
            "id": 1,
            "source_id": None,
            "code": "electricity",
            "name": "Electricity Meter",
            "category": "meter",
            "data_type": "counter",
            "unit": "kWh",
            "legacy_type_id": 2,  # Types.electricity
        },
        {
            "id": 2,
            "source_id": None,
            "code": "water",
            "name": "Water Meter",
            "category": "meter",
            "data_type": "counter",
            "unit": "m3",
            "legacy_type_id": 1,  # Types.water
        },
        {
            "id": 3,
            "source_id": None,
            "code": "heat",
            "name": "Heat Meter",
            "category": "meter",
            "data_type": "counter",
            "unit": "kWh",
            "legacy_type_id": 3,  # Types.heat
        },
        {
            "id": 4,
            "source_id": None,
            "code": "temperature",
            "name": "Temperature Sensor",
            "category": "sensor",
            "data_type": "gauge",
            "unit": "°C",
            "legacy_type_id": 4,  # Types.temperature
        },
        {
            "id": 5,
            "source_id": None,
            "code": "humidity",
            "name": "Humidity Sensor",
            "category": "sensor",
            "data_type": "gauge",
            "unit": "%",
            "legacy_type_id": None,
        },
    ]

    # Supla-specific functions (source_id = 3)
    supla_functions = [
        {
            "id": 10,
            "source_id": 3,
            "code": "SUPLA_ELECTRICITYMETER",
            "name": "Supla Electricity Meter",
            "category": "meter",
            "data_type": "counter",
            "unit": "kWh",
            "legacy_type_id": 2,
        },
        {
            "id": 11,
            "source_id": 3,
            "code": "SUPLA_WATERMETER",
            "name": "Supla Water Meter",
            "category": "meter",
            "data_type": "counter",
            "unit": "m3",
            "legacy_type_id": 1,
        },
        {
            "id": 12,
            "source_id": 3,
            "code": "SUPLA_GASMETER",
            "name": "Supla Gas Meter",
            "category": "meter",
            "data_type": "counter",
            "unit": "m3",
            "legacy_type_id": None,
        },
        {
            "id": 13,
            "source_id": 3,
            "code": "SUPLA_THERMOMETER",
            "name": "Supla Thermometer",
            "category": "sensor",
            "data_type": "gauge",
            "unit": "°C",
            "legacy_type_id": 4,
        },
        {
            "id": 14,
            "source_id": 3,
            "code": "SUPLA_HUMIDITY",
            "name": "Supla Humidity Sensor",
            "category": "sensor",
            "data_type": "gauge",
            "unit": "%",
            "legacy_type_id": None,
        },
        {
            "id": 15,
            "source_id": 3,
            "code": "SUPLA_HUMIDITYANDTEMPERATURE",
            "name": "Supla Humidity and Temperature Sensor",
            "category": "sensor",
            "data_type": "gauge",
            "unit": "mixed",
            "legacy_type_id": 4,
        },
        {
            "id": 16,
            "source_id": 3,
            "code": "SUPLA_DIMMER",
            "name": "Supla Dimmer",
            "category": "actuator",
            "data_type": "state",
            "unit": "%",
            "legacy_type_id": None,
        },
        {
            "id": 17,
            "source_id": 3,
            "code": "SUPLA_RGBLIGHTING",
            "name": "Supla RGB Lighting",
            "category": "actuator",
            "data_type": "state",
            "unit": None,
            "legacy_type_id": None,
        },
        {
            "id": 18,
            "source_id": 3,
            "code": "SUPLA_POWERSWITCH",
            "name": "Supla Power Switch",
            "category": "actuator",
            "data_type": "state",
            "unit": None,
            "legacy_type_id": None,
        },
    ]

    # ChirpStack-specific functions (source_id = 2)
    chirpstack_functions = [
        {
            "id": 20,
            "source_id": 2,
            "code": "chirpstack_temp",
            "name": "ChirpStack Temperature Sensor",
            "category": "sensor",
            "data_type": "gauge",
            "unit": "°C",
            "legacy_type_id": 4,
        },
        {
            "id": 21,
            "source_id": 2,
            "code": "chirpstack_temp_humidity",
            "name": "ChirpStack Temperature & Humidity Sensor",
            "category": "sensor",
            "data_type": "gauge",
            "unit": "mixed",
            "legacy_type_id": 4,
        },
    ]

    all_functions = generic_functions + supla_functions + chirpstack_functions

    for data in all_functions:
        # Check if exists
        existing = session.query(DimChannelFunction).filter_by(id=data["id"]).first()
        if existing:
            print(f"  - {data['code']} already exists, skipping")
            continue

        function = DimChannelFunction(**data)
        session.add(function)
        print(f"  + Added {data['code']}")

    session.commit()
    print("dim_channel_function seeded successfully\n")


def main():
    """Main entry point."""
    # Get database URL from environment or use default
    database_url = os.getenv(
        "IOT_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/iot_local"
    )

    print(f"Connecting to database: {database_url}\n")

    try:
        engine = create_engine(database_url)
        with Session(engine) as session:
            seed_data_sources(session)
            seed_channel_functions(session)

        print("All dimension data seeded successfully!")

    except Exception as e:
        print(f"Error seeding data: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
