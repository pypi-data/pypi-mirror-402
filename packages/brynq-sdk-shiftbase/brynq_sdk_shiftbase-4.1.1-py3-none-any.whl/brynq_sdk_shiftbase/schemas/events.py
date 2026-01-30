"""
Event schemas for Shiftbase SDK.

This module contains Pandera schemas for validating Event data from Shiftbase API.
All schemas follow BrynQ SDK standards and inherit from BrynQPanderaDataFrameModel.
"""

import pandera as pa
from pandera.typing import Series, Date, DateTime
from brynq_sdk_functions import BrynQPanderaDataFrameModel


class EventGet(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating Event GET data.
    This schema is used when retrieving events from Shiftbase.
    """
    id: Series[str] = pa.Field(coerce=True, description="Event identifier", nullable=True)
    department_id: Series[str] = pa.Field(coerce=True, description="Department identifier")
    sequence_id: Series[str] = pa.Field(coerce=True, description="Sequence identifier", nullable=True)
    account_id: Series[str] = pa.Field(coerce=True, description="Account identifier", nullable=True)
    date: Series[Date] = pa.Field(coerce=True, description="Date when the event takes place", nullable=True)
    start_time: Series[str] = pa.Field(coerce=True, description="Time when the event starts", alias="starttime")
    end_time: Series[str] = pa.Field(coerce=True, description="Time when the event ends", alias="endtime")
    title: Series[str] = pa.Field(coerce=True, description="Title of the event")
    team_id: Series[str] = pa.Field(coerce=True, description="Team identifier", nullable=True)
    description: Series[str] = pa.Field(coerce=True, description="Description of the event", nullable=True)
    deleted: Series[bool] = pa.Field(coerce=True, description="Whether the event is deleted", nullable=True)
    created: Series[DateTime] = pa.Field(coerce=True, description="Creation timestamp", nullable=True)
    updated: Series[DateTime] = pa.Field(coerce=True, description="Last update timestamp", nullable=True)
    created_by: Series[str] = pa.Field(coerce=True, description="ID of the user who created the event", nullable=True)
    modified_by: Series[str] = pa.Field(coerce=True, description="ID of the user who last modified the event", nullable=True)
    start_seconds: Series[int] = pa.Field(coerce=True, description="Start time in timestamp", nullable=True)
    end_seconds: Series[int] = pa.Field(coerce=True, description="End time in timestamp", nullable=True)

    class _Annotation:
        primary_key = "id"
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

    class Config:
        coerce = True
        strict = False
