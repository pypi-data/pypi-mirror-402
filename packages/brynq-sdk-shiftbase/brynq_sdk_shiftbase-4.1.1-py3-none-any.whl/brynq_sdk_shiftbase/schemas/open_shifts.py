"""
Schema definition for OpenShift data validation.
"""
import pandera as pa
from pandera.typing import Series
import pandas as pd
from datetime import datetime, date as date_type
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class OpenShiftGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating Open Shifts data from Shiftbase API
    """
    # Identifier and reference fields
    id: Series[str] = pa.Field(coerce=True, description="Unique identifier for the open shift")
    occurrence_id: Series[str] = pa.Field(coerce=True, description="Occurrence identifier for the open shift")
    account_id: Series[str] = pa.Field(coerce=True, description="Account ID that owns the open shift")
    department_id: Series[str] = pa.Field(coerce=True, description="Department ID for the open shift")
    team_id: Series[str] = pa.Field(coerce=True, description="Team ID for the open shift")
    shift_id: Series[str] = pa.Field(coerce=True, description="Shift ID for the open shift")

    # Date and time fields
    date: Series[date_type] = pa.Field(coerce=True, description="Date of the open shift")
    first_occurrence: Series[str] = pa.Field(coerce=True, description="First occurrence date", nullable=True)
    start_time: Series[str] = pa.Field(coerce=True, description="Start time of the open shift", alias="starttime")
    end_time: Series[str] = pa.Field(coerce=True, description="End time of the open shift", alias="endtime")
    start_seconds: Series[int] = pa.Field(coerce=True, description="Start time in seconds", nullable=True)
    end_seconds: Series[int] = pa.Field(coerce=True, description="End time in seconds", nullable=True)

    # Instance and recurring fields
    instances: Series[str] = pa.Field(coerce=True, description="Number of instances", nullable=True)
    instances_remaining: Series[str] = pa.Field(coerce=True, description="Number of instances remaining", nullable=True)
    recurring: Series[bool] = pa.Field(coerce=True, description="Whether the shift is recurring", nullable=True)
    repeat_until: Series[str] = pa.Field(coerce=True, description="Repeat until date", nullable=True)
    interval: Series[str] = pa.Field(coerce=True, description="Repeat interval", nullable=True)

    # Day of week fields
    mo: Series[bool] = pa.Field(coerce=True, description="Monday", nullable=True)
    tu: Series[bool] = pa.Field(coerce=True, description="Tuesday", nullable=True)
    we: Series[bool] = pa.Field(coerce=True, description="Wednesday", nullable=True)
    th: Series[bool] = pa.Field(coerce=True, description="Thursday", nullable=True)
    fr: Series[bool] = pa.Field(coerce=True, description="Friday", nullable=True)
    sa: Series[bool] = pa.Field(coerce=True, description="Saturday", nullable=True)
    su: Series[bool] = pa.Field(coerce=True, description="Sunday", nullable=True)

    # Status and display fields
    deleted: Series[bool] = pa.Field(coerce=True, description="Whether the open shift has been deleted")
    hide_end_time: Series[bool] = pa.Field(coerce=True, description="Whether to hide end time", nullable=True)
    break_time: Series[str] = pa.Field(coerce=True, description="Break time duration", alias="break", nullable=True)
    description: Series[str] = pa.Field(coerce=True, description="Description of the open shift", nullable=True)
    total: Series[float] = pa.Field(coerce=True, description="Total hours", nullable=True)

    # Tracking fields
    created_by: Series[str] = pa.Field(coerce=True, description="User who created the open shift", nullable=True)
    modified_by: Series[str] = pa.Field(coerce=True, description="User who last modified the open shift", nullable=True)
    created: Series[datetime] = pa.Field(coerce=True, description="Creation date and time", nullable=True)
    updated: Series[datetime] = pa.Field(coerce=True, description="Last update date and time", nullable=True)

    # Additional fields
    custom_fields: Series[str] = pa.Field(coerce=True, description="Custom fields data", nullable=True)
    approval_required: Series[bool] = pa.Field(coerce=True, description="Whether approval is required", nullable=True)
    can_pickup_open_shift: Series[bool] = pa.Field(coerce=True, description="Whether shift can be picked up", nullable=True)
    has_rejected: Series[bool] = pa.Field(coerce=True, description="Whether shift has been rejected", alias="hasRejected", nullable=True)

    # Department fields (from nested Department object)
    department_id_field: Series[str] = pa.Field(coerce=True, description="Department ID from nested object", alias="Department_id", nullable=True)
    department_name: Series[str] = pa.Field(coerce=True, description="Department name from nested object", alias="Department_name", nullable=True)
    department_location_id: Series[str] = pa.Field(coerce=True, description="Department location ID from nested object", alias="Department_location_id", nullable=True)

    # Location fields (from nested Department.Location object)
    department_location_id_field: Series[str] = pa.Field(coerce=True, description="Department location ID from nested object", alias="Department_Location_id", nullable=True)
    department_location_name: Series[str] = pa.Field(coerce=True, description="Department location name from nested object", alias="Department_Location_name", nullable=True)

    @pa.check("id", "account_id", "department_id", "team_id", "shift_id", "created_by", "modified_by")
    def check_id_format(cls, series: Series[str]) -> Series[bool]:
        """Validate IDs are numeric strings."""
        valid = series.str.match(r"^[0-9]+$") | series.isna()
        return valid

    @pa.check("occurrence_id")
    def check_occurrence_id_format(cls, series: Series[str]) -> Series[bool]:
        """Validate occurrence_id format: ID:YYYY-MM-DD"""
        valid = series.str.match(r"^[0-9]+:[0-9]{4}-[0-9]{2}-[0-9]{2}$") | series.isna()
        return valid

    class _Annotation:
        primary_key = "id"
        foreign_keys = {
            "account_id": {
                "parent_schema": "AccountGet",
                "parent_column": "id",
                "cardinality": "N:1"
            },
            "department_id": {
                "parent_schema": "DepartmentGet",
                "parent_column": "id",
                "cardinality": "N:1"
            },
            "team_id": {
                "parent_schema": "TeamGet",
                "parent_column": "id",
                "cardinality": "N:1"
            },
            "shift_id": {
                "parent_schema": "ShiftGet",
                "parent_column": "id",
                "cardinality": "N:1"
            },
            "created_by": {
                "parent_schema": "UserGet",
                "parent_column": "id",
                "cardinality": "N:1"
            },
            "modified_by": {
                "parent_schema": "UserGet",
                "parent_column": "id",
                "cardinality": "N:1"
            }
        }
