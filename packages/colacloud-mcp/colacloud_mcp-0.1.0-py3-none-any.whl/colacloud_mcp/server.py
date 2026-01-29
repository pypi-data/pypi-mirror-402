"""COLA Cloud MCP Server - tools for querying US alcohol label data."""

from fastmcp import FastMCP

from colacloud_mcp.client import ColaCloudError, get_client

mcp = FastMCP(
    "COLA Cloud",
    instructions="Access the COLA Cloud database of US alcohol product labels. "
    "Search 2.5M+ label approvals, look up products by barcode, and explore permit holders.",
)


@mcp.tool()
def search_colas(
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
) -> dict:
    """
    Search and filter COLA (Certificate of Label Approval) records.

    COLAs are federal approvals for alcohol product labels in the US. Each record
    includes brand name, product details, label images, and enriched data like
    barcodes and AI-extracted features.

    Args:
        q: Full-text search query (searches brand, product name, origin)
        product_type: Filter by type - "malt beverage", "wine", or "distilled spirits"
        origin: Filter by country or US state (e.g., "california", "france")
        brand_name: Filter by brand name (partial match, case-insensitive)
        approval_date_from: Minimum approval date (YYYY-MM-DD)
        approval_date_to: Maximum approval date (YYYY-MM-DD)
        abv_min: Minimum alcohol by volume percentage
        abv_max: Maximum alcohol by volume percentage
        page: Page number for pagination (default: 1)
        per_page: Results per page (default: 20, max: 100)

    Returns:
        Search results with COLA summaries and pagination info
    """
    try:
        client = get_client()
        return client.search_colas(
            q=q,
            product_type=product_type,
            origin=origin,
            brand_name=brand_name,
            approval_date_from=approval_date_from,
            approval_date_to=approval_date_to,
            abv_min=abv_min,
            abv_max=abv_max,
            page=page,
            per_page=per_page,
        )
    except ColaCloudError as e:
        return {"error": {"code": e.code, "message": e.message}}


@mcp.tool()
def get_cola(ttb_id: str) -> dict:
    """
    Get detailed information about a specific COLA by its TTB ID.

    Returns the full record including all label images, extracted barcodes,
    and AI-enriched fields like product descriptions, tasting notes, and
    category classifications.

    Args:
        ttb_id: The TTB (Alcohol and Tobacco Tax and Trade Bureau) ID,
                e.g., "23001001000001"

    Returns:
        Complete COLA record with images, barcodes, and enrichment data
    """
    try:
        client = get_client()
        return client.get_cola(ttb_id)
    except ColaCloudError as e:
        return {"error": {"code": e.code, "message": e.message}}


@mcp.tool()
def search_permittees(
    q: str | None = None,
    state: str | None = None,
    is_active: bool | None = None,
    page: int = 1,
    per_page: int = 20,
) -> dict:
    """
    Search permit holders (companies authorized to produce/import alcohol).

    Permittees are businesses that hold federal permits to manufacture, import,
    or wholesale alcohol products. Each permittee can have many COLAs.

    Args:
        q: Search by company name (partial match)
        state: Filter by US state (two-letter code, e.g., "CA", "NY")
        is_active: Filter by active permit status (true/false)
        page: Page number for pagination (default: 1)
        per_page: Results per page (default: 20, max: 100)

    Returns:
        Search results with permittee summaries and pagination info
    """
    try:
        client = get_client()
        return client.search_permittees(
            q=q,
            state=state,
            is_active=is_active,
            page=page,
            per_page=per_page,
        )
    except ColaCloudError as e:
        return {"error": {"code": e.code, "message": e.message}}


@mcp.tool()
def get_permittee(permit_number: str) -> dict:
    """
    Get detailed information about a permit holder.

    Returns the permittee's company details and their 10 most recent COLAs.

    Args:
        permit_number: The federal permit number, e.g., "NY-I-123"

    Returns:
        Permittee details with recent COLA summaries
    """
    try:
        client = get_client()
        return client.get_permittee(permit_number)
    except ColaCloudError as e:
        return {"error": {"code": e.code, "message": e.message}}


@mcp.tool()
def lookup_barcode(barcode_value: str) -> dict:
    """
    Find COLAs by product barcode (UPC, EAN, etc.).

    Barcodes are extracted from label images using computer vision. This tool
    finds all COLAs that contain a specific barcode, useful for identifying
    products or tracking label changes over time.

    Args:
        barcode_value: The barcode number (UPC, EAN, etc.), e.g., "012345678905"

    Returns:
        Barcode info and all associated COLAs
    """
    try:
        client = get_client()
        return client.lookup_barcode(barcode_value)
    except ColaCloudError as e:
        return {"error": {"code": e.code, "message": e.message}}


@mcp.tool()
def get_api_usage() -> dict:
    """
    Check your COLA Cloud API usage and rate limits.

    Returns current usage statistics including requests used this month,
    remaining quota, and rate limit information.

    Returns:
        Usage stats including tier, limits, and current period usage
    """
    try:
        client = get_client()
        return client.get_usage()
    except ColaCloudError as e:
        return {"error": {"code": e.code, "message": e.message}}
