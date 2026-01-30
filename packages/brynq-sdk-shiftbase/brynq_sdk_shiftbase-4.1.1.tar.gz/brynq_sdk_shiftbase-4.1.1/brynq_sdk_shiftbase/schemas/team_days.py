"""
Schema definition for TeamDay data validation.
"""
import pandera as pa
from pandera.typing import Series
from datetime import datetime, date as date_type
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class TeamDayGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating TeamDay data returned from Shiftbase API.
    """
    # Read-only fields
    id: Series[str] = pa.Field(coerce=True, description="Team day ID")
    account_id: Series[str] = pa.Field(coerce=True, description="Account ID")
    created: Series[datetime] = pa.Field(nullable=True, coerce=True, description="Creation date")
    updated: Series[datetime] = pa.Field(nullable=True, coerce=True, description="Last update date")
    created_by: Series[str] = pa.Field(nullable=True, coerce=True, description="Created by user ID")
    modified_by: Series[str] = pa.Field(nullable=True, coerce=True, description="Modified by user ID")

    # Required fields
    team_id: Series[str] = pa.Field(coerce=True, description="Team ID")
    date: Series[date_type] = pa.Field(coerce=True, description="Date in YYYY-MM-DD format")

    # Optional fields
    note: Series[str] = pa.Field(nullable=True, coerce=True, description="Team note for the day")
    budget_cost: Series[str] = pa.Field(nullable=True, coerce=True, description="Budget for the day")
    budget_time: Series[str] = pa.Field(nullable=True, coerce=True, description="Budgeted time in hours")
    turnover: Series[str] = pa.Field(nullable=True, coerce=True, description="Turnover for the day")
    expenses: Series[str] = pa.Field(nullable=True, coerce=True, description="Expenses for the day")


    @pa.check("budget_cost", "budget_time", "turnover", "expenses")
    def check_numeric_format(cls, series: Series[str]) -> Series[bool]:
        """Validate numeric fields have correct format (decimal)."""
        valid = series.str.match(r"^([0-9]*[.])?[0-9]+$") | series.isna()
        return valid

    class _Annotation:
        primary_key = "id"
        foreign_keys = {
            "account_id": "AccountGet",
            "team_id": "TeamGet",
            "created_by": "UserGet",
            "modified_by": "UserGet"
        }
