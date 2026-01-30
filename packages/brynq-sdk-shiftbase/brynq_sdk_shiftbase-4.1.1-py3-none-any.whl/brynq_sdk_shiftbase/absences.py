from typing import Dict, Optional, Union, Literal, List, Any
import pandas as pd
import requests
from datetime import date

from pydantic_core._pydantic_core import ValidationError

from .absence_types import AbsenceTypes
from .absence_policies import AbsencePolicies
from .schemas.absences import AbsenceGet, AbsenceGetById, AbsenceCreate, AbsenceUpdate
from brynq_sdk_functions import Functions

class Absences:
    """
    Handles all absence related operations in Shiftbase
    """

    def __init__(self, shiftbase):
        self.shiftbase = shiftbase
        self.uri = "absentees/"
        self.types = AbsenceTypes(shiftbase=shiftbase)
        self.policies = AbsencePolicies(shiftbase=shiftbase)


    def get(
        self,
        filters: Optional[Dict] = None,
        include: Optional[Union[Literal["AbsenteeDay", "User", "AbsenteeOption"], List[Literal["AbsenteeDay", "User", "AbsenteeOption"]]]] = None,
        max_date: Optional[date] = None,
        min_date: Optional[date] = None,
        only_open_ended: bool = False,
        status: Optional[Literal["Approved", "Declined", "Pending"]] = None,
        user_id: Optional[str] = None
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves the absence data from Shiftbase.

        Args:
            filters (Dict, optional): Additional query parameters
            include (Union[str, list], optional): Include additional related data in the response.
                Allowed values: "AbsenteeDay", "User", "AbsenteeOption"
            max_date (Union[str, date], optional): The maximum date for the returned absentees.
                If not present the current day will be used.
            min_date (Union[str, date], optional): The minimum date for the returned absentees.
                If not present the current day will be used.
            only_open_ended (bool, optional): Filter results to only return open ended absentees.
                Default: False
            status (str, optional): Filter on a status.
                Allowed values: "Approved", "Declined", "Pending"
            user_id (str, optional): Filter on a User ID.
                Must match pattern: ^[0-9]+$

                Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data).

        Raises:
            ValueError: If the absence data fails validation
        """
        # Prepare query parameters
        if filters is None:
            params = {}
        elif isinstance(filters, dict):
            params = filters.copy()
        else:
            params = {}

        # Handle include parameter
        if include:
            if isinstance(include, list):
                params["include"] = ",".join(include)
            else:
                params["include"] = include

        # Handle date parameters
        if max_date:
            if not isinstance(max_date, date):
                params["max_date"] = max_date
            else:
                params["max_date"] = max_date.strftime("%Y-%m-%d")

        if min_date:
            if not isinstance(min_date, date):
                params["min_date"] = min_date
            else:
                params["min_date"] = min_date.strftime("%Y-%m-%d")

        # Handle boolean parameter
        params["only_open_ended"] = "1" if only_open_ended else "0"

        # Handle status and user_id
        if status:
            params["status"] = status
        if user_id:
            params["user_id"] = user_id

        response_data = self.shiftbase.get(self.uri, params)
        if response_data:
            # Use pandas json_normalize to flatten the nested structure
            df = pd.json_normalize(response_data, sep="_", max_level=1)

            if df.empty:
                return pd.DataFrame(), pd.DataFrame()

            # Validate the DataFrame against the schema using brynq_sdk_functions
            try:
                valid_data, invalid_data = Functions.validate_data(df, AbsenceGet)
                return valid_data, invalid_data
            except Exception as e:
                raise ValueError(f"Invalid absence data: {str(e)}")
        else:
            return pd.DataFrame(), pd.DataFrame()

    def get_by_id(self, absentee_id: str, allow_deleted: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves a specific absentee by ID from Shiftbase.

        Args:
            absentee_id (str): The unique identifier of an absentee.
                Must match pattern: ^[0-9]+$
            allow_deleted (bool, optional): Whether to include deleted records.
                Default: False

                Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data).

        Raises:
            ValueError: If absentee_id doesn't match the required pattern or if the data fails validation
        """
        # Validate absentee_id pattern
        if not absentee_id.isdigit():
            raise ValueError("absentee_id must contain only digits")

        # Prepare query parameters
        params = {"allow_deleted": "1" if allow_deleted else "0"}

        # Get the absentee data
        response_data = self.shiftbase.get(f"{self.uri}{absentee_id}", params)

        if not response_data:
            return pd.DataFrame(), pd.DataFrame()

        # Use pandas json_normalize to flatten the nested structure
        df = pd.json_normalize(response_data, sep="_", max_level=1)

        if df.empty:
            return pd.DataFrame(), pd.DataFrame()

        # Validate the DataFrame against the AbsenceGetById schema
        try:
            valid_data, invalid_data = Functions.validate_data(df, AbsenceGetById)
            return valid_data, invalid_data
        except Exception as e:
            raise ValueError(f"Invalid absence data for ID {absentee_id}: {str(e)}")

    def get_review(self, absentee_id: str, end_date: Optional[date] = None,) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves the review results for a specific absentee from Shiftbase.
        This endpoint returns an array of checks performed on the absence and if the absence passed or didn't pass the check.

        Args:
            absentee_id (str): The unique identifier of an absence.
                Must match pattern: ^[0-9]+$
            end_date (Optional[date]): Provide endDate to review the absence request based on this end date.

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data).

        Raises:
            ValueError: If absentee_id doesn't match the required pattern
        """
        # Validate absentee_id pattern
        if not absentee_id.isdigit():
            raise ValueError("absentee_id must contain only digits")

        # Prepare query parameters
        params = {}
        if end_date:
            if not isinstance(end_date, date):
                raise TypeError("max_date must be a datetime object")
            params["max_date"] = end_date.strftime("%Y-%m-%d")

        # Get the review data
        response_data = self.shiftbase.get(f"{self.uri}{absentee_id}/review", params)

        if not response_data:
            return pd.DataFrame(), pd.DataFrame()

        df = pd.DataFrame(response_data)

        if df.empty:
            return pd.DataFrame(), pd.DataFrame()

        # Return as valid data (no schema validation for review endpoint)
        # Returns 2 DataFrames to follow the pattern of the other methods.
        return df, pd.DataFrame()

    def create(self, data: Dict) -> requests.Response:
        """
        Creates a new absence in Shiftbase.

        Args:
            data (Dict): Dictionary containing the absence data to create.
                Must match the AbsenceCreate structure.

        Returns:
            requests.Response: Response from the API containing the created absence details

        Raises:
            ValueError: If the data fails validation or if the creation fails
        """
        # Validate input data against the schema using direct Pydantic instantiation
        try:
            validated_data = AbsenceCreate(**data)
        except Exception as e:
            raise ValueError(f"Invalid absence data: {str(e)}")

        # Prepare request body
        request_body = validated_data.model_dump(by_alias=True, mode='json')

        # Make POST request
        response = self.shiftbase.session.post(f"{self.shiftbase.base_url}{self.uri}", json=request_body)
        return response

    def update(self, absentee_id: str, data: Dict) -> requests.Response:
        """
        Updates an existing absence in Shiftbase.

        Args:
            absentee_id (str): The unique identifier of the absence to update.
                Must match pattern: ^[0-9]+$
            data (Dict): Dictionary containing the absence data to update.
                Must match the AbsenceUpdate structure.

        Returns:
            requests.Response: Response from the API containing the updated absence details

        Raises:
            ValueError: If absentee_id is invalid or if the data fails validation
        """
        # Validate absentee_id pattern
        if not absentee_id.isdigit():
            raise ValueError("absentee_id must contain only digits")

        # Validate input data against the schema using direct Pydantic instantiation
        try:
            validated_data = AbsenceUpdate(**data)
        except Exception as e:
            raise ValueError(f"Invalid absence data: {str(e)}")

        # Prepare request body
        request_body = validated_data.model_dump(by_alias=True, mode='json')
        request_body["id"] = absentee_id
        # Make PUT request
        response = self.shiftbase.session.put(f"{self.shiftbase.base_url}{self.uri}{absentee_id}", json=request_body)
        return response

    def delete(self, absentee_id: str) -> requests.Response:
        """
        Deletes a specific absence from Shiftbase.

        Args:
            absentee_id (str): The unique identifier of an absence.
                Must match pattern: ^[0-9]+$

        Returns:
            requests.Response: Response from the API containing status and metadata

        Raises:
            ValueError: If absentee_id doesn't match the required pattern
        """
        # Validate absentee_id pattern
        if not absentee_id.isdigit():
            raise ValueError("absentee_id must contain only digits")

        # Send DELETE request to the API
        response = self.shiftbase.session.delete(f"{self.shiftbase.base_url}{self.uri}{absentee_id}")
        return response
