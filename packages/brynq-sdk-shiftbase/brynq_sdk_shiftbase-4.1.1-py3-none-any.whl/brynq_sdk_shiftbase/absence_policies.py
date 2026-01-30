from typing import Dict, Optional, List, Any
import pandas as pd
from uuid import UUID
from .schemas.absence_policies import AbsencePolicyGet
from brynq_sdk_functions import Functions

class AbsencePolicies:
    """
    Handles all absence policy related operations in Shiftbase.
    This class provides methods to interact with the absence policies endpoint.
    An AbsencePolicy is a wrapper around a group of absence settings that can be linked to a user on ContractType level.
    It basically says which AbsenceTypes and TimeOffBalances are available for a ContractType.
    """

    def __init__(self, shiftbase):
        self.shiftbase = shiftbase
        self.uri = "absence/policies/"

    def get(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves all absence policies from Shiftbase.
        This endpoint returns a list of all available absence policies in the system.

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data).
                Each row represents an AbsencePolicy with its properties.
                Nested data structures are flattened using json_normalize.

        Raises:
            ValueError: If the absence policies data fails validation
        """
        response_data = self.shiftbase.get(self.uri)
        if response_data:
            # Normalize nested dictionary data to flat DataFrame first
            normalized_df = pd.json_normalize(
                response_data,
                record_path='configuration',
                meta=['id', 'name', 'description', 'timeOffAccrualSourceHours', 'waitHoursFrom',
                      'waitHoursFromTimeOffBalanceId', 'publicHolidayAbsenceTypeId']
            )

            if normalized_df.empty:
                return pd.DataFrame(), pd.DataFrame()

            # Validate the flattened DataFrame using Pandera schema
            try:
                valid_data, invalid_data = Functions.validate_data(normalized_df, AbsencePolicyGet)
                return valid_data, invalid_data
            except Exception as e:
                raise ValueError(f"Invalid absence policy data: {str(e)}")
        else:
            return pd.DataFrame(), pd.DataFrame()

    def get_by_id(self, policy_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves a specific absence policy by ID from Shiftbase.

        Args:
            policy_id (str): The unique identifier of an absence policy (UUID)

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data).
                Single row DataFrame representing the AbsencePolicy with its properties.
                Nested data structures are flattened using json_normalize.

        Raises:
            ValueError: If policy_id is not a valid UUID or if the data fails validation
        """
        try:
            # Validate UUID format
            UUID(policy_id)
        except ValueError:
            raise ValueError(f"Invalid policy_id: {policy_id}. Must be a valid UUID format.")

        # Get the absence policy data
        response_data = self.shiftbase.get(f"{self.uri}{policy_id}")

        if not response_data:
            return pd.DataFrame(), pd.DataFrame()

        # Normalize nested dictionary data to flat DataFrame first
        normalized_df = pd.json_normalize(
            response_data,
            record_path='configuration',
            meta=['id', 'name', 'description', 'timeOffAccrualSourceHours', 'waitHoursFrom','waitHoursFromTimeOffBalanceId','publicHolidayAbsenceTypeId']
        )

        if normalized_df.empty:
            return pd.DataFrame(), pd.DataFrame()

        # Validate the flattened DataFrame using Pandera schema
        try:
            valid_data, invalid_data = Functions.validate_data(normalized_df, AbsencePolicyGet)
            return valid_data, invalid_data
        except Exception as e:
            raise ValueError(f"Invalid absence policy data for ID {policy_id}: {str(e)}")

    def delete(self, policy_id: str) -> Dict[str, Any]:
        """
        Deletes a specific absence policy from Shiftbase.

        Args:
            policy_id (str): The unique identifier of an absence policy (UUID)

        Returns:
            Dict[str, Any]: Response from the API containing status and metadata

        Raises:
            ValueError: If policy_id is not a valid UUID
        """
        try:
            # Validate UUID format
            UUID(policy_id)
        except ValueError:
            raise ValueError(f"Invalid policy_id: {policy_id}. Must be a valid UUID format.")

        # Send DELETE request to the API
        response = self.shiftbase.session.delete(f"{self.shiftbase.base_url}{self.uri}{policy_id}")
        return response
