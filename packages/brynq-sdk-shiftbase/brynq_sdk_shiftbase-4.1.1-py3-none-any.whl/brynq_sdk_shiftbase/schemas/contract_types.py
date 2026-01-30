import pandera as pa
from pandera.typing import Series, DateTime
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class ContractTypeGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating Contract Type data returned from Shiftbase API.
    Every employee in Shiftbase has a contract associated with a contract type.
    A contract type is a set of rules related to a contract.
    """
    id: Series[str] = pa.Field(coerce=True, description="Unique identifier for the contract type")
    account_id: Series[str] = pa.Field(coerce=True, description="Account identifier")
    name: Series[str] = pa.Field(coerce=True, description="Name of the contract type")
    plus_min: Series[bool] = pa.Field(coerce=True, description="Whether plus-minus calculation is enabled")
    salary_calc_type: Series[str] = pa.Field(coerce=True, description="Salary calculation type (CONTRACT or WORKED)")
    rate_card_id: Series[str] = pa.Field(coerce=True, description="Rate card identifier", nullable=True)
    overtime_policy_id: Series[str] = pa.Field(coerce=True, description="Overtime policy identifier", nullable=True)
    absence_policy_id: Series[str] = pa.Field(coerce=True, description="Absence policy identifier", nullable=True)
    created: Series[DateTime] = pa.Field(coerce=True, description="Creation date and time")
    modified: Series[DateTime] = pa.Field(coerce=True, description="Last modification date and time")
    created_by: Series[str] = pa.Field(coerce=True, description="User who created the contract type")
    modified_by: Series[str] = pa.Field(coerce=True, description="User who last modified the contract type")
    deleted: Series[bool] = pa.Field(coerce=True, description="Whether the contract type is deleted")
    deleted_date: Series[DateTime] = pa.Field(coerce=True, description="Date when the contract type was deleted", nullable=True)
    coc: Series[str] = pa.Field(coerce=True, description="Cost of company factor", nullable=True)
    salary_calc_option: Series[str] = pa.Field(coerce=True, description="Translated label of salary_calc_type", nullable=True)

    class _Annotation:
        primary_key = "id"
        foreign_keys = {
            "account_id": {"parent_schema": "Account", "parent_column": "id", "cardinality": "N:1"},
            "absence_policy_id": {"parent_schema": "AbsencePolicy", "parent_column": "id", "cardinality": "N:1"},
            "rate_card_id": {"parent_schema": "RateCard", "parent_column": "id", "cardinality": "N:1"},
            "overtime_policy_id": {"parent_schema": "OvertimePolicy", "parent_column": "id", "cardinality": "N:1"},
            "created_by": {"parent_schema": "User", "parent_column": "id", "cardinality": "N:1"},
            "modified_by": {"parent_schema": "User", "parent_column": "id", "cardinality": "N:1"}
        }

    class Config:
        coerce = True
        strict = False
