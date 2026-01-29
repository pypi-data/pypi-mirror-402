"""Measurement fact table - counter-based measurements from meters."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from iot_db.models.base import Base


class FactMeasurement(Base):
    """Fact table for counter-based measurements (electricity, water, heat, gas).

    This table stores cumulative counter readings from various meters across all
    IoT sources. Counter values are monotonically increasing over time.

    Supports two measurement modes:
    1. Simple meters (water, gas, heat) - use 'value' field
    2. Complex electricity meters - use dedicated energy fields with phase support

    Used for:
    - Electricity meters (kWh) - with phase-level detail and energy type breakdown
    - Water meters (m3) - simple counter
    - Heat meters (kWh) - simple counter
    - Gas meters (m3) - simple counter

    The table is optimized for time-series queries and supports partitioning
    by measured_ts for efficient data management.

    Example records:

    Simple water meter reading:
        tenant: <uuid>
        device_id: 456
        measured_ts: 2026-01-10 12:00:00
        value: 234.56  # m3
        measurement_type: 'simple'
        phase_number: NULL
        quality: 95
        flags: 0

    Electricity meter reading (3-phase, detailed):
        Phase 1:
            tenant: <uuid>
            device_id: 123
            measured_ts: 2026-01-10 12:00:00
            measurement_type: 'phase'
            phase_number: 1
            active_forward: 1896.79  # kWh consumed
            active_reverse: 5831.56  # kWh produced
            reactive_forward: 425.01  # kVArh consumed
            reactive_reverse: 789.78  # kVArh produced
            value: NULL
            quality: 100
        # + Phase 2 and Phase 3 records

    Electricity meter reading (total):
        tenant: <uuid>
        device_id: 789
        measured_ts: 2026-01-10 12:00:00
        measurement_type: 'total'
        phase_number: NULL
        active_forward: 4777.04  # kWh consumed (sum of all phases)
        active_reverse: 0.275    # kWh produced
        value: NULL

    Attributes:
        id: Primary key (BigInteger for high volume)
        tenant: Tenant UUID (multi-tenant support)
        device_id: FK to dim_device
        measured_ts: Timestamp of measurement (partitioning key)
        date_id: Optional FK to dim_date for date-based aggregations

        value: Counter value for simple meters (water, gas, heat)

        active_forward: Active energy consumed/imported (kWh)
        active_reverse: Active energy produced/exported (kWh)
        reactive_forward: Reactive energy consumed/imported (kVArh)
        reactive_reverse: Reactive energy produced/exported (kVArh)

        phase_number: Phase identifier (1, 2, 3) or NULL for single-phase/total
        measurement_type: 'simple', 'phase', or 'total'

        quality: Quality score (0-100, optional)
        flags: Bit flags for data quality indicators:
            - 0x01: estimated value
            - 0x02: interpolated
            - 0x04: suspicious/anomaly
            - 0x08: manually entered
        created_ts: Record creation timestamp

    Table configuration:
        - Partitioned by measured_ts (monthly partitions recommended)
        - Unique constraint: (tenant, device_id, measured_ts, phase_number)
        - Indexes optimized for time-series queries and phase-based analysis
    """

    __tablename__ = "fact_measurement"

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
    measured_ts = Column(DateTime, nullable=False, index=True)
    date_id = Column(
        Integer,
        ForeignKey("dim_date.date_id", ondelete="SET NULL"),
        nullable=True,
    )  # Optional link to dim_date

    # Measurement value (for simple meters: water, gas, heat)
    value = Column(Float, nullable=True)  # Counter value (kWh, m3, etc.)

    # Energy fields (for electricity meters)
    # Active energy (energia czynna)
    active_forward = Column(Float, nullable=True)  # kWh consumed (import)
    active_reverse = Column(Float, nullable=True)  # kWh produced (export)

    # Reactive energy (energia bierna)
    reactive_forward = Column(Float, nullable=True)  # kVArh consumed (import)
    reactive_reverse = Column(Float, nullable=True)  # kVArh produced (export)

    # Phase identification (for multi-phase meters)
    phase_number = Column(SmallInteger, nullable=True)  # 1, 2, 3, or NULL

    # Measurement type indicator
    measurement_type = Column(Text, nullable=True)
    # Values: 'simple' (water/gas), 'total' (sum of phases), 'phase' (individual phase)

    # Data quality
    quality = Column(SmallInteger)  # 0-100 quality score
    flags = Column(Integer, default=0)  # Bit flags: estimated, interpolated, etc.

    # Timestamps
    created_ts = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        # Unique constraint: one measurement per device per timestamp per phase
        UniqueConstraint(
            "tenant",
            "device_id",
            "measured_ts",
            "phase_number",
            name="uq_measurement_device_ts_phase",
        ),
        # Composite indexes for common query patterns
        Index("idx_measurement_tenant_ts", "tenant", "measured_ts"),
        Index("idx_measurement_device_ts", "device_id", "measured_ts"),
        Index("idx_measurement_date", "date_id"),
        # Indexes for phase-based queries
        Index("idx_measurement_phase", "device_id", "phase_number", "measured_ts"),
        Index("idx_measurement_type", "measurement_type"),
        # Partitioning configuration (requires manual partition creation)
        # {'postgresql_partition_by': 'RANGE (measured_ts)'},
    )

    def __repr__(self):
        return (
            f"<FactMeasurement(id={self.id}, device_id={self.device_id}, "
            f"measured_ts={self.measured_ts}, value={self.value})>"
        )

    # Flag bit masks
    FLAG_ESTIMATED = 0x01
    FLAG_INTERPOLATED = 0x02
    FLAG_SUSPICIOUS = 0x04
    FLAG_MANUAL = 0x08

    def is_estimated(self) -> bool:
        """Check if measurement is estimated."""
        return bool(self.flags & self.FLAG_ESTIMATED)

    def is_interpolated(self) -> bool:
        """Check if measurement is interpolated."""
        return bool(self.flags & self.FLAG_INTERPOLATED)

    def is_suspicious(self) -> bool:
        """Check if measurement is marked as suspicious."""
        return bool(self.flags & self.FLAG_SUSPICIOUS)

    def is_manual(self) -> bool:
        """Check if measurement was manually entered."""
        return bool(self.flags & self.FLAG_MANUAL)

    def set_flag(self, flag: int):
        """Set a quality flag."""
        self.flags = (self.flags or 0) | flag

    def clear_flag(self, flag: int):
        """Clear a quality flag."""
        self.flags = (self.flags or 0) & ~flag

    # Measurement type constants
    TYPE_SIMPLE = "simple"
    TYPE_PHASE = "phase"
    TYPE_TOTAL = "total"

    def is_simple(self) -> bool:
        """Check if this is a simple meter measurement (water, gas, heat)."""
        return self.measurement_type == self.TYPE_SIMPLE

    def is_electricity(self) -> bool:
        """Check if this is an electricity meter measurement."""
        return self.measurement_type in (self.TYPE_PHASE, self.TYPE_TOTAL)

    def is_phase(self) -> bool:
        """Check if this is a phase-specific measurement."""
        return self.measurement_type == self.TYPE_PHASE

    def is_total(self) -> bool:
        """Check if this is a total (sum of phases) measurement."""
        return self.measurement_type == self.TYPE_TOTAL

    def get_net_active_energy(self) -> float | None:
        """Calculate net active energy (forward - reverse).

        Returns:
            Net active energy in kWh or None if data incomplete
        """
        if self.active_forward is not None and self.active_reverse is not None:
            return self.active_forward - self.active_reverse
        return None

    def get_total_active_energy(self) -> float | None:
        """Get total active energy (forward + reverse).

        Returns:
            Total active energy in kWh or None if data incomplete
        """
        if self.active_forward is not None and self.active_reverse is not None:
            return self.active_forward + self.active_reverse
        return None
