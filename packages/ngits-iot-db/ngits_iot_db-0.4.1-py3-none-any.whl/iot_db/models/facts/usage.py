"""Usage fact table - aggregated consumption data for meters."""

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


class FactUsage(Base):
    """Fact table for aggregated consumption/usage data from meters.

    This table stores pre-calculated consumption values for various time periods
    (hourly, daily, monthly). It's derived from FactMeasurement by calculating
    the difference between counter readings.

    Supports two usage modes:
    1. Simple meters (water, gas, heat) - use start_value/end_value/consumption
    2. Complex electricity meters - use detailed energy breakdown with phase support

    Used for:
    - Daily/monthly electricity consumption reports (with phase detail)
    - Water usage statistics
    - Heat consumption tracking
    - Cost calculations per period
    - Energy balance tracking (consumption vs production)

    The table enables fast reporting and analytics without needing to recalculate
    consumption from raw measurements.

    Example records:

    Daily water usage (simple):
        tenant: <uuid>
        device_id: 456
        date_id: 20260110
        period_type: "daily"
        usage_type: "simple"
        start_ts: 2026-01-10 00:00:00
        end_ts: 2026-01-10 23:59:59
        start_value: 234.56
        end_value: 241.23
        consumption: 6.67  # m3
        price_per_unit: 4.50
        total_cost: 30.02
        currency: "PLN"
        quality_score: 98

    Daily electricity usage (per phase):
        tenant: <uuid>
        device_id: 123
        date_id: 20260110
        period_type: "daily"
        usage_type: "phase"
        phase_number: 1
        start_ts: 2026-01-10 00:00:00
        end_ts: 2026-01-10 23:59:59
        active_forward_start: 1896.79
        active_forward_end: 1920.50
        active_forward_consumption: 23.71  # kWh consumed
        active_reverse_start: 5831.56
        active_reverse_end: 5835.00
        active_reverse_production: 3.44  # kWh produced
        net_consumption: 20.27  # 23.71 - 3.44
        price_per_unit: 0.65
        total_cost: 13.18
        currency: "PLN"
        # + Phase 2 and Phase 3 records

    Daily electricity usage (total):
        tenant: <uuid>
        device_id: 123
        date_id: 20260110
        period_type: "daily"
        usage_type: "total"
        phase_number: NULL
        start_ts: 2026-01-10 00:00:00
        end_ts: 2026-01-10 23:59:59
        active_forward_consumption: 70.13  # sum of all phases
        active_reverse_production: 10.32
        net_consumption: 59.81
        total_cost: 38.88
        currency: "PLN"

    Attributes:
        id: Primary key (BigInteger)
        tenant: Tenant UUID (multi-tenant support)
        device_id: FK to dim_device
        date_id: FK to dim_date (date of period start)
        time_id: FK to dim_time (time of period start)
        period_type: Period granularity ("hourly", "daily", "monthly", "yearly")
        start_ts: Period start timestamp
        end_ts: Period end timestamp

        start_value: Counter value at period start (simple meters)
        end_value: Counter value at period end (simple meters)
        consumption: Calculated consumption (simple meters)

        active_forward_start/end/consumption: Active energy consumed (kWh)
        active_reverse_start/end/production: Active energy produced (kWh)
        reactive_forward_start/end/consumption: Reactive energy consumed (kVArh)
        reactive_reverse_start/end/production: Reactive energy produced (kVArh)

        net_consumption: Net active energy (consumption - production)
        phase_number: Phase identifier (1, 2, 3) or NULL for single-phase/total
        usage_type: 'simple', 'phase', or 'total'

        price_per_unit: Price per unit for this period
        total_cost: Total cost (consumption * price_per_unit)
        currency: Currency code (PLN, EUR, USD, etc.)
        calculation_ts: When consumption was calculated
        quality_score: Data completeness score (0-100%)
        created_ts: Record creation timestamp

    Table configuration:
        - Unique constraint: (tenant, device_id, period_type, start_ts, phase_number)
        - Indexes optimized for period-based queries and phase analysis
        - Quality score indicates data completeness (100% = no gaps)
    """

    __tablename__ = "fact_usage"

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
    date_id = Column(
        Integer, ForeignKey("dim_date.date_id", ondelete="SET NULL"), nullable=True
    )
    time_id = Column(
        Integer, ForeignKey("dim_time.time_id", ondelete="SET NULL"), nullable=True
    )

    # Period definition
    period_type = Column(
        Text, nullable=False, index=True
    )  # "hourly", "daily", "monthly", "yearly"
    start_ts = Column(DateTime, nullable=False, index=True)
    end_ts = Column(DateTime, nullable=False)

    # Counter values (for simple meters: water, gas, heat)
    start_value = Column(Float, nullable=True)  # Counter value at start
    end_value = Column(Float, nullable=True)  # Counter value at end
    consumption = Column(Float, nullable=True)  # end_value - start_value

    # Active energy forward (consumption) - for electricity meters
    active_forward_start = Column(Float, nullable=True)
    active_forward_end = Column(Float, nullable=True)
    active_forward_consumption = Column(Float, nullable=True)  # end - start

    # Active energy reverse (production) - for electricity meters
    active_reverse_start = Column(Float, nullable=True)
    active_reverse_end = Column(Float, nullable=True)
    active_reverse_production = Column(Float, nullable=True)  # end - start

    # Reactive energy forward (consumption) - for electricity meters
    reactive_forward_start = Column(Float, nullable=True)
    reactive_forward_end = Column(Float, nullable=True)
    reactive_forward_consumption = Column(Float, nullable=True)

    # Reactive energy reverse (production) - for electricity meters
    reactive_reverse_start = Column(Float, nullable=True)
    reactive_reverse_end = Column(Float, nullable=True)
    reactive_reverse_production = Column(Float, nullable=True)

    # Net consumption (active forward - active reverse)
    net_consumption = Column(Float, nullable=True)

    # Phase identification (for multi-phase meters)
    phase_number = Column(SmallInteger, nullable=True)  # 1, 2, 3, or NULL

    # Usage type indicator
    usage_type = Column(Text, nullable=True)
    # Values: 'simple' (water/gas), 'total' (sum of phases), 'phase' (individual phase)

    # Cost calculation (optional)
    price_per_unit = Column(Float)  # Price per unit (per kWh, m3, etc.)
    total_cost = Column(Float)  # consumption * price_per_unit
    currency = Column(Text)  # PLN, EUR, USD, etc.

    # Metadata
    calculation_ts = Column(DateTime)  # When this record was calculated
    quality_score = Column(SmallInteger)  # 0-100 - data completeness percentage

    # Timestamps
    created_ts = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        # Unique constraint: one usage record per device per period per phase
        UniqueConstraint(
            "tenant",
            "device_id",
            "period_type",
            "start_ts",
            "phase_number",
            name="uq_usage_device_period_phase",
        ),
        # Composite indexes for common query patterns
        Index("idx_usage_tenant_period", "tenant", "period_type", "start_ts"),
        Index("idx_usage_device_period", "device_id", "start_ts"),
        Index("idx_usage_date", "date_id"),
        Index("idx_usage_time", "time_id"),
        # Index for cost queries
        Index(
            "idx_usage_cost",
            "tenant",
            "start_ts",
            postgresql_where=(Column("total_cost").isnot(None)),
        ),
        # Indexes for phase-based queries
        Index(
            "idx_usage_phase", "device_id", "phase_number", "period_type", "start_ts"
        ),
        Index(
            "idx_usage_net",
            "tenant",
            "start_ts",
            postgresql_where=(Column("net_consumption").isnot(None)),
        ),
    )

    def __repr__(self):
        return (
            f"<FactUsage(id={self.id}, device_id={self.device_id}, "
            f"period_type={self.period_type}, start_ts={self.start_ts}, "
            f"consumption={self.consumption})>"
        )

    # Period type constants
    PERIOD_HOURLY = "hourly"
    PERIOD_DAILY = "daily"
    PERIOD_MONTHLY = "monthly"
    PERIOD_YEARLY = "yearly"

    def calculate_cost(self) -> float | None:
        """Calculate total cost from consumption and price.

        Returns:
            Total cost or None if price not available
        """
        if self.consumption is not None and self.price_per_unit is not None:
            return self.consumption * self.price_per_unit
        return None

    def set_cost(self, price_per_unit: float, currency: str = "PLN"):
        """Set price and calculate total cost.

        Args:
            price_per_unit: Price per unit of consumption
            currency: Currency code (default: PLN)
        """
        self.price_per_unit = price_per_unit
        self.currency = currency
        self.total_cost = self.calculate_cost()

    def is_complete(self, threshold: int = 95) -> bool:
        """Check if usage data is complete enough.

        Args:
            threshold: Minimum quality score (default: 95%)

        Returns:
            True if quality_score >= threshold
        """
        return self.quality_score is not None and self.quality_score >= threshold

    # Usage type constants
    TYPE_SIMPLE = "simple"
    TYPE_PHASE = "phase"
    TYPE_TOTAL = "total"

    def is_simple(self) -> bool:
        """Check if this is a simple meter usage (water, gas, heat)."""
        return self.usage_type == self.TYPE_SIMPLE

    def is_electricity(self) -> bool:
        """Check if this is an electricity meter usage."""
        return self.usage_type in (self.TYPE_PHASE, self.TYPE_TOTAL)

    def is_phase(self) -> bool:
        """Check if this is a phase-specific usage."""
        return self.usage_type == self.TYPE_PHASE

    def is_total(self) -> bool:
        """Check if this is a total (sum of phases) usage."""
        return self.usage_type == self.TYPE_TOTAL

    def calculate_net_consumption(self) -> float | None:
        """Calculate net consumption (forward - reverse) for active energy.

        Returns:
            Net consumption in kWh or None if data incomplete
        """
        if (
            self.active_forward_consumption is not None
            and self.active_reverse_production is not None
        ):
            return self.active_forward_consumption - self.active_reverse_production
        return None

    def get_energy_balance(self) -> dict | None:
        """Get complete energy balance for electricity meters.

        Returns:
            Dictionary with energy balance or None if not electricity meter
        """
        if not self.is_electricity():
            return None

        return {
            "active": {
                "consumed": self.active_forward_consumption,
                "produced": self.active_reverse_production,
                "net": self.net_consumption,
            },
            "reactive": {
                "consumed": self.reactive_forward_consumption,
                "produced": self.reactive_reverse_production,
            },
            "phase": self.phase_number,
        }
