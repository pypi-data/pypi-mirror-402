"""
Kipu API Python library

A comprehensive Python library for the Kipu Healthcare API (V3).
Supports all endpoints with HMAC SHA1 authentication and recursive JSON flattening.

Installation:
    pip install kipu-python

Quick Start:
    .. code-block:: python

    import asyncio
    from kipu import KipuClient

    async def main():
        async with KipuClient(
            access_id="your_access_id",
            secret_key="your_secret_key",
            app_id="your_app_id"
        ) as client:
            # Get patient census as flattened DataFrame
            census_df = await client.get_patients_census()
            print(f"Found {len(census_df)} patients")

    asyncio.run(main())

Documentation: https://kipu-python.readthedocs.io/
Source Code: https://github.com/Rahulkumar010/kipu-python
"""

from .client import KipuClient
from .exceptions import (
    KipuAPIError,
    KipuAuthenticationError,
    KipuForbiddenError,
    KipuNotFoundError,
    KipuServerError,
    KipuValidationError,
)
from .flattener import JsonFlattener

__version__ = "0.0.2"
__author__ = "Rahul"
__email__ = "rahul01110100@gmail.com"
__license__ = "MIT"
__description__ = """The Kipu Python library provides convenient access to the Kipu API (V3) from any Python 3.8+ application. The library includes HMAC SHA1 authentication,
                recursive JSON flattening capabilities and type definitions for most of the request params and response fields, and offers asynchronous clients powered by [asyncio]."""

__all__ = [
    "KipuClient",
    "JsonFlattener",
    "KipuAPIError",
    "KipuAuthenticationError",
    "KipuValidationError",
    "KipuNotFoundError",
    "KipuServerError",
    "KipuForbiddenError",
    "__version__",
]

# Package metadata for introspection
__metadata__ = {
    "name": "kipu-python",
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "author_email": __email__,
    "license": __license__,
    "url": "https://github.com/Rahulkumar010/kipu-python",
    "keywords": ["kipu", "healthcare", "api", "library", "medical", "ehr"],
    "python_requires": ">=3.8",
}
