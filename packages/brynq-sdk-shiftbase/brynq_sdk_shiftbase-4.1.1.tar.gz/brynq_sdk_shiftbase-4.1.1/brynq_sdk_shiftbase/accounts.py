from typing import Dict
import pandas as pd
import requests
from .schemas.accounts import AccountGet, AccountUpdate
from brynq_sdk_functions import Functions

class Accounts:
    """
    Handles account related operations in Shiftbase
    """
    def __init__(self, shiftbase):
        self.shiftbase = shiftbase
        self.uri = "accounts"

    def get(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves account information from Shiftbase.

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data).

        Raises:
            ValueError: If account data fails validation
            requests.HTTPError:
                - 501: If the API doesn't support this operation
        """
        # Make the request
        response_data = self.shiftbase.get(self.uri)

        if not response_data or not response_data.get("Account"):
            return pd.DataFrame(), pd.DataFrame()

        # Extract account data
        account_info = response_data.get("Account")

        # Convert to DataFrame
        df = pd.DataFrame([account_info])

        # Validate with Functions.validate_data
        try:
            valid_data, invalid_data = Functions.validate_data(df, AccountGet)
            return valid_data, invalid_data
        except Exception as e:
            error_message = f"Invalid account data: {str(e)}"
            raise ValueError(error_message)

    def get_by_id(self, account_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves account information of a specific account by ID.

        Args:
            account_id (str): The unique identifier of the account

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data).

        Raises:
            ValueError: If account_id is invalid
            requests.HTTPError:
                - 400: If the request is invalid
                - 403: If access is forbidden
                - 404: If the account is not found
        """
        if not account_id or not isinstance(account_id, str):
            raise ValueError("account_id must be a valid string")

        # Construct the endpoint URL
        endpoint = f"{self.uri}/{account_id}"

        # Make the request
        response_data = self.shiftbase.get(endpoint)

        if not response_data or not response_data.get("Account"):
            return pd.DataFrame(), pd.DataFrame()

        account_info = response_data.get("Account")

        # Convert to DataFrame
        df = pd.DataFrame([account_info])

        # Validate with Functions.validate_data
        try:
            valid_data, invalid_data = Functions.validate_data(df, AccountGet)
            return valid_data, invalid_data
        except Exception as e:
            error_message = f"Invalid account data: {str(e)}"
            raise ValueError(error_message)

    def update(self, account_id: str, data: Dict) -> requests.Response:
        """
        Updates an existing account in Shiftbase.

        Args:
            account_id (str): The unique identifier of the account to update
            data (Dict): Dictionary containing the account data to update
                Must match the AccountUpdate structure

        Returns:
            requests.Response: Response from the API containing the updated account details

        Raises:
            ValueError: If account_id is invalid or if the data fails validation
        """
        if not account_id or not isinstance(account_id, str):
            raise ValueError("account_id must be a valid string")

        # Validate input data against the schema using direct Pydantic instantiation
        try:
            # Make sure the ID is included in the data
            update_data = data.copy()
            update_data["id"] = account_id

            validated_data = AccountUpdate(**update_data)
        except Exception as e:
            raise ValueError(f"Invalid account data: {str(e)}")

        # Prepare request body
        request_body = {"Account": validated_data.model_dump(by_alias=True, mode='json')}

        # Construct the endpoint URL
        endpoint = f"{self.shiftbase.base_url}{self.uri}/{account_id}"

        # Make PUT request
        response = self.shiftbase.session.put(endpoint, json=request_body)
        return response
