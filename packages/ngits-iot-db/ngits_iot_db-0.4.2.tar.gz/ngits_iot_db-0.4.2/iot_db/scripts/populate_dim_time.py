#!/usr/bin/env python3
"""Populate dim_time table with time dimension data.

This script generates time records for every minute of the day (1440 records),
calculating all time attributes (hour, minute, period, business hours, etc.).

Usage:
    python -m iot_db.scripts.populate_dim_time

Examples:
    # Populate all times (00:00 to 23:59)
    python -m iot_db.scripts.populate_dim_time
"""

import os
import sys
from datetime import time

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from iot_db.models import DimTime


def get_time_period(hour: int) -> str:
    """Get time period from hour.

    Args:
        hour: Hour of day (0-23)

    Returns:
        Period name: "night", "morning", "afternoon", or "evening"
    """
    if 0 <= hour < 6:
        return "night"
    elif 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    else:  # 18 <= hour < 24
        return "evening"


def is_business_hours(hour: int) -> bool:
    """Check if hour is within business hours (8:00-17:00).

    Args:
        hour: Hour of day (0-23)

    Returns:
        True if business hours, False otherwise
    """
    return 8 <= hour < 17


def populate_dim_time(session: Session):
    """Populate dim_time table with time records for every minute.

    Generates 1440 records (24 hours * 60 minutes).

    Args:
        session: SQLAlchemy session
    """
    batch_size = 100
    batch = []
    total = 0

    print("Populating dim_time with 1440 time records (every minute)...")

    for hour in range(24):
        for minute in range(60):
            # Create time_id in HHMMSS format (seconds always 00)
            time_id = hour * 10000 + minute * 100
            time_value = time(hour, minute, 0)

            # Check if record already exists
            existing = session.query(DimTime).filter_by(time_id=time_id).first()

            if not existing:
                dim_time = DimTime(
                    time_id=time_id,
                    time=time_value,
                    hour=hour,
                    minute=minute,
                    second=0,  # Always 0 for minute granularity
                    hour_of_day=hour,
                    is_business_hours=is_business_hours(hour),
                    time_period=get_time_period(hour),
                )
                batch.append(dim_time)
                total += 1

                # Commit in batches
                if len(batch) >= batch_size:
                    session.add_all(batch)
                    session.commit()
                    print(f"  Inserted {total} records...", end="\r")
                    batch = []

    # Commit remaining records
    if batch:
        session.add_all(batch)
        session.commit()

    print(f"\nSuccessfully populated {total} time records!")


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
            populate_dim_time(session)

        print("\nDim_time populated successfully!")

    except Exception as e:
        print(f"Error populating dim_time: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
