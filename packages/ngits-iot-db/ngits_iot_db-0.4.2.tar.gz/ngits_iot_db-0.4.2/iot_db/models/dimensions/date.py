"""Date dimension table for date-based analytics."""

from sqlalchemy import Boolean, Column, Date, Integer, SmallInteger

from iot_db.models.base import Base


class DimDate(Base):
    """Date dimension table - used for date-based aggregations and BI reporting.

    This table contains pre-calculated date attributes to speed up date-based queries
    and aggregations. It's a standard component in data warehouse architectures.

    The table should be populated with dates covering the expected operational period
    (e.g., 5+ years). A script to populate this table should be created.

    Example records:
        date_id: 20260109
        date: 2026-01-09
        year: 2026
        quarter: 1
        month: 1
        week: 2
        day_of_month: 9
        day_of_week: 5 (Friday)
        is_weekend: False
        is_holiday: False

    Attributes:
        date_id: Primary key in YYYYMMDD format (e.g., 20260109)
        date: Date value
        year: Year (e.g., 2026)
        quarter: Quarter (1-4)
        month: Month (1-12)
        week: ISO week number (1-53)
        day_of_month: Day of month (1-31)
        day_of_week: Day of week (1=Monday, 7=Sunday)
        is_weekend: Weekend flag (Saturday or Sunday)
        is_holiday: Holiday flag (requires configuration)
    """

    __tablename__ = "dim_date"

    date_id = Column(Integer, primary_key=True)  # YYYYMMDD format
    date = Column(Date, unique=True, nullable=False, index=True)
    year = Column(SmallInteger, nullable=False, index=True)
    quarter = Column(SmallInteger, nullable=False)
    month = Column(SmallInteger, nullable=False, index=True)
    week = Column(SmallInteger, nullable=False)  # ISO week
    day_of_month = Column(SmallInteger, nullable=False)
    day_of_week = Column(SmallInteger, nullable=False)  # 1=Monday, 7=Sunday
    is_weekend = Column(Boolean, default=False, nullable=False, index=True)
    is_holiday = Column(Boolean, default=False, nullable=False, index=True)

    def __repr__(self):
        return f"<DimDate(date_id={self.date_id}, date={self.date}, year={self.year}, month={self.month})>"
