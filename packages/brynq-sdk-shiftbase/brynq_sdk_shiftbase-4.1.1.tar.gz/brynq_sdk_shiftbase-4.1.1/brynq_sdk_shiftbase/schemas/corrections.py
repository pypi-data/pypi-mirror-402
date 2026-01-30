"""
Schema definition for Correction data validation.
"""
import pandera as pa
from pandera.typing import Series, DateTime, Date
from brynq_sdk_functions import BrynQPanderaDataFrameModel
from typing import Optional, List, Union
from pydantic import BaseModel, Field
from datetime import date as date_type
from enum import Enum


class CorrectionGet(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating Correction GET data.
    This schema is used when retrieving corrections from Shiftbase.
    """
    id: Series[str] = pa.Field(coerce=True, description="Unique identifier for the correction")
    user_id: Series[str] = pa.Field(coerce=True, description="User identifier")
    account_id: Series[str] = pa.Field(coerce=True, description="Account identifier", nullable=True)
    date: Series[Date] = pa.Field(coerce=True, description="Date of the correction")
    type: Series[str] = pa.Field(coerce=True, description="Type of correction")
    amount: Series[float] = pa.Field(coerce=True, description="Amount of the correction", nullable=True)
    coc: Series[float] = pa.Field(coerce=True, description="Cost of the correction", nullable=True)
    note: Series[str] = pa.Field(coerce=True, description="Note about the correction", nullable=True)
    time_off_balance_id: Series[str] = pa.Field(coerce=True, description="Time off balance identifier", nullable=True)
    pay: Series[bool] = pa.Field(coerce=True, description="If the correction is a payout correction", nullable=True)
    public: Series[bool] = pa.Field(coerce=True, description="If the correction is public", nullable=True)
    payout_date: Series[DateTime] = pa.Field(coerce=True, description="Payout date of the correction", nullable=True)
    expire_date: Series[DateTime] = pa.Field(coerce=True, description="Expiration date for the correction", nullable=True)
    created: Series[DateTime] = pa.Field(coerce=True, description="Creation timestamp", nullable=True)
    updated: Series[DateTime] = pa.Field(coerce=True, description="Last update timestamp", nullable=True)
    created_by: Series[str] = pa.Field(coerce=True, description="ID of the user who created the correction", nullable=True)
    modified_by: Series[str] = pa.Field(coerce=True, description="ID of the user who last modified the correction", nullable=True)

    class _Annotation:
        primary_key = ["id"]
        foreign_keys = ["user_id", "account_id"]


# ============================================================================
# PYDANTIC SCHEMAS (Create/Update operations) - Inherit from BaseModel
# ============================================================================

class CorrectionType(str, Enum):
    """Enum for correction type values"""
    OVERTIME = "Overtime"
    TIME_OFF_BALANCE = "Time off balance"
    TIME_OFF_BALANCE_CYCLE = "Time off balance cycle"


class CorrectionAction(str, Enum):
    """Enum for correction action values"""
    CORRECT = "correct"
    CORRECTION = "correction"
    PAY = "pay"
    BALANCE_MOVE = "balance move"
    OVERTIME_MOVE = "overtime move"


class CorrectionCreate(BaseModel):
    """
    Schema for creating new Correction data in Shiftbase API
    Used for both single and batch corrections
    """
    user_id: str = Field(description="User ID", pattern=r"^[0-9]+$")
    type: CorrectionType = Field(description="Type of correction")
    date: date_type = Field(description="The date on which the correction should take place")
    hours: Optional[float] = Field(None, description="Required if type is Overtime or time off balance is in hours")
    days: Optional[float] = Field(None, description="Required if time off balance is in days")
    action: Optional[CorrectionAction] = Field(None, description="The action of the correction")
    note: Optional[str] = Field(None, description="Note about the correction")
    payout_date: Optional[date_type] = Field(None, description="The date on which the correction should be paid out")
    time_off_balance_id: Optional[str] = Field(None, description="For which time off balance the correction is. Is required when type is Time off balance")
    time_off_balance_name: Optional[str] = Field(None, description="Name of the source balance")
    to_time_off_balance_id: Optional[str] = Field(None, description="Target time off balance. Required when action is balance move")
    to_time_off_balance_name: Optional[str] = Field(None, description="Name of the target time off balance")
    expire_date: Optional[date_type] = Field(None, description="For a time off balance cycle correction to set new expire date")

    class Config:
        use_enum_values = True


class CorrectionBatchCreate(BaseModel):
    """
    Schema for creating multiple corrections in batch
    """
    Correction: List[CorrectionCreate] = Field(description="List of corrections to create")

    class Config:
        use_enum_values = True
