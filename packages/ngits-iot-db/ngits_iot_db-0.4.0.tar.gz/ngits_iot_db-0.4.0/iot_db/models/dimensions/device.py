"""Device dimension table - universal device/channel registry."""

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON

from iot_db.models.base import Base, IdentityBase, TimeSign


class DimDevice(IdentityBase, TimeSign):
    """Dimension table for devices/channels from all sources.

    This is a denormalized dimension table that stores device metadata from
    various IoT sources (Supla, ChirpStack, SensorHub). Denormalization improves
    query performance by reducing JOIN operations.

    The model inherits from:
    - IdentityBase: provides id, tenant, external_id, meter_id
    - TimeSign: provides created_ts, updated_ts

    Example records:

    Single-channel ChirpStack temperature sensor:
        tenant: <uuid>
        meter_id: "chirpstack_0004a30b001b9a3e"
        device_id: "0004a30b001b9a3e"
        device_channel_id: None
        device_name: "LoRa Temp Sensor Garage"
        device_model: "LoRa Temp Sensor"
        external_id: "0004a30b001b9a3e"  # DEPRECATED
        source_id: 2
        source_name: "chirpstack"
        function_id: 20
        function_code: "temperature"
        function_category: "sensor"
        source_metadata: {"devEui": "0004a30b001b9a3e", "fPort": 2}
        location_name: "Garage"
        is_active: True

    Multi-channel Supla device (Channel 1: Electricity meter):
        tenant: <uuid>
        meter_id: "supla_device_12345_ch1"
        device_id: "supla_device_12345"
        device_channel_id: "4765"
        device_name: "SUPLA-iO Kitchen"
        device_model: "SUPLA-iO v2.0"
        external_id: "4765"  # DEPRECATED
        source_id: 3
        source_name: "supla"
        function_id: 10
        function_code: "SUPLA_ELECTRICITYMETER"
        function_category: "meter"
        source_metadata: {"function": "ELECTRICITYMETER", "deviceId": 12345}
        location_name: "Kitchen"
        is_active: True

    Multi-channel Supla device (Channel 2: Thermometer):
        tenant: <uuid>
        meter_id: "supla_device_12345_ch2"
        device_id: "supla_device_12345"  # SAME device_id as channel 1
        device_channel_id: "4702"
        device_name: "SUPLA-iO Kitchen"
        device_model: "SUPLA-iO v2.0"
        external_id: "4702"  # DEPRECATED
        source_id: 3
        source_name: "supla"
        function_id: 15
        function_code: "SUPLA_THERMOMETER"
        function_category: "sensor"
        source_metadata: {"function": "THERMOMETER", "deviceId": 12345}
        location_name: "Kitchen"
        is_active: True

    Attributes:
        # From IdentityBase:
        id: Primary key
        tenant: Tenant UUID (multi-tenant support)
        external_id: DEPRECATED - Use device_id instead. Kept for backward compatibility.
        meter_id: Business key (unique per tenant)

        # Device/Channel hierarchy (multi-channel support):
        device_id: Physical device ID (shared across channels)
        device_channel_id: Device's channel ID
        device_name: Physical device name (denormalized, may be duplicated across channels)
        device_model: Physical device model (denormalized, may be duplicated across channels)
        parent_device_id: Optional FK to parent device record (for hierarchical organization)

        # Source information (denormalized for performance):
        source_id: FK to dim_data_source
        source_name: Denormalized source name ("supla", "chirpstack", "sensorhub")

        # Function/type information (denormalized for performance):
        function_id: FK to dim_channel_function
        function_code: Denormalized function code ("ELECTRICITYMETER", "temperature", etc.)
        function_category: Denormalized category ("meter", "sensor", "actuator")

        # Source-specific metadata:
        source_metadata: JSON with additional source-specific data

        # Location information (denormalized):
        location_name: Location name
        location_building: Building name
        location_room: Room name
        location_coordinates: JSON with {"lat": ..., "lng": ...}

        # Status:
        is_active: Device active flag

        # From TimeSign:
        created_ts: Record creation timestamp
        updated_ts: Record update timestamp
    """

    __tablename__ = "dim_device"

    # Source information (denormalized)
    source_id = Column(
        SmallInteger,
        ForeignKey("dim_data_source.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_name = Column(Text, index=True)  # Denormalized for fast queries

    # Function/type information (denormalized)
    function_id = Column(
        Integer,
        ForeignKey("dim_channel_function.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    function_code = Column(Text, index=True)  # Denormalized
    function_category = Column(
        Text, index=True
    )  # Denormalized: meter, sensor, actuator

    # Device/Channel hierarchy (multi-channel support)
    device_id = Column(Text, nullable=True, index=True)  # Physical device ID
    device_channel_id = Column(Text, nullable=True)  # Device's channel ID

    # Device metadata (denormalized for performance)
    device_name = Column(Text, nullable=True)  # "ESP32 Salon", "SUPLA-iO Kitchen"
    device_model = Column(Text, nullable=True)  # "ESP32-WROOM-32", "SUPLA-iO v2.0"

    # Optional: Parent device support
    parent_device_id = Column(
        Integer,
        ForeignKey("dim_device.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Source-specific metadata
    source_metadata = Column(JSON)  # Additional source-specific data

    # Location information (denormalized)
    location_name = Column(Text)
    location_building = Column(Text)
    location_room = Column(Text)
    location_coordinates = Column(JSON)  # {"lat": float, "lng": float}

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("tenant", "meter_id", name="uq_device_tenant_meter"),
        Index("idx_device_tenant_source", "tenant", "source_id"),
        Index("idx_device_tenant_active", "tenant", "is_active"),
        Index("idx_device_device_id", "device_id"),
        Index("idx_device_device_channel", "device_id", "device_channel_id"),
    )

    def __repr__(self):
        return (
            f"<DimDevice(id={self.id}, meter_id={self.meter_id}, "
            f"source={self.source_name}, function={self.function_code})>"
        )
