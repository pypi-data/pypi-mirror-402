import requests
import os

class ImmichBaseClient:
    """
    Base client for Immich API, handling authentication and low-level requests.

    Attributes:
        server_url (str): The base URL of the Immich server.
        api_url (str): The full URL for the API endpoints.
        headers (dict): Standard headers used for every request.
        session (requests.Session): Persistent session for HTTP requests.
    """
    def __init__(self, server_url, api_key):
        """
        Initialize the ImmichBaseClient.

        Args:
            server_url (str): The base URL of the Immich server (e.g., http://immich.local:2283).
            api_key (str): The API key for authentication.
        """
        self.server_url = server_url.rstrip("/")
        self.api_url = f"{self.server_url}/api"
        self.headers = {
            "x-api-key": api_key,
            "Accept": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _request(self, method, endpoint, **kwargs):
        """
        Internal helper to perform HTTP requests with error handling and response parsing.

        Args:
            method (str): HTTP method (GET, POST, etc.).
            endpoint (str): API endpoint relative to /api.
            **kwargs: Additional arguments passed to requests.request.

        Returns:
            dict | bool | requests.Response: Parsed JSON, True if 204, or raw Response if streaming.

        Raises:
            requests.exceptions.HTTPError: If the request failed.
        """
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
        # Merge extra headers if provided
        headers = kwargs.pop('headers', {})
        
        response = self.session.request(method, url, headers=headers, **kwargs)
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # Try to extract error message from JSON response
            try:
                error_data = response.json()
                error_msg = error_data.get('message', str(e))
                print(f"Immich API Error ({response.status_code}): {error_msg}")
            except Exception:
                print(f"Immich API Error ({response.status_code}): {e}")
            raise

        if response.status_code == 204:
            return True
        
        # For stream downloads or specific content types, return raw response if requested
        if kwargs.get('stream') or 'application/json' not in response.headers.get('Content-Type', ''):
            return response

        return response.json()

    def get(self, endpoint, **kwargs):
        """Perform a GET request."""
        return self._request("GET", endpoint, **kwargs)

    def post(self, endpoint, **kwargs):
        """Perform a POST request."""
        return self._request("POST", endpoint, **kwargs)

    def put(self, endpoint, **kwargs):
        """Perform a PUT request."""
        return self._request("PUT", endpoint, **kwargs)

    def delete(self, endpoint, **kwargs):
        """Perform a DELETE request."""
        return self._request("DELETE", endpoint, **kwargs)

    def patch(self, endpoint, **kwargs):
        """Perform a PATCH request."""
        return self._request("PATCH", endpoint, **kwargs)
