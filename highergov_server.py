import os
from datetime import datetime, timedelta
import httpx
from fastmcp import FastMCP

mcp = FastMCP("highergov-mcp")

HIGHERGOV_API_KEY = os.environ.get("HIGHERGOV_API_KEY")
if not HIGHERGOV_API_KEY:
    raise RuntimeError("Missing HIGHERGOV_API_KEY env var")

BASE_URL = "https://www.highergov.com/api-external"


async def hg_get(endpoint: str, params: dict) -> dict:
    """Make authenticated GET request to HigherGov API."""
    params = {k: v for k, v in params.items() if v is not None}
    params["api_key"] = HIGHERGOV_API_KEY
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{BASE_URL}/{endpoint}/", params=params)
        r.raise_for_status()
        return r.json()


def days_ago(days: int) -> str:
    """Return date string in YYYY-MM-DD format for N days ago."""
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


@mcp.tool
async def search_opportunities(
    search_id: str | None = None,
    agency_key: str | None = None,
    source_type: str | None = None,
    captured_date_min: str | None = None,
    captured_date_max: str | None = None,
    ordering: str | None = None,
    page_number: int = 1,
    page_size: int = 25,
) -> dict:
    """
    Search federal contract and grant opportunities from HigherGov.
    Updated every 20 minutes with data from SAM.gov, grants.gov, and more.

    Args:
        search_id: HigherGov search ID (from saved searches on highergov.com)
        agency_key: Filter by agency key
        source_type: Filter by source (e.g., "sam_gov", "grants_gov")
        captured_date_min: Minimum captured date (YYYY-MM-DD)
        captured_date_max: Maximum captured date (YYYY-MM-DD)
        ordering: Sort order (e.g., "-captured_date" for newest first)
        page_number: Page number (default 1)
        page_size: Results per page (max 100, default 25)

    Returns:
        Paginated list of opportunities with metadata
    """
    data = await hg_get("opportunity", {
        "search_id": search_id,
        "agency_key": agency_key,
        "source_type": source_type,
        "captured_date__gte": captured_date_min,
        "captured_date__lte": captured_date_max,
        "ordering": ordering or "-captured_date",
        "page_number": page_number,
        "page_size": min(page_size, 100),
    })

    opportunities = []
    for opp in data.get("results", []):
        opportunities.append({
            "opportunity_key": opp.get("opportunity_key"),
            "title": opp.get("title"),
            "agency": opp.get("agency_name"),
            "source_type": opp.get("source_type"),
            "posted_date": opp.get("posted_date"),
            "due_date": opp.get("due_date"),
            "naics_codes": opp.get("naics_codes"),
            "psc_codes": opp.get("psc_codes"),
            "set_aside": opp.get("set_aside"),
            "place_of_performance": opp.get("place_of_performance"),
            "estimated_value": opp.get("estimated_value"),
            "url": opp.get("url"),
            "document_path": opp.get("document_path"),
        })

    return {
        "total_count": data.get("meta", {}).get("total_count", 0),
        "page": page_number,
        "page_size": page_size,
        "opportunities": opportunities,
    }


@mcp.tool
async def search_contracts(
    search_id: str | None = None,
    award_id: str | None = None,
    awardee_key: str | None = None,
    naics_code: str | None = None,
    psc_code: str | None = None,
    last_modified_date_min: str | None = None,
    ordering: str | None = None,
    page_number: int = 1,
    page_size: int = 25,
) -> dict:
    """
    Search federal contract awards (61M+ records). Updated daily.

    Args:
        search_id: HigherGov search ID
        award_id: Specific award ID (e.g., PIID)
        awardee_key: Filter by awardee key
        naics_code: Filter by NAICS code
        psc_code: Filter by Product/Service Code
        last_modified_date_min: Minimum last modified date (YYYY-MM-DD)
        ordering: Sort order
        page_number: Page number
        page_size: Results per page (max 100)

    Returns:
        Paginated list of contract awards
    """
    data = await hg_get("contract", {
        "search_id": search_id,
        "award_id": award_id,
        "awardee_key": awardee_key,
        "naics_code": naics_code,
        "psc_code": psc_code,
        "last_modified_date__gte": last_modified_date_min,
        "ordering": ordering or "-last_modified_date",
        "page_number": page_number,
        "page_size": min(page_size, 100),
    })

    contracts = []
    for c in data.get("results", []):
        contracts.append({
            "contract_key": c.get("contract_key"),
            "award_id": c.get("award_id"),
            "title": c.get("title"),
            "agency": c.get("agency_name"),
            "awardee_name": c.get("awardee_name"),
            "awardee_cage": c.get("awardee_cage"),
            "awardee_uei": c.get("awardee_uei"),
            "obligated_amount": c.get("obligated_amount"),
            "potential_value": c.get("potential_value"),
            "start_date": c.get("start_date"),
            "end_date": c.get("end_date"),
            "naics_code": c.get("naics_code"),
            "psc_code": c.get("psc_code"),
            "place_of_performance": c.get("place_of_performance_state"),
            "contract_type": c.get("contract_type"),
            "set_aside": c.get("set_aside"),
        })

    return {
        "total_count": data.get("meta", {}).get("total_count", 0),
        "page": page_number,
        "contracts": contracts,
    }


@mcp.tool
async def search_grants(
    search_id: str | None = None,
    awardee_key: str | None = None,
    cfda_program_number: str | None = None,
    last_modified_date_min: str | None = None,
    ordering: str | None = None,
    page_number: int = 1,
    page_size: int = 25,
) -> dict:
    """
    Search federal grant awards (4M+ records). Updated daily.

    Args:
        search_id: HigherGov search ID
        awardee_key: Filter by awardee key
        cfda_program_number: Filter by CFDA/Assistance Listing number
        last_modified_date_min: Minimum last modified date (YYYY-MM-DD)
        ordering: Sort order
        page_number: Page number
        page_size: Results per page (max 100)

    Returns:
        Paginated list of grant awards
    """
    data = await hg_get("grant", {
        "search_id": search_id,
        "awardee_key": awardee_key,
        "cfda_program_number": cfda_program_number,
        "last_modified_date__gte": last_modified_date_min,
        "ordering": ordering or "-last_modified_date",
        "page_number": page_number,
        "page_size": min(page_size, 100),
    })

    grants = []
    for g in data.get("results", []):
        grants.append({
            "grant_key": g.get("grant_key"),
            "award_id": g.get("award_id"),
            "title": g.get("title"),
            "agency": g.get("agency_name"),
            "awardee_name": g.get("awardee_name"),
            "awardee_uei": g.get("awardee_uei"),
            "obligated_amount": g.get("obligated_amount"),
            "start_date": g.get("start_date"),
            "end_date": g.get("end_date"),
            "cfda_number": g.get("cfda_program_number"),
            "cfda_title": g.get("cfda_program_title"),
            "place_of_performance": g.get("place_of_performance_state"),
        })

    return {
        "total_count": data.get("meta", {}).get("total_count", 0),
        "page": page_number,
        "grants": grants,
    }


@mcp.tool
async def search_awardees(
    cage_code: str | None = None,
    uei: str | None = None,
    awardee_key_parent: str | None = None,
    primary_naics: str | None = None,
    registration_last_update_date_min: str | None = None,
    ordering: str | None = None,
    page_number: int = 1,
    page_size: int = 25,
) -> dict:
    """
    Search government contractors/awardees (1.5M+ records). Updated daily.

    Args:
        cage_code: CAGE code
        uei: Unique Entity Identifier
        awardee_key_parent: Parent company key
        primary_naics: Primary NAICS code
        registration_last_update_date_min: Filter by SAM registration update date
        ordering: Sort order
        page_number: Page number
        page_size: Results per page (max 100)

    Returns:
        Paginated list of awardees/contractors
    """
    data = await hg_get("awardee", {
        "cage_code": cage_code,
        "uei": uei,
        "awardee_key_parent": awardee_key_parent,
        "primary_naics": primary_naics,
        "registration_last_update_date__gte": registration_last_update_date_min,
        "ordering": ordering,
        "page_number": page_number,
        "page_size": min(page_size, 100),
    })

    awardees = []
    for a in data.get("results", []):
        awardees.append({
            "awardee_key": a.get("awardee_key"),
            "name": a.get("name"),
            "cage_code": a.get("cage_code"),
            "uei": a.get("uei"),
            "duns": a.get("duns"),
            "address": a.get("address"),
            "city": a.get("city"),
            "state": a.get("state"),
            "country": a.get("country"),
            "primary_naics": a.get("primary_naics"),
            "naics_codes": a.get("naics_codes"),
            "small_business": a.get("small_business"),
            "woman_owned": a.get("woman_owned"),
            "veteran_owned": a.get("veteran_owned"),
            "minority_owned": a.get("minority_owned"),
            "8a_certified": a.get("8a_certified"),
            "hubzone": a.get("hubzone"),
            "sdvosb": a.get("sdvosb"),
            "total_awards": a.get("total_awards"),
            "total_obligated": a.get("total_obligated"),
        })

    return {
        "total_count": data.get("meta", {}).get("total_count", 0),
        "page": page_number,
        "awardees": awardees,
    }


@mcp.tool
async def get_documents(
    related_key: str,
    page_number: int = 1,
    page_size: int = 25,
) -> dict:
    """
    Get documents associated with an opportunity.
    Download URLs expire after 60 minutes.

    Args:
        related_key: The opportunity_key or document_path from opportunity search
        page_number: Page number
        page_size: Results per page

    Returns:
        List of documents with download URLs
    """
    data = await hg_get("document", {
        "related_key": related_key,
        "page_number": page_number,
        "page_size": min(page_size, 100),
    })

    documents = []
    for doc in data.get("results", []):
        documents.append({
            "document_key": doc.get("document_key"),
            "filename": doc.get("filename"),
            "file_type": doc.get("file_type"),
            "file_size": doc.get("file_size"),
            "download_url": doc.get("download_url"),
            "expires_in": "60 minutes",
        })

    return {
        "total_count": data.get("meta", {}).get("total_count", 0),
        "documents": documents,
    }


@mcp.tool
async def search_agencies(
    agency_key: str | None = None,
    page_number: int = 1,
    page_size: int = 25,
) -> dict:
    """
    Search federal agencies (3K+ records).

    Args:
        agency_key: Specific agency key
        page_number: Page number
        page_size: Results per page

    Returns:
        List of agencies
    """
    data = await hg_get("agency", {
        "agency_key": agency_key,
        "page_number": page_number,
        "page_size": min(page_size, 100),
    })

    agencies = []
    for a in data.get("results", []):
        agencies.append({
            "agency_key": a.get("agency_key"),
            "name": a.get("name"),
            "abbreviation": a.get("abbreviation"),
            "parent_agency": a.get("parent_agency_name"),
            "agency_type": a.get("agency_type"),
        })

    return {
        "total_count": data.get("meta", {}).get("total_count", 0),
        "agencies": agencies,
    }


@mcp.tool
async def search_contract_vehicles(
    vehicle_key: str | None = None,
    ordering: str | None = None,
    page_number: int = 1,
    page_size: int = 25,
) -> dict:
    """
    Search government contract vehicles (GWACs, BPAs, IDIQs, etc.).

    Args:
        vehicle_key: Specific vehicle key
        ordering: Sort order
        page_number: Page number
        page_size: Results per page

    Returns:
        List of contract vehicles
    """
    data = await hg_get("vehicle", {
        "vehicle_key": vehicle_key,
        "ordering": ordering,
        "page_number": page_number,
        "page_size": min(page_size, 100),
    })

    vehicles = []
    for v in data.get("results", []):
        vehicles.append({
            "vehicle_key": v.get("vehicle_key"),
            "name": v.get("name"),
            "abbreviation": v.get("abbreviation"),
            "agency": v.get("agency_name"),
            "vehicle_type": v.get("vehicle_type"),
            "ceiling": v.get("ceiling"),
            "start_date": v.get("start_date"),
            "end_date": v.get("end_date"),
            "naics_codes": v.get("naics_codes"),
            "psc_codes": v.get("psc_codes"),
        })

    return {
        "total_count": data.get("meta", {}).get("total_count", 0),
        "vehicles": vehicles,
    }


@mcp.tool
async def search_people(
    contact_email: str | None = None,
    ordering: str | None = None,
    page_number: int = 1,
    page_size: int = 25,
) -> dict:
    """
    Search government personnel/contacts (130K+ records).

    Args:
        contact_email: Filter by email address
        ordering: Sort order
        page_number: Page number
        page_size: Results per page

    Returns:
        List of government contacts
    """
    data = await hg_get("people", {
        "contact_email": contact_email,
        "ordering": ordering,
        "page_number": page_number,
        "page_size": min(page_size, 100),
    })

    people = []
    for p in data.get("results", []):
        people.append({
            "people_key": p.get("people_key"),
            "name": p.get("name"),
            "title": p.get("title"),
            "agency": p.get("agency_name"),
            "email": p.get("email"),
            "phone": p.get("phone"),
        })

    return {
        "total_count": data.get("meta", {}).get("total_count", 0),
        "people": people,
    }


@mcp.tool
async def lookup_naics(
    naics_code: str | None = None,
    page_size: int = 50,
) -> dict:
    """
    Look up NAICS codes and descriptions.

    Args:
        naics_code: Specific NAICS code (partial match supported)
        page_size: Results per page

    Returns:
        List of NAICS codes with descriptions
    """
    data = await hg_get("naics", {
        "naics_code": naics_code,
        "page_size": min(page_size, 100),
    })

    codes = []
    for n in data.get("results", []):
        codes.append({
            "naics_code": n.get("naics_code"),
            "title": n.get("title"),
            "description": n.get("description"),
        })

    return {"naics_codes": codes}


@mcp.tool
async def lookup_psc(
    psc_code: str | None = None,
    page_size: int = 50,
) -> dict:
    """
    Look up Product/Service Codes (PSC) and descriptions.

    Args:
        psc_code: Specific PSC code (partial match supported)
        page_size: Results per page

    Returns:
        List of PSC codes with descriptions
    """
    data = await hg_get("psc", {
        "psc_code": psc_code,
        "page_size": min(page_size, 100),
    })

    codes = []
    for p in data.get("results", []):
        codes.append({
            "psc_code": p.get("psc_code"),
            "title": p.get("title"),
            "description": p.get("description"),
        })

    return {"psc_codes": codes}
