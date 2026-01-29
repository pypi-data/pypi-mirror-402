"""
Tests for JSON flattener module
"""

import pandas as pd
import pytest

from kipu.flattener import JsonFlattener


class TestJsonFlattener:
    def test_initialization(self):
        """Test flattener initialization"""
        flattener = JsonFlattener()
        assert flattener.sep == "_"

        custom_flattener = JsonFlattener(sep="__")
        assert custom_flattener.sep == "__"

    def test_simple_flattening(self):
        """Test simple JSON flattening"""
        flattener = JsonFlattener()

        data = {"name": "John", "age": 30, "city": "New York"}

        result = flattener.flatten_json(data)
        assert len(result) == 1
        assert result[0]["name"] == "John"
        assert result[0]["age"] == 30
        assert result[0]["city"] == "New York"

    def test_nested_flattening(self):
        """Test nested JSON flattening"""
        flattener = JsonFlattener()

        data = {
            "name": "John",
            "address": {
                "street": "123 Main St",
                "city": "New York",
                "coordinates": {"lat": 40.7128, "lng": -74.0060},
            },
        }

        result = flattener.flatten_json(data)
        assert len(result) == 1
        assert result[0]["name"] == "John"
        assert result[0]["address_street"] == "123 Main St"
        assert result[0]["address_city"] == "New York"
        assert result[0]["address_coordinates_lat"] == 40.7128
        assert result[0]["address_coordinates_lng"] == -74.0060

    def test_list_flattening(self):
        """Test list flattening"""
        flattener = JsonFlattener()

        data = {
            "name": "John",
            "contacts": [
                {"type": "email", "value": "john@example.com"},
                {"type": "phone", "value": "555-1234"},
            ],
        }

        result = flattener.flatten_json(data)
        assert len(result) == 2

        # First contact
        assert result[0]["name"] == "John"
        assert result[0]["contacts_type"] == "email"
        assert result[0]["contacts_value"] == "john@example.com"

        # Second contact
        assert result[1]["name"] == "John"
        assert result[1]["contacts_type"] == "phone"
        assert result[1]["contacts_value"] == "555-1234"

    def test_mixed_flattening(self):
        """Test complex mixed structure flattening"""
        flattener = JsonFlattener()

        data = {
            "patient_id": "12345",
            "demographics": {"name": "John Doe", "age": 30},
            "vitals": [
                {"type": "bp", "systolic": 120, "diastolic": 80},
                {"type": "temp", "value": 98.6},
            ],
            "medications": [],
        }

        result = flattener.flatten_json(data)
        assert len(result) == 2

        # Check patient info is preserved in both records
        assert all(r["patient_id"] == "12345" for r in result)
        assert all(r["demographics_name"] == "John Doe" for r in result)
        assert all(r["demographics_age"] == 30 for r in result)

        # Check vitals are split correctly
        bp_record = next(r for r in result if r.get("vitals_type") == "bp")
        temp_record = next(r for r in result if r.get("vitals_type") == "temp")

        assert bp_record["vitals_systolic"] == 120
        assert bp_record["vitals_diastolic"] == 80
        assert temp_record["vitals_value"] == 98.6

    @pytest.mark.asyncio
    async def test_flatten_json_df(self):
        """Test DataFrame flattening"""
        flattener = JsonFlattener()

        data = [
            {
                "name": "John",
                "address": {"city": "New York"},
                "contacts": [{"type": "email", "value": "john@example.com"}],
            },
            {
                "name": "Jane",
                "address": {"city": "Boston"},
                "contacts": [{"type": "phone", "value": "555-5678"}],
            },
        ]

        result = await flattener.flatten_json_df(data)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "name" in result.columns
        assert "address_city" in result.columns
        assert "contacts_type" in result.columns
        assert "contacts_value" in result.columns

        # Check data integrity
        john_row = result[result["name"] == "John"].iloc[0]
        assert john_row["address_city"] == "New York"
        assert john_row["contacts_type"] == "email"

        jane_row = result[result["name"] == "Jane"].iloc[0]
        assert jane_row["address_city"] == "Boston"
        assert jane_row["contacts_type"] == "phone"

    def test_custom_separator(self):
        """Test custom separator"""
        flattener = JsonFlattener(sep="__")

        data = {"user": {"profile": {"name": "John"}}}

        result = flattener.flatten_json(data)
        assert "user__profile__name" in result[0]
        assert result[0]["user__profile__name"] == "John"
