"""Tests for the COLA Cloud MCP client."""

import os

import pytest
import respx
from httpx import Response

# Set test API key before importing modules
os.environ["COLA_API_KEY"] = "test_key_123"
os.environ["COLA_API_URL"] = "https://test.colacloud.us/api/v1"

from colacloud_mcp.client import ColaCloudClient, ColaCloudError


@pytest.fixture
def client():
    """Create a test client."""
    return ColaCloudClient(api_key="test_key_123", base_url="https://test.colacloud.us/api/v1")


@pytest.fixture
def mock_api():
    """Mock the COLA Cloud API."""
    with respx.mock(base_url="https://test.colacloud.us/api/v1", assert_all_called=False) as mock:
        yield mock


class TestSearchColas:
    def test_basic_search(self, client, mock_api):
        mock_api.get("/colas").mock(
            return_value=Response(
                200,
                json={
                    "data": [
                        {
                            "ttb_id": "23001001000001",
                            "brand_name": "Test Brand",
                            "product_name": "Test Product",
                            "product_type": "wine",
                        }
                    ],
                    "pagination": {"page": 1, "per_page": 20, "total": 1, "pages": 1},
                },
            )
        )

        result = client.search_colas(q="test")

        assert "data" in result
        assert len(result["data"]) == 1
        assert result["data"][0]["brand_name"] == "Test Brand"

    def test_search_with_filters(self, client, mock_api):
        mock_api.get("/colas").mock(return_value=Response(200, json={"data": [], "pagination": {}}))

        result = client.search_colas(
            product_type="wine",
            origin="california",
            abv_min=12.0,
            abv_max=15.0,
        )

        assert "data" in result
        request = mock_api.calls[0].request
        assert "product_type=wine" in str(request.url)
        assert "origin=california" in str(request.url)

    def test_api_error(self, client, mock_api):
        mock_api.get("/colas").mock(
            return_value=Response(
                429,
                json={"error": {"code": "rate_limit_exceeded", "message": "Too many requests"}},
            )
        )

        with pytest.raises(ColaCloudError) as exc_info:
            client.search_colas()

        assert exc_info.value.code == "rate_limit_exceeded"
        assert exc_info.value.status_code == 429


class TestGetCola:
    def test_get_existing_cola(self, client, mock_api):
        mock_api.get("/colas/23001001000001").mock(
            return_value=Response(
                200,
                json={
                    "data": {
                        "ttb_id": "23001001000001",
                        "brand_name": "Test Brand",
                        "images": [],
                        "barcodes": [],
                    }
                },
            )
        )

        result = client.get_cola("23001001000001")

        assert result["data"]["ttb_id"] == "23001001000001"

    def test_cola_not_found(self, client, mock_api):
        mock_api.get("/colas/invalid").mock(
            return_value=Response(
                404,
                json={"error": {"code": "not_found", "message": "COLA invalid not found"}},
            )
        )

        with pytest.raises(ColaCloudError) as exc_info:
            client.get_cola("invalid")

        assert exc_info.value.code == "not_found"
        assert exc_info.value.status_code == 404


class TestSearchPermittees:
    def test_basic_search(self, client, mock_api):
        mock_api.get("/permittees").mock(
            return_value=Response(
                200,
                json={
                    "data": [
                        {
                            "permit_number": "CA-I-123",
                            "company_name": "Test Winery",
                            "company_state": "CA",
                        }
                    ],
                    "pagination": {"page": 1, "per_page": 20, "total": 1, "pages": 1},
                },
            )
        )

        result = client.search_permittees(q="winery", state="CA")

        assert len(result["data"]) == 1
        assert result["data"][0]["company_name"] == "Test Winery"


class TestGetPermittee:
    def test_get_permittee(self, client, mock_api):
        mock_api.get("/permittees/CA-I-123").mock(
            return_value=Response(
                200,
                json={
                    "data": {
                        "permit_number": "CA-I-123",
                        "company_name": "Test Winery",
                        "recent_colas": [],
                    }
                },
            )
        )

        result = client.get_permittee("CA-I-123")

        assert result["data"]["permit_number"] == "CA-I-123"


class TestLookupBarcode:
    def test_barcode_found(self, client, mock_api):
        mock_api.get("/barcode/012345678905").mock(
            return_value=Response(
                200,
                json={
                    "data": {
                        "barcode_value": "012345678905",
                        "barcode_type": "UPC-A",
                        "colas": [{"ttb_id": "23001001000001", "brand_name": "Test"}],
                        "total_colas": 1,
                    }
                },
            )
        )

        result = client.lookup_barcode("012345678905")

        assert result["data"]["barcode_value"] == "012345678905"
        assert len(result["data"]["colas"]) == 1

    def test_barcode_not_found(self, client, mock_api):
        mock_api.get("/barcode/000000000000").mock(
            return_value=Response(
                404,
                json={"error": {"code": "not_found", "message": "No COLAs found"}},
            )
        )

        with pytest.raises(ColaCloudError) as exc_info:
            client.lookup_barcode("000000000000")

        assert exc_info.value.code == "not_found"


class TestGetApiUsage:
    def test_get_usage(self, client, mock_api):
        mock_api.get("/usage").mock(
            return_value=Response(
                200,
                json={
                    "data": {
                        "tier": "free",
                        "monthly_limit": 500,
                        "current_period": "2024-01",
                        "requests_used": 42,
                        "requests_remaining": 458,
                        "per_minute_limit": 10,
                    }
                },
            )
        )

        result = client.get_usage()

        assert result["data"]["tier"] == "free"
        assert result["data"]["requests_used"] == 42


class TestClientAuthentication:
    def test_missing_api_key(self):
        # Temporarily unset the env var
        old_key = os.environ.pop("COLA_API_KEY", None)
        try:
            with pytest.raises(ColaCloudError) as exc_info:
                ColaCloudClient(api_key=None)

            assert exc_info.value.code == "missing_api_key"
        finally:
            if old_key:
                os.environ["COLA_API_KEY"] = old_key

    def test_api_key_in_header(self, mock_api):
        mock_api.get("/colas").mock(return_value=Response(200, json={"data": [], "pagination": {}}))

        client = ColaCloudClient(api_key="my_test_key", base_url="https://test.colacloud.us/api/v1")
        client.search_colas()

        request = mock_api.calls[0].request
        assert request.headers["X-API-Key"] == "my_test_key"
