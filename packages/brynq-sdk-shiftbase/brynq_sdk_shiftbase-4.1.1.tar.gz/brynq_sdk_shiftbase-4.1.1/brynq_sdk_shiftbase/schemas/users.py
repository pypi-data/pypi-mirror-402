import pandera as pa
from pandera.typing import Series
from typing import Optional, Any, Dict, List, Union
from pydantic import BaseModel, Field, field_validator
import re
from datetime import date, datetime
import pandas as pd
from brynq_sdk_functions import BrynQPanderaDataFrameModel


# ============================================================================
# PANDERA SCHEMAS (GET operations) - Inherit from BrynQPanderaDataFrameModel
# ============================================================================

class UserGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating User GET data from Shiftbase API
    """
    user_id: Series[str] = pa.Field(coerce=True, description="User ID", alias="User_id")
    account_id: Series[str] = pa.Field(coerce=True, description="Account ID", alias="User_account_id")
    first_name: Series[str] = pa.Field(coerce=True, description="First name of user", alias="User_first_name")
    prefix: Series[str] = pa.Field(coerce=True, description="Prefix of last name", alias="User_prefix")
    last_name: Series[str] = pa.Field(coerce=True, description="Last name of user", alias="User_last_name")
    avatar_file_name: Series[pd.StringDtype] = pa.Field(coerce=True, description="Avatar file name", alias="User_avatar_file_name", nullable=True)
    locale: Series[str] = pa.Field(coerce=True, description="The locale of the user", alias="User_locale")
    order: Series[str] = pa.Field(coerce=True, description="Used for sorting users", alias="User_order")
    start_date: Series[date] = pa.Field(coerce=True, description="Date the user is active in the system", alias="User_startdate")
    end_date: Series[date] = pa.Field(coerce=True, description="Date the user is inactive in the system", alias="User_enddate", nullable=True)
    anonymized: Series[pd.BooleanDtype] = pa.Field(coerce=True, description="Whether the user is anonymized", alias="User_anonymized")

    # Fields only with specific permissions
    street_address: Series[pd.StringDtype] = pa.Field(coerce=True, description="Street address", alias="User_street_address", nullable=True)
    post_code: Series[pd.StringDtype] = pa.Field(coerce=True, description="Postal code", alias="User_post_code", nullable=True)
    city: Series[pd.StringDtype] = pa.Field(coerce=True, description="City", alias="User_city", nullable=True)
    phone_nr: Series[pd.StringDtype] = pa.Field(coerce=True, description="Phone number", alias="User_phone_nr", nullable=True)
    mobile_nr: Series[pd.StringDtype] = pa.Field(coerce=True, description="Mobile number", alias="User_mobile_nr", nullable=True)
    emergency_nr: Series[pd.StringDtype] = pa.Field(coerce=True, description="Emergency contact number", alias="User_emergency_nr", nullable=True)
    email: Series[pd.StringDtype] = pa.Field(coerce=True, description="Email address of the user", alias="User_email", nullable=True)
    verified: Series[pd.BooleanDtype] = pa.Field(coerce=True, description="Whether the user is verified", alias="User_verified", nullable=True)
    hire_date: Series[pd.StringDtype] = pa.Field(coerce=True, description="Date the user is hired", alias="User_hire_date", nullable=True)
    birth_place: Series[pd.StringDtype] = pa.Field(coerce=True, description="Birthplace", alias="User_birthplace", nullable=True)
    birth_date: Series[pd.StringDtype] = pa.Field(coerce=True, description="Birth date", alias="User_birthdate", nullable=True)
    nationality: Series[pd.StringDtype] = pa.Field(coerce=True, description="Nationality of user", alias="User_nationality", nullable=True)
    ssn: Series[pd.StringDtype] = pa.Field(coerce=True, description="Social security number", alias="User_ssn", nullable=True)
    passport_number: Series[pd.StringDtype] = pa.Field(coerce=True, description="Document number of passport", alias="User_passport_number", nullable=True)
    banknr: Series[pd.StringDtype] = pa.Field(coerce=True, description="Bank number of user", alias="User_banknr", nullable=True)
    nr_of_logins: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Number of logins", alias="User_nr_of_logins", nullable=True)
    last_login: Series[datetime] = pa.Field(coerce=True, description="Date and time of last login", alias="User_last_login", nullable=True)
    employee_nr: Series[pd.StringDtype] = pa.Field(coerce=True, description="Employee number", alias="User_employee_nr", nullable=True)
    custom_fields: Series[object] = pa.Field(coerce=True, description="User custom fields", alias="User_custom_fields", nullable=True)
    roster_note: Series[pd.StringDtype] = pa.Field(coerce=True, description="Note that shows up in the schedule", alias="User_roster_note", nullable=True)
    invited: Series[pd.BooleanDtype] = pa.Field(coerce=True, description="Whether the user is invited", alias="User_invited", nullable=True)
    plus_min_hours: Series[pd.StringDtype] = pa.Field(coerce=True, description="Plus/minus hours", alias="User_plus_min_hours", nullable=True)
    birthday: Series[datetime] = pa.Field(coerce=True, description="User's birthday", alias="User_birthday", nullable=True)
    birthday_age: Series[pd.StringDtype] = pa.Field(coerce=True, description="User's age on birthday", alias="User_birthday_age", nullable=True)
    age: Series[pd.StringDtype] = pa.Field(coerce=True, description="User's age", alias="User_age", nullable=True)
    has_login: Series[pd.BooleanDtype] = pa.Field(coerce=True, description="Whether the user has login credentials", alias="User_has_login", nullable=True)
    mfa_enabled: Series[pd.BooleanDtype] = pa.Field(coerce=True, description="Whether multi-factor authentication is enabled", alias="User_mfa_enabled", nullable=True)

    # Auto-generated fields
    name: Series[str] = pa.Field(coerce=True, description="Full name of the user", alias="User_name")
    display_name: Series[str] = pa.Field(coerce=True, description="Display name of the user", alias="User_display_name")
    avatar_15x15: Series[str] = pa.Field(coerce=True, description="URL to 15x15 avatar image", alias="User_avatar_15x15")
    avatar_24x24: Series[str] = pa.Field(coerce=True, description="URL to 24x24 avatar image", alias="User_avatar_24x24")
    avatar_30x30: Series[str] = pa.Field(coerce=True, description="URL to 30x30 avatar image", alias="User_avatar_30x30")
    avatar_45x45: Series[str] = pa.Field(coerce=True, description="URL to 45x45 avatar image", alias="User_avatar_45x45")
    avatar_60x60: Series[str] = pa.Field(coerce=True, description="URL to 60x60 avatar image", alias="User_avatar_60x60")
    avatar_150x200: Series[str] = pa.Field(coerce=True, description="URL to 150x200 avatar image", alias="User_avatar_150x200")

    class _Annotation:
        primary_key = "user_id"
        foreign_keys = {}



class UserGetById(BrynQPanderaDataFrameModel):
    """
    Schema for validating User GET by ID data from Shiftbase API
    """
    user_id: Series[str] = pa.Field(coerce=True, description="User ID", alias="id")
    account_id: Series[str] = pa.Field(coerce=True, description="Account ID", alias="account_id")
    first_name: Series[str] = pa.Field(coerce=True, description="First name of user", alias="first_name")
    prefix: Series[str] = pa.Field(coerce=True, description="Prefix of last name", alias="prefix")
    last_name: Series[str] = pa.Field(coerce=True, description="Last name of user", alias="last_name")
    avatar_file_name: Series[pd.StringDtype] = pa.Field(coerce=True, description="Avatar file name", alias="avatar_file_name", nullable=True)
    locale: Series[str] = pa.Field(coerce=True, description="The locale of the user", alias="locale")
    order: Series[str] = pa.Field(coerce=True, description="Used for sorting users", alias="order")
    start_date: Series[date] = pa.Field(coerce=True, description="Date the user is active in the system", alias="startdate")
    end_date: Series[date] = pa.Field(coerce=True, description="Date the user is inactive in the system", alias="enddate", nullable=True)
    anonymized: Series[pd.BooleanDtype] = pa.Field(coerce=True, description="Whether the user is anonymized", alias="anonymized")

    # Fields only with specific permissions
    street_address: Series[pd.StringDtype] = pa.Field(coerce=True, description="Street address", alias="street_address", nullable=True)
    post_code: Series[pd.StringDtype] = pa.Field(coerce=True, description="Postal code", alias="post_code", nullable=True)
    city: Series[pd.StringDtype] = pa.Field(coerce=True, description="City", alias="city", nullable=True)
    phone_nr: Series[pd.StringDtype] = pa.Field(coerce=True, description="Phone number", alias="phone_nr", nullable=True)
    mobile_nr: Series[pd.StringDtype] = pa.Field(coerce=True, description="Mobile number", alias="mobile_nr", nullable=True)
    emergency_nr: Series[pd.StringDtype] = pa.Field(coerce=True, description="Emergency contact number", alias="emergency_nr", nullable=True)
    email: Series[pd.StringDtype] = pa.Field(coerce=True, description="Email address of the user", alias="email", nullable=True)
    verified: Series[pd.BooleanDtype] = pa.Field(coerce=True, description="Whether the user is verified", alias="verified", nullable=True)
    hire_date: Series[pd.StringDtype] = pa.Field(coerce=True, description="Date the user is hired", alias="hire_date", nullable=True)
    birthplace: Series[pd.StringDtype] = pa.Field(coerce=True, description="Birthplace", alias="birthplace", nullable=True)
    birthdate: Series[pd.StringDtype] = pa.Field(coerce=True, description="Birth date", alias="birthdate", nullable=True)
    nationality: Series[pd.StringDtype] = pa.Field(coerce=True, description="Nationality of user", alias="nationality", nullable=True)
    ssn: Series[pd.StringDtype] = pa.Field(coerce=True, description="Social security number", alias="ssn", nullable=True)
    passport_number: Series[pd.StringDtype] = pa.Field(coerce=True, description="Document number of passport", alias="passport_number", nullable=True)
    banknr: Series[pd.StringDtype] = pa.Field(coerce=True, description="Bank number of user", alias="banknr", nullable=True)
    nr_of_logins: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Number of logins", alias="nr_of_logins", nullable=True)
    last_login: Series[datetime] = pa.Field(coerce=True, description="Date and time of last login", alias="last_login", nullable=True)
    employee_nr: Series[pd.StringDtype] = pa.Field(coerce=True, description="Employee number", alias="employee_nr", nullable=True)
    custom_fields: Series[object] = pa.Field(coerce=True, description="User custom fields", alias="custom_fields", nullable=True)
    roster_note: Series[pd.StringDtype] = pa.Field(coerce=True, description="Note that shows up in the schedule", alias="roster_note", nullable=True)
    invited: Series[pd.BooleanDtype] = pa.Field(coerce=True, description="Whether the user is invited", alias="invited", nullable=True)
    plus_min_hours: Series[pd.StringDtype] = pa.Field(coerce=True, description="Plus/minus hours", alias="plus_min_hours", nullable=True)
    birthday: Series[datetime] = pa.Field(coerce=True, description="User's birthday", alias="birthday", nullable=True)
    birthday_age: Series[pd.StringDtype] = pa.Field(coerce=True, description="User's age on birthday", alias="birthday_age", nullable=True)
    age: Series[pd.StringDtype] = pa.Field(coerce=True, description="User's age", alias="age", nullable=True)
    has_login: Series[pd.BooleanDtype] = pa.Field(coerce=True, description="Whether the user has login credentials", alias="has_login", nullable=True)
    mfa_enabled: Series[pd.BooleanDtype] = pa.Field(coerce=True, description="Whether multi-factor authentication is enabled", alias="mfa_enabled", nullable=True)

    # Auto-generated fields
    name: Series[str] = pa.Field(coerce=True, description="Full name of the user", alias="name")
    display_name: Series[str] = pa.Field(coerce=True, description="Display name of the user", alias="display_name")
    avatar_15x15: Series[str] = pa.Field(coerce=True, description="URL to 15x15 avatar image", alias="avatar_15x15")
    avatar_24x24: Series[str] = pa.Field(coerce=True, description="URL to 24x24 avatar image", alias="avatar_24x24")
    avatar_30x30: Series[str] = pa.Field(coerce=True, description="URL to 30x30 avatar image", alias="avatar_30x30")
    avatar_45x45: Series[str] = pa.Field(coerce=True, description="URL to 45x45 avatar image", alias="avatar_45x45")
    avatar_60x60: Series[str] = pa.Field(coerce=True, description="URL to 60x60 avatar image", alias="avatar_60x60")
    avatar_150x200: Series[str] = pa.Field(coerce=True, description="URL to 150x200 avatar image", alias="avatar_150x200")

    class _Annotation:
        primary_key = "user_id"
        foreign_keys = {}


class UsersGroupGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating User Group GET data from Shiftbase API
    """
    id: Series[str] = pa.Field(coerce=True, description="User group ID", alias="id")
    department_id: Series[str] = pa.Field(coerce=True, description="Department ID", alias="department_id")
    user_id: Series[str] = pa.Field(coerce=True, description="User ID", alias="user_id")
    group_id: Series[str] = pa.Field(coerce=True, description="Group ID", alias="group_id")

    class _Annotation:
        primary_key = "id"
        foreign_keys = {
            "user_id": {
                "parent_schema": "UserGet",
                "parent_column": "user_id",
                "cardinality": "N:1"
            }
        }

# ============================================================================
# PYDANTIC SCHEMAS (Create/Update operations) - Inherit from BaseModel
# ============================================================================

class UserModel(BaseModel):
    """
    Pydantic validation schema for User data from Shiftbase API
    """
    id: str = Field(description="User ID")
    account_id: str = Field(description="Account ID")
    first_name: str = Field(description="First name of user")
    prefix: str = Field(description="Prefix of last name")
    last_name: str = Field(description="Last name of user")
    avatar_file_name: Optional[str] = Field(default=None, description="Avatar file name")
    locale: str = Field(description="The locale of the user", pattern=r"^(nl-NL|en-GB|fr-FR|de-DE|es-ES|pl-PL|sv-SE|ro-RO)$")
    order: str = Field(description="Used for sorting users")
    startdate: date = Field(description="Date the user is active in the system")
    enddate: Optional[date] = Field(default=None, description="Date the user is inactive in the system")
    anonymized: bool = Field(description="Whether the user is anonymized")

    # Fields only with specific permissions
    street_address: Optional[str] = Field(default=None, description="Street address")
    post_code: Optional[str] = Field(default=None, description="Postal code")
    city: Optional[str] = Field(default=None, description="City")
    phone_nr: Optional[str] = Field(default=None, description="Phone number")
    mobile_nr: Optional[str] = Field(default=None, description="Mobile number")
    emergency_nr: Optional[str] = Field(default=None, description="Emergency contact number")
    email: Optional[str] = Field(default=None, description="Email address of the user")
    verified: Optional[bool] = Field(default=None, description="Whether the user is verified")
    hire_date: Optional[date] = Field(default=None, description="Date the user is hired")
    birthplace: Optional[str] = Field(default=None, description="Birthplace")
    birthdate: Optional[date] = Field(default=None, description="Birth date")
    nationality: Optional[str] = Field(default=None, description="Nationality of user")
    ssn: Optional[str] = Field(default=None, description="Social security number")
    passport_number: Optional[str] = Field(default=None, description="Document number of passport")
    banknr: Optional[str] = Field(default=None, description="Bank number of user")
    nr_of_logins: Optional[int] = Field(default=None, description="Number of logins")
    last_login: Optional[datetime] = Field(default=None, description="Date and time of last login")
    employee_nr: Optional[str] = Field(default=None, description="Employee number")
    custom_fields: Optional[Union[Dict[str, Any], str]] = Field(default=None, description="User custom fields")
    roster_note: Optional[str] = Field(default=None, description="Note that shows up in the schedule")
    invited: Optional[bool] = Field(default=None, description="Whether the user is invited")
    plus_min_hours: Optional[str] = Field(default=None, description="Plus/minus hours")
    birthday: Optional[datetime] = Field(default=None, description="User's birthday")
    birthday_age: Optional[str] = Field(default=None, description="User's age on birthday")
    age: Optional[str] = Field(default=None, description="User's age")
    has_login: Optional[bool] = Field(default=None, description="Whether the user has login credentials")
    mfa_enabled: Optional[bool] = Field(default=None, description="Whether multi-factor authentication is enabled")

    # Auto-generated fields
    name: str = Field(description="Full name of the user")
    display_name: str = Field(description="Display name of the user")
    avatar_15x15: str = Field(description="URL to 15x15 avatar image")
    avatar_24x24: str = Field(description="URL to 24x24 avatar image")
    avatar_30x30: str = Field(description="URL to 30x30 avatar image")
    avatar_45x45: str = Field(description="URL to 45x45 avatar image")
    avatar_60x60: str = Field(description="URL to 60x60 avatar image")
    avatar_150x200: str = Field(description="URL to 150x200 avatar image")

    class Config:
        """Pydantic configuration"""
        extra = "ignore"  # Ignore extra fields

class UsersGroupModel(BaseModel):
    """
    Pydantic validation schema for User Group data from Shiftbase API
    """
    id: str = Field(description="User group ID")
    department_id: str = Field(description="Department ID")
    user_id: str = Field(description="User ID")
    group_id: str = Field(description="Group ID")

    @field_validator('id', 'department_id', 'user_id', 'group_id')
    @classmethod
    def validate_id_format(cls, v):
        """Validates IDs are numeric strings."""
        if not re.match(r"^[0-9]+$", v):
            raise ValueError(f"Invalid ID format: {v}. Expected numeric string.")
        return v

    class Config:
        """Pydantic configuration"""
        extra = "ignore"  # Ignore extra fields

class TeamModel(BaseModel):
    """
    Pydantic validation schema for Team data from Shiftbase API
    """
    id: str = Field(description="The unique identifier for the team", pattern=r"^[0-9]+$")
    account_id: str = Field(default=None,description="The account ID to which this team belongs to", pattern=r"^[0-9]+$")
    department_id: str = Field(description="The department ID this team belongs to", pattern=r"^[0-9]+$")
    name: str = Field(description="The name of the team", min_length=1)
    color: str = Field(description="This must be a valid hexadecimal color like '#FFFFFF' for white", min_length=1)
    order: str = Field(description="In which order the teams are displayed", pattern=r"^[0-9]+$")
    created: datetime = Field(default=None,description="When the team was created")
    created_by: Optional[str] = Field(default=None, description="The user ID that created the team", pattern=r"^[0-9]+$")
    updated: datetime = Field(default=None,description="When the team was last updated")
    modified_by: Optional[str] = Field(default=None, description="The user ID that last updated the team", pattern=r"^[0-9]+$")
    deleted: bool = Field(default=False, description="If the team is deleted")
    deleted_date: Optional[datetime] = Field(default=None, description="When the team was deleted")
    hidden: bool = Field(default=False, description="Whether the team is hidden")
    type: str = Field(
        default="default",
        description="default: The team is shown in the schedule an timesheet. "
                   "flexpool: The team is not shown, but the employees within this team can be scheduled in the standard teams. "
                   "hidden: The team is not shown in the schedule and the timesheet, but it is shown in the list of employees.",
        pattern=r"^(default|flexpool|hidden)$"
    )

    @field_validator('color')
    @classmethod
    def validate_color(cls, v):
        """Validates hexadecimal color format"""
        color_pattern = r"^#[0-9A-Fa-f]{6}$"
        if not re.match(color_pattern, v):
            raise ValueError(f"Invalid color format: {v}. Expected format: #RRGGBB (e.g. #FFFFFF)")
        return v

    class Config:
        """Pydantic configuration"""
        extra = "ignore"  # Ignore extra fields
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class User(BaseModel):
    """Pydantic model for User response"""
    User: Optional[UserModel] = Field(None)
    UsersGroup: Optional[List[UsersGroupModel]] = Field(default_factory=list)
    Team: Optional[List[TeamModel]] = Field(default_factory=list)
    Skill: Optional[List] = Field(default_factory=list)

class UserCreate(BaseModel):
    """
    Schema for validating User creation data.
    This schema is used when creating new users in Shiftbase.
    """
    # Required fields
    first_name: str = Field(description="First name of user")
    last_name: str = Field(description="Last name of user")
    locale: str = Field(
        description="The locale of the user, in RFC5646 format",
        pattern=r"^(nl-NL|en-GB|fr-FR|de-DE|es-ES|pl-PL|sv-SE|ro-RO)$"
    )
    start_date: date = Field(description="Date the user is active in the system", alias="startdate")
    email: str = Field(description="Email address of the user")
    team_id: Optional[str] = Field(default=None, description="Team ID for the user")
    department_id: Optional[str] = Field(default=None, description="Department ID for the user")

    # Optional fields
    prefix: Optional[str] = Field(default="", description="Prefix of last name")
    order: Optional[str] = Field(default="50", description="Used for sorting users")
    end_date: Optional[date] = Field(default=None, description="Date the user is inactive in the system", alias="enddate")
    street_address: Optional[str] = Field(default=None, description="Street address")
    post_code: Optional[str] = Field(default=None, description="Postal code")
    city: Optional[str] = Field(default=None, description="City")
    phone_nr: Optional[str] = Field(default=None, description="Phone number")
    mobile_nr: Optional[str] = Field(default=None, description="Mobile number")
    emergency_nr: Optional[str] = Field(default=None, description="Emergency contact number")
    hire_date: Optional[date] = Field(default=None, description="Date the user is hired")
    birth_place: Optional[str] = Field(default=None, description="Birthplace", alias="birthplace")
    birth_date: Optional[date] = Field(default=None, description="Birth date", alias="birthdate")
    nationality: Optional[str] = Field(default=None, description="Nationality of user")
    ssn: Optional[str] = Field(default=None, description="Social security number")
    passport_number: Optional[str] = Field(default=None, description="Document number of passport")
    banknr: Optional[str] = Field(default=None, description="Bank number of user")
    employee_nr: Optional[str] = Field(default=None, description="Employee number")
    custom_fields: Optional[Union[Dict[str, Any], str]] = Field(default=None, description="User custom fields")
    roster_note: Optional[str] = Field(default=None, description="Note that shows up in the schedule")
    invited: Optional[bool] = Field(default=False, description="Whether the user is invited")
    notify_employee: Optional[bool] = Field(default=False, description="Whether to notify the employee")
    plus_min_hours: Optional[str] = Field(default=None, description="Plus min hours of user")
    birthday: Optional[date] = Field(default=None, description="Date of the next birthday", alias="birthday")
    birthday_age: Optional[str] = Field(default=None, description="Age of the user on birthday date")
    age: Optional[str] = Field(default=None, description="Age of the user")
    minijob: Optional[bool] = Field(default=False, description="Whether the employee is currently on a minijob contract")

    # Contract fields - Defining what contracts the user should have
    contract: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of contracts for the user"
    )

    # Team membership
    team: Optional[List[Union[str, int]]] = Field(
        default=None,
        description="List of team IDs the user belongs to"
    )

    # Group membership
    users_group: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="User group memberships"
    )

    # Skills
    skill: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="User skills"
    )

    class Config:
        """Pydantic configuration"""
        extra = "ignore"  # Ignore extra fields
        populate_by_name = True

class UserUpdate(BaseModel):
    """
    Schema for validating User update data.
    This schema is used when updating existing users in Shiftbase.
    """
    # Optional fields - all fields are optional for update
    first_name: Optional[str] = Field(default=None, description="First name of user")
    prefix: Optional[str] = Field(default=None, description="Prefix of last name")
    last_name: Optional[str] = Field(default=None, description="Last name of user")
    locale: Optional[str] = Field(
        default=None,
        description="The locale of the user, in RFC5646 format",
        pattern=r"^(nl-NL|en-GB|fr-FR|de-DE|es-ES|pl-PL|sv-SE|ro-RO)$"
    )
    order: Optional[str] = Field(default=None, description="Used for sorting users")
    start_date: Optional[date] = Field(default=None, description="Date the user is active in the system", alias="startdate")
    end_date: Optional[date] = Field(default=None, description="Date the user is inactive in the system", alias="enddate")
    street_address: Optional[str] = Field(default=None, description="Street address")
    post_code: Optional[str] = Field(default=None, description="Postal code")
    city: Optional[str] = Field(default=None, description="City")
    phone_nr: Optional[str] = Field(default=None, description="Phone number")
    mobile_nr: Optional[str] = Field(default=None, description="Mobile number")
    emergency_nr: Optional[str] = Field(default=None, description="Emergency contact number")
    email: Optional[str] = Field(default=None, description="Email address of the user")
    hire_date: Optional[date] = Field(default=None, description="Date the user is hired")
    birth_place: Optional[str] = Field(default=None, description="Birthplace", alias="birthplace")
    birth_date: Optional[date] = Field(default=None, description="Birth date", alias="birthdate")
    nationality: Optional[str] = Field(default=None, description="Nationality of user")
    ssn: Optional[str] = Field(default=None, description="Social security number")
    passport_number: Optional[str] = Field(default=None, description="Document number of passport")
    banknr: Optional[str] = Field(default=None, description="Bank number of user")
    employee_nr: Optional[str] = Field(default=None, description="Employee number")
    custom_fields: Optional[Union[Dict[str, Any], str]] = Field(default=None, description="User custom fields")
    roster_note: Optional[str] = Field(default=None, description="Note that shows up in the schedule")
    invited: Optional[bool] = Field(default=None, description="Whether the user is invited")
    plus_min_hours: Optional[str] = Field(default=None, description="Plus min hours of user")
    birthday: Optional[date] = Field(default=None, description="Date of the next birthday", alias="birthday")
    birthday_age: Optional[str] = Field(default=None, description="Age of the user on birthday date")
    age: Optional[str] = Field(default=None, description="Age of the user")
    minijob: Optional[bool] = Field(default=None, description="Whether the employee is currently on a minijob contract")

    class Config:
        """Pydantic configuration"""
        extra = "ignore"  # Ignore extra fields
        populate_by_name = True


# BrynQ SDK Pandera Schemas for Employees class
import pandera as pa
from pandera.typing import Series, Date, DateTime
from brynq_sdk_functions import BrynQPanderaDataFrameModel


class TimeOffBalanceDetailsGet(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating Time Off Balance Details GET data.
    This schema is used when retrieving time off balance details from Shiftbase.
    """
    # Main balance information
    time_off_balance_id: Series[str] = pa.Field(coerce=True, description="Time off balance identifier", alias="timeOffBalanceId")
    time_off_balance_name: Series[str] = pa.Field(coerce=True, description="Name of the time off balance", alias="timeOffBalanceName")
    end_date: Series[str] = pa.Field(coerce=True, description="End date of the balance period", alias="endDate")
    percentage: Series[float] = pa.Field(coerce=True, description="Percentage of the balance", alias="percentage")
    total: Series[float] = pa.Field(coerce=True, description="Total balance amount", alias="total")
    unit: Series[str] = pa.Field(coerce=True, description="Unit of measurement (hours, days)", alias="unit")

    # Accrual information (json_normalize creates these field names)
    accrued: Series[float] = pa.Field(coerce=True, description="Accrued amount", alias="accrual.accrued")
    carryover: Series[float] = pa.Field(coerce=True, description="Carryover amount", alias="accrual.carryover")
    forecast: Series[float] = pa.Field(coerce=True, description="Forecast amount", alias="accrual.forecast")
    accrual_total: Series[float] = pa.Field(coerce=True, description="Total accrual amount", alias="accrual.total")

    # Used information (json_normalize creates these field names)
    used_pending: Series[float] = pa.Field(coerce=True, description="Pending used amount", alias="used.pending")
    used_pending_wait_hours: Series[float] = pa.Field(coerce=True, description="Pending wait hours", alias="used.pendingWaitHours")
    used_taken: Series[float] = pa.Field(coerce=True, description="Taken amount", alias="used.taken")
    used_total: Series[float] = pa.Field(coerce=True, description="Total used amount", alias="used.total")
    used_wait_hours: Series[float] = pa.Field(coerce=True, description="Wait hours", alias="used.waitHours")

    # Corrected information (json_normalize creates these field names)
    corrected_total_days: Series[float] = pa.Field(coerce=True, description="Total corrected days", alias="corrected.totalDays")
    corrected_total_hours: Series[float] = pa.Field(coerce=True, description="Total corrected hours", alias="corrected.totalHours")

    # Expiries (will be handled as JSON/object since it's an array)
    expiries: Series[object] = pa.Field(coerce=True, description="List of expiries", alias="expiries", nullable=True)

    class _Annotation:
        primary_key = "time_off_balance_id"
        foreign_keys = {
            "time_off_balance_id": {
                "parent_schema": "TimeOffBalanceGet",
                "parent_column": "id",
                "cardinality": "N:1"
            }
        }

    class Config:
        coerce = True
        strict = False


class TimeOffBalanceExpiriesGet(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating Time Off Balance Expiries GET data.
    This schema is used when retrieving time off balance expiries from Shiftbase.
    """
    id: Series[str] = pa.Field(coerce=True, description="Time off balance expiry identifier")
    user_id: Series[str] = pa.Field(coerce=True, description="User identifier")
    balance_id: Series[str] = pa.Field(coerce=True, description="Balance identifier", nullable=True)
    balance_name: Series[str] = pa.Field(coerce=True, description="Balance name", nullable=True)
    total: Series[float] = pa.Field(coerce=True, description="Total balance", nullable=True)
    used: Series[float] = pa.Field(coerce=True, description="Used balance", nullable=True)
    remaining: Series[float] = pa.Field(coerce=True, description="Remaining balance", nullable=True)
    expire_date: Series[Date] = pa.Field(coerce=True, description="Expiration date", nullable=True)
    days_until_expiry: Series[int] = pa.Field(coerce=True, description="Days until expiry", nullable=True)

    class _Annotation:
        primary_key = "id"
        foreign_keys = {
            "user_id": {
                "parent_schema": "UserGet",
                "parent_column": "id",
                "cardinality": "N:1"
            },
            "balance_id": {
                "parent_schema": "TimeOffBalanceGet",
                "parent_column": "id",
                "cardinality": "N:1"
            }
        }

    class Config:
        coerce = True
        strict = False
