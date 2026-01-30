from typing import Dict, Optional, List
import pandas as pd
from .schemas.locations import LocationGet
from brynq_sdk_functions import Functions

class Locations:
    """
    Handles all location related operations in Shiftbase
    """
    def __init__(self, shiftbase):
        self.shiftbase = shiftbase
        self.uri = "locations"

    def get(self, include: Optional[str] = None) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves the list of all active locations from Shiftbase.

        Args:
            include (str, optional): Additional related data to include in the response.
                Example: "Department,Department.Team,Department.Shift"

        Returns:
            tuple: (valid_data, invalid_data) - Valid and invalid location data

        Raises:
            ValueError: If the location data fails validation
            requests.HTTPError: If the API request fails
        """
        # Prepare query parameters
        params = {}
        if include:
            params["include"] = include

        # Make the request
        response_data = self.shiftbase.get(self.uri, params)

        # Extract locations data
        locations = [location.get("Location") for location in response_data]

        # Convert to DataFrame
        df = pd.DataFrame(locations)

        # Validate with Functions.validate_data
        try:
            valid_data, invalid_data = Functions.validate_data(df, LocationGet)
            return valid_data, invalid_data
        except Exception as e:
            error_message = f"Invalid location data: {str(e)}"
            raise ValueError(error_message)
