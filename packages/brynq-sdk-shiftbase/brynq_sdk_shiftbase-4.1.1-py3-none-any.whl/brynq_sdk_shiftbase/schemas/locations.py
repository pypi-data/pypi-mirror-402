"""
Schema definition for Location data validation.
"""
import pandera as pa
from pandera.typing import Series
import pandas as pd
from datetime import datetime
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class LocationGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating Location data returned from Shiftbase API.
    """
    # Read-only fields
    id: Series[str] = pa.Field(coerce=True, description="Unique identifier for the location")
    account_id: Series[str] = pa.Field(coerce=True, description="Account ID that owns the location")
    deleted: Series[bool] = pa.Field(coerce=True, description="Whether the location has been deleted", nullable=True)
    created: Series[datetime] = pa.Field(coerce=True, description="Creation date and time", nullable=True)
    created_by: Series[str] = pa.Field(coerce=True, description="User who created the location", nullable=True)
    modified_by: Series[str] = pa.Field(coerce=True, description="User who last modified the location", nullable=True)

    # Required fields
    name: Series[str] = pa.Field(coerce=True, description="Name of the location")

    # Optional fields
    street_address: Series[str] = pa.Field(coerce=True, description="Street address of the location", nullable=True)
    zipcode: Series[str] = pa.Field(coerce=True, description="ZIP/postal code of the location", nullable=True)
    city: Series[str] = pa.Field(coerce=True, description="City where the location is situated", nullable=True)
    country: Series[str] = pa.Field(coerce=True, description="Country where the location is situated", nullable=True)
    email: Series[str] = pa.Field(coerce=True, description="Email address associated with the location", nullable=True)
    telephone: Series[str] = pa.Field(coerce=True, description="Telephone number of the location", nullable=True)
    order: Series[str] = pa.Field(coerce=True, description="Sort order for the location", nullable=True)

    @pa.check("id", "account_id")
    def validate_id(cls, series: Series[str]) -> Series[bool]:
        """Validates ID format"""
        return series.str.match(r"^[0-9]+$") | series.isna()

    class _Annotation:
        primary_key = "id"
        foreign_keys = {
            "account_id": {
                "parent_schema": "AccountGet",
                "parent_column": "id",
                "cardinality": "N:1"
            }
        }
