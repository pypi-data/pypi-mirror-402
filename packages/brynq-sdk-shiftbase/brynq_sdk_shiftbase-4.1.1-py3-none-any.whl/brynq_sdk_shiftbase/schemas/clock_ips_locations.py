import pandera as pa
from pandera.typing import Series, DateTime
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class ClockIpGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating Clock IP data returned from Shiftbase API.
    """
    id: Series[str] = pa.Field(coerce=True, description="Unique identifier for the clock IP")
    account_id: Series[str] = pa.Field(coerce=True, description="Account identifier")
    name: Series[str] = pa.Field(coerce=True, description="Name of the clock IP")
    ip: Series[str] = pa.Field(coerce=True, description="IP address", regex=r"^(\d{1,3}\.){3}\d{1,3}$")
    created: Series[DateTime] = pa.Field(coerce=True, description="Creation date and time")
    modified: Series[DateTime] = pa.Field(coerce=True, description="Last modification date and time")
    created_by: Series[str] = pa.Field(coerce=True, description="User who created the IP")
    modified_by: Series[str] = pa.Field(coerce=True, description="User who last modified the IP")
    deleted: Series[bool] = pa.Field(coerce=True, description="Whether the IP is deleted")
    deleted_date: Series[DateTime] = pa.Field(coerce=True, description="Date when the IP was deleted", nullable=True)

    class _Annotation:
        primary_key = "id"
        foreign_keys = {
            "account_id": {"parent_schema": "Account", "parent_column": "id", "cardinality": "N:1"},
            "created_by": {"parent_schema": "User", "parent_column": "id", "cardinality": "N:1"},
            "modified_by": {"parent_schema": "User", "parent_column": "id", "cardinality": "N:1"}
        }

    class Config:
        coerce = True
        strict = False

class ClockLocationGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating Clock Location data returned from Shiftbase API.
    """
    id: Series[str] = pa.Field(coerce=True, description="Unique identifier for the clock location")
    account_id: Series[str] = pa.Field(coerce=True, description="Account identifier")
    name: Series[str] = pa.Field(coerce=True, description="Name of the clock location")
    latitude: Series[str] = pa.Field(coerce=True, description="Latitude coordinate", regex=r"^(\+|-)?(?:90(?:(?:\.0{1,6})?)|(?:[0-9]|[1-8][0-9])(?:(?:\.[0-9]{1,6})?))$")
    longitude: Series[str] = pa.Field(coerce=True, description="Longitude coordinate", regex=r"^(\+|-)?(?:180(?:(?:\.0{1,6})?)|(?:[0-9]|[1-9][0-9]|1[0-7][0-9])(?:(?:\.[0-9]{1,6})?))$")
    radius: Series[str] = pa.Field(coerce=True, description="Radius in meters", regex=r"^[0-9]+$")
    created: Series[DateTime] = pa.Field(coerce=True, description="Creation date and time")
    modified: Series[DateTime] = pa.Field(coerce=True, description="Last modification date and time")
    created_by: Series[str] = pa.Field(coerce=True, description="User who created the location")
    modified_by: Series[str] = pa.Field(coerce=True, description="User who last modified the location")
    deleted: Series[bool] = pa.Field(coerce=True, description="Whether the location is deleted")
    deleted_date: Series[DateTime] = pa.Field(coerce=True, description="Date when the location was deleted", nullable=True)

    class _Annotation:
        primary_key = "id"
        foreign_keys = {
            "account_id": {"parent_schema": "Account", "parent_column": "id", "cardinality": "N:1"},
            "created_by": {"parent_schema": "User", "parent_column": "id", "cardinality": "N:1"},
            "modified_by": {"parent_schema": "User", "parent_column": "id", "cardinality": "N:1"}
        }

    class Config:
        coerce = True
        strict = False
