"""
Schema definition for Absentee data validation.
"""
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from datetime import date as date_type
from uuid import UUID
import pandas as pd
import pandera as pa
from pandera.typing import Series, DateTime
from pydantic import BaseModel, Field
from brynq_sdk_functions import BrynQPanderaDataFrameModel


class RosterAction(str, Enum):
    """Roster action options"""
    NONE = "none"
    HIDE = "hide"
    MOVE_TO_OPEN_SHIFT = "move_to_open_shift"


class AbsenteeStatus(str, Enum):
    """Absentee status options"""
    APPROVED = "Approved"
    DECLINED = "Declined"
    PENDING = "Pending"


class AbsenceGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating Absentee data returned from Shiftbase API.
    An Absentee represents an absence record for a user.
    """
    # Required fields
    id: Series[str] = pa.Field(coerce=True, description="The unique identifier of the absentee", alias="Absentee_id")
    account_id: Series[str] = pa.Field(coerce=True, description="Account identifier", alias="Absentee_account_id", nullable=True)
    user_id: Series[str] = pa.Field(coerce=True, description="User identifier", alias="Absentee_user_id")
    start_date: Series[DateTime] = pa.Field(coerce=True, description="First day of the absentee (YYYY-MM-DD)", alias="Absentee_startdate")
    end_date: Series[DateTime] = pa.Field(coerce=True, description="Last day of the absentee (YYYY-MM-DD)", alias="Absentee_enddate")
    absentee_option_id: Series[str] = pa.Field(coerce=True, description="Identifier of the absence type", alias="Absentee_absentee_option_id")

    # Optional fields
    exclude: Series[bool] = pa.Field(coerce=True, description="Deprecated field", alias="Absentee_exclude", nullable=True)
    roster_action: Series[str] = pa.Field(coerce=True, description="What to do with the shift in the schedule", alias="Absentee_roster_action", nullable=True, isin=[e.value for e in RosterAction])
    note: Series[str] = pa.Field(coerce=True, description="Optional text added by the requester", alias="Absentee_note", nullable=True)
    created: Series[str] = pa.Field(coerce=True, description="Creation date and time", alias="Absentee_created", nullable=True)
    updated: Series[DateTime] = pa.Field(coerce=True, description="Last update date and time", alias="Absentee_updated", nullable=True)
    reviewed: Series[str] = pa.Field(coerce=True, description="Review date and time", alias="Absentee_reviewed", nullable=True)
    status: Series[str] = pa.Field(coerce=True, description="Status of the absence request", alias="Absentee_status", isin=[e.value for e in AbsenteeStatus])
    hours: Series[str] = pa.Field(coerce=True, description="Total hours of absence", alias="Absentee_hours", nullable=True)
    wait_hours: Series[str] = pa.Field(coerce=True, description="Total wait hours", alias="Absentee_wait_hours", nullable=True)
    wait_days: Series[str] = pa.Field(coerce=True, description="Total wait days", alias="Absentee_wait_days", nullable=True)
    partial_day: Series[bool] = pa.Field(coerce=True, description="Indicates if the absence is for part of the day", alias="Absentee_partial_day", nullable=True)
    start_time: Series[str] = pa.Field(coerce=True, description="Start time of the absence", alias="Absentee_start_time", nullable=True)
    end_time: Series[str] = pa.Field(coerce=True, description="End time of the absence", alias="Absentee_end_time", nullable=True)
    deleted: Series[bool] = pa.Field(coerce=True, description="Indicates if the absence is deleted", alias="Absentee_deleted", nullable=True)
    created_by: Series[str] = pa.Field(coerce=True, description="User ID of the creator", alias="Absentee_created_by", nullable=True)
    modified_by: Series[str] = pa.Field(coerce=True, description="User ID of the last modifier", alias="Absentee_modified_by", nullable=True)
    reviewed_by: Series[str] = pa.Field(coerce=True, description="User ID of the reviewer", alias="Absentee_reviewed_by", nullable=True)
    hide_days_without_hours: Series[bool] = pa.Field(coerce=True, description="Whether to hide days without hours", alias="Absentee_hide_days_without_hours", nullable=True)
    days: Series[int] = pa.Field(coerce=True, description="Number of days of absence", alias="Absentee_days", nullable=True)
    hours_per_day: Series[float] = pa.Field(coerce=True, description="Average hours per day", alias="Absentee_hours_per_day", nullable=True)
    total: Series[float] = pa.Field(coerce=True, description="Total hours", alias="Absentee_total", nullable=True)
    percentage: Series[str] = pa.Field(coerce=True, description="Percentage from the AbsenteeOption", alias="Absentee_percentage", nullable=True)
    surcharge_name: Series[str] = pa.Field(coerce=True, description="Surcharge name from the AbsenteeOption", alias="Absentee_surcharge_name", nullable=True)
    surcharge_total: Series[float] = pa.Field(coerce=True, description="Surcharge total", alias="Absentee_surcharge_total", nullable=True)
    salary: Series[float] = pa.Field(coerce=True, description="Salary amount", alias="Absentee_salary", nullable=True)
    absence_unit: Series[str] = pa.Field(coerce=True, description="Unit of absence (days or hours)", alias="Absentee_absence_unit", nullable=True)
    open_ended: Series[bool] = pa.Field(coerce=True, description="Indicates if the absentee is open-ended", alias="Absentee_open_ended", nullable=True)
    is_public_holiday: Series[bool] = pa.Field(coerce=True, description="Indicates if the absence is on a public holiday", alias="Absentee_is_public_holiday", nullable=True)

    # Reviewer fields (from ReviewedBy object)
    reviewer_id: Series[str] = pa.Field(coerce=True, description="The unique identifier of the reviewer", alias="ReviewedBy_id", nullable=True)
    reviewer_first_name: Series[str] = pa.Field(coerce=True, description="First name of the reviewer", alias="ReviewedBy_first_name", nullable=True)
    reviewer_prefix: Series[str] = pa.Field(coerce=True, description="Name prefix of the reviewer", alias="ReviewedBy_prefix", nullable=True)
    reviewer_last_name: Series[str] = pa.Field(coerce=True, description="Last name of the reviewer", alias="ReviewedBy_last_name", nullable=True)
    reviewer_name: Series[str] = pa.Field(coerce=True, description="Full name of the reviewer", alias="ReviewedBy_name", nullable=True)

    class _Annotation:
        primary_key = "id"
        foreign_keys = {
            "user_id": {
                "parent_schema": "User",
                "parent_column": "id",
                "cardinality": "N:1"
            },
            "absentee_option_id": {
                "parent_schema": "AbsenteeOption",
                "parent_column": "id",
                "cardinality": "N:1"
            },
            "account_id": {
                "parent_schema": "Account",
                "parent_column": "id",
                "cardinality": "N:1"
            }
        }

    class Config:
        coerce = True
        strict = False


class AbsenteeDayCreate(BaseModel):
    """
    Absence day details for creating absences.
    This model is used for both days and hours units in create operations.
    """
    date: date_type = Field(description="Date of the absence day", example="2025-03-10")
    partial_day: bool = Field(description="Indicates if the absence is for part of the day", default=False, example=False)
    time_off_balance_id: Optional[UUID] = Field(description="UUID of the time off balance", default=None, example="1ef6f6e9-5fd7-66fe-9c38-9ad1f201cf44")
    # For days unit
    days: Optional[float] = Field(description="The amount of days. Needs to be a number between 0 and 1", default=None, example=1.0)
    from_time: Optional[str] = Field(description="If absence is half a day the from_time", default=None, example="09:00:00")
    until_time: Optional[str] = Field(description="If absence is half a day the until_time", default=None, example="17:00:00")
    # For hours unit
    start_time: Optional[str] = Field(description="Start time of the absence", default=None, example="12:00:00")
    hours: Optional[str] = Field(description="The amount of hours", default="0.0000", example="8.0000")
    wait_hours: Optional[float] = Field(description="Wait hours for this day", default=0, example=0)
    wait_hours_balance_id: Optional[UUID] = Field(description="UUID of the wait hours balance", default=None, example=None)


class AbsenceDayDetail(BaseModel):
    """
    Absence day details for a specific date.
    This model can be used for both days and hours units in GET operations.
    """
    date: date_type = Field(description="Date of the absence day", example="2025-03-10")
    partial_day: bool = Field(description="Indicates if the absence is for part of the day", example=True)
    start_time: str = Field(description="Start time of the absence", example="12:00:00")
    hours: str = Field(description="Hours of absence for this day", example="4.00000")
    wait_hours: str = Field(description="Wait hours for this day", example="0.00000")
    wait_hours_balance_id: Optional[UUID] = Field(description="UUID of the wait hours balance", default=None, example=None)
    time_off_balance_id: Optional[UUID] = Field(description="UUID of the time off balance", default=None, example="1ef6f6e9-5fd7-66fe-9c38-9ad1f201cf44")
    salary: Optional[float] = Field(description="Salary amount", default=0.0, example=100.0)
    coc: Optional[float] = Field(description="Cost of compensation", default=0.0, example=135.0)
    department_id: Optional[str] = Field(description="Department ID for this absence day", default=None, example="171407")


class AbsenceCreate(BaseModel):
    """
    Schema for validating Absentee creation data.
    This schema is used when creating new absences in Shiftbase.
    """
    # Required fields
    user_id: str = Field(description="User identifier", pattern=r"^[0-9]+$", alias="user_id", example="1089480")
    start_date: date_type = Field(description="First day of the absentee (YYYY-MM-DD)", alias="startdate", example="2025-03-10")
    end_date: date_type = Field(description="Last day of the absentee (YYYY-MM-DD)", alias="enddate", example="2025-03-12")
    absentee_option_id: str = Field(description="Identifier of the absence type", pattern=r"^[0-9]+$", alias="absentee_option_id", example="1116860")

    # Optional fields
    roster_action: RosterAction = Field(description="What to do with the shift in the schedule", alias="roster_action", default=RosterAction.NONE, example="none")
    note: Optional[str] = Field(description="Optional text added by the requester", alias="note", default=None, example="Vacation request")
    status: AbsenteeStatus = Field(description="Status of the absence request", alias="status", default=AbsenteeStatus.PENDING, example="Pending")
    hide_days_without_hours: bool = Field(description="Whether to hide days without hours", alias="hide_days_without_hours", default=False, example=False)
    absence_day: Optional[List[AbsenteeDayCreate]] = Field(description="Absence details per day in the absence", alias="AbsenteeDay", default=None, example=[])
    open_ended: bool = Field(description="Indicates if the absentee is open-ended", alias="open_ended", default=False, example=False)
    notify_employee: bool = Field(description="Whether to notify the employee", alias="notify_employee", default=False, example=True)

    class Config:
        populate_by_name = True
        """Pydantic configuration"""
        use_enum_values = True


class AbsenceUpdate(BaseModel):
    """
    Schema for validating Absentee update data.
    This schema is used when updating existing absences in Shiftbase.
    """
    # Required fields
    user_id: str = Field(description="User identifier", pattern=r"^[0-9]+$", alias="user_id", example="1089480")
    start_date: date_type = Field(description="First day of the absentee (YYYY-MM-DD)", alias="startdate", example="2025-03-10")
    end_date: date_type = Field(description="Last day of the absentee (YYYY-MM-DD)", alias="enddate", example="2025-03-12")
    absentee_option_id: str = Field(description="Identifier of the absence type", pattern=r"^[0-9]+$", alias="absentee_option_id", example="1116860")

    # Optional fields
    id: Optional[str] = Field(description="The unique identifier of the absentee", pattern=r"^[0-9]+$", alias="id", default=None, example="6939346")
    roster_action: RosterAction = Field(description="What to do with the shift in the schedule", alias="roster_action", default=RosterAction.NONE, example="hide")
    note: Optional[str] = Field(description="Optional text added by the requester", alias="note", default=None, example="Updated vacation request")
    status: AbsenteeStatus = Field(description="Status of the absence request", alias="status", default=AbsenteeStatus.PENDING, example="Approved")
    hide_days_without_hours: bool = Field(description="Whether to hide days without hours", alias="hide_days_without_hours", default=False, example=False)
    absence_day: Optional[List[AbsenteeDayCreate]] = Field(description="Absence details per day in the absence", alias="AbsenteeDay", default_factory=list, example=[])
    open_ended: bool = Field(description="Indicates if the absentee is open-ended", alias="open_ended", default=False, example=False)
    notify_employee: bool = Field(description="Whether to notify the employee", alias="notify_employee", default=False, example=True)
    wait_days: Optional[str] = Field(description="Total wait days", alias="wait_days", default=None, example="0")

    class Config:
        populate_by_name = True
        """Pydantic configuration"""
        use_enum_values = True


class ReviewedBy(BaseModel):
    """
    Schema for reviewer information when Absences, Timesheets,
    or exchanges are approved or denied.
    This tracks the user that performed the approval/denial action.
    """
    id: Optional[str] = Field(description="The unique identifier of the reviewer", default=None, example="1089480")
    first_name: Optional[str] = Field(description="First name of the reviewer", default=None, example="Jop")
    prefix: Optional[str] = Field(description="Name prefix of the reviewer", default=None, example="")
    last_name: Optional[str] = Field(description="Last name of the reviewer", default=None, example="Belger")
    name: Optional[str] = Field(description="Full name of the user. The format is based on account setting. The default format is 'first name prefix last name'", default=None, example="Jop Belger")

    class Config:
        """Pydantic configuration"""
        use_enum_values = True

class AbsenceGetById(BrynQPanderaDataFrameModel):
    """Schema for absence GET by ID operations - includes normalized AbsenteeDay fields."""

    # Main Absentee fields
    absence_unit: Series[str] = pa.Field(coerce=True, description="Unit of absence measurement", alias="Absentee_absence_unit", nullable=True)
    absentee_option_id: Series[str] = pa.Field(coerce=True, description="ID of the absence type/option", alias="Absentee_absentee_option_id")
    account_id: Series[str] = pa.Field(coerce=True, description="Account ID", alias="Absentee_account_id")
    coc: Series[int] = pa.Field(coerce=True, description="COC value", alias="Absentee_coc", nullable=True)
    created: Series[str] = pa.Field(coerce=True, description="Creation timestamp", alias="Absentee_created", nullable=True)
    created_by: Series[str] = pa.Field(coerce=True, description="ID of user who created the record", alias="Absentee_created_by", nullable=True)
    day_total: Series[int] = pa.Field(coerce=True, description="Total number of days", alias="Absentee_day_total", nullable=True)
    days: Series[int] = pa.Field(coerce=True, description="Number of days", alias="Absentee_days", nullable=True)
    deleted: Series[bool] = pa.Field(coerce=True, description="Whether the record is deleted", alias="Absentee_deleted", nullable=True)
    end_time: Series[str] = pa.Field(coerce=True, description="End time", alias="Absentee_end_time", nullable=True)
    end_date: Series[str] = pa.Field(coerce=True, description="End date", alias="Absentee_enddate")
    exclude: Series[bool] = pa.Field(coerce=True, description="Whether to exclude from calculations", alias="Absentee_exclude", nullable=True)
    hide_days_without_hours: Series[bool] = pa.Field(coerce=True, description="Whether to hide days without hours", alias="Absentee_hide_days_without_hours", nullable=True)
    hours: Series[str] = pa.Field(coerce=True, description="Number of hours", alias="Absentee_hours", nullable=True)
    hours_per_day: Series[float] = pa.Field(coerce=True, description="Hours per day", alias="Absentee_hours_per_day", nullable=True)
    id: Series[str] = pa.Field(coerce=True, description="Unique identifier", alias="Absentee_id")
    is_public_holiday: Series[bool] = pa.Field(coerce=True, description="Whether it's a public holiday", alias="Absentee_is_public_holiday", nullable=True)
    modified_by: Series[str] = pa.Field(coerce=True, description="ID of user who last modified", alias="Absentee_modified_by", nullable=True)
    note: Series[str] = pa.Field(coerce=True, description="Additional notes", alias="Absentee_note", nullable=True)
    open_ended: Series[bool] = pa.Field(coerce=True, description="Whether the absence is open-ended", alias="Absentee_open_ended", nullable=True)
    partial_day: Series[bool] = pa.Field(coerce=True, description="Whether it's a partial day", alias="Absentee_partial_day", nullable=True)
    percentage: Series[str] = pa.Field(coerce=True, description="Percentage value", alias="Absentee_percentage", nullable=True)
    reviewed: Series[str] = pa.Field(coerce=True, description="Review timestamp", alias="Absentee_reviewed", nullable=True)
    reviewed_by: Series[str] = pa.Field(coerce=True, description="ID of reviewer", alias="Absentee_reviewed_by", nullable=True)
    roster_action: Series[str] = pa.Field(coerce=True, description="Roster action", alias="Absentee_roster_action", nullable=True, isin=[e.value for e in RosterAction])
    salary: Series[int] = pa.Field(coerce=True, description="Salary amount", alias="Absentee_salary", nullable=True)
    start_time: Series[str] = pa.Field(coerce=True, description="Start time", alias="Absentee_start_time", nullable=True)
    start_date: Series[str] = pa.Field(coerce=True, description="Start date", alias="Absentee_startdate")
    status: Series[str] = pa.Field(coerce=True, description="Status", alias="Absentee_status", isin=[e.value for e in AbsenteeStatus])
    surcharge_name: Series[str] = pa.Field(coerce=True, description="Surcharge name", alias="Absentee_surcharge_name", nullable=True)
    surcharge_total: Series[int] = pa.Field(coerce=True, description="Total surcharge amount", alias="Absentee_surcharge_total", nullable=True)
    total: Series[int] = pa.Field(coerce=True, description="Total amount", alias="Absentee_total", nullable=True)
    updated: Series[str] = pa.Field(coerce=True, description="Last update timestamp", alias="Absentee_updated", nullable=True)
    user_id: Series[str] = pa.Field(coerce=True, description="User ID", alias="Absentee_user_id")
    wait_days: Series[str] = pa.Field(coerce=True, description="Wait days", alias="Absentee_wait_days", nullable=True)
    wait_hours: Series[str] = pa.Field(coerce=True, description="Wait hours", alias="Absentee_wait_hours", nullable=True)

    # AbsenteeDay details as original dict structure
    absentee_day_details: Series[object] = pa.Field(coerce=True, description="AbsenteeDay details as original nested dictionary with date keys", alias="Absentee_AbsenteeDay", nullable=True)

    # ReviewedBy fields (flattened)
    reviewer_first_name: Series[str] = pa.Field(coerce=True, description="Reviewer's first name", alias="ReviewedBy_first_name", nullable=True)
    reviewer_id: Series[str] = pa.Field(coerce=True, description="Reviewer's ID", alias="ReviewedBy_id", nullable=True)
    reviewer_last_name: Series[str] = pa.Field(coerce=True, description="Reviewer's last name", alias="ReviewedBy_last_name", nullable=True)
    reviewer_name: Series[str] = pa.Field(coerce=True, description="Reviewer's full name", alias="ReviewedBy_name", nullable=True)
    reviewer_prefix: Series[str] = pa.Field(coerce=True, description="Reviewer's name prefix", alias="ReviewedBy_prefix", nullable=True)

    class _Annotation:
        primary_key = "id"
        foreign_keys = {
            "user_id": {
                "parent_schema": "User",
                "parent_column": "id",
                "cardinality": "N:1"
            },
            "absentee_option_id": {
                "parent_schema": "AbsenteeOption",
                "parent_column": "id",
                "cardinality": "N:1"
            },
            "account_id": {
                "parent_schema": "Account",
                "parent_column": "id",
                "cardinality": "N:1"
            }
        }
