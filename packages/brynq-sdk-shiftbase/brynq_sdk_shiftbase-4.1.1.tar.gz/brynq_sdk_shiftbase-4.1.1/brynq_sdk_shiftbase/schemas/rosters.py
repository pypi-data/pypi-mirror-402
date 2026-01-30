"""
Schema definition for Roster data validation.
"""
import pandera as pa
from pandera.typing import Series
from datetime import datetime, date as date_type
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class RosterGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating Roster data returned from Shiftbase API.
    """
    # Read-only fields
    id: Series[str] = pa.Field(nullable=True, coerce=True, description="Roster ID")
    occurrence_id: Series[str] = pa.Field(coerce=True, description="Occurrence ID")
    account_id: Series[str] = pa.Field(coerce=True, description="Account ID")
    created: Series[datetime] = pa.Field(nullable=True, coerce=True, description="Creation date")
    modified: Series[datetime] = pa.Field(nullable=True, coerce=True, description="Last modification date")
    deleted: Series[bool] = pa.Field(nullable=True, coerce=True, description="Deleted flag")
    color: Series[str] = pa.Field(nullable=True, coerce=True, description="Roster color")
    name: Series[str] = pa.Field(nullable=True, coerce=True, description="Roster name")
    is_task: Series[bool] = pa.Field(nullable=True, coerce=True, description="Is task flag")
    created_by: Series[str] = pa.Field(nullable=True, coerce=True, description="Created by user ID")
    modified_by: Series[str] = pa.Field(nullable=True, coerce=True, description="Modified by user ID")
    rate_card_id: Series[str] = pa.Field(nullable=True, coerce=True, description="Rate card ID")
    start_seconds: Series[int] = pa.Field(nullable=True, coerce=True, description="Start time in seconds")
    end_seconds: Series[int] = pa.Field(nullable=True, coerce=True, description="End time in seconds")

    # Required fields
    team_id: Series[str] = pa.Field(coerce=True, description="Team ID")
    shift_id: Series[str] = pa.Field(coerce=True, description="Shift ID")
    user_id: Series[str] = pa.Field(coerce=True, description="User ID")
    date: Series[date_type] = pa.Field(coerce=True, description="Roster date")
    start_time: Series[str] = pa.Field(coerce=True, description="Start time", alias="starttime")
    end_time: Series[str] = pa.Field(coerce=True, description="End time", alias="endtime")
    break_time: Series[str] = pa.Field(coerce=True, description="Break time")

    # Optional fields
    department_id: Series[str] = pa.Field(nullable=True, coerce=True, description="Department ID")
    first_occurrence: Series[str] = pa.Field(nullable=True, coerce=True, description="First occurrence date")
    hide_end_time: Series[bool] = pa.Field(nullable=True, coerce=True, description="Hide end time flag")
    description: Series[str] = pa.Field(nullable=True, coerce=True, description="Description")

    # Recurring fields
    recurring: Series[bool] = pa.Field(nullable=True, coerce=True, description="Recurring flag")
    repeat_until: Series[str] = pa.Field(nullable=True, coerce=True, description="Repeat until date")
    nr_of_repeats: Series[str] = pa.Field(nullable=True, coerce=True, description="Number of repeats")
    interval: Series[str] = pa.Field(nullable=True, coerce=True, description="Repeat interval")
    mo: Series[bool] = pa.Field(nullable=True, coerce=True, description="Monday flag")
    tu: Series[bool] = pa.Field(nullable=True, coerce=True, description="Tuesday flag")
    we: Series[bool] = pa.Field(nullable=True, coerce=True, description="Wednesday flag")
    th: Series[bool] = pa.Field(nullable=True, coerce=True, description="Thursday flag")
    fr: Series[bool] = pa.Field(nullable=True, coerce=True, description="Friday flag")
    sa: Series[bool] = pa.Field(nullable=True, coerce=True, description="Saturday flag")
    su: Series[bool] = pa.Field(nullable=True, coerce=True, description="Sunday flag")

    # Additional fields
    wage: Series[str] = pa.Field(nullable=True, coerce=True, description="Wage")
    loaned: Series[bool] = pa.Field(nullable=True, coerce=True, description="Loaned flag")
    total: Series[float] = pa.Field(nullable=True, coerce=True, description="Total hours")

    class _Annotation:
        primary_key = "id"
        foreign_keys = {
            "department_id": "DepartmentGet",
            "team_id": "TeamGet",
            "account_id": "AccountGet",
            "shift_id": "ShiftGet",
            "user_id": "UserGet",
            "created_by": "UserGet",
            "modified_by": "UserGet",
            "rate_card_id": "RateCardGet"
        }