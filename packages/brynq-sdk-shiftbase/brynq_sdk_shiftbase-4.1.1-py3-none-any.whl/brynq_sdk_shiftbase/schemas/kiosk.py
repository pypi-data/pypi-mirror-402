import pandera as pa
from pandera.typing import Series
import pandas as pd
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class KioskGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating Kiosk data from Shiftbase API
    """
    id: Series[str] = pa.Field(coerce=True, description="Unique identifier for the kiosk")
    name: Series[str] = pa.Field(coerce=True, description="Name of the kiosk")
    team_ids: Series[object] = pa.Field(coerce=True, description="List of team IDs associated with the kiosk")
    clock_department: Series[str] = pa.Field(coerce=True, description="Department ID for clocking", nullable=True)
    ip_restricted: Series[bool] = pa.Field(coerce=True, description="Whether the kiosk is IP restricted")
    link: Series[str] = pa.Field(coerce=True, description="Link to access the kiosk")
    short_id: Series[str] = pa.Field(coerce=True, description="Short identifier for the kiosk")
    account_id: Series[str] = pa.Field(coerce=True, description="Account ID that owns the kiosk")

    @pa.check("id", "clock_department", "account_id")
    def check_id_format(cls, series: Series[str]) -> Series[bool]:
        """Validate IDs are numeric strings."""
        valid = series.str.match(r"^[0-9]+$") | series.isna()
        return valid

    class _Annotation:
        primary_key = "id"
        foreign_keys = {
            "clock_department": {
                "parent_schema": "DepartmentGet",
                "parent_column": "id",
                "cardinality": "N:1"
            },
            "account_id": {
                "parent_schema": "AccountGet",
                "parent_column": "id",
                "cardinality": "N:1"
            }
        }
