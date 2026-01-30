"""
Holiday schemas for Shiftbase SDK.

This module contains Pandera schemas for validating Holiday data from Shiftbase API.
All schemas follow BrynQ SDK standards and inherit from BrynQPanderaDataFrameModel.
"""

import pandera as pa
from pandera.typing import Series, Date, DateTime
from brynq_sdk_functions import BrynQPanderaDataFrameModel


class HolidayGroupGet(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating Holiday Group GET data.
    This schema is used when retrieving holiday groups from Shiftbase.
    """
    id: Series[str] = pa.Field(coerce=True, description="Holiday group identifier")
    name: Series[str] = pa.Field(coerce=True, description="Name of the holiday group")
    created: Series[DateTime] = pa.Field(coerce=True, description="Creation timestamp", nullable=True)

    class _Annotation:
        primary_key = "id"

    class Config:
        coerce = True
        strict = False


class PublicHolidayGet(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating Public Holiday GET data.
    This schema is used when retrieving public holidays from Shiftbase.
    """
    name: Series[str] = pa.Field(coerce=True, description="Name of the public holiday")
    date: Series[Date] = pa.Field(coerce=True, description="Date of the public holiday")
    country_code: Series[str] = pa.Field(coerce=True, description="Country code", nullable=True, alias="countryCode")
    region: Series[str] = pa.Field(coerce=True, description="Region code", nullable=True)

    class _Annotation:
        primary_key = "date"

    class Config:
        coerce = True
        strict = False
