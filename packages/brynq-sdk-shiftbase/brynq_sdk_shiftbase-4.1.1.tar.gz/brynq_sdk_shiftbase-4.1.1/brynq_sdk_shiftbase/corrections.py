from typing import Dict, Optional, List
import pandas as pd
from datetime import date
import requests
from .schemas.corrections import CorrectionGet, CorrectionCreate, CorrectionBatchCreate
from brynq_sdk_functions import Functions

class Corrections:
    """
    Handles all correction related operations in Shiftbase
    """
    def __init__(self, shiftbase):
        self.shiftbase = shiftbase
        self.uri = "corrections"

    def get(self,
            max_date: Optional[date] = None,
            min_date: Optional[date] = None,
            type: Optional[str] = None,
            user_id: Optional[str] = None) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves the list of corrections from Shiftbase.

        Args:
            max_date (str, optional): The maximum date for the returned corrections.
                                      If not present the current day will be used.
            min_date (str, optional): The minimum date for the returned corrections.
                                      If not present the current day will be used.
            type (str, optional): Filter on correction type.
                                  Allowed values: Overtime, Time off balance
            user_id (str, optional): Returns correction from a specific user.

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data)

        Raises:
            ValueError: If the correction data fails validation or parameters are invalid
        """
        # Validate parameters
        if type and type not in ["Overtime", "Time off balance", "Time off balance cycle"]:
            raise ValueError("type must be one of: Overtime, Time off balance, Time off balance cycle")

        # Prepare query parameters
        params = {}
        if max_date:
            if not isinstance(max_date, date):
                raise TypeError("max_date must be a datetime object")
            params["max_date"] = max_date.strftime("%Y-%m-%d")
        if min_date:
            if not isinstance(min_date, date):
                raise TypeError("min_date must be a datetime object")
            params["min_date"] = min_date.strftime("%Y-%m-%d")
        if type:
            params["type"] = type
        if user_id:
            params["user_id"] = user_id

        # Make the request
        response_data = self.shiftbase.get(self.uri, params)
        if not response_data or not response_data.get("data"):
            return pd.DataFrame(), pd.DataFrame()

        # Extract corrections data
        corrections = response_data.get("data", [])

        # Convert to DataFrame and validate
        df = pd.DataFrame(corrections)
        try:
            valid_data, invalid_data = Functions.validate_data(df, CorrectionGet)
            return valid_data, invalid_data
        except Exception as e:
            raise ValueError(f"Invalid correction data: {str(e)}")

    def get_by_id(self, correction_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves a specific correction by ID.

        Args:
            correction_id (str): The unique identifier of the correction

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data)

        Raises:
            ValueError: If correction_id is invalid or correction data fails validation
            requests.HTTPError:
                - 403: If the user doesn't have required permissions
                - 404: If the correction is not found
        """
        # Validate correction_id
        if not correction_id:
            raise ValueError("correction_id cannot be empty")

        # Construct the endpoint URL
        endpoint = f"{self.uri}/{correction_id}"

        # Make the request
        response_data = self.shiftbase.get(endpoint)

        # Extract correction data
        correction_data = response_data.get("data", {})
        if not correction_data:
            return pd.DataFrame(), pd.DataFrame()

        # Convert to DataFrame and validate
        df = pd.DataFrame([correction_data])
        try:
            valid_data, invalid_data = Functions.validate_data(df, CorrectionGet)
            return valid_data, invalid_data
        except Exception as e:
            raise ValueError(f"Invalid correction data: {str(e)}")

    def create(self, data: Dict) -> requests.Response:
        """
        Creates a new correction in Shiftbase.

        Endpoint: POST https://api.shiftbase.com/api/corrections

        Args:
            data (Dict): Correction data to create. Must contain:
                CorrectionCreate

        Returns:
            requests.Response: Created correction data

        Raises:
            ValueError: If parameters are invalid or correction data fails validation
            requests.HTTPError: If the API request fails
        """
        # Validate input data against the pydantic schema
        try:
            validated_data = CorrectionCreate(**data)
            # Prepare request body - convert validated pydantic model to dict
            request_body = validated_data.model_dump(mode="json",by_alias=True, exclude_none=True)
        except Exception as e:
            raise ValueError(f"Invalid correction data: {str(e)}")

        # Make the request
        response = self.shiftbase.session.post(f"{self.shiftbase.base_url}{self.uri}", json=request_body)
        response.raise_for_status()
        return response

    def create_batch(self, data_list: List[Dict]) -> requests.Response:
        """
        Creates multiple corrections in a batch operation.

        Endpoint: POST https://api.shiftbase.com/api/corrections/batch

        Args:
            data_list (List[Dict]): List of correction data to create. Each dict must contain:
                CorrectionCreate
                And may contain the same optional fields as in create method.

        Returns:
            requests.Response: API response containing created correction data

        Raises:
            ValueError: If parameters are invalid or correction data fails validation
            requests.HTTPError: If the API request fails
        """
        # Prepare batch request body
        batch_data = {"Correction": data_list}

        # Validate the entire batch structure (this will validate each correction automatically)
        try:
            validated_batch = CorrectionBatchCreate(**batch_data)
            request_body = validated_batch.model_dump(mode="json", by_alias=True, exclude_none=True)
        except Exception as e:
            raise ValueError(f"Invalid batch correction data: {str(e)}")

        # Make the request
        endpoint = f"{self.uri}/batch"
        response = self.shiftbase.session.post(f"{self.shiftbase.base_url}{endpoint}", json=request_body)
        response.raise_for_status()
        return response

    def delete(self, correction_id: str) -> requests.Response:
        """
        Deletes a specific correction from Shiftbase.

        Endpoint: DELETE https://api.shiftbase.com/api/corrections/{correctionId}

        Args:
            correction_id (str): The unique identifier of the correction to delete.
                Must match pattern: ^[0-9]+$

        Returns:
            requests.Response: Response from the API containing status and metadata

        Raises:
            ValueError: If correction_id doesn't match the required pattern
            requests.HTTPError: If the API request fails
        """
        # Validate correction_id pattern
        if not correction_id:
            raise ValueError("correction_id cannot be empty")

        if not correction_id.isdigit():
            raise ValueError("correction_id must contain only digits")

        # Send DELETE request to the API
        response = self.shiftbase.session.delete(f"{self.shiftbase.base_url}{self.uri}/{correction_id}")
        response.raise_for_status()
        return response
