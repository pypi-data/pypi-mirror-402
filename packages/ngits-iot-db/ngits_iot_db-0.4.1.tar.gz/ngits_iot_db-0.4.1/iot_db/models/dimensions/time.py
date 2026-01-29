"""Time dimension table for time-based analytics."""

from sqlalchemy import Boolean, Column, Integer, SmallInteger, Text, Time

from iot_db.models.base import Base


class DimTime(Base):
    """Time dimension table - used for time-based aggregations and BI reporting.

    This table contains pre-calculated time attributes to speed up time-based queries
    and aggregations. It's a standard component in data warehouse architectures.

    The table should be populated with all possible time values (86400 records for
    second-level granularity, or 1440 for minute-level granularity).

    Example records:
        time_id: 143052
        time: 14:30:52
        hour: 14
        minute: 30
        second: 52
        hour_of_day: 14
        is_business_hours: True
        time_period: "afternoon"

    Attributes:
        time_id: Primary key in HHMMSS format (e.g., 143052 for 14:30:52)
        time: Time value
        hour: Hour (0-23)
        minute: Minute (0-59)
        second: Second (0-59)
        hour_of_day: Hour of day (0-23) - duplicate of hour for clarity
        is_business_hours: Business hours flag (8:00-17:00)
        time_period: Period of day (night, morning, afternoon, evening)
    """

    __tablename__ = "dim_time"

    time_id = Column(Integer, primary_key=True)  # HHMMSS format
    time = Column(Time, unique=True, nullable=False, index=True)
    hour = Column(SmallInteger, nullable=False, index=True)
    minute = Column(SmallInteger, nullable=False)
    second = Column(SmallInteger, nullable=False)
    hour_of_day = Column(SmallInteger, nullable=False, index=True)
    is_business_hours = Column(Boolean, default=False, nullable=False, index=True)
    time_period = Column(
        Text, nullable=False, index=True
    )  # "night", "morning", "afternoon", "evening"

    def __repr__(self):
        return f"<DimTime(time_id={self.time_id}, time={self.time}, hour={self.hour}, minute={self.minute})>"
