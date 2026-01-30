from typing import Dict, Optional
import pandas as pd
from .schemas.contract_types import ContractTypeGet
from brynq_sdk_functions import Functions

class ContractTypes:
    """
    Handles all contract type related operations in Shiftbase
    """
    def __init__(self, shiftbase):
        self.shiftbase = shiftbase
        self.uri = "contract_types"

    def get(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves the list of all contract types from Shiftbase.

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data)

        Raises:
            ValueError: If the contract type data fails validation
        """
        # Make the request
        response_data = self.shiftbase.get(self.uri)

        if not response_data:
            return pd.DataFrame(), pd.DataFrame()

        # Extract contract types data
        contract_types = [contract_type.get("ContractType") for contract_type in response_data if contract_type.get("ContractType")]

        # Create DataFrame from response
        df = pd.DataFrame(contract_types)

        # If no data is returned, return empty DataFrames
        if df.empty:
            return pd.DataFrame(), pd.DataFrame()

        # Validate with Functions.validate_data
        try:
            valid_data, invalid_data = Functions.validate_data(df, ContractTypeGet)
            return valid_data, invalid_data
        except Exception as e:
            raise ValueError(f"Invalid contract type data: {str(e)}")

    def get_by_id(self, contract_type_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves a specific contract type by ID.

        Args:
            contract_type_id (str): The unique identifier of the contract type

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data)

        Raises:
            ValueError: If contract_type_id is invalid or contract type data fails validation
            requests.HTTPError:
                - 404: If the contract type is not found
        """
        # Validate contract_type_id
        if not contract_type_id:
            raise ValueError("contract_type_id cannot be empty")

        # Construct the endpoint URL
        endpoint = f"{self.uri}/{contract_type_id}"

        # Make the request
        response_data = self.shiftbase.get(endpoint)

        if not response_data or not response_data.get("ContractType"):
            return pd.DataFrame(), pd.DataFrame()

        contract_type_data = response_data.get("ContractType")

        # Validate with ContractTypeGet
        df = pd.DataFrame([contract_type_data])
        try:
            valid_data, invalid_data = Functions.validate_data(df, ContractTypeGet)
            return valid_data, invalid_data
        except Exception as e:
            raise ValueError(f"Invalid contract type data: {str(e)}")
