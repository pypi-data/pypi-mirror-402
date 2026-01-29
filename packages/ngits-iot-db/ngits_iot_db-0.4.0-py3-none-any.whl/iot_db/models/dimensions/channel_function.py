"""Channel function dimension table - dictionary of device types and functions."""

from sqlalchemy import Column, ForeignKey, Integer, SmallInteger, Text

from iot_db.models.base import Base


class DimChannelFunction(Base):
    """Dimension table for channel functions (device types, sensor types, etc.)

    This table maps various device functions from different sources to a unified schema.
    It supports mapping Supla channel functions, ChirpStack device types, and custom
    SensorHub sensors to common categories.

    Example data:
        - Generic functions (source_id=NULL):
          (1, NULL, 'electricity', 'Electricity Meter', 'meter', 'counter', 'kWh', 2)
          (2, NULL, 'water', 'Water Meter', 'meter', 'counter', 'm3', 1)
          (4, NULL, 'temperature', 'Temperature Sensor', 'sensor', 'gauge', '°C', 4)

        - Supla-specific functions (source_id=3):
          (10, 3, 'SUPLA_ELECTRICITYMETER', 'Supla Electricity Meter', 'meter', 'counter', 'kWh', 2)
          (12, 3, 'SUPLA_THERMOMETER', 'Supla Thermometer', 'sensor', 'gauge', '°C', 4)

        - ChirpStack-specific functions (source_id=2):
          (20, 2, 'chirpstack_temp', 'ChirpStack Temperature', 'sensor', 'gauge', '°C', 4)

    Attributes:
        id: Primary key
        source_id: Optional FK to dim_data_source (NULL for generic functions)
        code: Unique code identifying the function (e.g., 'ELECTRICITYMETER', 'electricity')
        name: Human-readable name
        category: Function category ('meter', 'sensor', 'actuator')
        data_type: Type of data ('counter', 'gauge', 'state')
        unit: Unit of measurement ('kWh', '°C', 'm3', etc.)
        legacy_type_id: Mapping to legacy Types enum (1=water, 2=electricity, 3=heat, 4=temperature)
    """

    __tablename__ = "dim_channel_function"

    id = Column(Integer, primary_key=True)
    source_id = Column(
        SmallInteger,
        ForeignKey("dim_data_source.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    code = Column(Text, unique=True, nullable=False, index=True)
    name = Column(Text, nullable=False)
    category = Column(Text, nullable=False, index=True)  # meter, sensor, actuator
    data_type = Column(Text, nullable=False)  # counter, gauge, state
    unit = Column(Text)  # kWh, °C, m3, etc.

    # Mapping to legacy Types enum for backward compatibility
    legacy_type_id = Column(SmallInteger, index=True)  # 1=water, 2=electricity, etc.

    def __repr__(self):
        return f"<DimChannelFunction(id={self.id}, code={self.code}, category={self.category})>"
