"""
Schema definition for AbsencePolicy data validation.
"""
from typing import List
from enum import Enum
import pandera as pa
from pandera.typing import Series
from brynq_sdk_functions import BrynQPanderaDataFrameModel


class TimeOffDetermination(str, Enum):
    """Time off determination options"""
    SCHEDULED = "SCHEDULED"
    CONTRACT = "CONTRACT"
    NONE = "NONE"


class DayValueDetermination(str, Enum):
    """Day value determination options"""
    CONTRACT = "CONTRACT"
    GERMAN_13_WEEK = "GERMAN_13_WEEK"
    NONE = "NONE"


class TimeOffAccrualSourceHours(str, Enum):
    """Time off accrual source hours options"""
    CONTRACT = "CONTRACT"
    WORKED = "WORKED"
    NONE = "NONE"


class WaitHoursFrom(str, Enum):
    """Wait hours from options"""
    SALARY = "SALARY"
    TIME_OFF_BALANCE = "TIME_OFF_BALANCE"


class AbsencePolicyGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating AbsencePolicy data returned from Shiftbase API.
    An AbsencePolicy is a wrapper around a group of absence settings that can be linked
    to a user on ContractType level.
    """
    # Primary fields (from meta columns)
    id: Series[str] = pa.Field(coerce=True, description="The unique identifier of the policy", alias="id")
    name: Series[str] = pa.Field(coerce=True, description="A short name for the policy", alias="name")
    description: Series[str] = pa.Field(coerce=True, description="Optional extra description for the policy", alias="description", nullable=True)
    time_off_accrual_source_hours: Series[str] = pa.Field(coerce=True, description="Specify how the time off balances should be accrued", alias="timeOffAccrualSourceHours", isin=[e.value for e in TimeOffAccrualSourceHours])
    wait_hours_from: Series[str] = pa.Field(coerce=True, description="Specify where the waiting hours will be deducted from", alias="waitHoursFrom", isin=[e.value for e in WaitHoursFrom])
    wait_hours_from_time_off_balance_id: Series[str] = pa.Field(coerce=True, description="If the waitHoursFrom is set to TIME_OFF_BALANCE here, you can specify which time off balance the wait hours are deducted from", alias="waitHoursFromTimeOffBalanceId", nullable=True)
    public_holiday_absence_type_id: Series[str] = pa.Field(coerce=True, description="Specify the absence type to automatically create absences on public holidays", alias="publicHolidayAbsenceTypeId", nullable=True)

    # Configuration fields (from record_path - flattened from nested structure)
    absence_type_id: Series[str] = pa.Field(coerce=True, description="The unique identifier of an absence type", alias="absenceTypeId")
    balance_ids: Series[List[str]] = pa.Field(coerce=True, description="The unique identifiers of time off balances", alias="balanceIds", nullable=True)
    time_off_determination: Series[str] = pa.Field(coerce=True, description="Time off determination - defines how time-off hours are calculated for the absence type", alias="timeOffDetermination", isin=[e.value for e in TimeOffDetermination])
    day_value_determination: Series[str] = pa.Field(coerce=True, description="Day value determination. Only available when the unit of the absence type is days", alias="dayValueDetermination", nullable=True, isin=[e.value for e in DayValueDetermination])

    class _Annotation:
        primary_key = "id"
        foreign_keys = {
            "absence_type_id": {
                "parent_schema": "AbsenceType",
                "parent_column": "id",
                "cardinality": "N:1"
            },
            "public_holiday_absence_type_id": {
                "parent_schema": "AbsenceType",
                "parent_column": "id",
                "cardinality": "N:1"
            }
        }

    class Config:
        coerce = True
        strict = False
