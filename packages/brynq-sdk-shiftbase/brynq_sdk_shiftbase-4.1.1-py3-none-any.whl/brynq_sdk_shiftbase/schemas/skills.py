import pandera as pa
from pandera.typing import Series
from datetime import datetime
from brynq_sdk_functions import BrynQPanderaDataFrameModel


class SkillGet(BrynQPanderaDataFrameModel):
    """
    Validation schema for Skill data from Shiftbase API
    """
    id: Series[str] = pa.Field(coerce=True, description="The skill ID")
    account_id: Series[str] = pa.Field(coerce=True, description="The account ID")
    skill_group_id: Series[str] = pa.Field(coerce=True, description="The skill group ID")
    name: Series[str] = pa.Field(coerce=True, description="The name of the skill")
    created: Series[datetime] = pa.Field(coerce=True, description="The datetime when the skill has been created")
    updated: Series[datetime] = pa.Field(coerce=True, description="The datetime when the skill has been updated")
    created_by: Series[str] = pa.Field(coerce=True, description="Id of the employee that added this skill")
    modified_by: Series[str] = pa.Field(coerce=True, description="Id of the employee that modified this skill")
    deleted: Series[bool] = pa.Field(coerce=True, description="Indicates whether the skill has been deleted")

    class _Annotation:
        primary_key = "id"
        foreign_keys = {}


class SkillGroupGet(BrynQPanderaDataFrameModel):
    """
    Validation schema for Skill Group data from Shiftbase API
    """
    id: Series[str] = pa.Field(coerce=True, description="The skill group ID")
    account_id: Series[str] = pa.Field(coerce=True, description="The account ID")
    name: Series[str] = pa.Field(coerce=True, description="The name of the skill group")
    created: Series[datetime] = pa.Field(coerce=True, description="The datetime when the skill group has been created")
    updated: Series[datetime] = pa.Field(coerce=True, description="The datetime when the skill group has been updated")
    created_by: Series[str] = pa.Field(coerce=True, description="Id of the user that added this skill group")
    modified_by: Series[str] = pa.Field(coerce=True, description="Id of the user that modified this skill group")
    deleted: Series[bool] = pa.Field(coerce=True, description="Indicates whether the skill group has been deleted")

    class _Annotation:
        primary_key = "id"
        foreign_keys = {}
