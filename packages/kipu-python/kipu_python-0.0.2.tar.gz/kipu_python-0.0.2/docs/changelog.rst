Changelog
=========


Changelog
=========

All notable changes to the Kipu API Python library will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_\ ,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

[0.0.2] - 2026-01-19
--------------------

Added
^^^^^


* 🔒 **SECURITY.md**\ : Comprehensive security documentation for HIPAA compliance
* 🧪 **V4 Authentication Tests**\ : Added tests for SHA256 authentication (API v4)
* ✅ **Enhanced Test Coverage**\ : Added 3 new tests for V3/V4 authentication verification

Changed
^^^^^^^


* 📝 **Documentation Improvements**\ : 

  * Fixed syntax error in README.md code example
  * Simplified kipu/README.md to avoid duplication
  * Enhanced auth.py docstrings to clarify V3 (SHA1) and V4 (SHA256) support

* 🔐 **Security Enhancements**\ : Added explicit SSL verification in HTTP client

Fixed
^^^^^


* 🐛 **Test Fixes**\ : Added missing version parameter to all KipuAuth test initializations

----

[0.0.1] - 2025-01-19
--------------------

Added
^^^^^


* 🎉 Initial release of the Kipu API Python library
* ✅ Complete implementation of all 80+ Kipu API V3 endpoints
* 🔐 HMAC SHA1 authentication with automatic signature generation
* 📊 Automatic JSON flattening to pandas DataFrames using recursive algorithm
* ⚡ Async/await support for high-performance API calls
* 🛡️ Comprehensive error handling with custom exception hierarchy
* 📝 Full type hints for better IDE support and development experience
* 🔄 Flexible response format (raw JSON or flattened DataFrames)
* 📦 PyPI package distribution with proper metadata
* 🧪 Complete test suite with validation
* 📚 Comprehensive documentation and examples
* 🖥️ Command-line interface (CLI) for testing and utilities
* 🏥 Healthcare-focused API coverage including:

  * Patient management (CRUD operations)
  * Medical records (vital signs, allergies, assessments)
  * Appointments and scheduling
  * Evaluations and forms
  * User and provider management
  * Administrative functions
  * Insurance and billing
  * Group sessions and care teams

Security
^^^^^^^^


* 🔒 Secure HMAC SHA1 signature generation
* 🛡️ Proper handling of sensitive healthcare data
* 🔐 Environment variable-based credential management

Documentation
^^^^^^^^^^^^^


* 📖 Complete README with usage examples
* 📚 API reference documentation
* 🚀 Quick start guide
* 💡 Code examples for all major use cases
* 🧪 Testing and development guidelines

Dependencies
^^^^^^^^^^^^


* ``aiohttp>=3.8.0`` - Async HTTP client
* ``pandas>=1.3.0`` - Data manipulation and analysis
* ``numpy>=1.20.0`` - Numerical computing
* ``tqdm>=4.60.0`` - Progress bars for data processing

Endpoints Implemented
^^^^^^^^^^^^^^^^^^^^^


* **Patient Management**\ : Census, individual records, create/update, admissions
* **Medical Records**\ : Vital signs, allergies, assessments (CIWA, COWS), glucose logs
* **Appointments**\ : Scheduling, types, statuses, resources, patient/provider scoped
* **Evaluations**\ : Patient evaluations, templates, forms
* **Users & Providers**\ : User management, provider records, roles, permissions
* **Administrative**\ : Locations, care levels, flags, patient settings
* **Insurance**\ : Records, verification, updates
* **Groups**\ : Group sessions, patient groups, care teams
* **Consent Forms**\ : Forms, records, patient consent management
* **Utilization Reviews**\ : Patient UR records, latest updates

CLI Features
^^^^^^^^^^^^


* Connection testing
* Patient census retrieval
* Vital signs data access
* Raw JSON or flattened DataFrame output options
* Environment variable credential management

----

Development Notes
-----------------

Version 0.0.1 Implementation Details
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


* Built with modern Python async/await patterns
* Comprehensive error handling for healthcare data sensitivity
* Automated testing and validation
* Production-ready code with proper logging
* Memory-efficient data processing for large datasets
* Flexible authentication handling for different environments

Future Roadmap
^^^^^^^^^^^^^^


* Enhanced caching mechanisms
* Bulk data operations
* WebSocket support for real-time updates
* Advanced filtering and query builders
* Integration with popular healthcare frameworks
* Enhanced CLI with interactive features
