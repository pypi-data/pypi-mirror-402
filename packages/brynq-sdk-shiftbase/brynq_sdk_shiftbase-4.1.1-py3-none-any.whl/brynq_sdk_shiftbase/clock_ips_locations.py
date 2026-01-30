from typing import Dict, Optional
import pandas as pd
from .schemas.clock_ips_locations import ClockIpGet, ClockLocationGet
from brynq_sdk_functions import Functions

class ClockIpsLocations:
    """
    Handles all clock IP and location related operations in Shiftbase
    """
    def __init__(self, shiftbase):
        self.shiftbase = shiftbase
        self.clock_ips_uri = "clock_ips"
        self.clock_locations_uri = "clock_locations"

    def get_ips(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves all clock IPs from Shiftbase.

        Endpoint: GET https://api.shiftbase.com/api/clock_ips

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data)

        Raises:
            ValueError: If clock IP data fails validation
            requests.HTTPError: If the API request fails
        """
        # Make the request
        response_data = self.shiftbase.get(self.clock_ips_uri)

        if not response_data:
            return pd.DataFrame(), pd.DataFrame()
        clock_ip_list = [item["ClockIp"] for item in response_data]

        # Create DataFrame from response
        df = pd.DataFrame(clock_ip_list)

        # If no data is returned, return empty DataFrames
        if df.empty:
            return pd.DataFrame(), pd.DataFrame()

        # Validate with Functions.validate_data
        try:
            valid_data, invalid_data = Functions.validate_data(df, ClockIpGet)
            return valid_data, invalid_data
        except Exception as e:
            raise ValueError(f"Invalid clock IP data: {str(e)}")

    def get_ip_by_id(self, clock_ip_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves a specific clock IP by its ID.

        Endpoint: GET https://api.shiftbase.com/api/clock_ips/{clockIpId}

        Args:
            clock_ip_id (str): The unique identifier of the clock IP

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data)

        Raises:
            ValueError: If clock_ip_id is invalid or clock IP data fails validation
            requests.HTTPError:
                - 404: Clock IP not found
        """
        # Validate clock_ip_id
        if not clock_ip_id:
            raise ValueError("clock_ip_id cannot be empty")

        # Construct the endpoint URL
        endpoint = f"{self.clock_ips_uri}/{clock_ip_id}"

        try:
            # Make the request
            response_data = self.shiftbase.get(endpoint)

            # Extract clock IP data
            if not response_data or not "ClockIp" in response_data:
                return pd.DataFrame(), pd.DataFrame()

            clock_ip_data = response_data["ClockIp"]

            # Validate with ClockIpGet
            df = pd.DataFrame([clock_ip_data])
            try:
                valid_data, invalid_data = Functions.validate_data(df, ClockIpGet)
                return valid_data, invalid_data
            except Exception as e:
                raise ValueError(f"Invalid clock IP data: {str(e)}")

        except Exception as e:
            if "404" in str(e):
                raise ValueError(f"Clock IP with ID {clock_ip_id} not found.")
            raise

    def get(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves all clock locations from Shiftbase.

        Endpoint: GET https://api.shiftbase.com/api/clock_locations

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data)

        Raises:
            ValueError: If clock location data fails validation
            requests.HTTPError: If the API request fails
        """
        # Make the request
        response_data = self.shiftbase.get(self.clock_locations_uri)

        if not response_data:
            return pd.DataFrame(), pd.DataFrame()

        # Extract clock location data from response
        locations = []
        for item in response_data:
            if "ClockLocation" in item:
                locations.append(item["ClockLocation"])

        # Create DataFrame from response
        df = pd.DataFrame(locations)

        # If no data is returned, return empty DataFrames
        if df.empty:
            return pd.DataFrame(), pd.DataFrame()

        # Validate with Functions.validate_data
        try:
            valid_data, invalid_data = Functions.validate_data(df, ClockLocationGet)
            return valid_data, invalid_data
        except Exception as e:
            raise ValueError(f"Invalid clock location data: {str(e)}")

    def get_by_id(self, clock_location_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves a specific clock location by its ID.

        Endpoint: GET https://api.shiftbase.com/api/clock_locations/{clockLocationId}

        Args:
            clock_location_id (str): The unique identifier of the clock location

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data)

        Raises:
            ValueError: If clock_location_id is invalid or clock location data fails validation
            requests.HTTPError:
                - 404: Clock location not found
                - 403: Unauthorized access
        """
        # Validate clock_location_id
        if not clock_location_id:
            raise ValueError("clock_location_id cannot be empty")

        # Construct the endpoint URL
        endpoint = f"{self.clock_locations_uri}/{clock_location_id}"

        try:
            # Make the request
            response_data = self.shiftbase.get(endpoint)

            # Extract clock location data
            if not response_data or not "ClockLocation" in response_data:
                return pd.DataFrame(), pd.DataFrame()

            clock_location_data = response_data["ClockLocation"]

            # Validate with ClockLocationGet
            df = pd.DataFrame([clock_location_data])
            try:
                valid_data, invalid_data = Functions.validate_data(df, ClockLocationGet)
                return valid_data, invalid_data
            except Exception as e:
                raise ValueError(f"Invalid clock location data: {str(e)}")

        except Exception as e:
            if "404" in str(e):
                raise ValueError(f"Clock location with ID {clock_location_id} not found.")
            raise
