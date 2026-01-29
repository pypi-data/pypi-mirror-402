Usage
=====

Here are some examples to help you get started with kipu-python.

.. code-block:: python
   
    import asyncio
    from kipu import KipuClient

    # Example usage
    async def main():
        async with KipuClient(
            access_id="your_access_id",
            secret_key="your_secret_key",
            app_id="your_app_id",
            version=3  # Use 3 for SHA1, 4 for SHA256
        ) as client:
            # Get patient census as flattened DataFrame
            census_df = await client.get_patients_census({"phi_level": "high",
                                                            "page": 1, 
                                                            "per": 10})
            print(f"Found {len(census_df)} patients")

    asyncio.run(main())

API Version Support
-------------------

The library supports both Kipu API v3 and v4:

- **V3:** Uses HMAC-SHA1 authentication (default, most stable)
- **V4:** Uses HMAC-SHA256 authentication (newer, more secure)

.. code-block:: python

    # Use V3 (SHA1)
    client_v3 = KipuClient(access_id, secret_key, app_id, version=3)
    
    # Use V4 (SHA256 - recommended for new integrations)
    client_v4 = KipuClient(access_id, secret_key, app_id, version=4)

Refer to the API Reference for detailed function descriptions.