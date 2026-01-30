"""
Schema definition for Team data validation.
"""
import pandera as pa
from pandera.typing import Series
from datetime import datetime
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class TeamGet(BrynQPanderaDataFrameModel):
    """
    Validation schema for Team data from Shiftbase API
    """
    id: Series[str] = pa.Field(coerce=True, description="Team ID")
    account_id: Series[str] = pa.Field(nullable=True, coerce=True, description="Account ID")
    department_id: Series[str] = pa.Field(coerce=True, description="Department ID")
    name: Series[str] = pa.Field(coerce=True, description="Team name")
    color: Series[str] = pa.Field(coerce=True, description="Team color")
    order: Series[str] = pa.Field(nullable=True, coerce=True, description="Team order")
    created: Series[datetime] = pa.Field(nullable=True, coerce=True, description="Creation date")
    created_by: Series[str] = pa.Field(nullable=True, coerce=True, description="Created by user ID")
    modified_by: Series[str] = pa.Field(nullable=True, coerce=True, description="Modified by user ID")
    deleted: Series[bool] = pa.Field(nullable=True, coerce=True, description="Deleted flag")
    deleted_date: Series[datetime] = pa.Field(nullable=True, coerce=True, description="Deletion date")
    hidden: Series[bool] = pa.Field(nullable=True, coerce=True, description="Hidden flag")
    type: Series[str] = pa.Field(nullable=True, coerce=True, description="Team type")

    @pa.check("color")
    def check_color_format(cls, series: Series[str]) -> Series[bool]:
        """Validate color is in hexadecimal format."""
        valid = series.str.match(r"^#[0-9A-Fa-f]{6}$")
        return valid

    @pa.check("type")
    def check_type_values(cls, series: Series[str]) -> Series[bool]:
        """Validate type field has correct value."""
        valid = series.str.match(r"^(default|flexpool|hidden)$") | series.isna()
        return valid

    class _Annotation:
        primary_key = "id"
        foreign_keys = {}
