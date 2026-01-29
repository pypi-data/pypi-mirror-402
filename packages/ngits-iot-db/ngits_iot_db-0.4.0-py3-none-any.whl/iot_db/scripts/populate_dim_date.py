#!/usr/bin/env python3
"""Populate dim_date table with date dimension data.

This script generates date records for a specified range of years,
calculating all date attributes (year, quarter, month, week, day, etc.).

Usage:
    python -m iot_db.scripts.populate_dim_date [--start-year YYYY] [--end-year YYYY]

Examples:
    # Populate 5 years (2021-2030)
    python -m iot_db.scripts.populate_dim_date --start-year 2021 --end-year 2030

    # Default: current year ± 2 years
    python -m iot_db.scripts.populate_dim_date
"""

import argparse
import os
import sys
from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from iot_db.models import DimDate


def is_weekend(date_obj: date) -> bool:
    """Check if date is weekend (Saturday or Sunday)."""
    return date_obj.weekday() >= 5  # 5=Saturday, 6=Sunday


def get_iso_week(date_obj: date) -> int:
    """Get ISO week number (1-53)."""
    return date_obj.isocalendar()[1]


def get_quarter(month: int) -> int:
    """Get quarter from month (1-4)."""
    return (month - 1) // 3 + 1


def populate_dim_date(
    session: Session,
    start_year: int,
    end_year: int,
    holidays: set[date] | None = None,
):
    """Populate dim_date table with date records.

    Args:
        session: SQLAlchemy session
        start_year: Start year (inclusive)
        end_year: End year (inclusive)
        holidays: Set of holiday dates (optional)
    """
    if holidays is None:
        holidays = set()

    start_date = date(start_year, 1, 1)
    end_date = date(end_year, 12, 31)

    current_date = start_date
    batch_size = 100
    batch = []
    total = 0

    print(f"Populating dim_date from {start_date} to {end_date}...")

    while current_date <= end_date:
        # Check if record already exists
        date_id = int(current_date.strftime("%Y%m%d"))
        existing = session.query(DimDate).filter_by(date_id=date_id).first()

        if not existing:
            dim_date = DimDate(
                date_id=date_id,
                date=current_date,
                year=current_date.year,
                quarter=get_quarter(current_date.month),
                month=current_date.month,
                week=get_iso_week(current_date),
                day_of_month=current_date.day,
                day_of_week=current_date.weekday()
                + 1,  # 1=Monday, 7=Sunday (ISO standard)
                is_weekend=is_weekend(current_date),
                is_holiday=current_date in holidays,
            )
            batch.append(dim_date)
            total += 1

            # Commit in batches
            if len(batch) >= batch_size:
                session.add_all(batch)
                session.commit()
                print(f"  Inserted {total} records...", end="\r")
                batch = []

        current_date += timedelta(days=1)

    # Commit remaining records
    if batch:
        session.add_all(batch)
        session.commit()

    print(f"\nSuccessfully populated {total} date records!")


def load_polish_holidays(start_year: int, end_year: int) -> set[date]:
    """Load Polish public holidays for given year range.

    Note: This is a simplified implementation with static holidays.
    For production, consider using a library like 'holidays' package.
    """
    holidays = set()

    # Static holidays (same every year)
    static_holidays = [
        (1, 1),  # New Year's Day
        (1, 6),  # Epiphany
        (5, 1),  # Labour Day
        (5, 3),  # Constitution Day
        (8, 15),  # Assumption of Mary
        (11, 1),  # All Saints' Day
        (11, 11),  # Independence Day
        (12, 25),  # Christmas Day
        (12, 26),  # Second Day of Christmas
    ]

    for year in range(start_year, end_year + 1):
        for month, day in static_holidays:
            holidays.add(date(year, month, day))

        # Easter-dependent holidays (simplified - would need proper calculation)
        # For production, use: from dateutil.easter import easter
        # easter_date = easter(year)
        # holidays.add(easter_date)  # Easter Sunday
        # holidays.add(easter_date + timedelta(days=1))  # Easter Monday
        # holidays.add(easter_date + timedelta(days=49))  # Pentecost

    return holidays


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Populate dim_date table")
    parser.add_argument(
        "--start-year",
        type=int,
        default=date.today().year - 2,
        help="Start year (default: current year - 2)",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=date.today().year + 5,
        help="End year (default: current year + 5)",
    )
    parser.add_argument(
        "--include-holidays",
        action="store_true",
        help="Include Polish public holidays",
    )

    args = parser.parse_args()

    # Get database URL from environment or use default
    database_url = os.getenv(
        "IOT_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/iot_local"
    )

    print(f"Connecting to database: {database_url}\n")

    try:
        engine = create_engine(database_url)

        # Load holidays if requested
        holidays = None
        if args.include_holidays:
            print("Loading Polish public holidays...")
            holidays = load_polish_holidays(args.start_year, args.end_year)
            print(f"Loaded {len(holidays)} holidays\n")

        with Session(engine) as session:
            populate_dim_date(session, args.start_year, args.end_year, holidays)

        print("\nDim_time populated successfully!")

    except Exception as e:
        print(f"Error populating dim_date: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
