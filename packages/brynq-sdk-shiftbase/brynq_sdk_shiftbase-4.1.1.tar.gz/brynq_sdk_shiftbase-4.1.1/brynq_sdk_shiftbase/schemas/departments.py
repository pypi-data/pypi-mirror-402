"""
Department schemas for Shiftbase SDK.

This module contains Pandera schemas for validating Department data from Shiftbase API.
All schemas follow BrynQ SDK standards and inherit from BrynQPanderaDataFrameModel.
"""

import pandera as pa
from pandera.typing import Series, Date, DateTime
from brynq_sdk_functions import BrynQPanderaDataFrameModel


class DepartmentGet(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating Department GET data.
    This schema is used when retrieving departments from Shiftbase.
    """
    id: Series[str] = pa.Field(coerce=True, description="Unique identifier for the department")
    account_id: Series[str] = pa.Field(coerce=True, description="Account identifier", nullable=True)
    name: Series[str] = pa.Field(coerce=True, description="Department name")
    location_id: Series[str] = pa.Field(coerce=True, description="Location identifier", nullable=True)
    address: Series[str] = pa.Field(coerce=True, description="Department address", nullable=True)
    longitude: Series[str] = pa.Field(coerce=True, description="Longitude of the department's location", nullable=True)
    latitude: Series[str] = pa.Field(coerce=True, description="Latitude of the department's location", nullable=True)
    holiday_group_id: Series[str] = pa.Field(coerce=True, description="UUID of the holiday group", nullable=True)
    order: Series[str] = pa.Field(coerce=True, description="Used for sorting departments", nullable=True)
    price: Series[str] = pa.Field(coerce=True, description="Price information", nullable=True)
    timesheet_copy_starttime: Series[str] = pa.Field(coerce=True, description="Copy starttime from shift", nullable=True)
    timesheet_copy_endtime: Series[str] = pa.Field(coerce=True, description="Copy endtime from shift", nullable=True)
    break_rule_type: Series[str] = pa.Field(coerce=True, description="Break rule type", nullable=True)
    timesheet_surcharges: Series[bool] = pa.Field(coerce=True, description="Show surcharges in timesheet", nullable=True)
    meal_registration: Series[bool] = pa.Field(coerce=True, description="Show meal registration in timesheet", nullable=True)
    km_registration: Series[bool] = pa.Field(coerce=True, description="Show km-registration in timesheet", nullable=True)
    timesheet_copy_schedule: Series[bool] = pa.Field(coerce=True, description="Copy schedule to timesheet", nullable=True)
    timesheet_interval: Series[str] = pa.Field(coerce=True, description="Timesheet interval in minutes", nullable=True)
    break_interval: Series[str] = pa.Field(coerce=True, description="Break interval in minutes", nullable=True)
    round_clock_in: Series[str] = pa.Field(coerce=True, description="Clock in rounding method", nullable=True)
    round_clock_out: Series[str] = pa.Field(coerce=True, description="Clock out rounding method", nullable=True)
    round_clock_break: Series[str] = pa.Field(coerce=True, description="Break time rounding method", nullable=True)
    clock_out_after: Series[str] = pa.Field(coerce=True, description="Auto clock-out after hours", nullable=True)
    approve_clock: Series[str] = pa.Field(coerce=True, description="Clock approval settings", nullable=True)
    allow_clock_in_without_roster: Series[bool] = pa.Field(coerce=True, description="Allow clock in without roster", nullable=True)
    approve_schedule: Series[bool] = pa.Field(coerce=True, description="Auto approve scheduled hours", nullable=True)
    split_clocked_shifts: Series[str] = pa.Field(coerce=True, description="Split clocked shifts after minutes", nullable=True)
    default_clock_shift: Series[str] = pa.Field(coerce=True, description="Default clock shift ID", nullable=True)
    send_availability_reminder: Series[bool] = pa.Field(coerce=True, description="Send availability reminders", nullable=True)
    reminder_days_before: Series[str] = pa.Field(coerce=True, description="Reminder days before week start", nullable=True)
    lock_availability_days_before_period: Series[str] = pa.Field(coerce=True, description="Lock availability days before period", nullable=True)
    required_days_per_week: Series[str] = pa.Field(coerce=True, description="Required available days per week", nullable=True)
    publish_schedules: Series[str] = pa.Field(coerce=True, description="Publish schedules days ahead", nullable=True)
    show_open_shifts: Series[bool] = pa.Field(coerce=True, description="Show open shift option", nullable=True)
    show_required_shifts: Series[bool] = pa.Field(coerce=True, description="Show required shift option", nullable=True)
    deleted: Series[bool] = pa.Field(coerce=True, description="Whether the department is deleted", nullable=True)
    deleted_date: Series[DateTime] = pa.Field(coerce=True, description="Date when the department was deleted", nullable=True)
    created: Series[DateTime] = pa.Field(coerce=True, description="Creation timestamp", nullable=True)
    updated: Series[DateTime] = pa.Field(coerce=True, description="Last update timestamp", nullable=True)
    created_by: Series[str] = pa.Field(coerce=True, description="ID of the user who created the department", nullable=True)
    modified_by: Series[str] = pa.Field(coerce=True, description="ID of the user who last modified the department", nullable=True)
    availability_deadline_amount: Series[float] = pa.Field(coerce=True, description="Availability deadline amount", nullable=True)
    availability_deadline_type: Series[str] = pa.Field(coerce=True, description="Availability deadline type", nullable=True)
    availability_enabled: Series[bool] = pa.Field(coerce=True, description="Availability enabled", nullable=True)
    availability_maximum_unavailability_days_per_week: Series[str] = pa.Field(coerce=True, description="Maximum unavailability days per week", nullable=True)
    availability_minimum_availability_days_per_week: Series[str] = pa.Field(coerce=True, description="Minimum availability days per week", nullable=True)
    availability_reminder_days_before: Series[str] = pa.Field(coerce=True, description="Availability reminder days before", nullable=True)
    availability_send_availability_reminder: Series[str] = pa.Field(coerce=True, description="Send availability reminder", nullable=True)
    round_break_shift: Series[str] = pa.Field(coerce=True, description="Round break shift", nullable=True)
    timesheet_break_calculation: Series[str] = pa.Field(coerce=True, description="Timesheet break calculation", nullable=True)
    timesheet_sentiment_tracking: Series[bool] = pa.Field(coerce=True, description="Timesheet sentiment tracking", nullable=True)

    class _Annotation:
        primary_key = "id"

    class Config:
        coerce = True
        strict = False


class DepartmentEmployeeGet(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating Department Employee GET data.
    This schema is used when retrieving department employees from Shiftbase.
    """
    id: Series[str] = pa.Field(coerce=True, description="Employee identifier")
    full_name: Series[str] = pa.Field(coerce=True, description="Full name of the employee", alias="fullName")
    team_id: Series[str] = pa.Field(coerce=True, description="Team identifier", nullable=True, alias="teamId")
    type: Series[str] = pa.Field(coerce=True, description="Employee type", nullable=True)

    class _Annotation:
        primary_key = "id"
        foreign_keys = {
            "team_id": {
                "parent_schema": "TeamGet",
                "parent_column": "id",
                "cardinality": "N:1"
            }
        }

    class Config:
        coerce = True
        strict = False


class DepartmentTargetGet(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating Department Target GET data.
    This schema is used when retrieving department targets from Shiftbase.
    """
    start_date: Series[Date] = pa.Field(coerce=True, description="Start date for the target", alias="startDate")
    end_date: Series[Date] = pa.Field(coerce=True, description="End date for the target", alias="endDate")
    productivity: Series[float] = pa.Field(coerce=True, description="Productivity target", nullable=True)
    average_hourly_wage: Series[float] = pa.Field(coerce=True, description="Average hourly wage target", nullable=True, alias="averageHourlyWage")
    labor_cost_percentage: Series[float] = pa.Field(coerce=True, description="Labor cost percentage target", nullable=True, alias="laborCostPercentage")
    created: Series[DateTime] = pa.Field(coerce=True, description="The datetime when the target was created", nullable=True)
    modified: Series[DateTime] = pa.Field(coerce=True, description="The datetime when the target was last modified", nullable=True)
    created_by: Series[str] = pa.Field(coerce=True, description="ID of the user that created this target", nullable=True, alias="createdBy")
    modified_by: Series[str] = pa.Field(coerce=True, description="ID of the user that last modified this target", nullable=True, alias="modifiedBy")

    class _Annotation:
        primary_key = "start_date"
        foreign_keys = {
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

    class Config:
        coerce = True
        strict = False
