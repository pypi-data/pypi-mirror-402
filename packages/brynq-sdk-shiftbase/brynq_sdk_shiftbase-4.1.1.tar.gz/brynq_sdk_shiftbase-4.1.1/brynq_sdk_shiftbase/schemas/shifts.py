"""
Schema definition for Shift data validation.
"""
import pandera as pa
from pandera.typing import Series, DataFrame
from datetime import datetime
from typing import Optional
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class ShiftGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating Shift data returned from Shiftbase API.
    """
    # Read-only fields
    id: Series[str] = pa.Field(coerce=True, description="Shift ID")
    account_id: Series[str] = pa.Field(coerce=True, description="Account ID")
    created: Series[datetime] = pa.Field(nullable=True, coerce=True, description="Creation date")
    deleted: Series[bool] = pa.Field(nullable=True, coerce=True, description="Deleted flag")
    created_by: Series[str] = pa.Field(nullable=True, coerce=True, description="Created by user ID")
    modified_by: Series[str] = pa.Field(nullable=True, coerce=True, description="Modified by user ID")

    # Required fields
    department_id: Series[str] = pa.Field(coerce=True, description="Department ID")
    name: Series[str] = pa.Field(coerce=True, description="Short name of the shift")
    long_name: Series[str] = pa.Field(coerce=True, description="Full name of the shift")
    start_time: Series[str] = pa.Field(coerce=True, description="Start time (HH:MM:SS)", alias="starttime")
    break_time: Series[str] = pa.Field(nullable=True, coerce=True, description="Break time", alias="break")

    # Optional fields
    description: Series[str] = pa.Field(nullable=True, coerce=True, description="Description")
    end_time: Series[str] = pa.Field(nullable=True, coerce=True, description="End time (HH:MM:SS)", alias="endtime")
    hide_end_time: Series[bool] = pa.Field(nullable=True, coerce=True, description="Hide end time flag")
    is_task: Series[bool] = pa.Field(nullable=True, coerce=True, description="Is task flag")
    meals: Series[str] = pa.Field(nullable=True, coerce=True, description="Meals")
    rate_card_id: Series[str] = pa.Field(nullable=True, coerce=True, description="Rate card ID")
    color: Series[str] = pa.Field(nullable=True, coerce=True, description="Color")
    order: Series[str] = pa.Field(nullable=True, coerce=True, description="Order")


    @pa.check("color")
    def check_color_format(cls, series: Series[str]) -> Series[bool]:
        """Validate color is in hexadecimal format."""
        valid = series.str.match(r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$") | series.isna()
        return valid

    class _Annotation:
        primary_key = "id"
        foreign_keys = {
            "department_id": "DepartmentGet",
            "account_id": "AccountGet",
            "created_by": "UserGet",
            "modified_by": "UserGet",
            "rate_card_id": "RateCardGet"
        }
