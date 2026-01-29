"""Utility scripts for IoT Database DWH setup and maintenance."""

from .populate_dim_date import main as populate_dim_date
from .populate_dim_time import main as populate_dim_time
from .seed_dimension_data import main as seed_dimension_data

__all__ = ["seed_dimension_data", "populate_dim_date", "populate_dim_time"]
