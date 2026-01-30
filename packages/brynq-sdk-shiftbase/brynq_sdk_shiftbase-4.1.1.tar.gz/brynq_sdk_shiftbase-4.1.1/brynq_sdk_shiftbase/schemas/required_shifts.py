"""
Schema definition for RequiredShift data validation.
"""
import pandera as pa
from pandera.typing import Series
from datetime import datetime, date as date_type
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class RequiredShiftGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating RequiredShift data returned from Shiftbase API.
    """
    # Read-only fields
    id: Series[str] = pa.Field(coerce=True, description="Required shift ID")
    occurrence_id: Series[str] = pa.Field(nullable=True, coerce=True, description="Occurrence ID")
    account_id: Series[str] = pa.Field(nullable=True, coerce=True, description="Account ID")
    created_by: Series[str] = pa.Field(nullable=True, coerce=True, description="Created by user ID")
    modified_by: Series[str] = pa.Field(nullable=True, coerce=True, description="Modified by user ID")
    created: Series[datetime] = pa.Field(nullable=True, coerce=True, description="Creation date")
    updated: Series[datetime] = pa.Field(nullable=True, coerce=True, description="Last update date")
    deleted: Series[bool] = pa.Field(nullable=True, coerce=True, description="Deleted flag")

    # Required fields
    department_id: Series[str] = pa.Field(coerce=True, description="Department ID")
    date: Series[date_type] = pa.Field(coerce=True, description="Required shift date")
    start_time: Series[str] = pa.Field(coerce=True, description="Start time", alias="starttime")
    end_time: Series[str] = pa.Field(coerce=True, description="End time", alias="endtime")
    break_time: Series[str] = pa.Field(coerce=True, description="Break time")

    # Optional fields
    team_id: Series[str] = pa.Field(nullable=True, coerce=True, description="Team ID")
    shift_id: Series[str] = pa.Field(nullable=True, coerce=True, description="Shift ID")
    instances: Series[str] = pa.Field(nullable=True, coerce=True, description="Number of instances")
    hide_end_time: Series[bool] = pa.Field(nullable=True, coerce=True, description="Hide end time flag")
    description: Series[str] = pa.Field(nullable=True, coerce=True, description="Description")

    # Recurring pattern fields
    recurring: Series[bool] = pa.Field(nullable=True, coerce=True, description="Recurring flag")
    repeat_until: Series[str] = pa.Field(nullable=True, coerce=True, description="Repeat until date")
    interval: Series[str] = pa.Field(nullable=True, coerce=True, description="Repeat interval")
    mo: Series[bool] = pa.Field(nullable=True, coerce=True, description="Monday flag")
    tu: Series[bool] = pa.Field(nullable=True, coerce=True, description="Tuesday flag")
    we: Series[bool] = pa.Field(nullable=True, coerce=True, description="Wednesday flag")
    th: Series[bool] = pa.Field(nullable=True, coerce=True, description="Thursday flag")
    fr: Series[bool] = pa.Field(nullable=True, coerce=True, description="Friday flag")
    sa: Series[bool] = pa.Field(nullable=True, coerce=True, description="Saturday flag")
    su: Series[bool] = pa.Field(nullable=True, coerce=True, description="Sunday flag")

    # Match settings
    match: Series[str] = pa.Field(nullable=True, coerce=True, description="Match settings")
    time_settings: Series[str] = pa.Field(nullable=True, coerce=True, description="Time settings")

    @pa.check("id", "department_id", "team_id", "account_id")
    def check_id_format(cls, series: Series[str]) -> Series[bool]:
        """Validate IDs are numeric strings."""
        valid = series.str.match(r"^[0-9]+$") | series.isna()
        return valid

    @pa.check("match")
    def check_match_value(cls, series: Series[str]) -> Series[bool]:
        """Validate match field has correct value."""
        valid_values = ["min", "max", "exact"]
        valid = series.isin(valid_values) | series.isna()
        return valid

    @pa.check("time_settings")
    def check_time_settings_value(cls, series: Series[str]) -> Series[bool]:
        """Validate time_settings field has correct value."""
        valid_values = ["any", "exact", "starting", "ending", "outside"]
        valid = series.isin(valid_values) | series.isna()
        return valid

    class _Annotation:
        primary_key = "id"
        foreign_keys = {
            "department_id": "DepartmentGet",
            "team_id": "TeamGet",
            "account_id": "AccountGet",
            "shift_id": "ShiftGet",
            "created_by": "UserGet",
            "modified_by": "UserGet"
        }
