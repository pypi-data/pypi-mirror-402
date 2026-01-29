"""Dimension tables for Data Warehouse architecture."""

from iot_db.models.dimensions.channel_function import DimChannelFunction
from iot_db.models.dimensions.data_source import DimDataSource
from iot_db.models.dimensions.date import DimDate
from iot_db.models.dimensions.device import DimDevice
from iot_db.models.dimensions.time import DimTime

__all__ = [
    "DimDataSource",
    "DimChannelFunction",
    "DimDevice",
    "DimDate",
    "DimTime",
]
