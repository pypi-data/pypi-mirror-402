"""HTTP client for the COLA Cloud API."""

import os
from typing import Any

import httpx

DEFAULT_BASE_URL = "https://app.colacloud.us/api/v1"
TIMEOUT = 30.0


class ColaCloudError(Exception):
    """Error from the COLA Cloud API."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(f"{code}: {message}")


class ColaCloudClient:
    """Client for the COLA Cloud REST API."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.environ.get("COLA_API_KEY")
        if not self.api_key:
            raise ColaCloudError(
                "missing_api_key",
                "COLA_API_KEY environment variable is required",
                401,
            )
        self.base_url = base_url or os.environ.get("COLA_API_URL", DEFAULT_BASE_URL)
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key},
            timeout=TIMEOUT,
        )

    def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        """Make an API request and handle errors."""
        response = self._client.request(method, path, **kwargs)

        if response.status_code >= 400:
            try:
                error_data = response.json().get("error", {})
                raise ColaCloudError(
                    error_data.get("code", "unknown"),
                    error_data.get("message", response.text),
                    response.status_code,
                )
            except (ValueError, KeyError):
                raise ColaCloudError("api_error", response.text, response.status_code)

        return response.json()

    def search_colas(
        self,
        q: str | None = None,
        product_type: str | None = None,
        origin: str | None = None,
        brand_name: str | None = None,
        approval_date_from: str | None = None,
        approval_date_to: str | None = None,
        abv_min: float | None = None,
        abv_max: float | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        """Search and filter COLAs."""
        params = {"page": page, "per_page": per_page}
        if q:
            params["q"] = q
        if product_type:
            params["product_type"] = product_type
        if origin:
            params["origin"] = origin
        if brand_name:
            params["brand_name"] = brand_name
        if approval_date_from:
            params["approval_date_from"] = approval_date_from
        if approval_date_to:
            params["approval_date_to"] = approval_date_to
        if abv_min is not None:
            params["abv_min"] = abv_min
        if abv_max is not None:
            params["abv_max"] = abv_max

        return self._request("GET", "/colas", params=params)

    def get_cola(self, ttb_id: str) -> dict[str, Any]:
        """Get a single COLA by TTB ID."""
        return self._request("GET", f"/colas/{ttb_id}")

    def search_permittees(
        self,
        q: str | None = None,
        state: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        """Search permit holders."""
        params = {"page": page, "per_page": per_page}
        if q:
            params["q"] = q
        if state:
            params["state"] = state
        if is_active is not None:
            params["is_active"] = str(is_active).lower()

        return self._request("GET", "/permittees", params=params)

    def get_permittee(self, permit_number: str) -> dict[str, Any]:
        """Get a single permittee by permit number."""
        return self._request("GET", f"/permittees/{permit_number}")

    def lookup_barcode(self, barcode_value: str) -> dict[str, Any]:
        """Look up COLAs by barcode (UPC, EAN, etc.)."""
        return self._request("GET", f"/barcode/{barcode_value}")

    def get_usage(self) -> dict[str, Any]:
        """Get API usage statistics for the current key."""
        return self._request("GET", "/usage")

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# Module-level client instance (lazy-loaded)
_client: ColaCloudClient | None = None


def get_client() -> ColaCloudClient:
    """Get or create the shared client instance."""
    global _client
    if _client is None:
        _client = ColaCloudClient()
    return _client
