"""Data source dimension table - dictionary of IoT data sources."""

from sqlalchemy import Column, SmallInteger, Text

from iot_db.models.base import Base


class DimDataSource(Base):
    """Dimension table for data sources (Supla, ChirpStack, SensorHub, etc.)

    This is a dictionary/lookup table containing all supported IoT data sources.
    Each source has a unique ID and name.

    Example data:
        - (1, 'sensorhub', 'Custom scripts and sensors')
        - (2, 'chirpstack', 'ChirpStack LoRaWAN network')
        - (3, 'supla', 'Supla IoT platform')
    """

    __tablename__ = "dim_data_source"

    id = Column(SmallInteger, primary_key=True)
    name = Column(Text, unique=True, nullable=False, index=True)
    description = Column(Text)

    def __repr__(self):
        return f"<DimDataSource(id={self.id}, name={self.name})>"
