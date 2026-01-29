"""
Authentication module for Kipu API
Implements HMAC SHA1 signature generation as per Kipu API documentation
"""

import base64
import hashlib
import hmac
from email.utils import formatdate
from typing import Dict


class KipuAuth:
    def __init__(self, access_id: str, secret_key: str, app_id: str, version: int):
        """
        Initialize Kipu authentication

        Args:
            access_id: Your access ID provided by Kipu
            secret_key: Your secret key provided by Kipu
            app_id: Your app ID (also called recipient_id) provided by Kipu
            version: API version (3 for SHA1, 4 for SHA256)
        """
        self.access_id = access_id
        self.secret_key = secret_key
        self.app_id = app_id
        self.version = version

    def generate_signature(
        self,
        method: str,
        uri: str,
        date: str,
        content_type: str = "",
        content_md5: str = "",
    ) -> str:
        """
        Generate HMAC signature for Kipu API request
        Uses SHA1 for API v3, SHA256 for API v4

        Args:
            method: HTTP method (GET, POST, PATCH)
            uri: Request URI including query parameters
            date: RFC 822 formatted date string
            content_type: Content-Type header (for POST requests)
            content_md5: MD5 hash of request body (for POST requests)

        Returns:
            Base64 encoded HMAC signature (algorithm depends on version)
        """
        # Build canonical string based on method
        if method.upper() == "GET":
            # For GET: ,,request_uri,Date
            canonical_string = f",,{uri},{date}"
        else:
            # For POST/PATCH: Content-Type,Content-MD5,request_uri,Date
            canonical_string = f"{content_type},{content_md5},{uri},{date}"

        # Create HMAC SHA1 hash
        hmac_hash = hmac.new(
            self.secret_key.encode("utf-8"),
            canonical_string.encode("utf-8"),
            hashlib.sha1 if self.version <= 3 else hashlib.sha256,
        )

        # Base64 encode the hash
        signature = base64.b64encode(hmac_hash.digest()).decode("utf-8")

        return signature

    def get_auth_headers(
        self, method: str, uri: str, body: bytes = b"", content_type: str = ""
    ) -> Dict[str, str]:
        """
        Generate complete authentication headers for Kipu API request

        Args:
            method: HTTP method
            uri: Request URI
            body: Request body (for POST requests)
            content_type: Content-Type header

        Returns:
            Dictionary of headers needed for authentication
        """
        # Generate RFC 822 date
        date = formatdate(timeval=None, localtime=False, usegmt=True)

        # Generate Content-MD5 for POST requests
        content_md5 = ""
        if method.upper() in ["POST", "PATCH"] and body:
            md5_hash = hashlib.md5(body)  # nosec
            content_md5 = base64.b64encode(md5_hash.digest()).decode("utf-8")  # nosec

        # Generate signature
        signature = self.generate_signature(
            method, uri, date, content_type, content_md5
        )
        auth_type = "APIAuth" if self.version <= 3 else "APIAuth-HMAC-SHA256"

        # Build headers
        headers = {
            "Accept": f"application/vnd.kipusystems+json; version={self.version}",
            "Authorization": f"{auth_type} {self.access_id}:{signature}",
            "Date": date,
        }

        # Add content headers for POST/PATCH requests
        if method.upper() in ["POST", "PATCH"]:
            if content_type:
                headers["Content-Type"] = content_type
            if content_md5:
                headers["Content-MD5"] = content_md5

        return headers

    def add_app_id_to_params(self, params: Dict[str, str]) -> Dict[str, str]:
        """
        Add app_id to query parameters

        Args:
            params: Existing query parameters

        Returns:
            Parameters with app_id added
        """
        if params is None:
            params = {}
        params["app_id"] = self.app_id
        return params
