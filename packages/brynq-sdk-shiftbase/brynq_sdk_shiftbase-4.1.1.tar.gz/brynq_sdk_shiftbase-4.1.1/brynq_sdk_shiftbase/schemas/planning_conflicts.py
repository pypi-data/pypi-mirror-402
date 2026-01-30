import pandera as pa
from pandera.typing import Series
import pandas as pd
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class PlanningConflictGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating Planning Conflict data from Shiftbase API
    """
    occurrence_id: Series[str] = pa.Field(coerce=True, description="Occurrence identifier for the conflict")
    employee_id: Series[str] = pa.Field(coerce=True, description="Employee ID involved in the conflict")
    topic: Series[str] = pa.Field(coerce=True, isin=["availability", "schedule", "skill", "timeoff"], description="Type of conflict")
    message: Series[str] = pa.Field(coerce=True, description="Conflict message or description")

    @pa.check("employee_id")
    def check_employee_id_format(cls, series: Series[str]) -> Series[bool]:
        """Validate employee ID is a numeric string."""
        valid = series.str.match(r"^[0-9]+$") | series.isna()
        return valid

    @pa.check("occurrence_id")
    def check_occurrence_id_format(cls, series: Series[str]) -> Series[bool]:
        """Validate occurrence_id format: ID:YYYY-MM-DD"""
        valid = series.str.match(r"^[0-9]+:[0-9]{4}-[0-9]{2}-[0-9]{2}$") | series.isna()
        return valid

    class _Annotation:
        primary_key = "occurrence_id"
        foreign_keys = {
            "employee_id": {
                "parent_schema": "EmployeeGet",
                "parent_column": "id",
                "cardinality": "N:1"
            }
        }

class EmployabilityGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating Employability data from Shiftbase API
    """
    employee_id: Series[str] = pa.Field(coerce=True, description="Employee ID", alias="employeeId")
    employable: Series[bool] = pa.Field(coerce=True, description="Whether the employee is employable")

    @pa.check("employee_id")
    def check_employee_id_format(cls, series: Series[str]) -> Series[bool]:
        """Validate employee ID is a numeric string."""
        valid = series.str.match(r"^[0-9]+$") | series.isna()
        return valid

    class _Annotation:
        primary_key = "employee_id"
        foreign_keys = {
            "employee_id": {
                "parent_schema": "EmployeeGet",
                "parent_column": "id",
                "cardinality": "1:1"
            }
        }
