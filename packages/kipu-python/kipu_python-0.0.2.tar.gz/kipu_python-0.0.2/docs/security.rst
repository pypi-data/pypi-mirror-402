Security
========

Healthcare Data Handling
-------------------------

This library is designed for use with protected health information (PHI) and must comply with HIPAA regulations.

Supported Versions
------------------

+---------+-----------------------+
| Version | Supported             |
+=========+=======================+
| 0.0.x   | ✅ Yes                |
+---------+-----------------------+

Security Best Practices
-----------------------

1. Credential Management
^^^^^^^^^^^^^^^^^^^^^^^^

**DO:**

- Store credentials in environment variables or secure credential stores
- Use unique credentials per environment (dev/staging/production)
- Rotate credentials regularly

**DON'T:**

- Hardcode credentials in source code
- Commit credentials to version control
- Share credentials via email or chat

2. PHI Logging
^^^^^^^^^^^^^^

**CRITICAL:** Never log patient data or PHI

.. code-block:: python

    # BAD - Logs patient data
    logger.info(f"Patient data: {patient}")

    # GOOD - Log only non-PHI identifiers
    logger.info(f"Processing patient ID: {patient_id}")

3. Transport Security
^^^^^^^^^^^^^^^^^^^^^

- Always use HTTPS (default in this library)
- Verify SSL certificates (enabled by default)
- Use minimum TLS 1.2

4. Error Handling
^^^^^^^^^^^^^^^^^

When catching exceptions, avoid logging full response data which may contain PHI:

.. code-block:: python

    try:
        patient = await client.get_patient(patient_id)
    except KipuAPIError as e:
        # GOOD - Log only status code
        logger.error(f"API error: status {e.status_code}")
        
        # BAD - May log PHI
        # logger.error(f"API error: {e.response_data}")

5. Data at Rest
^^^^^^^^^^^^^^^

If caching responses:

- Encrypt cached data
- Use short TTL values
- Implement secure cache invalidation

Reporting a Vulnerability
--------------------------

To report a security vulnerability:

1. **Email:** rahul01110100@gmail.com with subject "SECURITY: kipu-python"
2. **Include:**

   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

3. **Response Time:** I aim to respond within 48 hours

**Please DO NOT:**

- Open public GitHub issues for security vulnerabilities
- Disclose vulnerabilities publicly before a fix is available

Security Updates
----------------

Security updates will be released as patch versions and documented in the changelog with a ``[SECURITY]`` tag.
