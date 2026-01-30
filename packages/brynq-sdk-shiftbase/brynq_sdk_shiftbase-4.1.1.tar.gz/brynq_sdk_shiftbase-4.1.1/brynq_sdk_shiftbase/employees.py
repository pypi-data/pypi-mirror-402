from typing import Dict, Optional, Tuple
import pandas as pd
from .contracts import Contracts
from .time_off_balances import TimeOffBalances
from .absences import Absences
from .schemas.users import TimeOffBalanceDetailsGet, TimeOffBalanceExpiriesGet
from brynq_sdk_functions import Functions

class Employees:
    """
    Handles all employee related operations in Shiftbase
    """
    def __init__(self, shiftbase):
        self.shiftbase = shiftbase
        self.uri = "employees/"

        # Initialize employee-related classes
        self.contracts = Contracts(shiftbase)
        self.time_off_balances = TimeOffBalances(shiftbase)
        self.absences = Absences(shiftbase)


    def get_time_off_balance_details(self, employee_id: str, year: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Returns the time off balances details for the given employee for a specific year.

        Will select end of contract OR end of year. Whichever is first for the given year.

        Args:
            employee_id (str): The unique identifier of the employee
            year (str): The full year to use

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data)

        Raises:
            ValueError: If employee_id is not a valid digit string
            ValueError: If year is not a valid 4-digit year string
            requests.HTTPError:
                - 403: If the user doesn't have required permissions (View time off balances, View own time off balances)
                - 404: If the employee is not found
                - 426: If the request fails for another reason
        """
        # Validate parameters
        if not employee_id.isdigit():
            raise ValueError("employee_id must contain only digits")

        if not (len(year) == 4 and year.isdigit()):
            raise ValueError("year must be a valid 4-digit year string")

        # Construct the endpoint URL
        endpoint = f"{self.uri}{employee_id}/timeOff/balances/details/{year}"

        # Make the request
        response_data = self.shiftbase.get(endpoint)
        if not response_data:
            return pd.DataFrame(), pd.DataFrame()

        # Convert to DataFrame using json_normalize to flatten nested structure
        df = pd.json_normalize(response_data)
        if df.empty:
            return pd.DataFrame(), pd.DataFrame()

        # Validate with Functions.validate_data
        try:
            valid_data, invalid_data = Functions.validate_data(df, TimeOffBalanceDetailsGet)
            return valid_data, invalid_data
        except Exception as e:
            raise ValueError(f"Invalid time off balance details data: {str(e)}")

    def get_upcoming_time_off_expiries(self, employee_id: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Returns a list of upcoming time-off balance expiries within the date range
        from today to six months in the future for the given employee.

        Args:
            employee_id (str): The unique identifier of the employee

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data)

        Raises:
            ValueError: If employee_id is not a valid digit string
            requests.HTTPError:
                - 403: If the user doesn't have required permissions (View time off balances, View own time off balances)
                - 426: If the request fails for another reason
        """
        # Validate employee_id parameter
        if not employee_id.isdigit():
            raise ValueError("employee_id must contain only digits")

        # Construct the endpoint URL
        endpoint = f"{self.uri}{employee_id}/timeOff/balances/expiries"

        # Make the request
        response_data = self.shiftbase.get(endpoint)
        if not response_data:
            return pd.DataFrame(), pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(response_data.get("data", []))
        if df.empty:
            return pd.DataFrame(), pd.DataFrame()

        # Validate with Functions.validate_data
        try:
            valid_data, invalid_data = Functions.validate_data(df, TimeOffBalanceExpiriesGet)
            return valid_data, invalid_data
        except Exception as e:
            raise ValueError(f"Invalid time off balance expiries data: {str(e)}")
