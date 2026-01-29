from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, SmallInteger, Text
from sqlalchemy.dialects.postgresql import JSON

from .base import Base, IdentityBase, Sources, TimeSign, Types


class RawMeasurement(IdentityBase, TimeSign, Base):
    __tablename__ = "measurement_raw"

    data = Column(JSON)
    type = Column(SmallInteger, nullable=True)  # Legacy field, nullable for new records
    source = Column(
        SmallInteger, nullable=False, server_default=str(Sources.sensorhub.value)
    )
    is_processed = Column(Boolean, default=False, nullable=False, index=True)
    processed_ts = Column(DateTime, nullable=True)  # When record was processed
    processing_error = Column(Text, nullable=True)  # Error message if processing failed

    # DWH Migration tracking
    migrated_to_dwh = Column(Boolean, default=False, nullable=False, index=True)
    migrated_ts = Column(DateTime, nullable=True)

    @property
    def source_enum(self):
        return Sources(self.source)

    @source_enum.setter
    def source_enum(self, source_enum):
        self.source = source_enum.value

    @property
    def type_enum(self):
        return Types(self.type)

    @type_enum.setter
    def type_enum(self, type_enum):
        self.type = type_enum.value

    def mark_as_migrated(self):
        """Mark this record as migrated to DWH"""
        self.migrated_to_dwh = True
        self.migrated_ts = datetime.utcnow()

    def mark_as_processed(self):
        """Mark record as successfully processed."""
        self.is_processed = True
        self.processed_ts = datetime.utcnow()
        self.processing_error = None

    def mark_as_failed(self, error: str):
        """Mark record as failed with error message.

        Args:
            error: Error message, e.g.:
                "Invalid data format: missing 'object' field"
        """
        self.is_processed = False
        self.processed_ts = datetime.utcnow()
        self.processing_error = error
