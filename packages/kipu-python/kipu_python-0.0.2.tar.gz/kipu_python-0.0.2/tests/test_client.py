"""
Tests for main client module
"""

from kipu import KipuClient


class TestKipuClient:
    def test_initialization(self):
        """Test client initialization"""
        client = KipuClient("access", "secret", "app")

        assert client.auth.access_id == "access"
        assert client.auth.secret_key == "secret"
        assert client.auth.app_id == "app"
        assert client.auto_flatten is True
        assert client.flattener is not None

    def test_initialization_custom_options(self):
        """Test client initialization with custom options"""
        client = KipuClient(
            "access",
            "secret",
            "app",
            base_url="https://custom.api.com",
            timeout=60,
            auto_flatten=False,
        )

        assert client.base_url == "https://custom.api.com"
        assert client.timeout == 60
        assert client.auto_flatten is False

    def test_available_methods(self):
        """Test that all expected methods are available"""
        client = KipuClient("access", "secret", "app")

        # Core patient methods
        patient_methods = [
            "get_patients_census",
            "get_patient",
            "create_patient",
            "update_patient",
            "get_patients_admissions",
            "get_patients_latest",
            "get_patients_occupancy",
            "get_patients_care_teams",
            "get_patient_care_team",
        ]

        for method in patient_methods:
            assert hasattr(client, method), f"Missing method: {method}"

        # Medical records methods
        medical_methods = [
            "get_vital_signs",
            "get_patient_vital_signs",
            "create_patient_vital_signs",
            "get_allergies",
            "get_patient_allergies",
            "get_allergens",
            "get_cows",
            "get_ciwa_ars",
            "get_ciwa_bs",
        ]

        for method in medical_methods:
            assert hasattr(client, method), f"Missing method: {method}"

        # Appointment methods
        appointment_methods = [
            "get_scheduler_appointments",
            "get_patient_appointments",
            "get_provider_appointments",
            "get_user_appointments",
            "get_scheduler_appointment_types",
            "get_scheduler_appointment_statuses",
        ]

        for method in appointment_methods:
            assert hasattr(client, method), f"Missing method: {method}"

        # Administrative methods
        admin_methods = [
            "get_users",
            "get_user",
            "get_providers",
            "get_provider",
            "get_locations",
            "get_roles",
            "get_care_levels",
        ]

        for method in admin_methods:
            assert hasattr(client, method), f"Missing method: {method}"

    def test_context_manager_protocol(self):
        """Test that client supports async context manager"""
        client = KipuClient("access", "secret", "app")

        # Check that async context manager methods exist
        assert hasattr(client, "__aenter__")
        assert hasattr(client, "__aexit__")
        assert callable(getattr(client, "__aenter__"))
        assert callable(getattr(client, "__aexit__"))
