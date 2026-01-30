"""
OO Client module for interacting with Operations Orchestration.
"""

from typing import Any
import logging

import requests
from requests.auth import HTTPBasicAuth

# Suppress InsecureRequestWarning when verify=False
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from itom_library.utilities import format_table

logger = logging.getLogger(__name__)


class OOClientError(Exception):
    """Base exception for OO Client errors."""
    pass


class OOAuthenticationError(OOClientError):
    """Raised when authentication fails."""
    pass


class OOAPIError(OOClientError):
    """Raised when an API call fails."""
    pass


class OOClient:
    """
    Client for interacting with OpenText Operations Orchestration (OO) REST API.

    This client handles authentication and provides methods to interact with
    OO flows and other resources.

    Args:
        base_url: The base URL of the OO server (e.g., 'https://localhost:5555/oo')
        username: Username for authentication
        password: Password for authentication
        timeout: Request timeout in seconds (default: 30)
        verify_ssl: Whether to verify SSL certificates (default: True)

    Example:
        >>> from itom_library import OOClient
        >>> client = OOClient(
        ...     base_url='https://localhost:5555/oo',
        ...     username='admin',
        ...     password='your_password'
        ... )
        >>> flows = client.get_flows()
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        timeout: int = 30,
        verify_ssl: bool = True,
        table: bool = False
    ):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.table = table
        
        self._x_csrf_token: str | None = None
        self._cookies: str | None = None
        
        # Authenticate during initialization
        self._authenticate()

    def _authenticate(self) -> None:
        """
        Authenticate with the OO server and obtain CSRF token.

        Raises:
            OOAuthenticationError: If authentication fails or token is not found.
        """
        try:
            response = requests.head(
                self.base_url,
                auth=HTTPBasicAuth(self.username, self.password),
                timeout=self.timeout,
                allow_redirects=True,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            
            x_csrf_token = response.headers.get('X-CSRF-TOKEN')
            if not x_csrf_token:
                raise OOAuthenticationError(
                    'Authentication token not found in response headers.'
                )
            
            self._x_csrf_token = x_csrf_token
            
            # Extract cookies from response
            cookies = response.cookies
            self._cookies = '; '.join(
                [f"{name}={value}" for name, value in cookies.items()]
            )
            
            logger.debug("Successfully authenticated with OO server")
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error during authentication: {e}")
            raise OOAuthenticationError(f'Authentication failed: {e}') from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error during authentication: {e}")
            raise OOAuthenticationError(
                f'Error connecting to OO server: {e}'
            ) from e

    def _get_headers(self) -> dict[str, str]:
        """Get headers for authenticated requests."""
        return {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': self._x_csrf_token or '',
            'Cookie': self._cookies or ''
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any
    ) -> requests.Response:
        """
        Make an authenticated request to the OO API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (will be appended to base_url)
            **kwargs: Additional arguments passed to requests

        Returns:
            Response object

        Raises:
            OOAPIError: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        # Set defaults
        kwargs.setdefault('headers', self._get_headers())
        kwargs.setdefault('timeout', self.timeout)
        kwargs.setdefault('verify', self.verify_ssl)
        
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {method} {url}: {e}")
            raise OOAPIError(f'API request failed: {e}') from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {method} {url}: {e}")
            raise OOAPIError(f'Error connecting to OO server: {e}') from e

    def get_flows(self) -> dict[str, Any]:
        """
        Get all flows from the OO library.

        Returns:
            dict: Dictionary containing the flows data.

        Raises:
            OOAPIError: If the request fails.

        Example:
            >>> client = OOClient(base_url, username, password)
            >>> flows = client.get_flows()
            >>> print(flows)
        """
        response = self._request('GET', '/rest/latest/flows/library')
        if self.table:
            return format_table(response.json())
        else:
            return response.json()

    def get_flow_inputs(self,flow_id: str) -> dict:
        """
        Fetch input details for a specified OO flow.
        
        Args:
            flow_id: The ID of the OO flow to fetch inputs for
            
        Returns:
            dict: Dictionary containing inputs
        
        Raises:
            OOAPIError: If the request fails.

        Example:
            >>> client = OOClient(base_url, username, password)
            >>> inputs = client.get_flow_inputs(flow_id)
            >>> print(inputs)
        """
        response = self._request('GET', f'/rest/latest/flows/{flow_id}/inputs')
        if self.table:
            return format_table(response.json())
        else:
            return response.json()
    
    def __repr__(self) -> str:
        return f"OOClient(base_url='{self.base_url}', username='{self.username}')"
