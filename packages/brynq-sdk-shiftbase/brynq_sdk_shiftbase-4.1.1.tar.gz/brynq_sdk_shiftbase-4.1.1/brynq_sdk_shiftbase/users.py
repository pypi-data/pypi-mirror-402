from typing import Dict, Optional, List, Any
import pandas as pd
import re
from .schemas.users import UserGet, UserGetById, UsersGroupGet, UserCreate, UserUpdate
from brynq_sdk_functions import Functions

class Users:
    """
    Handles all User related operations in Shiftbase
    """
    def __init__(self, shiftbase):
        self.shiftbase = shiftbase
        self.uri = "users"

    def get(self,
            active: Optional[str] = None,
            allow_hidden: Optional[str] = None,
            department_id: Optional[str] = None) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves all users from Shiftbase.

        Endpoint: GET https://api.shiftbase.com/api/users

        Notes:
            - It will only return users that are part of departments you have access to.
            - Depending on permissions, more user information may be available.

        Args:
            active (str, optional): '1' to fetch only active users, '0' to fetch only inactive users
            allow_hidden (str, optional): Set to any value to include hidden users
            department_id (str, optional): Filter on department ID

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data)

        Raises:
            ValueError: If parameters are invalid or user data fails validation
            requests.HTTPError: If the API request fails
        """
        # Validate parameters
        if active is not None and active not in ['0', '1']:
            raise ValueError("active must be '0' or '1'")

        if department_id is not None and not re.match(r"^[0-9]+$", department_id):
            raise ValueError("department_id must contain only digits")

        # Prepare query parameters
        params = {}
        if active is not None:
            params["active"] = active
        if allow_hidden is not None:
            params["allow_hidden"] = allow_hidden
        if department_id is not None:
            params["department_id"] = department_id

        # Make the request
        response_data = self.shiftbase.get(self.uri, params)

        if not response_data:
            return pd.DataFrame(), pd.DataFrame()

        # Use pandas json_normalize to flatten the nested structure
        df = pd.json_normalize(response_data, sep="_", max_level=1)

        if df.empty:
            return pd.DataFrame(), pd.DataFrame()

        # Validate the DataFrame against the schema using brynq_sdk_functions
        try:
            valid_data, invalid_data = Functions.validate_data(df, UserGet)
            return valid_data, invalid_data
        except Exception as e:
            raise ValueError(f"Invalid user data: {str(e)}")

    def get_by_id(self, identifier: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves a specific user by its ID or email.

        Endpoint: GET https://api.shiftbase.com/api/users/{identifier}

        Notes:
            - It will only return users that are part of departments you have access to.
            - Required permissions: View user details, View own profile, Edit own profile

        Args:
            identifier (str): A user ID or an email address

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data)

        Raises:
            ValueError: If identifier is invalid or user data fails validation
            requests.HTTPError:
                - 404: User not found
                - 403: Unauthorized access
        """
        # Validate identifier
        if not identifier:
            raise ValueError("identifier cannot be empty")

        # Construct the endpoint URL
        endpoint = f"{self.uri}/{identifier}"

        try:
            # Make the request
            response_data = self.shiftbase.get(endpoint)

            if not response_data or "User" not in response_data:
                return pd.DataFrame(), pd.DataFrame()

            # Extract the User data and flatten it
            user_data = response_data["User"]
            df = pd.json_normalize(user_data, sep="_", max_level=1)

            if df.empty:
                return pd.DataFrame(), pd.DataFrame()

            # Validate the DataFrame against the UserGetById schema
            try:
                valid_data, invalid_data = Functions.validate_data(df, UserGetById)
                return valid_data, invalid_data
            except Exception as e:
                raise ValueError(f"Invalid user data: {str(e)}")
        except Exception as e:
            if "404" in str(e):
                raise ValueError(f"User with identifier {identifier} not found.")
            if "403" in str(e):
                raise ValueError("Unauthorized access: You don't have permission to view this user.")
            raise

    def create(self, data: Dict) -> Dict:
        """
        Creates a new user in Shiftbase.

        Args:
            data (Dict): Must be of format:
                {
                    "User": { ...validated user fields... },
                    "Team": [...],
                    "UsersGroup": [...],
                    "Contract": [...],
                    "Skill": [...]
                }

        Returns:
            Dict: Response from Shiftbase API

        Raises:
            ValueError: On validation issues
            requests.HTTPError: On API response error
        """
        # Validate the "User" section against the schema using direct Pydantic instantiation
        try:
            user_data = data.get("User", {})
            validated_user = UserCreate(**user_data)
        except Exception as e:
            raise ValueError(f"Invalid user data: {str(e)}")

        # Convert Pydantic model to dict and strip None values
        cleaned_user = validated_user.model_dump(exclude_none=True, mode="json")

        # Build request payload
        request_payload = {
            "User": cleaned_user
        }

        # Attach any optional sections
        for key in ["Team", "UsersGroup", "Contract", "Skill"]:
            if key in data and data[key]:
                request_payload[key] = data[key]

        # Execute request
        response = self.shiftbase.session.post(
            f"{self.shiftbase.base_url}{self.uri}",
            json=request_payload,
            headers={"Content-Type": "application/json"}
        )

        # Raise any errors and return response
        response.raise_for_status()

        # Return the response JSON
        return response.json()

    def update(self, identifier: str, data: Dict) -> Dict:
        """
        Updates an existing user in Shiftbase.

        Calls the API endpoint: PUT https://api.shiftbase.com/api/users/{identifier}

        Args:
            identifier (str): A user ID or an email address
            data (Dict): Dictionary containing the user data to update.
                Must match the UserUpdateSchema structure.

        Returns:
            Dict: Response from the API containing the updated user details.

        Raises:
            ValueError: If the data fails validation or if the update fails
            requests.HTTPError: If the API returns a non-successful status
                - 400: Bad request or invalid parameters
                - 403: Missing required permission(s) - Need 'Edit users' or 'Edit own profile'
                - 404: User not found
                - 422: Unprocessable entity (e.g., validation failed)
        """
        # Validate identifier
        if not identifier:
            raise ValueError("identifier cannot be empty")

        # Validate input data against the schema using direct Pydantic instantiation
        try:
            validated_data = UserUpdate(**data)
        except Exception as e:
            raise ValueError(f"Invalid user data: {str(e)}")

        # Convert Pydantic model to dict and filter out None values
        request_body = validated_data.model_dump(exclude_none=True, mode="json")

        # Make PUT request
        endpoint = f"{self.uri}/{identifier}"
        response = self.shiftbase.session.put(
            f"{self.shiftbase.base_url}{endpoint}",
            json=request_body,
            headers={"Content-Type": "application/json"}
        )

        # Raise exception if the request failed
        response.raise_for_status()

        # Return the response JSON
        return response.json()


    def deactivate(self, identifier: str) -> Dict:
        """
        Deactivates a user in Shiftbase.

        This will disable the user from logging in but won't delete the user data completely.

        Calls the API endpoint: DELETE https://api.shiftbase.com/api/users/{identifier}

        Args:
            identifier (str): A user ID or an email address

        Returns:
            Dict: Response from the API confirming the deactivation.

        Raises:
            ValueError: If identifier is invalid
            requests.HTTPError: If the API returns a non-successful status
                - 403: Missing required permission(s) - Need 'Delete users'
                - 404: User not found
        """
        # Validate identifier
        if not identifier:
            raise ValueError("identifier cannot be empty")

        # Make DELETE request
        endpoint = f"{self.uri}/{identifier}"
        response = self.shiftbase.session.delete(f"{self.shiftbase.base_url}{endpoint}")

        # Raise exception if the request failed
        response.raise_for_status()

        # Return the response JSON
        return response.json()

    def activate(self, identifier: str) -> Dict:
        """
        (Re)activates a user in Shiftbase.

        This will enable a previously deactivated user to login again.

        Calls the API endpoint: PUT https://api.shiftbase.com/api/users/{identifier}/activate

        Args:
            identifier (str): A user ID or an email address

        Returns:
            Dict: Response from the API confirming the activation.

        Raises:
            ValueError: If identifier is invalid
            requests.HTTPError: If the API returns a non-successful status
                - 403: Missing required permission(s) - Need 'Activate users'
                - 404: User not found
        """
        # Validate identifier
        if not identifier:
            raise ValueError("identifier cannot be empty")

        # Make PUT request
        endpoint = f"{self.uri}/{identifier}/activate"
        response = self.shiftbase.session.put(f"{self.shiftbase.base_url}{endpoint}")

        # Raise exception if the request failed
        response.raise_for_status()

        # Return the response JSON
        return response.json()

    def anonymize(self, identifier: str) -> Dict:
        """
        Anonymizes a user's data in Shiftbase.

        This will anonymize the data of inactive employees.
        The user must be inactive (deactivated) before they can be anonymized.

        Calls the API endpoint: DELETE https://api.shiftbase.com/api/users/{identifier}/anonymize

        Args:
            identifier (str): A user ID or an email address

        Returns:
            Dict: Response from the API confirming the anonymization.

        Raises:
            ValueError: If identifier is invalid
            requests.HTTPError: If the API returns a non-successful status
                - 403: Missing required permission(s) - Need 'Delete users'
                - 404: User not found
                - 422: User is still active (must be deactivated first)
        """
        # Validate identifier
        if not identifier:
            raise ValueError("identifier cannot be empty")

        # Make DELETE request
        endpoint = f"{self.uri}/{identifier}/anonymize"
        response = self.shiftbase.session.delete(f"{self.shiftbase.base_url}{endpoint}")

        # Raise exception if the request failed
        response.raise_for_status()

        # Return the response JSON
        return response.json()
