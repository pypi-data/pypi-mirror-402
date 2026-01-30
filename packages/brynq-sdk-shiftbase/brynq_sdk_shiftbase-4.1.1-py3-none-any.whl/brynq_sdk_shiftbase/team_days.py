from typing import Dict, Optional, List, Union
import pandas as pd
import re
from .schemas.team_days import TeamDayGet
from brynq_sdk_functions import Functions

class TeamDays:
    """
    Handles all team day related operations in Shiftbase
    """
    def __init__(self, shiftbase):
        self.shiftbase = shiftbase
        self.uri = "team_days"

    def get(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves a list of team days from Shiftbase.

        Endpoint: GET https://api.shiftbase.com/api/team_days

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: (valid_data, invalid_data) - Valid and invalid team days data

        Raises:
            ValueError: If team day data fails validation
            requests.HTTPError:
                - 403: Forbidden access (insufficient permissions)
        """
        try:
            # Make the request
            response_data = self.shiftbase.get(self.uri)

            # Extract team day data from the response
            team_days = []

            for item in response_data:
                # Extract team day data
                team_day = item.get("TeamDay", {})
                if team_day:
                    team_days.append(team_day)

                # Team info is intentionally ignored in normalization

            # Convert to DataFrame
            df_team_days = pd.DataFrame(team_days)

            # If no data is returned, return empty DataFrames
            if df_team_days.empty:
                return pd.DataFrame(), pd.DataFrame()

            # Validate team day data with Functions.validate_data
            try:
                valid_data, invalid_data = Functions.validate_data(df_team_days, TeamDayGet)

                return valid_data, invalid_data
            except Exception as e:
                error_message = f"Invalid team day data: {str(e)}"
                raise ValueError(error_message)

        except Exception as e:
            if "403" in str(e):
                raise ValueError("Access forbidden. Check if you have 'View team notes' or 'View budget' permission.")
            raise

    def get_by_id(self, team_day_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves a specific team day by its ID.

        Endpoint: GET https://api.shiftbase.com/api/team_days/{teamDayId}

        Args:
            team_day_id (str): The unique identifier of the team day

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: (valid_data, invalid_data) - Valid and invalid team day data

        Raises:
            ValueError: If team_day_id is invalid or team day data fails validation
            requests.HTTPError:
                - 403: Forbidden access (insufficient permissions)
                - 404: Team day not found
        """
        # Validate team_day_id
        if not team_day_id:
            raise ValueError("team_day_id cannot be empty")

        if not re.match(r"^[0-9]+$", team_day_id):
            raise ValueError("team_day_id must contain only digits")

        # Construct the endpoint URL
        endpoint = f"{self.uri}/{team_day_id}"

        try:
            # Make the request
            response_data = self.shiftbase.get(endpoint)

            # The API may return an array with one item
            if isinstance(response_data, list) and len(response_data) > 0:
                response_item = response_data[0]
            else:
                response_item = response_data

            # Extract team day data and team information
            team_day_data = response_item.get("TeamDay", {})
            team_data = response_item.get("Team", {})

            # Convert to DataFrame for validation
            df_team_day = pd.DataFrame([team_day_data])

            # Validate with Functions.validate_data
            try:
                valid_data, invalid_data = Functions.validate_data(df_team_day, TeamDayGet)
                return valid_data, invalid_data
            except Exception as e:
                error_message = f"Invalid team day data: {str(e)}"
                raise ValueError(error_message)

        except Exception as e:
            if "403" in str(e):
                raise ValueError("Access forbidden. Check if you have 'View team notes' or 'View budget' permission.")
            elif "404" in str(e):
                raise ValueError(f"Team day with ID {team_day_id} not found.")
            raise
