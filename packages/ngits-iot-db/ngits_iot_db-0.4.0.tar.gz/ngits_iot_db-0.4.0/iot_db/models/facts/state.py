"""State fact table - device state snapshots for sensors and actuators."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from iot_db.models.base import Base


class FactState(Base):
    """Fact table for device state snapshots (sensors, actuators, complex meter states).

    This table stores state information from various IoT devices. Unlike FactMeasurement
    which stores cumulative counter values, this table stores state snapshots that may
    contain multiple attributes.

    Used for:
    - Sensor readings (temperature, humidity, pressure, etc.)
    - Actuator states (dimmer level, RGB color, switch state)
    - Complex meter states (multi-phase electricity meter with voltage, current, power)
    - Binary sensors (door open/close, motion detected)

    The table uses flexible JSON storage for complete state data while denormalizing
    key values for query performance.

    Example records:

    Temperature sensor:
        tenant: <uuid>
        device_id: 123
        state_ts: 2026-01-10 12:00:00
        state_data: {"temperature": 23.5}
        numeric_value: 23.5
        boolean_value: NULL
        text_value: NULL

    Humidity & Temperature sensor:
        tenant: <uuid>
        device_id: 456
        state_ts: 2026-01-10 12:00:00
        state_data: {"temperature": 22.8, "humidity": 45.2, "battery": 87}
        numeric_value: 22.8  # Primary value (temperature)
        boolean_value: NULL
        text_value: NULL

    Multi-phase electricity meter:
        tenant: <uuid>
        device_id: 789
        state_ts: 2026-01-10 12:00:00
        state_data: {
            "support": 127,
            "currency": "PLN",
            "phases": [
                {"voltage": 230.5, "current": 5.2, "powerActive": 1196.6, ...}
            ]
        }
        numeric_value: 1196.6  # Current power
        boolean_value: NULL
        text_value: NULL

    Door sensor:
        tenant: <uuid>
        device_id: 234
        state_ts: 2026-01-10 12:00:00
        state_data: {"open": true, "battery": 95}
        numeric_value: NULL
        boolean_value: True
        text_value: "open"

    Attributes:
        id: Primary key (BigInteger for high volume)
        tenant: Tenant UUID (multi-tenant support)
        device_id: FK to dim_device
        state_ts: Timestamp of state snapshot (partitioning key)
        date_id: Optional FK to dim_date for date-based aggregations
        state_data: Full state as JSON (flexible schema)
        numeric_value: Denormalized primary numeric value (for fast queries)
        boolean_value: Denormalized boolean state (for fast queries)
        text_value: Denormalized text status (for fast queries)
        created_ts: Record creation timestamp

    Table configuration:
        - Partitioned by state_ts (monthly partitions recommended)
        - Unique constraint: (tenant, device_id, state_ts)
        - GIN index on state_data for JSON queries
        - Denormalized values enable fast filtering without JSON extraction
    """

    __tablename__ = "fact_state"

    # Primary key
    id = Column(BigInteger, primary_key=True)

    # Dimension foreign keys
    tenant = Column(UUID(as_uuid=True), nullable=False, index=True)
    device_id = Column(
        Integer,
        ForeignKey("dim_device.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Time dimension (partitioning key)
    state_ts = Column(DateTime, nullable=False, index=True)
    date_id = Column(
        Integer,
        ForeignKey("dim_date.date_id", ondelete="SET NULL"),
        nullable=True,
    )  # Optional link to dim_date

    # State data - flexible JSON storage
    state_data = Column(JSONB, nullable=False)

    # Denormalized key values for performance
    numeric_value = Column(Float)  # Primary numeric value (temp, humidity, power, etc.)
    boolean_value = Column(Boolean)  # Binary state (on/off, open/closed)
    text_value = Column(Text)  # Text status/label

    # Timestamps
    created_ts = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        # Unique constraint: one state per device per timestamp
        UniqueConstraint("tenant", "device_id", "state_ts", name="uq_state_device_ts"),
        # Composite indexes for common query patterns
        Index("idx_state_tenant_ts", "tenant", "state_ts"),
        Index("idx_state_device_ts", "device_id", "state_ts"),
        Index("idx_state_date", "date_id"),
        # Index on numeric_value for range queries
        Index(
            "idx_state_numeric_value",
            "device_id",
            "state_ts",
            postgresql_where=(Column("numeric_value").isnot(None)),
        ),
        # GIN index for JSON queries on state_data
        Index("idx_state_data_gin", "state_data", postgresql_using="gin"),
        # Partitioning configuration (requires manual partition creation)
        # {'postgresql_partition_by': 'RANGE (state_ts)'},
    )

    def __repr__(self):
        return (
            f"<FactState(id={self.id}, device_id={self.device_id}, "
            f"state_ts={self.state_ts}, numeric_value={self.numeric_value})>"
        )

    def get_state_value(self, key: str, default=None):
        """Get a value from state_data JSON.

        Args:
            key: JSON key to extract
            default: Default value if key not found

        Returns:
            Value from state_data or default
        """
        if self.state_data and isinstance(self.state_data, dict):
            return self.state_data.get(key, default)
        return default

    def set_primary_value(self, value):
        """Set the appropriate denormalized value based on type.

        Args:
            value: Value to store (int, float, bool, or str)
        """
        if isinstance(value, bool):
            self.boolean_value = value
            self.text_value = str(value).lower()
        elif isinstance(value, (int, float)):
            self.numeric_value = float(value)
        elif isinstance(value, str):
            self.text_value = value
            # Try to parse as number or boolean
            try:
                self.numeric_value = float(value)
            except (ValueError, TypeError):
                if value.lower() in ("true", "false"):
                    self.boolean_value = value.lower() == "true"
