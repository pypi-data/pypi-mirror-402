import pandera as pa
from pandera.typing import Series, DateTime, Date
import pandas as pd
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date as date_type
from enum import Enum
from brynq_sdk_functions import BrynQPanderaDataFrameModel


# ============================================================================
# PANDERA SCHEMAS (GET operations) - Inherit from BrynQPanderaDataFrameModel
# ============================================================================

class TimesheetGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating Timesheet GET data from Shiftbase API
    """
    timesheet_id: Series[str] = pa.Field(coerce=True, description="Timesheet ID", alias="Timesheet_id")
    account_id: Series[str] = pa.Field(coerce=True, description="Account ID", alias="Timesheet_account_id")
    user_id: Series[str] = pa.Field(coerce=True, description="User ID", alias="Timesheet_user_id")
    team_id: Series[str] = pa.Field(coerce=True, description="Team ID", alias="Timesheet_team_id")
    shift_id: Series[str] = pa.Field(coerce=True, description="Shift ID", alias="Timesheet_shift_id")
    roster_id: Series[pd.StringDtype] = pa.Field(coerce=True, description="Roster ID", alias="Timesheet_roster_id", nullable=True)
    rate_card_id: Series[str] = pa.Field(coerce=True, description="Rate Card ID", alias="Timesheet_rate_card_id")
    date: Series[Date] = pa.Field(coerce=True, description="Date of the timesheet", alias="Timesheet_date")
    start_time: Series[str] = pa.Field(coerce=True, description="Start time of the timesheet", alias="Timesheet_starttime")
    end_time: Series[pd.StringDtype] = pa.Field(coerce=True, description="End time of the timesheet", alias="Timesheet_endtime", nullable=True)
    clocked_in: Series[DateTime] = pa.Field(coerce=True, description="Clock in timestamp", alias="Timesheet_clocked_in", nullable=True)
    clocked_out: Series[DateTime] = pa.Field(coerce=True, description="Clock out timestamp", alias="Timesheet_clocked_out", nullable=True)
    total: Series[pd.StringDtype] = pa.Field(coerce=True, description="Total worked hours", alias="Timesheet_total", nullable=True)
    status: Series[pd.StringDtype] = pa.Field(coerce=True, description="Timesheet status", alias="Timesheet_status", nullable=True)
    break_time: Series[pd.StringDtype] = pa.Field(coerce=True, description="Break duration in minutes", alias="Timesheet_break", nullable=True)
    meals: Series[pd.StringDtype] = pa.Field(coerce=True, description="Number of meals", alias="Timesheet_meals", nullable=True)
    kilometers: Series[pd.StringDtype] = pa.Field(coerce=True, description="Driven kilometers", alias="Timesheet_kilometers", nullable=True)
    note: Series[pd.StringDtype] = pa.Field(coerce=True, description="Timesheet note", alias="Timesheet_note", nullable=True)
    clock: Series[pd.BooleanDtype] = pa.Field(coerce=True, description="Whether timesheet is clock-based", alias="Timesheet_clock", nullable=True)
    created: Series[DateTime] = pa.Field(coerce=True, description="Creation timestamp", alias="Timesheet_created", nullable=True)
    updated: Series[DateTime] = pa.Field(coerce=True, description="Last update timestamp", alias="Timesheet_updated", nullable=True)

    # Clock in details
    clocked_in_latitude: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock in latitude", alias="Timesheet_clocked_in_latitude", nullable=True)
    clocked_in_longitude: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock in longitude", alias="Timesheet_clocked_in_longitude", nullable=True)
    clocked_in_accuracy: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock in accuracy", alias="Timesheet_clocked_in_accuracy", nullable=True)
    clocked_in_ip: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock in IP address", alias="Timesheet_clocked_in_ip", nullable=True)
    clocked_in_origin: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock in origin", alias="Timesheet_clocked_in_origin", nullable=True)
    clocked_in_verified_by: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock in verified by", alias="Timesheet_clocked_in_verified_by", nullable=True)

    # Clock out details
    clocked_out_latitude: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock out latitude", alias="Timesheet_clocked_out_latitude", nullable=True)
    clocked_out_longitude: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock out longitude", alias="Timesheet_clocked_out_longitude", nullable=True)
    clocked_out_accuracy: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock out accuracy", alias="Timesheet_clocked_out_accuracy", nullable=True)
    clocked_out_ip: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock out IP address", alias="Timesheet_clocked_out_ip", nullable=True)
    clocked_out_origin: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock out origin", alias="Timesheet_clocked_out_origin", nullable=True)
    clocked_out_verified_by: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock out verified by", alias="Timesheet_clocked_out_verified_by", nullable=True)

    # Additional timesheet fields
    clocked_break: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clocked break time", alias="Timesheet_clocked_break", nullable=True)
    overtime: Series[pd.StringDtype] = pa.Field(coerce=True, description="Overtime hours", alias="Timesheet_overtime", nullable=True)
    worked_for_vacation: Series[pd.StringDtype] = pa.Field(coerce=True, description="Hours worked for vacation", alias="Timesheet_worked_for_vacation", nullable=True)
    surcharge_time: Series[pd.StringDtype] = pa.Field(coerce=True, description="Surcharge time", alias="Timesheet_surcharge_time", nullable=True)
    surcharge_pay: Series[pd.StringDtype] = pa.Field(coerce=True, description="Surcharge pay", alias="Timesheet_surcharge_pay", nullable=True)
    custom_fields: Series[object] = pa.Field(coerce=True, description="Custom fields", alias="Timesheet_custom_fields", nullable=True)
    deleted: Series[pd.BooleanDtype] = pa.Field(coerce=True, description="Whether timesheet is deleted", alias="Timesheet_deleted", nullable=True)
    reviewed: Series[DateTime] = pa.Field(coerce=True, description="Review timestamp", alias="Timesheet_reviewed", nullable=True)
    created_by: Series[str] = pa.Field(coerce=True, description="Created by user ID", alias="Timesheet_created_by", nullable=True)
    modified_by: Series[str] = pa.Field(coerce=True, description="Modified by user ID", alias="Timesheet_modified_by", nullable=True)
    reviewed_by: Series[str] = pa.Field(coerce=True, description="Reviewed by user ID", alias="Timesheet_reviewed_by", nullable=True)
    regular_time: Series[pd.StringDtype] = pa.Field(coerce=True, description="Regular time hours", alias="Timesheet_regular_time", nullable=True)
    rates: Series[object] = pa.Field(coerce=True, description="Timesheet rates", alias="Timesheet_Rates", nullable=True)
    datetime: Series[object] = pa.Field(coerce=True, description="Timesheet datetime", alias="Timesheet_datetime", nullable=True)
    wage: Series[pd.StringDtype] = pa.Field(coerce=True, description="Wage amount", alias="Timesheet_wage", nullable=True)
    coc_rate: Series[pd.Float64Dtype] = pa.Field(coerce=True, description="COC rate", alias="Timesheet_coc_rate", nullable=True)
    surcharge_total: Series[pd.Float64Dtype] = pa.Field(coerce=True, description="Total surcharge", alias="Timesheet_surcharge_total", nullable=True)
    salary: Series[pd.Float64Dtype] = pa.Field(coerce=True, description="Salary amount", alias="Timesheet_salary", nullable=True)
    coc: Series[pd.Float64Dtype] = pa.Field(coerce=True, description="COC amount", alias="Timesheet_coc", nullable=True)
    active_clock: Series[pd.BooleanDtype] = pa.Field(coerce=True, description="Whether timesheet has active clock", alias="Timesheet_active_clock", nullable=True)

    # User details
    user_first_name: Series[str] = pa.Field(coerce=True, description="User first name", alias="User_first_name", nullable=True)
    user_prefix: Series[str] = pa.Field(coerce=True, description="User prefix", alias="User_prefix", nullable=True)
    user_last_name: Series[str] = pa.Field(coerce=True, description="User last name", alias="User_last_name", nullable=True)
    user_employee_nr: Series[str] = pa.Field(coerce=True, description="User employee number", alias="User_employee_nr", nullable=True)
    user_name: Series[str] = pa.Field(coerce=True, description="User full name", alias="User_name", nullable=True)

    # Shift details
    shift_name: Series[str] = pa.Field(coerce=True, description="Shift name", alias="Shift_name", nullable=True)
    shift_long_name: Series[str] = pa.Field(coerce=True, description="Shift long name", alias="Shift_long_name", nullable=True)
    shift_color: Series[str] = pa.Field(coerce=True, description="Shift color", alias="Shift_color", nullable=True)

    # Roster details
    roster_starttime: Series[str] = pa.Field(coerce=True, description="Roster start time", alias="Roster_starttime", nullable=True)
    roster_endtime: Series[str] = pa.Field(coerce=True, description="Roster end time", alias="Roster_endtime", nullable=True)
    roster_break: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Roster break time", alias="Roster_break", nullable=True)
    roster_shift_id: Series[str] = pa.Field(coerce=True, description="Roster shift ID", alias="Roster_shift_id", nullable=True)
    roster_team_id: Series[str] = pa.Field(coerce=True, description="Roster team ID", alias="Roster_team_id", nullable=True)
    roster_user_id: Series[str] = pa.Field(coerce=True, description="Roster user ID", alias="Roster_user_id", nullable=True)
    roster_total: Series[pd.Float64Dtype] = pa.Field(coerce=True, description="Roster total hours", alias="Roster_total", nullable=True)

    # Team details
    team_name: Series[str] = pa.Field(coerce=True, description="Team name", alias="Team_name", nullable=True)
    team_color: Series[str] = pa.Field(coerce=True, description="Team color", alias="Team_color", nullable=True)

    # Department details
    department_name: Series[str] = pa.Field(coerce=True, description="Department name", alias="Department_name", nullable=True)

    # Location details
    location_id: Series[str] = pa.Field(coerce=True, description="Location ID", alias="Location_id", nullable=True)
    location_name: Series[str] = pa.Field(coerce=True, description="Location name", alias="Location_name", nullable=True)

    # Nested objects
    clock_break: Series[object] = pa.Field(coerce=True, description="Clock break data", alias="ClockBreak", nullable=True)
    rate_block: Series[object] = pa.Field(coerce=True, description="Rate block data", alias="RateBlock", nullable=True)

    class _Annotation:
        primary_key = "timesheet_id"
        foreign_keys = {}

    class Config:
        coerce = True
        strict = False



class ClockBreakGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating ClockBreak GET data from Shiftbase API
    """
    id: Series[str] = pa.Field(coerce=True, description="Clock break ID", alias="id")
    account_id: Series[str] = pa.Field(coerce=True, description="Account ID", alias="accountId")
    timesheet_id: Series[pd.StringDtype] = pa.Field(coerce=True, description="Timesheet ID", alias="timesheetId", nullable=True)
    clocked_in: Series[DateTime] = pa.Field(coerce=True, description="Clock in timestamp", alias="clockedIn", nullable=True)
    clocked_out: Series[DateTime] = pa.Field(coerce=True, description="Clock out timestamp", alias="clockedOut", nullable=True)
    duration: Series[pd.StringDtype] = pa.Field(coerce=True, description="Break duration", alias="duration", nullable=True)
    created: Series[DateTime] = pa.Field(coerce=True, description="Creation timestamp", alias="created")
    updated: Series[DateTime] = pa.Field(coerce=True, description="Last update timestamp", alias="updated")

    class _Annotation:
        primary_key = "id"
        foreign_keys = {
            "timesheet_id": {
                "parent_schema": "TimesheetGet",
                "parent_column": "id",
                "cardinality": "N:1"
            }
        }


class TimesheetGetById(BrynQPanderaDataFrameModel):
    """
    Schema for validating Timesheet GET by ID data from Shiftbase API
    """
    timesheet_id: Series[str] = pa.Field(coerce=True, description="Timesheet ID", alias="id")
    account_id: Series[str] = pa.Field(coerce=True, description="Account ID", alias="account_id")
    user_id: Series[str] = pa.Field(coerce=True, description="User ID", alias="user_id")
    team_id: Series[str] = pa.Field(coerce=True, description="Team ID", alias="team_id")
    shift_id: Series[str] = pa.Field(coerce=True, description="Shift ID", alias="shift_id")
    roster_id: Series[pd.StringDtype] = pa.Field(coerce=True, description="Roster ID", alias="roster_id", nullable=True)
    rate_card_id: Series[str] = pa.Field(coerce=True, description="Rate Card ID", alias="rate_card_id")
    date: Series[Date] = pa.Field(coerce=True, description="Date of the timesheet", alias="date")
    start_time: Series[str] = pa.Field(coerce=True, description="Start time of the timesheet", alias="starttime")
    end_time: Series[pd.StringDtype] = pa.Field(coerce=True, description="End time of the timesheet", alias="endtime", nullable=True)
    clocked_in: Series[DateTime] = pa.Field(coerce=True, description="Clock in timestamp", alias="clocked_in", nullable=True)
    clocked_out: Series[DateTime] = pa.Field(coerce=True, description="Clock out timestamp", alias="clocked_out", nullable=True)
    total: Series[pd.Float64Dtype] = pa.Field(coerce=True, description="Total worked hours", alias="total", nullable=True)
    status: Series[pd.StringDtype] = pa.Field(coerce=True, description="Timesheet status", alias="status", nullable=True)
    break_time: Series[pd.StringDtype] = pa.Field(coerce=True, description="Break duration in minutes", alias="break", nullable=True)
    meals: Series[pd.StringDtype] = pa.Field(coerce=True, description="Number of meals", alias="meals", nullable=True)
    kilometers: Series[pd.StringDtype] = pa.Field(coerce=True, description="Driven kilometers", alias="kilometers", nullable=True)
    note: Series[pd.StringDtype] = pa.Field(coerce=True, description="Timesheet note", alias="note", nullable=True)
    clock: Series[pd.BooleanDtype] = pa.Field(coerce=True, description="Whether timesheet is clock-based", alias="clock", nullable=True)
    created: Series[DateTime] = pa.Field(coerce=True, description="Creation timestamp", alias="created", nullable=True)
    updated: Series[DateTime] = pa.Field(coerce=True, description="Last update timestamp", alias="updated", nullable=True)

    # Clock in details
    clocked_in_latitude: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock in latitude", alias="clocked_in_latitude", nullable=True)
    clocked_in_longitude: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock in longitude", alias="clocked_in_longitude", nullable=True)
    clocked_in_accuracy: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock in accuracy", alias="clocked_in_accuracy", nullable=True)
    clocked_in_ip: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock in IP address", alias="clocked_in_ip", nullable=True)
    clocked_in_origin: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock in origin", alias="clocked_in_origin", nullable=True)
    clocked_in_verified_by: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock in verified by", alias="clocked_in_verified_by", nullable=True)

    # Clock out details
    clocked_out_latitude: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock out latitude", alias="clocked_out_latitude", nullable=True)
    clocked_out_longitude: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock out longitude", alias="clocked_out_longitude", nullable=True)
    clocked_out_accuracy: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock out accuracy", alias="clocked_out_accuracy", nullable=True)
    clocked_out_ip: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock out IP address", alias="clocked_out_ip", nullable=True)
    clocked_out_origin: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock out origin", alias="clocked_out_origin", nullable=True)
    clocked_out_verified_by: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clock out verified by", alias="clocked_out_verified_by", nullable=True)

    # Additional timesheet fields
    clocked_break: Series[pd.StringDtype] = pa.Field(coerce=True, description="Clocked break time", alias="clocked_break", nullable=True)
    overtime: Series[pd.StringDtype] = pa.Field(coerce=True, description="Overtime hours", alias="overtime", nullable=True)
    worked_for_vacation: Series[pd.StringDtype] = pa.Field(coerce=True, description="Hours worked for vacation", alias="worked_for_vacation", nullable=True)
    surcharge_time: Series[pd.StringDtype] = pa.Field(coerce=True, description="Surcharge time", alias="surcharge_time", nullable=True)
    surcharge_pay: Series[pd.StringDtype] = pa.Field(coerce=True, description="Surcharge pay", alias="surcharge_pay", nullable=True)
    deleted: Series[pd.BooleanDtype] = pa.Field(coerce=True, description="Whether timesheet is deleted", alias="deleted", nullable=True)
    reviewed: Series[DateTime] = pa.Field(coerce=True, description="Review timestamp", alias="reviewed", nullable=True)
    created_by: Series[str] = pa.Field(coerce=True, description="Created by user ID", alias="created_by", nullable=True)
    modified_by: Series[str] = pa.Field(coerce=True, description="Modified by user ID", alias="modified_by", nullable=True)
    reviewed_by: Series[str] = pa.Field(coerce=True, description="Reviewed by user ID", alias="reviewed_by", nullable=True)
    regular_time: Series[pd.StringDtype] = pa.Field(coerce=True, description="Regular time hours", alias="regular_time", nullable=True)
    wage: Series[pd.StringDtype] = pa.Field(coerce=True, description="Wage amount", alias="wage", nullable=True)
    coc_rate: Series[pd.Float64Dtype] = pa.Field(coerce=True, description="COC rate", alias="coc_rate", nullable=True)
    surcharge_total: Series[pd.Float64Dtype] = pa.Field(coerce=True, description="Total surcharge", alias="surcharge_total", nullable=True)
    salary: Series[pd.Float64Dtype] = pa.Field(coerce=True, description="Salary amount", alias="salary", nullable=True)
    coc: Series[pd.Float64Dtype] = pa.Field(coerce=True, description="COC amount", alias="coc", nullable=True)
    active_clock: Series[pd.BooleanDtype] = pa.Field(coerce=True, description="Whether timesheet has active clock", alias="active_clock", nullable=True)

    class _Annotation:
        primary_key = "timesheet_id"
        foreign_keys = {}


class ClockGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating Clock GET data from Shiftbase API
    """
    department_id: Series[str] = pa.Field(coerce=True, description="Department ID", alias="Department_id")
    team_id: Series[str] = pa.Field(coerce=True, description="Team ID", alias="Team_id")
    shift_id: Series[str] = pa.Field(coerce=True, description="Shift ID", alias="Shift_id")
    user_id: Series[str] = pa.Field(coerce=True, description="User ID", alias="User_id")
    roster_id: Series[pd.StringDtype] = pa.Field(coerce=True, description="Roster ID", alias="Roster_id", nullable=True)
    break_time: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Break time in minutes", alias="Roster_break", nullable=True)
    date: Series[Date] = pa.Field(coerce=True, description="Clock date", alias="Timesheet_date")
    starttime: Series[str] = pa.Field(coerce=True, description="Start time", alias="Timesheet_starttime")

    class _Annotation:
        primary_key = "user_id"
        foreign_keys = {}


# ============================================================================
# PYDANTIC SCHEMAS (Create/Update operations) - Inherit from BaseModel
# ============================================================================

class ClockOrigin(str, Enum):
    """Enum for clock origin values"""
    TERMINAL = "terminal"
    WEB_APP = "web_app"
    MOBILE_APP = "mobile_app"
    API = "api"


class TimesheetStatus(str, Enum):
    """Enum for timesheet status values"""
    APPROVED = "Approved"
    DECLINED = "Declined"
    PENDING = "Pending"


class TimesheetCreate(BaseModel):
    """
    Schema for creating new Timesheet data in Shiftbase API
    """
    user_id: str = Field(description="User ID")
    team_id: str = Field(description="Team ID", pattern=r"^[0-9]+$")
    shift_id: str = Field(description="Shift ID", pattern=r"^[0-9]+$")
    roster_id: Optional[str] = Field(None, description="Roster ID", pattern=r"^[0-9]+$")
    rate_card_id: str = Field(description="Rate Card ID", pattern=r"^[0-9]+$")
    date: date_type = Field(description="Date of the timesheet")
    start_time: str = Field(description="Start time of the timesheet", alias="starttime")
    end_time: Optional[str] = Field(None, description="End time of the timesheet", alias="endtime")
    clocked_in: Optional[datetime] = Field(None, description="Clock in timestamp")
    clocked_out: Optional[datetime] = Field(None, description="Clock out timestamp")
    total: Optional[str] = Field(None, description="Total worked hours")
    status: Optional[TimesheetStatus] = Field(None, description="Timesheet status")
    break_time: Optional[str] = Field(None, description="Break duration in minutes", alias="break")
    meals: Optional[str] = Field(None, description="Number of meals")
    kilometers: Optional[str] = Field(None, description="Driven kilometers")
    note: Optional[str] = Field(None, description="Timesheet note")
    clock: Optional[bool] = Field(None, description="Whether timesheet is clock-based")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Custom fields")

    class Config:
        populate_by_name = True


class TimesheetUpdate(BaseModel):
    """
    Schema for updating existing Timesheet data in Shiftbase API
    """
    user_id: Optional[str] = Field(None, description="User ID", alias="userId")
    team_id: Optional[str] = Field(None, description="Team ID", pattern=r"^[0-9]+$", alias="teamId")
    shift_id: Optional[str] = Field(None, description="Shift ID", pattern=r"^[0-9]+$", alias="shiftId")
    roster_id: Optional[str] = Field(None, description="Roster ID", pattern=r"^[0-9]+$", alias="rosterId")
    rate_card_id: Optional[str] = Field(None, description="Rate Card ID", pattern=r"^[0-9]+$", alias="rateCardId")
    date: Optional[date_type] = Field(None, description="Date of the timesheet", alias="date")
    start_time: Optional[str] = Field(None, description="Start time of the timesheet", alias="starttime")
    end_time: Optional[str] = Field(None, description="End time of the timesheet", alias="endtime")
    clocked_in: Optional[datetime] = Field(None, description="Clock in timestamp", alias="clockedIn")
    clocked_out: Optional[datetime] = Field(None, description="Clock out timestamp", alias="clockedOut")
    total: Optional[str] = Field(None, description="Total worked hours", alias="total")
    status: Optional[TimesheetStatus] = Field(None, description="Timesheet status", alias="status")
    break_time: Optional[str] = Field(None, description="Break duration in minutes", alias="break")
    meals: Optional[str] = Field(None, description="Number of meals", alias="meals")
    kilometers: Optional[str] = Field(None, description="Driven kilometers", alias="kilometers")
    note: Optional[str] = Field(None, description="Timesheet note", alias="note")
    clock: Optional[bool] = Field(None, description="Whether timesheet is clock-based", alias="clock")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Custom fields", alias="customFields")

    class Config:
        allow_population_by_field_name = True


class ClockBreakCreate(BaseModel):
    """
    Schema for creating new ClockBreak data in Shiftbase API
    """
    timesheet_id: Optional[str] = Field(None, description="Timesheet ID", pattern=r"^[0-9]+$", alias="timesheetId")
    clocked_in: Optional[datetime] = Field(None, description="Clock in timestamp", alias="clockedIn")
    clocked_out: Optional[datetime] = Field(None, description="Clock out timestamp", alias="clockedOut")
    duration: Optional[str] = Field(None, description="Break duration", alias="duration")

    class Config:
        allow_population_by_field_name = True


class ClockBreakUpdate(BaseModel):
    """
    Schema for updating existing ClockBreak data in Shiftbase API
    """
    timesheet_id: Optional[str] = Field(None, description="Timesheet ID", pattern=r"^[0-9]+$", alias="timesheetId")
    clocked_in: Optional[datetime] = Field(None, description="Clock in timestamp", alias="clockedIn")
    clocked_out: Optional[datetime] = Field(None, description="Clock out timestamp", alias="clockedOut")
    duration: Optional[str] = Field(None, description="Break duration", alias="duration")

    class Config:
        allow_population_by_field_name = True
