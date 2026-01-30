"""
Schema definition for AbsenteeOption data validation.
"""
from typing import List, Optional
from enum import Enum
import pandera as pa
from pandera.typing import Series
from pydantic import BaseModel, Field
from brynq_sdk_functions import BrynQPanderaDataFrameModel


class AbsenteeIcon(str, Enum):
    """Allowed values for absence icons"""
    LEAVE_1 = "leave-1"
    LEAVE_2 = "leave-2"
    LEAVE_4 = "leave-4"
    LEAVE_5 = "leave-5"
    LEAVE_6 = "leave-6"
    BAN = "ban"
    BELL = "bell"
    BOOK = "book"
    BULLHORN = "bullhorn"
    CALCULATOR = "calculator"
    CALENDAR = "calendar"
    CALENDAR_DAY = "calendar-day"
    CALENDAR_GROUP = "calendar-group"
    CALENDAR_MONTH = "calendar-month"
    CALENDAR_WEEK = "calendar-week"
    CALENDAR_APPROVED = "calendar_approved"
    CALENDAR_DENIED = "calendar_denied"
    CAR = "car"
    CHANGE_SHIFT = "change_shift"
    COFFEE = "coffee"
    COMMENT = "comment"
    CLIPBOARD = "clipboard"
    CUTLERY = "cutlery"
    EXCLAMATION_TRIANGLE = "exclamation-triangle"
    DELETE = "delete"
    EYE = "eye"
    FLAG = "flag"
    INFO = "info"
    MAP_MARKER = "map-marker"
    PAPER_PLANE = "paper-plane"
    PAYMENT = "payment"
    RECLOCK = "reclock"
    TEAM = "team"
    STOPWATCH = "stopwatch"
    TOUR = "tour"
    ZOOM = "zoom"
    OVERTIME = "overtime"
    ABSENTEE_VACATION = "absentee-vacation"
    ABSENTEE_SICK = "absentee-sick"
    ABSENTEE_UNAVAILABLE = "absentee-unavailable"
    ABSENTEE_NATIONAL_DAY = "absentee-national_day"
    ABSENTEE_MATERNITY_LEAVE = "absentee_maternity_leave"
    ABSENTEE_OTHER = "absentee_other"
    RATECARD = "ratecard"


class RosterAction(str, Enum):
    """Allowed values for default_roster_action"""
    HIDE = "hide"
    NONE = "none"
    MOVE_TO_OPEN_SHIFT = "move_to_open_shift"


class UnitType(str, Enum):
    """Allowed values for unit"""
    HOURS = "hours"
    DAYS = "days"


class AbsenteeOptionGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating AbsenteeOption data returned from Shiftbase API.
    """
    # Required Fields
    id: Series[str] = pa.Field(coerce=True, description="Unique identifier for the absence type", alias="id")
    account_id: Series[str] = pa.Field(coerce=True, description="Account identifier for the absence type", alias="account_id")
    option: Series[str] = pa.Field(coerce=True, description="Name of the absence type", alias="option")
    percentage: Series[str] = pa.Field(coerce=True, description="Surcharge percentage by which the absence should be recorded", alias="percentage")
    weight: Series[str] = pa.Field(coerce=True, description="Used for ordering the absence types", alias="weight")
    has_vacation_accrual: Series[bool] = pa.Field(coerce=True, description="Leave hours are accrued during the absence", alias="has_vacation_accrual")
    costs_vacation_hours: Series[bool] = pa.Field(coerce=True, description="Deduct hours from vacation hours", alias="costs_vacation_hours")
    is_counted: Series[bool] = pa.Field(coerce=True, description="If set to false no hours are calculated for this type", alias="is_counted")
    has_wait_hours: Series[bool] = pa.Field(coerce=True, description="When an absence of this type is requested, wait hours can be specified", alias="has_wait_hours")
    leave: Series[bool] = pa.Field(coerce=True, description="Determines if absence falls under leave or non-attendance group", alias="leave")
    color: Series[str] = pa.Field(coerce=True, description="Color of the absence in the schedule (hexadecimal)", alias="color")
    icon: Series[str] = pa.Field(coerce=True, description="Icon shown with the absence type", alias="icon", isin=[e.value for e in AbsenteeIcon])
    deleted: Series[bool] = pa.Field(coerce=True, description="Whether the absence type is deleted (read-only)", alias="deleted")

    # Optional Fields
    permission: Series[str] = pa.Field(coerce=True, description="Permission name (deprecated, read-only)", alias="permission", nullable=True)
    default_roster_action: Series[str] = pa.Field(coerce=True, description="Sets the default intermediate shift option on an absence request", alias="default_roster_action", nullable=True, isin=[e.value for e in RosterAction])
    allow_open_ended: Series[bool] = pa.Field(coerce=True, description="Whether the absence type allows open-ended requests", alias="allow_open_ended", nullable=True)
    unit: Series[str] = pa.Field(coerce=True, description="Whether absence is measured in days or hours", alias="unit", nullable=True, isin=[e.value for e in UnitType])

    class _Annotation:
        primary_key = "id"
        foreign_keys = {
            "account_id": {
                "parent_schema": "Account",
                "parent_column": "id",
                "cardinality": "N:1"
            }
        }

    class Config:
        coerce = True
        strict = False


class AbsenteeOptionCreate(BaseModel):
    """
    Schema for validating AbsenteeOption creation data.
    This schema is used when creating new absence types in Shiftbase.
    """
    # Required fields
    option: str = Field(description="Name of the absence type", max_length=160, example="Vacation")
    percentage: str = Field(description="Surcharge percentage by which the absence should be recorded", pattern=r"^[0-9]+$", example="100")
    weight: str = Field(description="Used for ordering the absence types", pattern=r"^[0-9]+$", example="10")
    has_vacation_accrual: bool = Field(description="Leave hours are accrued during the absence", example=True)
    costs_vacation_hours: bool = Field(description="Deduct hours from vacation hours", example=True)
    is_counted: bool = Field(description="If set to false no hours are calculated for this type", example=True)
    has_wait_hours: bool = Field(description="When an absence of this type is requested, wait hours can be specified", example=False)
    leave: bool = Field(description="Determines if absence falls under leave or non-attendance group", example=True)
    color: str = Field(description="Color of the absence in the schedule (hexadecimal)", pattern=r"^#[0-9A-Fa-f]{6}$", example="#F2CA00")
    icon: str = Field(description="Icon shown with the absence type", example="absentee-vacation")

    # Optional fields
    default_roster_action: Optional[RosterAction] = Field(description="Sets the default intermediate shift option on an absence request", default=RosterAction.HIDE, example="hide")
    allow_open_ended: Optional[bool] = Field(description="Whether the absence type allows open-ended requests", default=False, example=False)
    unit: Optional[UnitType] = Field(description="Whether absence is measured in days or hours", default=UnitType.HOURS, example="hours")
    group_ids: Optional[List[str]] = Field(description="List of group IDs that can request the absence type", example=["group1", "group2"])


    class Config:
        """Pydantic configuration"""
        use_enum_values = True


class AbsenteeOptionUpdate(BaseModel):
    """
    Schema for validating AbsenteeOption update data.
    This schema is used when updating existing absence types in Shiftbase.
    """
    # Required fields
    option: str = Field(description="Name of the absence type", max_length=160, example="Vacation")
    percentage: str = Field(description="Surcharge percentage by which the absence should be recorded", pattern=r"^[0-9]+$", example="100")
    weight: str = Field(description="Used for ordering the absence types", pattern=r"^[0-9]+$", example="10")
    has_vacation_accrual: bool = Field(description="Leave hours are accrued during the absence", example=True)
    costs_vacation_hours: bool = Field(description="Deduct hours from vacation hours", example=True)
    is_counted: bool = Field(description="If set to false no hours are calculated for this type", example=True)
    has_wait_hours: bool = Field(description="When an absence of this type is requested, wait hours can be specified", example=False)
    leave: bool = Field(description="Determines if absence falls under leave or non-attendance group", example=True)
    color: str = Field(description="Color of the absence in the schedule (hexadecimal)", pattern=r"^#[0-9A-Fa-f]{6}$", example="#F2CA00")
    icon: str = Field(description="Icon shown with the absence type", example="absentee-vacation")

    # Optional fields
    default_roster_action: Optional[str] = Field(description="Sets the default intermediate shift option on an absence request", default="hide", example="hide")
    allow_open_ended: Optional[bool] = Field(description="Whether the absence type allows open-ended requests", default=False, example=False)
    unit: Optional[str] = Field(description="Whether absence is measured in days or hours", default="hours", example="hours")
    group_ids: Optional[List[str]] = Field(description="List of group IDs that can request the absence type", example=["group1", "group2"])

    class Config:
        """Pydantic configuration"""
        use_enum_values = True
