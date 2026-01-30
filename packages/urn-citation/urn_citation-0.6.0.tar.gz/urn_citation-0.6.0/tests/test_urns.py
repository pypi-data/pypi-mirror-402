import pytest
from pydantic import ValidationError

from urn_citation import Urn


class TestUrn:
    """Tests for the Urn base class."""

    def test_urn_creation_with_valid_data(self):
        """Test creating a Urn with valid data."""
        urn = Urn(urn_type="test")
        assert urn.urn_type == "test"

    def test_urn_requires_urn_type(self):
        """Test that urn_type is required."""
        with pytest.raises(ValidationError) as exc_info:
            Urn()
        assert "urn_type" in str(exc_info.value)

    def test_urn_urn_type_is_string(self):
        """Test that urn_type accepts string values."""
        urn = Urn(urn_type="custom_type")
        assert isinstance(urn.urn_type, str)
        assert urn.urn_type == "custom_type"

    def test_urn_equality(self):
        """Test that two Urns with the same urn_type are equal."""
        urn1 = Urn(urn_type="test")
        urn2 = Urn(urn_type="test")
        assert urn1 == urn2

    def test_urn_inequality(self):
        """Test that two Urns with different urn_type values are not equal."""
        urn1 = Urn(urn_type="test1")
        urn2 = Urn(urn_type="test2")
        assert urn1 != urn2

    def test_urn_model_dump(self):
        """Test that Urn can be serialized to a dictionary."""
        urn = Urn(urn_type="test")
        data = urn.model_dump()
        assert data["urn_type"] == "test"

