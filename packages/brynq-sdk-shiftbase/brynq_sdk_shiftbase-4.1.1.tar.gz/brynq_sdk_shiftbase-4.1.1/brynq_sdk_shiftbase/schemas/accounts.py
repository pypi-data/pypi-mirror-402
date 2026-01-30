import pandera as pa
from pandera.typing import Series, DateTime, Date
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import date
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class AccountGet(BrynQPanderaDataFrameModel):
    """
    Schema for validating Account data returned from Shiftbase API.
    """
    # Read-only fields
    id: Series[str] = pa.Field(coerce=True, description="Unique identifier for the account")
    created: Series[DateTime] = pa.Field(coerce=True, description="Creation date and time", nullable=True)

    # Required fields (API documentation)
    account_type_id: Series[str] = pa.Field(coerce=True, description="Account type identifier")
    subscription_id: Series[str] = pa.Field(coerce=True, description="Subscription identifier")
    company: Series[str] = pa.Field(coerce=True, description="Company name")
    country: Series[str] = pa.Field(coerce=True, description="Country code")
    currency_id: Series[str] = pa.Field(coerce=True, description="Currency identifier")
    domain: Series[str] = pa.Field(coerce=True, description="Domain for the account")
    host: Series[str] = pa.Field(coerce=True, description="Host information")
    day_start: Series[str] = pa.Field(coerce=True, description="Default start time of day")
    day_end: Series[str] = pa.Field(coerce=True, description="Default end time of day")
    time_zone: Series[str] = pa.Field(coerce=True, description="Time zone")
    user_sortfield: Series[str] = pa.Field(coerce=True, description="Field used for sorting users")
    user_sortdirection: Series[str] = pa.Field(coerce=True, description="Direction for user sorting")
    user_name_format: Series[str] = pa.Field(coerce=True, description="Format for displaying user names")
    enforce_mfa: Series[bool] = pa.Field(coerce=True, description="Whether multi-factor authentication is required")
    servicedesk_access_enabled: Series[bool] = pa.Field(coerce=True, description="Whether servicedesk access is enabled")
    test: Series[bool] = pa.Field(coerce=True, description="Whether this is a test account")
    onboarding: Series[str] = pa.Field(coerce=True, description="Onboarding status")
    estimated_users: Series[str] = pa.Field(coerce=True, description="Estimated number of users")
    group_id: Series[str] = pa.Field(coerce=True, description="Group identifier")
    schedule_compliance_check: Series[bool] = pa.Field(coerce=True, description="Whether schedule compliance check is enabled")
    publish_schedules: Series[bool] = pa.Field(coerce=True, description="Whether schedules are published")
    coc_in_schedule: Series[bool] = pa.Field(coerce=True, description="Whether COC is included in schedule")
    contract_reminder_first: Series[str] = pa.Field(coerce=True, description="Days for first contract reminder")
    contract_reminder_second: Series[str] = pa.Field(coerce=True, description="Days for second contract reminder")
    invoice_company: Series[str] = pa.Field(coerce=True, description="Invoice company name")
    first_name: Series[str] = pa.Field(coerce=True, description="First name of account owner")
    last_name: Series[str] = pa.Field(coerce=True, description="Last name of account owner")
    street_address: Series[str] = pa.Field(coerce=True, description="Street address")
    zipcode: Series[str] = pa.Field(coerce=True, description="Zip/postal code", nullable=True)
    city: Series[str] = pa.Field(coerce=True, description="City", nullable=True)
    email: Series[str] = pa.Field(coerce=True, description="Primary email address")
    invoice_email: Series[str] = pa.Field(coerce=True, description="Email address for invoices")
    vat: Series[str] = pa.Field(coerce=True, description="VAT number", nullable=True)
    vat_valid: Series[bool] = pa.Field(coerce=True, description="Whether VAT is valid", nullable=True)
    vat_reverse_charge: Series[str] = pa.Field(coerce=True, description="VAT reverse charge", nullable=True)
    user_id: Series[str] = pa.Field(coerce=True, description="User identifier")
    start_date: Series[date] = pa.Field(coerce=True, description="Account start date")
    continue_subscription: Series[bool] = pa.Field(coerce=True, description="Whether to continue subscription")
    vacationhours_default: Series[str] = pa.Field(coerce=True, description="Default vacation hours")
    wait_hours: Series[str] = pa.Field(coerce=True, description="Wait hours")
    invoice_send_method: Series[str] = pa.Field(coerce=True, description="Method for sending invoices")
    invoice_due_date_interval: Series[str] = pa.Field(coerce=True, description="Due date interval for invoices")
    payment_method: Series[str] = pa.Field(coerce=True, description="Payment method")
    debit_name: Series[str] = pa.Field(coerce=True, description="Debit name", nullable=True)
    debit_banknr: Series[str] = pa.Field(coerce=True, description="Bank account number", nullable=True)
    debit_bic: Series[str] = pa.Field(coerce=True, description="BIC code", nullable=True)
    phone_nr: Series[str] = pa.Field(coerce=True, description="Phone number", nullable=True)
    deleted: Series[bool] = pa.Field(coerce=True, description="Whether the account is deleted")
    send_invoice_to_reseller: Series[bool] = pa.Field(coerce=True, description="Whether to send invoice to reseller")
    integration_plus: Series[bool] = pa.Field(coerce=True, description="Whether integration plus is enabled")
    language: Series[str] = pa.Field(coerce=True, description="Language", nullable=True)
    support_phone: Series[str] = pa.Field(coerce=True, description="Support phone number", nullable=True)
    support: Series[str] = pa.Field(coerce=True, description="Support information", nullable=True)

    class _Annotation:
        primary_key = "id"
        foreign_keys = {
            "account_type_id": {
                "parent_schema": "AccountType",
                "parent_column": "id",
                "cardinality": "N:1"
            },
            "subscription_id": {
                "parent_schema": "Subscription",
                "parent_column": "id",
                "cardinality": "N:1"
            },
            "currency_id": {
                "parent_schema": "Currency",
                "parent_column": "id",
                "cardinality": "N:1"
            },
            "group_id": {
                "parent_schema": "Group",
                "parent_column": "id",
                "cardinality": "N:1"
            },
            "user_id": {
                "parent_schema": "User",
                "parent_column": "id",
                "cardinality": "N:1"
            }
        }

    class Config:
        coerce = True
        strict = False


class AccountUpdate(BaseModel):
    """
    Schema for validating Account update data.
    This schema is used when updating existing accounts in Shiftbase.
    """
    # Required fields
    id: str = Field(description="Unique identifier for the account", example="12345")
    account_type_id: str = Field(description="Account type identifier", example="1")
    company: str = Field(description="Company name", example="Acme Corp")
    country: str = Field(description="Country code (e.g., NL)", example="NL")
    domain: str = Field(description="Domain for the account", example="acme.com")
    host: str = Field(description="Host information", example="api.shiftbase.com")
    user_sortfield: str = Field(description="Field used for sorting users", example="last_name")
    user_sortdirection: str = Field(description="Direction for user sorting (ASC/DESC)", example="ASC")
    user_name_format: str = Field(description="Format for displaying user names", example="first_name last_name")
    enforce_mfa: bool = Field(description="Whether multi-factor authentication is required", example=True)
    servicedesk_access_enabled: bool = Field(description="Whether servicedesk access is enabled", example=False)
    test: bool = Field(description="Whether this is a test account", example=False)
    onboarding: str = Field(description="Onboarding status", example="completed")
    estimated_users: str = Field(description="Estimated number of users", example="100")
    group_id: str = Field(description="Group identifier", example="1")
    schedule_compliance_check: bool = Field(description="Whether schedule compliance check is enabled", example=True)
    publish_schedules: bool = Field(description="Whether schedules are published", example=True)
    coc_in_schedule: bool = Field(description="Whether COC is included in schedule", example=False)
    contract_reminder_first: str = Field(description="Days for first contract reminder", example="30")
    contract_reminder_second: str = Field(description="Days for second contract reminder", example="7")
    invoice_company: str = Field(description="Invoice company name", example="Acme Corp")
    first_name: str = Field(description="First name of account owner", example="John")
    last_name: str = Field(description="Last name of account owner", example="Doe")
    street_address: str = Field(description="Street address", example="123 Main St")
    zipcode: str = Field(description="Zip/postal code", example="12345")
    city: str = Field(description="City", example="Amsterdam")
    email: str = Field(description="Primary email address", example="admin@acme.com")
    invoice_email: str = Field(description="Email address for invoices", example="billing@acme.com")
    user_id: str = Field(description="User identifier", example="12345")
    start_date: date = Field(description="Account start date", example="2024-01-01")
    continue_subscription: bool = Field(description="Whether to continue subscription", example=True)
    vacationhours_default: str = Field(description="Default vacation hours", example="160")
    wait_hours: str = Field(description="Wait hours", example="0")
    invoice_send_method: str = Field(description="Method for sending invoices", example="email")
    invoice_due_date_interval: str = Field(description="Due date interval for invoices", example="30")
    payment_method: str = Field(description="Payment method", example="credit_card")
    deleted: bool = Field(description="Whether the account is deleted", example=False)
    send_invoice_to_reseller: bool = Field(description="Whether to send invoice to reseller", example=False)
    integration_plus: bool = Field(description="Whether integration plus is enabled", example=False)

    # Optional fields
    created: Optional[DateTime] = Field(description="Creation date and time", default=None, example="2024-01-01T00:00:00Z")
    subscription_id: Optional[str] = Field(description="Subscription identifier", default=None, example="sub_12345")
    currency_id: Optional[str] = Field(description="Currency identifier", default=None, example="1")
    day_start: Optional[str] = Field(description="Default start time of day", default=None, example="08:00:00")
    day_end: Optional[str] = Field(description="Default end time of day", default=None, example="18:00:00")
    time_zone: Optional[str] = Field(description="Time zone", default=None, example="Europe/Amsterdam")
    vat: Optional[str] = Field(description="VAT number", default=None, example="NL123456789B01")
    vat_valid: Optional[bool] = Field(description="Whether VAT is valid", default=None, example=True)
    vat_reverse_charge: Optional[str] = Field(description="VAT reverse charge", default=None, example="0")
    debit_name: Optional[str] = Field(description="Debit name", default=None, example="Acme Corp")
    debit_banknr: Optional[str] = Field(description="Bank account number", default=None, example="NL91ABNA0417164300")
    debit_bic: Optional[str] = Field(description="BIC code", default=None, example="ABNANL2A")
    phone_nr: Optional[str] = Field(description="Phone number", default=None, example="+31201234567")
    language: Optional[str] = Field(description="Language", default=None, example="en")
    support_phone: Optional[str] = Field(description="Support phone number", default=None, example="+31201234568")
    support: Optional[str] = Field(description="Support information", default=None, example="support@acme.com")
    is_beta_account: Optional[bool] = Field(description="Whether this is a beta account", default=False, example=False)

    class Config:
        """Pydantic configuration"""
        extra = "allow"  # Allow additional fields not defined in the schema
        coerce = True
