"""
Tests for authentication module
"""

from kipu.auth import KipuAuth


class TestKipuAuth:
    def test_initialization(self):
        """Test auth object initialization"""
        auth = KipuAuth("test_access", "test_secret", "test_app", version=3)
        assert auth.access_id == "test_access"
        assert auth.secret_key == "test_secret"
        assert auth.app_id == "test_app"
        assert auth.version == 3

    def test_signature_generation_get(self):
        """Test GET request signature generation"""
        auth = KipuAuth("test_access", "test_secret", "test_app", version=3)

        signature = auth.generate_signature(
            method="GET",
            uri="/api/patients/census?app_id=test_app",
            date="Wed, 06 Nov 2019 15:38:34 GMT",
        )

        assert isinstance(signature, str)
        assert len(signature) > 0

    def test_signature_generation_post(self):
        """Test POST request signature generation"""
        auth = KipuAuth("test_access", "test_secret", "test_app", version=3)

        signature = auth.generate_signature(
            method="POST",
            uri="/api/patients",
            date="Wed, 06 Nov 2019 15:38:34 GMT",
            content_type="application/json",
            content_md5="VpofNeoRAzRvCD/YjO1mSw==",
        )

        assert isinstance(signature, str)
        assert len(signature) > 0

    def test_auth_headers_get(self):
        """Test GET request headers generation"""
        auth = KipuAuth("test_access", "test_secret", "test_app", version=3)

        headers = auth.get_auth_headers("GET", "/api/patients/census")

        assert "Authorization" in headers
        assert "Accept" in headers
        assert "Date" in headers
        assert headers["Accept"] == "application/vnd.kipusystems+json; version=3"
        assert "APIAuth" in headers["Authorization"]

    def test_auth_headers_post(self):
        """Test POST request headers generation"""
        auth = KipuAuth("test_access", "test_secret", "test_app", version=3)

        headers = auth.get_auth_headers(
            "POST",
            "/api/patients",
            body=b'{"test": "data"}',
            content_type="application/json",
        )

        assert "Authorization" in headers
        assert "Accept" in headers
        assert "Date" in headers
        assert "Content-Type" in headers
        assert "Content-MD5" in headers
        assert headers["Content-Type"] == "application/json"

    def test_add_app_id_to_params(self):
        """Test adding app_id to parameters"""
        auth = KipuAuth("test_access", "test_secret", "test_app", version=3)

        params = {"page": 1, "per": 10}
        updated_params = auth.add_app_id_to_params(params)

        assert updated_params["app_id"] == "test_app"
        assert updated_params["page"] == 1
        assert updated_params["per"] == 10

        # Test with None params
        none_params = auth.add_app_id_to_params(None)
        assert none_params["app_id"] == "test_app"

    def test_v4_authentication(self):
        """Test V4 (SHA256) authentication"""
        auth_v3 = KipuAuth("test_access", "test_secret", "test_app", version=3)
        auth_v4 = KipuAuth("test_access", "test_secret", "test_app", version=4)

        # Same inputs should produce different signatures (different hash algorithms)
        signature_v3 = auth_v3.generate_signature(
            method="GET",
            uri="/api/test",
            date="Wed, 06 Nov 2019 15:38:34 GMT",
        )
        signature_v4 = auth_v4.generate_signature(
            method="GET",
            uri="/api/test",
            date="Wed, 06 Nov 2019 15:38:34 GMT",
        )

        assert signature_v3 != signature_v4  # Different hash algorithms
        assert isinstance(signature_v3, str)
        assert isinstance(signature_v4, str)

    def test_v4_auth_headers(self):
        """Test V4 headers include SHA256 auth type"""
        auth = KipuAuth("test_access", "test_secret", "test_app", version=4)
        headers = auth.get_auth_headers("GET", "/api/test")

        assert "APIAuth-HMAC-SHA256" in headers["Authorization"]
        assert headers["Accept"] == "application/vnd.kipusystems+json; version=4"

    def test_v3_auth_type(self):
        """Test V3 uses standard APIAuth"""
        auth = KipuAuth("test_access", "test_secret", "test_app", version=3)
        headers = auth.get_auth_headers("GET", "/api/test")

        # V3 should use "APIAuth" without SHA256 suffix
        assert "APIAuth " in headers["Authorization"]
        assert "APIAuth-HMAC-SHA256" not in headers["Authorization"]
        assert headers["Accept"] == "application/vnd.kipusystems+json; version=3"
