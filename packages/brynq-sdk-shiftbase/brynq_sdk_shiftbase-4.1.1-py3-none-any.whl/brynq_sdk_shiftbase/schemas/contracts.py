"""
Schema definition for Contract data validation.
"""
from typing import Dict, List, Optional, Union
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
import re
from datetime import date
import pandera as pa
from pandera.typing import Series, DateTime, Date
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class ContractGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating Contract data returned from Shiftbase API.
    Each employee has their own contract, which defines working hours, job details, etc.
    """
    id: Series[str] = pa.Field(coerce=True, description="Unique identifier for the contract")
    user_id: Series[str] = pa.Field(coerce=True, description="User identifier")
    department_id: Series[str] = pa.Field(coerce=True, description="Department identifier")
    contract_type_id: Series[str] = pa.Field(coerce=True, description="Contract type identifier")
    start_date: Series[DateTime] = pa.Field(coerce=True, description="Start date of the contract", alias="startdate")
    end_date: Series[DateTime] = pa.Field(coerce=True, description="End date of the contract", nullable=True, alias="enddate")
    function: Series[str] = pa.Field(coerce=True, description="Job title", nullable=True)
    wage: Series[str] = pa.Field(coerce=True, description="Hourly wage", nullable=True)
    coc: Optional[Series[str]] = pa.Field(coerce=True, description="Cost of company factor", nullable=True)
    contract_hours: Series[str] = pa.Field(coerce=True, description="Total contract hours per week", nullable=True)
    mo: Series[str] = pa.Field(coerce=True, description="Monday hours", nullable=True)
    tu: Series[str] = pa.Field(coerce=True, description="Tuesday hours", nullable=True)
    we: Series[str] = pa.Field(coerce=True, description="Wednesday hours", nullable=True)
    th: Series[str] = pa.Field(coerce=True, description="Thursday hours", nullable=True)
    fr: Series[str] = pa.Field(coerce=True, description="Friday hours", nullable=True)
    sa: Series[str] = pa.Field(coerce=True, description="Saturday hours", nullable=True)
    su: Series[str] = pa.Field(coerce=True, description="Sunday hours", nullable=True)
    wage_tax: Series[bool] = pa.Field(coerce=True, description="Whether wage tax should be withheld", nullable=True)
    note: Series[str] = pa.Field(coerce=True, description="Additional notes", nullable=True)
    vacation_calc: Series[str] = pa.Field(coerce=True, description="Vacation calculation (deprecated)", nullable=True)

    class _Annotation:
        primary_key = "id"
        foreign_keys = {
            "user_id": {"parent_schema": "User", "parent_column": "id", "cardinality": "N:1"},
            "department_id": {"parent_schema": "Department", "parent_column": "id", "cardinality": "N:1"},
            "contract_type_id": {"parent_schema": "ContractType", "parent_column": "id", "cardinality": "N:1"}
        }

    class Config:
        coerce = True
        strict = False



class Contract(BaseModel):
    """
    Schema for validating Contract data returned from Shiftbase API.
    Each employee has their own contract, which defines working hours, job details, etc.
    """
    # Required fields
    id: Optional[str] = Field(
        description="The unique identifier of the contract",
        pattern=r"^[0-9]+$",
        default=None
    )
    user_id: str = Field(
        description="User identifier",
        pattern=r"^[0-9]+$"
    )
    department_id: str = Field(
        description="Department identifier",
        pattern=r"^[0-9]+$"
    )
    contract_type_id: str = Field(
        description="Id of the contract type",
        pattern=r"^[0-9]+$"
    )
    startdate: date = Field(
        description="Start date of the contract (YYYY-MM-DD)"
    )

    # Optional fields
    vacation_calc: Optional[str] = Field(
        description="Deprecated field",
        default="0.000000000"
    )
    function: Optional[str] = Field(
        description="Job title",
        default=""
    )
    mo: Optional[str] = Field(
        description="Hours scheduled to work on Monday",
        default="0.0000000"
    )
    tu: Optional[str] = Field(
        description="Hours scheduled to work on Tuesday",
        default="0.0000000"
    )
    we: Optional[str] = Field(
        description="Hours scheduled to work on Wednesday",
        default="0.0000000"
    )
    th: Optional[str] = Field(
        description="Hours scheduled to work on Thursday",
        default="0.0000000"
    )
    fr: Optional[str] = Field(
        description="Hours scheduled to work on Friday",
        default="0.0000000"
    )
    sa: Optional[str] = Field(
        description="Hours scheduled to work on Saturday",
        default="0.0000000"
    )
    su: Optional[str] = Field(
        description="Hours scheduled to work on Sunday",
        default="0.0000000"
    )
    enddate: Optional[date] = Field(
        description="End date of the contract (YYYY-MM-DD), null means indefinite",
        default=None
    )
    wage_tax: Optional[bool] = Field(
        description="Should the employer withold wage taxes",
        default=True
    )
    note: Optional[str] = Field(
        description="Additional notes",
        default=None
    )
    time_off_accrual: Optional[Dict[str, float]] = Field(
        description="Key-Value pair of the time off balance id with a build up factor",
    )
    wage: Optional[str] = Field(
        description="Hourly wage",
        default="0.00"
    )
    coc: Optional[Union[str, float, int]] = Field(
        description="Wage included Cost of Company",
        default="0.00"
    )
    contract_hours: Optional[str] = Field(
        description="Sum of the contract hours from the separate days",
        default="0.00"
    )
    day_list: Optional[List[int]] = Field(
        description="List of day numbers (1=Monday, 7=Sunday)",
    )

    @field_validator('mo', 'tu', 'we', 'th', 'fr', 'sa', 'su', 'wage', 'contract_hours')
    @classmethod
    def validate_numeric_string(cls, v):
        """Validates numeric string format"""
        if v is None:
            return "0.0000000"

        # Allow numeric strings like "0.00" or "12.3456789"
        numeric_pattern = r"^\d+(\.\d+)?$"
        if not re.match(numeric_pattern, v):
            raise ValueError(f"Invalid numeric string: {v}. Expected format: digits with optional decimal places")
        return v

    @field_validator('coc')
    @classmethod
    def validate_coc(cls, v):
        """Validates coc value - can be string, float or int"""
        if v is None:
            return "0.00"

        # If it's already a number, convert to string
        if isinstance(v, (int, float)):
            return str(v)

        # If it's a string, validate the format
        if isinstance(v, str):
            numeric_pattern = r"^\d+(\.\d+)?$"
            if not re.match(numeric_pattern, v):
                raise ValueError(f"Invalid coc value: {v}. Expected format: digits with optional decimal places")
            return v

        raise ValueError(f"Invalid coc type: {type(v)}. Expected string, float, or int")

    @field_validator('time_off_accrual')
    @classmethod
    def validate_time_off_accrual(cls, v):
        """Validates time_off_accrual structure"""
        if v is None:
            return {}

        # Check that all keys are valid UUIDs and values are numbers
        for key, value in v.items():
            try:
                UUID(key)
            except ValueError:
                raise ValueError(f"Invalid UUID as key in time_off_accrual: {key}")

            if not isinstance(value, (int, float)):
                raise ValueError(f"Invalid value in time_off_accrual: {value}. Expected numeric value")

        return v

    @field_validator('day_list')
    @classmethod
    def validate_day_list(cls, v):
        """Validates day_list values"""
        if v is None:
            return []

        # Check that all values are between 1 and 7
        for day in v:
            if not isinstance(day, int) or day < 1 or day > 7:
                raise ValueError(f"Invalid day in day_list: {day}. Expected an integer between 1 and 7")

        return v

    class Config:
        """Pydantic configuration"""
        extra = "ignore"  # Ignore extra fields


class ContractCreate(BaseModel):
    """
    Schema for validating Contract creation data.
    This schema is used when creating new contracts in Shiftbase.
    """
    # Required fields
    user_id: str = Field(description="User identifier", pattern=r"^[0-9]+$", example="12345")
    department_id: str = Field(description="Department identifier", pattern=r"^[0-9]+$", example="67890")
    contract_type_id: str = Field(description="Id of the contract type", pattern=r"^[0-9]+$", example="181928")
    start_date: date = Field(description="Start date of the contract (YYYY-MM-DD)", example="2024-01-01", alias="startdate")

    # Optional fields
    time_off_accrual: Optional[Dict[str, float]] = Field(description="Key-Value pair of the time off balance id with a build up factor", default=None, example={"123": 1.0})
    vacation_calc: Optional[str] = Field(description="Deprecated field", default="0.000000000", example="0.000000000")
    function: Optional[str] = Field(description="Job title", default="", example="Software Developer")
    mo: Optional[Union[str, int, float]] = Field(description="Hours scheduled to work on Monday", default="0.0000000", example="8.0")
    tu: Optional[Union[str, int, float]] = Field(description="Hours scheduled to work on Tuesday", default="0.0000000", example="8.0")
    we: Optional[Union[str, int, float]] = Field(description="Hours scheduled to work on Wednesday", default="0.0000000", example="8.0")
    th: Optional[Union[str, int, float]] = Field(description="Hours scheduled to work on Thursday", default="0.0000000", example="8.0")
    fr: Optional[Union[str, int, float]] = Field(description="Hours scheduled to work on Friday", default="0.0000000", example="8.0")
    sa: Optional[Union[str, int, float]] = Field(description="Hours scheduled to work on Saturday", default="0.0000000", example="0.0")
    su: Optional[Union[str, int, float]] = Field(description="Hours scheduled to work on Sunday", default="0.0000000", example="0.0")
    end_date: Optional[date] = Field(description="End date of the contract (YYYY-MM-DD), null means indefinite", default=None, example="2024-12-31", alias="enddate")
    wage_tax: Optional[bool] = Field(description="Should the employer withold wage taxes", default=True, example=True)
    note: Optional[str] = Field(description="Additional notes", default=None, example="Full-time contract")
    wage: Optional[Union[str, float]] = Field(description="Hourly wage", default="0.00", example="25.50")
    coc: Optional[Union[str, float, int]] = Field(description="Wage included Cost of Company", default="0.00", example="1.35")

    @field_validator('mo', 'tu', 'we', 'th', 'fr', 'sa', 'su')
    @classmethod
    def validate_day_hours(cls, v):
        """Validates and converts day hours to string format"""
        if v is None:
            return "0.0000000"

        # Convert numeric values to string
        if isinstance(v, (int, float)):
            return str(v)

        # Validate string format
        if isinstance(v, str):
            numeric_pattern = r"^\d+(\.\d+)?$"
            if not re.match(numeric_pattern, v):
                raise ValueError(f"Invalid numeric string: {v}. Expected format: digits with optional decimal places")
            return v

        raise ValueError(f"Invalid type: {type(v)}. Expected string, int, or float")

    @field_validator('wage')
    @classmethod
    def validate_wage(cls, v):
        """Validates wage value"""
        if v is None:
            return "0.00"

        # Convert numeric to string
        if isinstance(v, (int, float)):
            return str(v)

        # Validate string format
        if isinstance(v, str):
            numeric_pattern = r"^\d+(\.\d+)?$"
            if not re.match(numeric_pattern, v):
                raise ValueError(f"Invalid wage value: {v}. Expected format: digits with optional decimal places")
            return v

        raise ValueError(f"Invalid wage type: {type(v)}. Expected string, float, or int")

    @field_validator('coc')
    @classmethod
    def validate_coc(cls, v):
        """Validates coc value"""
        if v is None:
            return "0.00"

        # Convert numeric to string
        if isinstance(v, (int, float)):
            return str(v)

        # Validate string format
        if isinstance(v, str):
            numeric_pattern = r"^\d+(\.\d+)?$"
            if not re.match(numeric_pattern, v):
                raise ValueError(f"Invalid coc value: {v}. Expected format: digits with optional decimal places")
            return v

        raise ValueError(f"Invalid coc type: {type(v)}. Expected string, float, or int")

    @field_validator('time_off_accrual')
    @classmethod
    def validate_time_off_accrual(cls, v):
        """Validates time_off_accrual structure"""
        if v is None:
            return {}

        # Check that all keys are valid UUIDs and values are numbers
        for key, value in v.items():
            try:
                UUID(key)
            except ValueError:
                raise ValueError(f"Invalid UUID as key in time_off_accrual: {key}")

            if not isinstance(value, (int, float)):
                raise ValueError(f"Invalid value in time_off_accrual: {value}. Expected numeric value")

        return v

    class Config:
        """Pydantic configuration"""
        extra = "ignore"  # Ignore extra fields
        populate_by_name = True


class ContractUpdate(BaseModel):
    """
    Schema for validating Contract update data.
    This schema is used when updating existing contracts in Shiftbase.
    """
    # Required fields for update
    id: str = Field(description="The unique identifier of the contract", pattern=r"^[0-9]+$", coerce_numbers_to_str=True, example="12345")
    user_id: str = Field(description="User identifier", pattern=r"^[0-9]+$", example="12345")
    department_id: str = Field(description="Department identifier", pattern=r"^[0-9]+$", example="67890")
    contract_type_id: str = Field(description="Id of the contract type", pattern=r"^[0-9]+$", example="181928")
    start_date: date = Field(alias="startdate",description="Start date of the contract (YYYY-MM-DD)", example="2024-01-01")

    # Optional fields
    vacation_calc: Optional[str] = Field(description="Deprecated field", default="0.000000000", example="0.000000000")
    function: Optional[str] = Field(description="Job title", default="", example="Software Developer")
    mo: Optional[Union[str, int, float]] = Field(description="Hours scheduled to work on Monday", default="0.0000000", example="8.0")
    tu: Optional[Union[str, int, float]] = Field(description="Hours scheduled to work on Tuesday", default="0.0000000", example="8.0")
    we: Optional[Union[str, int, float]] = Field(description="Hours scheduled to work on Wednesday", default="0.0000000", example="8.0")
    th: Optional[Union[str, int, float]] = Field(description="Hours scheduled to work on Thursday", default="0.0000000", example="8.0")
    fr: Optional[Union[str, int, float]] = Field(description="Hours scheduled to work on Friday", default="0.0000000", example="8.0")
    sa: Optional[Union[str, int, float]] = Field(description="Hours scheduled to work on Saturday", default="0.0000000", example="0.0")
    su: Optional[Union[str, int, float]] = Field(description="Hours scheduled to work on Sunday", default="0.0000000", example="0.0")
    end_date: Optional[date] = Field(alias="enddate", description="End date of the contract (YYYY-MM-DD), null means indefinite", default=None, example="2024-12-31")
    wage_tax: Optional[bool] = Field(description="Should the employer withold wage taxes", default=True, example=True)
    note: Optional[str] = Field(description="Additional notes", default=None, example="Full-time contract")
    time_off_accrual: Optional[Dict[str, float]] = Field(description="Key-Value pair of the time off balance id with a build up factor", default=None, example={"123": 1.0})
    wage: Optional[Union[str, float]] = Field(description="Hourly wage", default="0.00", example="25.50")
    coc: Optional[Union[str, float, int]] = Field(description="Wage included Cost of Company", default="0.00", example="1.35")

    class Config:
        """Pydantic configuration"""
        extra = "ignore"  # Ignore extra fields
        populate_by_name = True
