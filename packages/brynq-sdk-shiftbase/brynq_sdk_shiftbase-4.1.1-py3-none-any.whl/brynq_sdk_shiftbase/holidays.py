from typing import Dict, Optional, List, Tuple
import pandas as pd
from .schemas.holidays import HolidayGroupGet, PublicHolidayGet
from brynq_sdk_functions import Functions

class Holidays:
    """
    Handles all holiday related operations in Shiftbase
    """
    def __init__(self, shiftbase):
        self.shiftbase = shiftbase
        self.base_uri = "holidays"

    def get_public_holidays(self, country: str, year: Optional[str] = None, region: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves public holidays for a given country and optionally a region.

        Args:
            country (str): Alpha-3 country code (e.g., "NLD" for Netherlands)
            year (str, optional): Selected year (e.g., "2023")
            region (str, optional): Either Alpha-2 or Alpha-3 region code

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data)

        Raises:
            ValueError: If parameters are invalid
            ValueError: If holiday data fails validation
            requests.HTTPError: If the API request fails
        """

        # Construct the endpoint URL
        endpoint = f"{self.base_uri}/calendars/{country}"

        # Prepare query parameters
        params = {}
        if year:
            params["year"] = year
        if region:
            params["region"] = region

        # Make the request
        response_data = self.shiftbase.get(endpoint, params)
        if not response_data:
            return pd.DataFrame(), pd.DataFrame()

        # Extract holidays data
        holidays = response_data.get("data", [])
        if not holidays:
            return pd.DataFrame(), pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(holidays)

        # Validate with Functions.validate_data
        try:
            valid_data, invalid_data = Functions.validate_data(df, PublicHolidayGet)
            return valid_data, invalid_data
        except Exception as e:
            raise ValueError(f"Invalid holiday data: {str(e)}")

    def get_holiday_groups(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves the list of holiday groups from Shiftbase.

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data)

        Raises:
            ValueError: If the holiday groups data fails validation
            requests.HTTPError: If the API request fails
        """
        # Construct the endpoint URL
        endpoint = f"{self.base_uri}/groups"

        # Make the request
        response_data = self.shiftbase.get(endpoint)
        if not response_data:
            return pd.DataFrame(), pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(response_data)
        if df.empty:
            return pd.DataFrame(), pd.DataFrame()

        # Validate with Functions.validate_data
        try:
            valid_data, invalid_data = Functions.validate_data(df, HolidayGroupGet)
            return valid_data, invalid_data
        except Exception as e:
            raise ValueError(f"Invalid holiday group data: {str(e)}")
