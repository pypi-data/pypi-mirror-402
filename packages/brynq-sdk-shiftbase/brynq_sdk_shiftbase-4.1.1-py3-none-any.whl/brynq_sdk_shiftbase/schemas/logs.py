"""
Schema definition for Log data validation.
"""
import pandera as pa
from pandera.typing import Series
import pandas as pd
from datetime import datetime
from datetime import date as date_type
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class LogGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating Log data returned from Shiftbase API.

    The log contains daily information per department such as the turnover and
    expected turnover as well as the publishing status of a schedule and
    if timesheets are open for modification.
    """
    # Required fields
    id: Series[str] = pa.Field(coerce=True, regex=r"^[0-9]+$", description="Unique identifier for the log entry")
    department_id: Series[str] = pa.Field(coerce=True, regex=r"^[0-9]+$", description="Department ID for the log entry")
    date: Series[date_type] = pa.Field(coerce=True, description="Date of the log entry")

    # Read-only fields
    account_id: Series[str] = pa.Field(coerce=True, regex=r"^[0-9]+$", description="Account ID that owns the log", nullable=True)
    created: Series[datetime] = pa.Field(coerce=True, description="Creation date and time", nullable=True)
    modified: Series[datetime] = pa.Field(coerce=True, description="Last modification date and time", nullable=True)
    created_by: Series[str] = pa.Field(coerce=True, regex=r"^[0-9]+$", description="User who created the log", nullable=True)
    modified_by: Series[str] = pa.Field(coerce=True, regex=r"^[0-9]+$", description="User who last modified the log", nullable=True)
    turnover: Series[str] = pa.Field(coerce=True, description="Actual turnover amount", nullable=True)
    expenses: Series[str] = pa.Field(coerce=True, description="Expenses amount", nullable=True)

    # Optional fields
    finished_timesheet: Series[bool] = pa.Field(coerce=True, description="Whether timesheet is finished", nullable=True)
    published_schedule: Series[bool] = pa.Field(coerce=True, description="Whether schedule is published", nullable=True)
    log: Series[str] = pa.Field(coerce=True, description="Log message or notes", nullable=True)
    expected_turnover: Series[str] = pa.Field(coerce=True, description="Expected turnover amount", nullable=True)

    @pa.check("date")
    def validate_date(cls, series: Series[date_type]) -> Series[bool]:
        """Validates date format YYYY-MM-DD"""
        return series.dt.strftime("%Y-%m-%d").str.match(r"^\d{4}-\d{2}-\d{2}$")

    class _Annotation:
        primary_key = "id"
        foreign_keys = {
            "department_id": {
                "parent_schema": "DepartmentGet",
                "parent_column": "id",
                "cardinality": "N:1"
            },
            "account_id": {
                "parent_schema": "AccountGet",
                "parent_column": "id",
                "cardinality": "N:1"
            },
            "created_by": {
                "parent_schema": "UserGet",
                "parent_column": "id",
                "cardinality": "N:1"
            },
            "modified_by": {
                "parent_schema": "UserGet",
                "parent_column": "id",
                "cardinality": "N:1"
            }
        }
