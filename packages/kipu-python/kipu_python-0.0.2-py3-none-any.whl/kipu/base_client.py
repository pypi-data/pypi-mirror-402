"""
Base HTTP client for Kipu API
Handles low-level HTTP operations with proper authentication and error handling
"""

import json
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import aiohttp

from .auth import KipuAuth
from .exceptions import (
    KipuAPIError,
    KipuAuthenticationError,
    KipuForbiddenError,
    KipuNotFoundError,
    KipuServerError,
    KipuValidationError,
)


class BaseKipuClient:
    def __init__(
        self,
        access_id: str,
        secret_key: str,
        app_id: str,
        base_url: str = "https://api.kipuapi.com",
        version: int = 3,
        timeout: int = 30,
    ):
        """
        Initialize base Kipu API client

        Args:
            access_id: Your access ID provided by Kipu
            secret_key: Your secret key provided by Kipu
            app_id: Your app ID provided by Kipu
            base_url: Base URL for Kipu API (default: https://api.kipuapi.com)
            version: API version (3 for SHA1, 4 for SHA256)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.auth = KipuAuth(access_id, secret_key, app_id, version)
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        # Explicit SSL verification for security
        connector = aiohttp.TCPConnector(ssl=True)
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout), connector=connector
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def _handle_error(self, status_code: int, response_data: dict) -> None:
        """
        Handle API errors based on status code

        Args:
            status_code: HTTP status code
            response_data: Response data from API

        Raises:
            Appropriate KipuAPIError subclass
        """
        error_message = response_data.get("error", f"HTTP {status_code} error")

        if status_code == 401:
            raise KipuAuthenticationError(error_message, status_code, response_data)
        elif status_code == 403:
            raise KipuForbiddenError(error_message, status_code, response_data)
        elif status_code == 404:
            raise KipuNotFoundError(error_message, status_code, response_data)
        elif status_code in [400, 422]:
            raise KipuValidationError(error_message, status_code, response_data)
        elif status_code >= 500:
            raise KipuServerError(error_message, status_code, response_data)
        else:
            raise KipuAPIError(error_message, status_code, response_data)

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make authenticated HTTP request to Kipu API

        Args:
            method: HTTP method (GET, POST, PATCH)
            endpoint: API endpoint (e.g., '/api/patients')
            params: Query parameters
            data: Request body data
            files: Files for multipart upload

        Returns:
            JSON response data

        Raises:
            Various KipuAPIError subclasses
        """
        if not self.session:
            raise KipuAPIError(
                "Client session not initialized. Use 'async with' context manager."
            )

        # Add app_id to parameters
        if params is None:
            params = {}
        params = self.auth.add_app_id_to_params(params)

        # Build full URL
        url = f"{self.base_url}{endpoint}"
        if params:
            url += f"?{urlencode(params)}"

        # Prepare request body and content type
        request_body = None
        content_type = ""

        if files:
            # Handle multipart form data (for file uploads)
            form_data = aiohttp.FormData()

            # Add regular data fields
            if data:
                for key, value in data.items():
                    form_data.add_field(key, str(value))

            # Add file fields
            for key, file_info in files.items():
                if isinstance(file_info, dict):
                    form_data.add_field(
                        key,
                        file_info["content"],
                        filename=file_info.get("filename", "file"),
                        content_type=file_info.get(
                            "content_type", "application/octet-stream"
                        ),
                    )
                else:
                    form_data.add_field(key, file_info)

            request_body = form_data
            content_type = f"multipart/form-data; boundary={form_data._boundary}"

        elif data and method.upper() in ["POST", "PATCH"]:
            # Handle JSON data
            request_body = json.dumps(data).encode("utf-8")
            content_type = "application/json"

        # Get authentication headers
        uri_path = endpoint
        if params:
            uri_path += f"?{urlencode(params)}"

        headers = self.auth.get_auth_headers(
            method,
            uri_path,
            request_body if isinstance(request_body, bytes) else None,
            content_type,
        )

        # Make request
        try:
            async with self.session.request(
                method,
                url,
                headers=headers,
                data=request_body if not files else form_data,
            ) as response:

                # Get response data
                try:
                    response_data = await response.json()
                except Exception:
                    response_data = {"error": await response.text()}

                # Handle errors
                if response.status >= 400:
                    self._handle_error(response.status, response_data)

                return response_data

        except aiohttp.ClientError as e:
            raise KipuAPIError(f"HTTP client error: {str(e)}")

    async def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make GET request"""
        return await self._make_request("GET", endpoint, params=params)

    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make POST request"""
        return await self._make_request("POST", endpoint, data=data, files=files)

    async def patch(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make PATCH request"""
        return await self._make_request("PATCH", endpoint, data=data, files=files)
