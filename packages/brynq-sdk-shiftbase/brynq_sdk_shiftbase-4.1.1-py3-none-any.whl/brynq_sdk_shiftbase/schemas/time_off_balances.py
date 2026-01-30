import pandera as pa
from pandera.typing import Series
from datetime import date as date_type
from brynq_sdk_functions import BrynQPanderaDataFrameModel


class TimeOffBalanceGet(BrynQPanderaDataFrameModel):
    """
    Validation schema for Time Off Balance data from Shiftbase API
    """
    id: Series[str] = pa.Field(coerce=True, description="Time off balance identifier")
    name: Series[str] = pa.Field(coerce=True, description="Time off balance name")
    default_accrual: Series[float] = pa.Field(coerce=True, description="Default accrual amount")
    unit: Series[str] = pa.Field(coerce=True, description="Accrual unit", isin=["hours", "days"])
    allow_request_half_days: Series[bool] = pa.Field(coerce=True, description="Whether half days can be requested")
    active: Series[bool] = pa.Field(coerce=True, description="Whether the balance is active")
    expiration_in_months: Series[int] = pa.Field(nullable=True, coerce=True, description="Expiration in months if applicable")

    class _Annotation:
        primary_key = "id"
        foreign_keys = {}


class BalanceCycleGet(BrynQPanderaDataFrameModel):
    """
    Validation schema for Balance Cycle data from Shiftbase API
    """
    balance_id: Series[str] = pa.Field(coerce=True, description="Time off balance identifier", alias="balanceId")
    cycle_year: Series[str] = pa.Field(coerce=True, description="Cycle year in YYYY format", alias="cycleYear")
    expire_date: Series[date_type] = pa.Field(nullable=True, coerce=True, description="Expiration date in YYYY-MM-DD format", alias="expireDate")
    total: Series[float] = pa.Field(coerce=True, description="Total amount in the cycle")

    class _Annotation:
        primary_key = "balance_id"
        foreign_keys = {
            "balance_id": "TimeOffBalanceGet"
        }
