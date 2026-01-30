from typing import Dict, Optional, List, Union
import pandas as pd
import re
from .schemas.shifts import ShiftGet
from brynq_sdk_functions import Functions

class Shifts:
    """
    Handles all shift related operations in Shiftbase
    """
    def __init__(self, shiftbase):
        self.shiftbase = shiftbase
        self.uri = "shifts"

    def get(self,
           department_id: Optional[str] = None,
           allow_deleted: Optional[str] = None) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves a list of shifts from Shiftbase.

        Endpoint: GET https://api.shiftbase.com/api/shifts

        Args:
            department_id (str, optional): Filter on department ID. Must contain only digits.
            allow_deleted (str, optional): Include deleted shifts in the list.

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: (valid_data, invalid_data) - Valid and invalid shifts data

        Raises:
            ValueError: If parameters are invalid or shift data fails validation
            requests.HTTPError: If the API request fails
        """
        # Validate parameters
        if department_id and not re.match(r"^[0-9]+$", department_id):
            raise ValueError("department_id must contain only digits")

        # Prepare query parameters
        params = {}
        if department_id:
            params["department_id"] = department_id
        if allow_deleted:
            params["allow_deleted"] = allow_deleted

        # Make the request
        response_data = self.shiftbase.get(self.uri, params)

        shift_list = [shift.get("Shift") for shift in response_data]
        # Convert to DataFrame
        df = pd.DataFrame(shift_list)

        # If no data is returned, return empty DataFrames
        if df.empty:
            return pd.DataFrame(), pd.DataFrame()

        # Rename the 'break' column to 'break_time' before validation
        if 'break' in df.columns:
            df = df.rename(columns={'break': 'break_time'})

        # Validate with Functions.validate_data
        try:
            valid_data, invalid_data = Functions.validate_data(df, ShiftGet)
            return valid_data, invalid_data
        except Exception as e:
            raise ValueError(e)

    def get_by_id(self, shift_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves a specific shift by its ID.

        Endpoint: GET https://api.shiftbase.com/api/shifts/{shiftId}

        Args:
            shift_id (str): The unique identifier of the shift

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data)

        Raises:
            ValueError: If shift_id is invalid or shift data fails validation
            requests.HTTPError:
                - 404: Shift not found
        """
        # Validate shift_id
        if not shift_id:
            raise ValueError("shift_id cannot be empty")

        if not re.match(r"^[0-9]+$", shift_id):
            raise ValueError("shift_id must contain only digits")

        # Construct the endpoint URL
        endpoint = f"{self.uri}/{shift_id}"

        try:
            # Make the request
            response_data = self.shiftbase.get(endpoint)

            # Extract shift data
            shift_data = response_data.get("Shift", {})

            # Convert to DataFrame for validation
            df = pd.DataFrame([shift_data])

            # Validate with Functions.validate_data
            try:
                valid_data, invalid_data = Functions.validate_data(df, ShiftGet)
                return valid_data, invalid_data
            except Exception as e:
                error_message = f"Invalid shift data: {str(e)}"
                raise ValueError(error_message)

        except Exception as e:
            if "404" in str(e):
                raise ValueError(f"Shift with ID {shift_id} not found.")
            raise
