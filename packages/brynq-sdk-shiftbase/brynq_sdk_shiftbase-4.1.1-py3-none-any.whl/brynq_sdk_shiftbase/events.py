from typing import Dict, Optional, Tuple
from datetime import date
import pandas as pd
from .schemas.events import EventGet
from brynq_sdk_functions import Functions

class Events:
    """
    Handles all event related operations in Shiftbase
    """
    def __init__(self, shiftbase):
        self.shiftbase = shiftbase
        self.uri = "events"

    def get(self,
            department_id: Optional[str] = None,
            max_date: Optional[date] = None,
            min_date: Optional[date] = None,) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves the list of events from Shiftbase.

        Args:
            department_id (str, optional): Filter on passed department ids
            max_date (str, optional): End of the period to filter (YYYY-MM-DD)
            min_date (str, optional): Start of the period to filter (YYYY-MM-DD)

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data)

        Raises:
            ValueError: If the events data fails validation or parameters are invalid
        """
        # Prepare query parameters
        params = {}
        if department_id:
            params["department_id"] = department_id
        if max_date:
            if not isinstance(max_date, date):
                raise TypeError("max_date must be a datetime object")
            params["max_date"] = max_date.strftime("%Y-%m-%d")
        if min_date:
            if not isinstance(min_date, date):
                raise TypeError("min_date must be a datetime object")
            params["min_date"] = min_date.strftime("%Y-%m-%d")

        # Make the request
        response_data = self.shiftbase.get(self.uri, params)
        if not response_data:
            return pd.DataFrame(), pd.DataFrame()

        # Extract events data
        events = pd.DataFrame(response_data)
        if events.empty:
            return pd.DataFrame(), pd.DataFrame()

        # Validate the data using brynq_sdk_functions
        try:
            valid_data, invalid_data = Functions.validate_data(events, EventGet)
            return valid_data, invalid_data
        except Exception as e:
            raise ValueError(f"Invalid event data: {str(e)}")

    def get_by_id(self, event_id: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves a specific event by ID.

        Args:
            event_id (str): The unique identifier of the event

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data)

        Raises:
            ValueError: If event_id is invalid or event data fails validation
            requests.HTTPError:
                - 400: If the request is invalid
        """
        # Validate event_id
        if not event_id:
            raise ValueError("event_id cannot be empty")

        # Construct the endpoint URL
        endpoint = f"{self.uri}/{event_id}"

        # Make the request
        response_data = self.shiftbase.get(endpoint)
        if not response_data:
            return pd.DataFrame(), pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame([response_data])

        # Validate the data using brynq_sdk_functions
        try:
            valid_data, invalid_data = Functions.validate_data(df, EventGet)
            return valid_data, invalid_data
        except Exception as e:
            raise ValueError(f"Invalid event data: {str(e)}")

    def get_by_sequence(self, sequence_id: str,
                      from_date: Optional[date] = None,
                      to_date: Optional[date] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves a list of events that are part of a sequence.

        When no period is passed, all current events for the sequence will be returned.
        When a period is specified, only events that occur in the given sequence during
        the requested period are returned.

        Args:
            sequence_id (str): Sequence ID to use for fetching a list of events
            from_date (date, optional): Filter for returning only occurrences on/after this date
            to_date (date, optional): Filter for returning only occurrences before/on this date

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (valid_data, invalid_data)

        Raises:
            ValueError: If sequence_id is invalid or events data fails validation
            requests.HTTPError: If the API request fails
        """
        # Validate sequence_id
        if not sequence_id:
            raise ValueError("sequence_id cannot be empty")

        # Construct the endpoint URL
        endpoint = f"{self.uri}/sequence/{sequence_id}"

        # Prepare query parameters
        params = {}
        if from_date:
            if not isinstance(from_date, date):
                raise TypeError("from_date must be a datetime object")
            params["from_date"] = from_date.strftime("%Y-%m-%d")
        if to_date:
            if not isinstance(to_date, date):
                raise TypeError("to_date must be a datetime object")
            params["to_date"] = to_date.strftime("%Y-%m-%d")

        # Make the request
        response_data = self.shiftbase.get(endpoint, params)
        if not response_data:
            return pd.DataFrame(), pd.DataFrame()

        # Extract events data
        events = response_data.get("data", [])
        if not events:
            return pd.DataFrame(), pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(events)

        # Validate the data using brynq_sdk_functions
        try:
            valid_data, invalid_data = Functions.validate_data(df, EventGet)
            return valid_data, invalid_data
        except Exception as e:
            raise ValueError(f"Invalid event data: {str(e)}")
