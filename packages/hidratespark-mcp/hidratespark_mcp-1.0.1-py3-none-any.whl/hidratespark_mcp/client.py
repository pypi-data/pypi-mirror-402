"""
HidrateSpark API Client

Python client for HidrateSpark Parse API with session token caching.
"""

import os
import json
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any


class HidrateClient:
    """Client for HidrateSpark Parse API"""

    def __init__(
        self,
        app_id: Optional[str] = None,
        client_key: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        server_url: Optional[str] = None
    ):
        """
        Initialize HidrateSpark client.

        Args:
            app_id: Parse Application ID (from env HIDRATE_APP_ID if not provided)
            client_key: Parse Client Key (from env HIDRATE_CLIENT_KEY if not provided)
            email: User email (from env HIDRATE_EMAIL if not provided)
            password: User password (from env HIDRATE_PASSWORD if not provided)
            server_url: Server URL (default: https://www.hidrateapp.com/parse)
        """
        self.app_id = app_id or os.getenv("HIDRATE_APP_ID")
        self.client_key = client_key or os.getenv("HIDRATE_CLIENT_KEY")
        self.email = email or os.getenv("HIDRATE_EMAIL")
        self.password = password or os.getenv("HIDRATE_PASSWORD")
        self.server_url = server_url or os.getenv(
            "HIDRATE_SERVER_URL", "https://www.hidrateapp.com/parse"
        )

        if not all([self.app_id, self.client_key, self.email, self.password]):
            raise ValueError(
                "Missing required credentials. Provide via parameters or environment variables:\n"
                "HIDRATE_APP_ID, HIDRATE_CLIENT_KEY, HIDRATE_EMAIL, HIDRATE_PASSWORD"
            )

        # Session token cache (in-memory only, not persisted for security)
        self._session_token: Optional[str] = None
        self._user_data: Optional[Dict[str, Any]] = None

    def _get_headers(self, include_session: bool = False) -> Dict[str, str]:
        """Generate headers for API requests."""
        headers = {
            'X-Parse-Application-Id': self.app_id,
            'X-Parse-REST-API-Key': self.client_key,
            'X-Parse-Client-Key': self.client_key,
            'Content-Type': 'application/json'
        }

        if include_session and self._session_token:
            headers['X-Parse-Session-Token'] = self._session_token

        return headers

    def _ensure_logged_in(self):
        """Ensure user is logged in (lazy authentication)."""
        if not self._session_token:
            self.login()

    def login(self) -> Dict[str, Any]:
        """
        Login to HidrateSpark API.

        Returns:
            dict: User data including session token

        Raises:
            requests.HTTPError: If login fails
        """
        url = f"{self.server_url}/login"
        params = {
            'username': self.email,
            'password': self.password
        }

        resp = requests.get(url, headers=self._get_headers(), params=params)
        resp.raise_for_status()

        data = resp.json()
        self._session_token = data.get('sessionToken')
        self._user_data = data

        return data

    def get_bottles(self) -> List[Dict[str, Any]]:
        """
        Get list of registered bottles.

        Returns:
            list: List of bottle objects
        """
        self._ensure_logged_in()

        url = f"{self.server_url}/classes/Bottle"
        params = {'limit': 10}

        resp = requests.get(url, headers=self._get_headers(include_session=True), params=params)
        resp.raise_for_status()

        return resp.json().get('results', [])

    def get_sips(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get sips (water intake records).

        IMPORTANT: Filters on 'time' field (actual sip time), NOT 'createdAt' (sync time).
        This prevents including sips from previous days that were synced late.

        Args:
            start_date: Start date filter (inclusive)
            end_date: End date filter (inclusive)
            limit: Maximum number of results (default 100)

        Returns:
            list: List of sip objects
        """
        self._ensure_logged_in()

        url = f"{self.server_url}/classes/Sip"

        # Build MongoDB-style query
        where = {}

        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date)
            where['time'] = {'$gte': {'__type': 'Date', 'iso': start_date.isoformat()}}

        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)
            if 'time' in where:
                where['time']['$lte'] = {'__type': 'Date', 'iso': end_date.isoformat()}
            else:
                where['time'] = {'$lte': {'__type': 'Date', 'iso': end_date.isoformat()}}

        params = {
            'limit': limit,
            'order': '-time'  # Order by actual sip time, not sync time
        }

        if where:
            params['where'] = json.dumps(where)

        resp = requests.get(url, headers=self._get_headers(include_session=True), params=params)
        resp.raise_for_status()

        return resp.json().get('results', [])

    def get_daily_summary(self, date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Get daily summary for a specific date.

        Args:
            date: Date to get summary for (default: today)

        Returns:
            dict: Daily summary object or None if not found
        """
        self._ensure_logged_in()

        url = f"{self.server_url}/classes/Day"

        if date is None:
            date = datetime.now()
        elif isinstance(date, str):
            date = datetime.fromisoformat(date)

        date_str = date.strftime('%Y-%m-%d')

        where = {'date': date_str}
        params = {
            'where': json.dumps(where),
            'limit': 1
        }

        resp = requests.get(url, headers=self._get_headers(include_session=True), params=params)
        resp.raise_for_status()

        results = resp.json().get('results', [])
        return results[0] if results else None

    def log_sip(
        self,
        amount_ml: float,
        timestamp: Optional[datetime] = None,
        liquid_type_id: str = "lWmCrAgXtH"  # Default: water
    ) -> Dict[str, Any]:
        """
        Log a manual sip entry.

        Args:
            amount_ml: Amount in milliliters
            timestamp: When the sip occurred (default: now)
            liquid_type_id: LiquidTypeInfo objectId (default: water)

        Returns:
            dict: Created sip object
        """
        self._ensure_logged_in()

        url = f"{self.server_url}/classes/Sip"

        if timestamp is None:
            timestamp = datetime.now()
        elif isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        import uuid
        sip_id = str(uuid.uuid4())

        payload = {
            "time": {
                "__type": "Date",
                "iso": timestamp.isoformat()
            },
            "amount": amount_ml,
            "start": 0,
            "stop": 0,
            "max": 0,
            "min": 0,
            "liquidTypeInfo": {
                "__type": "Pointer",
                "className": "LiquidTypeInfo",
                "objectId": liquid_type_id
            },
            "clientSipId": sip_id,
            "uniqueSipId": sip_id,
            "hydrationImpact": 1,
            "timeZone": "Europe/Rome"
        }

        resp = requests.post(
            url,
            headers=self._get_headers(include_session=True),
            json=payload
        )
        resp.raise_for_status()

        return resp.json()

    def get_user_profile(self) -> Dict[str, Any]:
        """
        Get current user profile.

        Returns:
            dict: User profile data
        """
        if self._user_data:
            return self._user_data

        self._ensure_logged_in()
        return self._user_data
