import pandera as pa
from pandera.typing import Series
import pandas as pd
from datetime import date as date_type
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class InsightDetailGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating Insight Detail data from Shiftbase API
    """
    amount: Series[float] = pa.Field(coerce=True, description="The actual amount")
    target: Series[float] = pa.Field(coerce=True, description="The target amount")
    delta_percentage: Series[float] = pa.Field(coerce=True, description="The percentage difference from target", alias="deltaPercentage")
    status: Series[str] = pa.Field(coerce=True, isin=["on", "near", "off"], description="Status indicating target achievement")

    class _Annotation:
        primary_key = "amount"  # Using amount as primary identifier for detail records

class DepartmentInsightGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating Department Insight data from Shiftbase API
    """
    department_id: Series[str] = pa.Field(coerce=True, description="The department ID", alias="departmentId")

    @pa.check("department_id")
    def check_id_format(cls, series: Series[str]) -> Series[bool]:
        """Validate IDs are numeric strings."""
        valid = series.str.match(r"^[0-9]+$") | series.isna()
        return valid

    class _Annotation:
        primary_key = "department_id"
        foreign_keys = {
            "department_id": {
                "parent_schema": "DepartmentGet",
                "parent_column": "id",
                "cardinality": "N:1"
            }
        }

class TeamInsightGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating Team Insight data from Shiftbase API
    """
    department_id: Series[str] = pa.Field(coerce=True, description="The department ID", alias="departmentId")
    team_id: Series[str] = pa.Field(coerce=True, description="The team ID", alias="teamId")

    @pa.check("department_id", "team_id")
    def check_id_format(cls, series: Series[str]) -> Series[bool]:
        """Validate IDs are numeric strings."""
        valid = series.str.match(r"^[0-9]+$") | series.isna()
        return valid

    class _Annotation:
        primary_key = "team_id"
        foreign_keys = {
            "department_id": {
                "parent_schema": "DepartmentGet",
                "parent_column": "id",
                "cardinality": "N:1"
            },
            "team_id": {
                "parent_schema": "TeamGet",
                "parent_column": "id",
                "cardinality": "N:1"
            }
        }

class ScheduleInsightDayGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating Schedule Insight Day data from Shiftbase API
    """
    date: Series[date_type] = pa.Field(coerce=True, description="The date of the insight")
    department_id: Series[str] = pa.Field(coerce=True, regex=r"^[0-9]+$", description="The department ID", alias="departmentId")

    class _Annotation:
        primary_key = "date"
        foreign_keys = {
            "department_id": {
                "parent_schema": "DepartmentGet",
                "parent_column": "id",
                "cardinality": "N:1"
            }
        }

class ScheduleInsightTotalGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating Schedule Insight Total data from Shiftbase API
    """
    department_id: Series[str] = pa.Field(coerce=True, regex=r"^[0-9]+$", description="The department ID", alias="departmentId")

    class _Annotation:
        primary_key = "department_id"
        foreign_keys = {
            "department_id": {
                "parent_schema": "DepartmentGet",
                "parent_column": "id",
                "cardinality": "N:1"
            }
        }
