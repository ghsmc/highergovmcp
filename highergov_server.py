import os
from datetime import datetime, timedelta
import httpx
from fastmcp import FastMCP

mcp = FastMCP("highergov-mcp")

HIGHERGOV_API_KEY = os.environ.get("HIGHER_GOV_API_KEY")
if not HIGHERGOV_API_KEY:
    raise RuntimeError("Missing HIGHER_GOV_API_KEY env var")

BASE_URL = "https://www.highergov.com/api-external"


async def hg_get(endpoint: str, params: dict) -> dict:
    """Make authenticated GET request to HigherGov API."""
    params = {k: v for k, v in params.items() if v is not None}
    params["api_key"] = HIGHERGOV_API_KEY
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{BASE_URL}/{endpoint}/", params=params)
        r.raise_for_status()
        return r.json()


def today() -> str:
    """Return today's date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")


def days_ago(days: int) -> str:
    """Return date string in YYYY-MM-DD format for N days ago."""
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


@mcp.tool
async def search_opportunities(
    captured_date: str | None = None,
    posted_date: str | None = None,
    agency_key: int | None = None,
    opp_key: str | None = None,
    search_id: str | None = None,
    source_type: str | None = None,
    ordering: str | None = None,
    page_number: int = 1,
    page_size: int = 25,
) -> dict:
    """
    Search federal contract and grant opportunities from HigherGov.
    Updated every 30 minutes.

    IMPORTANT: At least one filter is REQUIRED: captured_date, posted_date, agency_key, opp_key, or search_id

    Args:
        captured_date: Date opportunity was added to HigherGov (YYYY-MM-DD) - RECOMMENDED
        posted_date: Date opportunity was posted by agency (YYYY-MM-DD)
        agency_key: HigherGov agency key (integer)
        opp_key: Specific HigherGov opportunity key
        search_id: HigherGov saved search ID (from highergov.com)
        source_type: Filter by source (sam, grants_gov, etc.)
        ordering: Sort order (-captured_date, -posted_date, -due_date)
        page_number: Page number (default 1)
        page_size: Results per page (max 100, default 25)

    Returns:
        Paginated list of opportunities
    """
    # Default to today if no filter provided
    if not any([captured_date, posted_date, agency_key, opp_key, search_id]):
        captured_date = today()

    data = await hg_get("opportunity", {
        "captured_date": captured_date,
        "posted_date": posted_date,
        "agency_key": agency_key,
        "opp_key": opp_key,
        "search_id": search_id,
        "source_type": source_type,
        "ordering": ordering or "-captured_date",
        "page_number": page_number,
        "page_size": min(page_size, 100),
    })

    opportunities = []
    for opp in data.get("results", []):
        agency = opp.get("agency") or {}
        naics = opp.get("naics_code") or {}
        psc = opp.get("psc_code") or {}
        contact = opp.get("primary_contact_email") or {}

        opportunities.append({
            "opp_key": opp.get("opp_key"),
            "title": opp.get("title"),
            "description": opp.get("description_text"),
            "agency_name": agency.get("agency_name"),
            "agency_key": agency.get("agency_key"),
            "source_type": opp.get("source_type"),
            "source_id": opp.get("source_id"),
            "posted_date": opp.get("posted_date"),
            "captured_date": opp.get("captured_date"),
            "due_date": opp.get("due_date"),
            "naics_code": naics.get("naics_code"),
            "psc_code": psc.get("psc_code"),
            "set_aside": opp.get("set_aside"),
            "estimated_value_low": opp.get("val_est_low"),
            "estimated_value_high": opp.get("val_est_high"),
            "place_of_performance": {
                "state": opp.get("pop_state"),
                "city": opp.get("pop_city"),
                "zip": opp.get("pop_zip"),
            },
            "contact_name": contact.get("contact_name"),
            "contact_email": contact.get("contact_email"),
            "contact_phone": contact.get("contact_phone"),
            "highergov_url": opp.get("path"),
            "source_url": opp.get("source_path"),
        })

    return {
        "total_count": data.get("meta", {}).get("total_count", 0),
        "page": page_number,
        "page_size": page_size,
        "opportunities": opportunities,
    }


@mcp.tool
async def search_contracts(
    naics_code: str | None = None,
    psc_code: str | None = None,
    awardee_key: int | None = None,
    awardee_uei: str | None = None,
    awarding_agency_key: int | None = None,
    award_id: str | None = None,
    search_id: str | None = None,
    last_modified_date: str | None = None,
    ordering: str | None = None,
    page_number: int = 1,
    page_size: int = 25,
) -> dict:
    """
    Search federal contract awards (61M+ records). Updated daily.

    IMPORTANT: At least one filter is REQUIRED.

    Args:
        naics_code: Filter by NAICS code (e.g., "541512")
        psc_code: Filter by Product/Service Code
        awardee_key: HigherGov awardee key
        awardee_uei: Awardee UEI
        awarding_agency_key: HigherGov agency key
        award_id: Specific government award ID
        search_id: HigherGov saved search ID
        last_modified_date: Filter by last modified date (YYYY-MM-DD)
        ordering: Sort order (-last_modified_date, -obligated_amount)
        page_number: Page number
        page_size: Results per page (max 100)

    Returns:
        Paginated list of contract awards
    """
    if not any([naics_code, psc_code, awardee_key, awardee_uei, awarding_agency_key, award_id, search_id, last_modified_date]):
        return {"error": "At least one filter parameter is required", "contracts": []}

    data = await hg_get("contract", {
        "naics_code": naics_code,
        "psc_code": psc_code,
        "awardee_key": awardee_key,
        "awardee_uei": awardee_uei,
        "awarding_agency_key": awarding_agency_key,
        "award_id": award_id,
        "search_id": search_id,
        "last_modified_date": last_modified_date,
        "ordering": ordering or "-last_modified_date",
        "page_number": page_number,
        "page_size": min(page_size, 100),
    })

    contracts = []
    for c in data.get("results", []):
        awardee = c.get("awardee") or {}
        agency = c.get("awarding_agency") or {}
        naics = c.get("naics_code") or {}
        psc = c.get("psc_code") or {}

        contracts.append({
            "contract_key": c.get("contract_key"),
            "award_id": c.get("award_id"),
            "title": c.get("title"),
            "description": c.get("description"),
            "awarding_agency": agency.get("agency_name"),
            "awardee_name": awardee.get("clean_name"),
            "awardee_uei": awardee.get("uei"),
            "awardee_cage": awardee.get("cage_code"),
            "obligated_amount": c.get("obligated_amount"),
            "potential_value": c.get("potential_value"),
            "base_and_all_options": c.get("base_and_all_options_value"),
            "start_date": c.get("period_of_performance_start_date"),
            "end_date": c.get("period_of_performance_current_end_date"),
            "naics_code": naics.get("naics_code") if isinstance(naics, dict) else naics,
            "psc_code": psc.get("psc_code") if isinstance(psc, dict) else psc,
            "place_of_performance_state": c.get("place_of_performance_state"),
            "contract_type": c.get("type_of_contract"),
            "set_aside": c.get("type_of_set_aside"),
            "last_modified_date": c.get("last_modified_date"),
            "highergov_url": c.get("path"),
        })

    return {
        "total_count": data.get("meta", {}).get("total_count", 0),
        "page": page_number,
        "contracts": contracts,
    }


@mcp.tool
async def search_grants(
    awardee_key: int | None = None,
    awardee_uei: str | None = None,
    cfda_program_number: str | None = None,
    awarding_agency_key: int | None = None,
    search_id: str | None = None,
    last_modified_date: str | None = None,
    ordering: str | None = None,
    page_number: int = 1,
    page_size: int = 25,
) -> dict:
    """
    Search federal grant awards (4M+ records). Updated daily.

    IMPORTANT: At least one filter is REQUIRED.

    Args:
        awardee_key: HigherGov awardee key
        awardee_uei: Awardee UEI
        cfda_program_number: CFDA/Assistance Listing number
        awarding_agency_key: HigherGov agency key
        search_id: HigherGov saved search ID
        last_modified_date: Filter by last modified date (YYYY-MM-DD)
        ordering: Sort order
        page_number: Page number
        page_size: Results per page (max 100)

    Returns:
        Paginated list of grant awards
    """
    if not any([awardee_key, awardee_uei, cfda_program_number, awarding_agency_key, search_id, last_modified_date]):
        return {"error": "At least one filter parameter is required", "grants": []}

    data = await hg_get("grant", {
        "awardee_key": awardee_key,
        "awardee_uei": awardee_uei,
        "cfda_program_number": cfda_program_number,
        "awarding_agency_key": awarding_agency_key,
        "search_id": search_id,
        "last_modified_date": last_modified_date,
        "ordering": ordering or "-last_modified_date",
        "page_number": page_number,
        "page_size": min(page_size, 100),
    })

    grants = []
    for g in data.get("results", []):
        awardee = g.get("awardee") or {}
        agency = g.get("awarding_agency") or {}

        grants.append({
            "grant_key": g.get("grant_key"),
            "award_id": g.get("award_id"),
            "title": g.get("title"),
            "awarding_agency": agency.get("agency_name"),
            "awardee_name": awardee.get("clean_name"),
            "awardee_uei": awardee.get("uei"),
            "obligated_amount": g.get("obligated_amount"),
            "start_date": g.get("period_of_performance_start_date"),
            "end_date": g.get("period_of_performance_current_end_date"),
            "cfda_number": g.get("cfda_program_number"),
            "cfda_title": g.get("cfda_program_title"),
            "place_of_performance_state": g.get("place_of_performance_state"),
            "last_modified_date": g.get("last_modified_date"),
            "highergov_url": g.get("path"),
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
    awardee_key_parent: int | None = None,
    primary_naics: str | None = None,
    registration_last_update_date: str | None = None,
    ordering: str | None = None,
    page_number: int = 1,
    page_size: int = 25,
) -> dict:
    """
    Search government contractors/awardees (1.5M+ SAM registrants). Updated monthly.

    Args:
        cage_code: CAGE code (e.g., "34ZB1")
        uei: Unique Entity Identifier
        awardee_key_parent: Parent company HigherGov key
        primary_naics: Primary NAICS code (e.g., "541512")
        registration_last_update_date: SAM registration update date (YYYY-MM-DD)
        ordering: Sort order (-last_update_date, last_update_date)
        page_number: Page number
        page_size: Results per page (max 100)

    Returns:
        Paginated list of awardees/contractors with certifications and business types
    """
    data = await hg_get("awardee", {
        "cage_code": cage_code,
        "uei": uei,
        "awardee_key_parent": awardee_key_parent,
        "primary_naics": primary_naics,
        "registration_last_update_date": registration_last_update_date,
        "ordering": ordering,
        "page_number": page_number,
        "page_size": min(page_size, 100),
    })

    awardees = []
    for a in data.get("results", []):
        primary_naics_obj = a.get("primary_naics") or {}
        naics_list = a.get("naics_codes") or []
        psc_list = a.get("psc_codes") or []
        bus_type_info = a.get("bus_type_info") or []
        parent = a.get("awardee_key_parent") or {}

        # Extract certification info with SBA-certified flag
        certifications = []
        for bt in bus_type_info:
            if isinstance(bt, dict):
                certifications.append({
                    "type": bt.get("bus_type"),
                    "description": bt.get("bus_type_description"),
                    "sba_certified": bt.get("cert_flag", False),
                })

        awardees.append({
            "awardee_key": a.get("awardee_key"),
            "name": a.get("clean_name"),
            "legal_name": a.get("legal_business_name"),
            "dba_name": a.get("dba_name"),
            "division_name": a.get("division_name"),
            "cage_code": a.get("cage_code"),
            "uei": a.get("uei"),
            "address": {
                "line1": a.get("physical_address_line_1"),
                "line2": a.get("physical_address_line_2"),
                "city": a.get("physical_address_city"),
                "state": a.get("physical_address_province_or_state"),
                "zip": a.get("physical_address_zip_postal_code"),
                "country": a.get("physical_address_country_code"),
            },
            "website": a.get("website"),
            "year_founded": a.get("year_founded"),
            "employee_count": a.get("employee_count"),
            "primary_naics": primary_naics_obj.get("naics_code") if isinstance(primary_naics_obj, dict) else primary_naics_obj,
            "naics_codes": [n.get("naics_code") if isinstance(n, dict) else n for n in naics_list],
            "psc_codes": [p.get("psc_code") if isinstance(p, dict) else p for p in psc_list],
            "certifications": certifications,
            "parent_company": {
                "awardee_key": parent.get("awardee_key") if isinstance(parent, dict) else None,
                "name": parent.get("clean_name") if isinstance(parent, dict) else None,
            } if parent else None,
            "registration": {
                "status": a.get("purpose_of_registration"),
                "initial_date": a.get("initial_registration_date"),
                "expiration_date": a.get("registration_expiration_date"),
                "last_update": a.get("registration_last_update_date"),
                "sam_extract_code": a.get("sam_extract_code"),
            },
            "govt_poc": {
                "name": f"{a.get('govt_bus_poc_first_name', '')} {a.get('govt_bus_poc_last_name', '')}".strip() or None,
                "title": a.get("govt_bus_poc_title"),
                "phone": a.get("govt_bus_poc_phone"),
                "email": a.get("govt_bus_poc_email"),
            },
            "highergov_url": a.get("path"),
        })

    return {
        "total_count": data.get("meta", {}).get("total_count", 0),
        "page": page_number,
        "awardees": awardees,
    }


@mcp.tool
async def get_awardee_details(
    awardee_key: int | None = None,
    cage_code: str | None = None,
    uei: str | None = None,
) -> dict:
    """
    Get comprehensive details for a specific awardee/contractor.
    Use this for detailed entity lookup when you have an identifier.

    Args:
        awardee_key: HigherGov awardee key (preferred - most precise)
        cage_code: CAGE code
        uei: Unique Entity Identifier

    Returns:
        Full entity details including all certifications, codes, contacts, and business info
    """
    if not any([awardee_key, cage_code, uei]):
        return {"error": "At least one identifier required: awardee_key, cage_code, or uei"}

    data = await hg_get("awardee", {
        "awardee_key": awardee_key,
        "cage_code": cage_code,
        "uei": uei,
        "page_size": 1,
    })

    results = data.get("results", [])
    if not results:
        return {"error": "Awardee not found", "awardee": None}

    a = results[0]
    primary_naics_obj = a.get("primary_naics") or {}
    naics_list = a.get("naics_codes") or []
    psc_list = a.get("psc_codes") or []
    bus_type_info = a.get("bus_type_info") or []
    parent = a.get("awardee_key_parent") or {}

    # Extract all certifications with SBA-certified flag
    certifications = []
    sba_certified_types = []
    self_certified_types = []
    for bt in bus_type_info:
        if isinstance(bt, dict):
            cert = {
                "type": bt.get("bus_type"),
                "description": bt.get("bus_type_description"),
                "sba_certified": bt.get("cert_flag", False),
            }
            certifications.append(cert)
            if bt.get("cert_flag"):
                sba_certified_types.append(bt.get("bus_type_description"))
            else:
                self_certified_types.append(bt.get("bus_type_description"))

    return {
        "awardee": {
            "awardee_key": a.get("awardee_key"),
            "name": a.get("clean_name"),
            "legal_name": a.get("legal_business_name"),
            "dba_name": a.get("dba_name"),
            "division_name": a.get("division_name"),
            "cage_code": a.get("cage_code"),
            "uei": a.get("uei"),
            "duns": a.get("duns"),
            "address": {
                "line1": a.get("physical_address_line_1"),
                "line2": a.get("physical_address_line_2"),
                "city": a.get("physical_address_city"),
                "state": a.get("physical_address_province_or_state"),
                "zip": a.get("physical_address_zip_postal_code"),
                "country": a.get("physical_address_country_code"),
            },
            "mailing_address": {
                "line1": a.get("mailing_address_line_1"),
                "line2": a.get("mailing_address_line_2"),
                "city": a.get("mailing_address_city"),
                "state": a.get("mailing_address_province_or_state"),
                "zip": a.get("mailing_address_zip_postal_code"),
                "country": a.get("mailing_address_country_code"),
            },
            "website": a.get("website"),
            "company_info": {
                "year_founded": a.get("year_founded"),
                "employee_count": a.get("employee_count"),
                "entity_type": a.get("entity_type"),
                "organization_type": a.get("organization_type"),
                "state_of_incorporation": a.get("state_of_incorporation"),
                "country_of_incorporation": a.get("country_of_incorporation"),
            },
            "naics_codes": {
                "primary": primary_naics_obj.get("naics_code") if isinstance(primary_naics_obj, dict) else primary_naics_obj,
                "primary_description": primary_naics_obj.get("naics_title") if isinstance(primary_naics_obj, dict) else None,
                "all_codes": [n.get("naics_code") if isinstance(n, dict) else n for n in naics_list],
            },
            "psc_codes": [p.get("psc_code") if isinstance(p, dict) else p for p in psc_list],
            "certifications": {
                "all": certifications,
                "sba_certified": sba_certified_types,
                "self_certified": self_certified_types,
            },
            "parent_company": {
                "awardee_key": parent.get("awardee_key") if isinstance(parent, dict) else None,
                "name": parent.get("clean_name") if isinstance(parent, dict) else None,
                "cage_code": parent.get("cage_code") if isinstance(parent, dict) else None,
            } if parent else None,
            "registration": {
                "purpose": a.get("purpose_of_registration"),
                "initial_date": a.get("initial_registration_date"),
                "activation_date": a.get("activation_date"),
                "expiration_date": a.get("registration_expiration_date"),
                "last_update": a.get("registration_last_update_date"),
                "sam_extract_code": a.get("sam_extract_code"),
            },
            "govt_business_poc": {
                "first_name": a.get("govt_bus_poc_first_name"),
                "last_name": a.get("govt_bus_poc_last_name"),
                "title": a.get("govt_bus_poc_title"),
                "phone": a.get("govt_bus_poc_phone"),
                "email": a.get("govt_bus_poc_email"),
            },
            "highergov_url": a.get("path"),
        }
    }


@mcp.tool
async def search_awardees_by_name(
    name: str,
    page_number: int = 1,
    page_size: int = 25,
) -> dict:
    """
    Search for contractors/awardees by company name.
    Returns matching companies with key identifiers and certifications.

    Args:
        name: Company name to search (partial match supported)
        page_number: Page number
        page_size: Results per page (max 100)

    Returns:
        List of matching awardees with basic info
    """
    data = await hg_get("awardee", {
        "clean_name": name,
        "page_number": page_number,
        "page_size": min(page_size, 100),
    })

    awardees = []
    for a in data.get("results", []):
        bus_type_info = a.get("bus_type_info") or []
        cert_types = [bt.get("bus_type_description") for bt in bus_type_info if isinstance(bt, dict)]

        awardees.append({
            "awardee_key": a.get("awardee_key"),
            "name": a.get("clean_name"),
            "legal_name": a.get("legal_business_name"),
            "cage_code": a.get("cage_code"),
            "uei": a.get("uei"),
            "city": a.get("physical_address_city"),
            "state": a.get("physical_address_province_or_state"),
            "employee_count": a.get("employee_count"),
            "certifications": cert_types,
            "highergov_url": a.get("path"),
        })

    return {
        "total_count": data.get("meta", {}).get("total_count", 0),
        "page": page_number,
        "awardees": awardees,
    }


@mcp.tool
async def get_awardee_certifications(
    cage_code: str | None = None,
    uei: str | None = None,
    primary_naics: str | None = None,
    page_size: int = 25,
) -> dict:
    """
    Get awardee small business certifications with SBA-certified vs self-certified distinction.

    Certification types include:
    - 8(a) Business Development Program (SBA-certified)
    - HUBZone (SBA-certified)
    - SDVOSB - Service-Disabled Veteran-Owned (VA-verified or self-certified)
    - WOSB/EDWOSB - Women-Owned (SBA-certified or self-certified)
    - Small Disadvantaged Business
    - Minority-Owned
    - And more...

    Args:
        cage_code: CAGE code
        uei: Unique Entity Identifier
        primary_naics: Primary NAICS code

    Returns:
        Awardees with detailed certification info including SBA-certified flag
    """
    data = await hg_get("awardee", {
        "cage_code": cage_code,
        "uei": uei,
        "primary_naics": primary_naics,
        "page_size": min(page_size, 100),
    })

    awardees = []
    for a in data.get("results", []):
        bus_type_info = a.get("bus_type_info") or []

        # Parse certifications with SBA-certified flag
        all_certs = []
        sba_certified = []
        self_certified = []
        for bt in bus_type_info:
            if isinstance(bt, dict):
                cert = {
                    "type": bt.get("bus_type"),
                    "description": bt.get("bus_type_description"),
                    "sba_certified": bt.get("cert_flag", False),
                }
                all_certs.append(cert)
                if bt.get("cert_flag"):
                    sba_certified.append(bt.get("bus_type_description"))
                else:
                    self_certified.append(bt.get("bus_type_description"))

        awardees.append({
            "awardee_key": a.get("awardee_key"),
            "name": a.get("clean_name"),
            "cage_code": a.get("cage_code"),
            "uei": a.get("uei"),
            "certifications": {
                "all": all_certs,
                "sba_certified": sba_certified,
                "self_certified": self_certified,
                "count": len(all_certs),
            },
            "highergov_url": a.get("path"),
        })

    return {
        "total_count": data.get("meta", {}).get("total_count", 0),
        "awardees": awardees,
    }


@mcp.tool
async def search_people(
    last_name: str | None = None,
    agency_key: int | None = None,
    page_number: int = 1,
    page_size: int = 25,
) -> dict:
    """
    Search government contacts and personnel (130K+ records).
    Useful for finding agency contacts, contracting officers, and program managers.

    Args:
        last_name: Contact's last name
        agency_key: HigherGov agency key to filter by agency
        page_number: Page number
        page_size: Results per page (max 100)

    Returns:
        List of government contacts with their agency and contact info
    """
    data = await hg_get("people", {
        "last_name": last_name,
        "agency_key": agency_key,
        "page_number": page_number,
        "page_size": min(page_size, 100),
    })

    people = []
    for p in data.get("results", []):
        agency = p.get("agency") or {}
        people.append({
            "person_key": p.get("person_key"),
            "first_name": p.get("first_name"),
            "last_name": p.get("last_name"),
            "title": p.get("title"),
            "agency": agency.get("agency_name") if isinstance(agency, dict) else agency,
            "agency_key": agency.get("agency_key") if isinstance(agency, dict) else None,
            "email": p.get("email"),
            "phone": p.get("phone"),
            "highergov_url": p.get("path"),
        })

    return {
        "total_count": data.get("meta", {}).get("total_count", 0),
        "page": page_number,
        "people": people,
    }


@mcp.tool
async def search_contract_vehicles(
    vehicle_name: str | None = None,
    agency_key: int | None = None,
    naics_code: str | None = None,
    page_number: int = 1,
    page_size: int = 25,
) -> dict:
    """
    Search government contract vehicles (GWACs, BPAs, IDIQs, GSA Schedules).
    Find which contractors hold positions on major contract vehicles.

    Args:
        vehicle_name: Contract vehicle name (partial match)
        agency_key: HigherGov agency key
        naics_code: NAICS code supported by vehicle
        page_number: Page number
        page_size: Results per page (max 100)

    Returns:
        List of contract vehicles with holder information
    """
    data = await hg_get("contract_vehicle", {
        "vehicle_name": vehicle_name,
        "agency_key": agency_key,
        "naics_code": naics_code,
        "page_number": page_number,
        "page_size": min(page_size, 100),
    })

    vehicles = []
    for v in data.get("results", []):
        agency = v.get("agency") or {}
        vehicles.append({
            "vehicle_key": v.get("vehicle_key"),
            "name": v.get("vehicle_name"),
            "abbreviation": v.get("abbreviation"),
            "agency": agency.get("agency_name") if isinstance(agency, dict) else agency,
            "vehicle_type": v.get("vehicle_type"),
            "ordering_start_date": v.get("ordering_start_date"),
            "ordering_end_date": v.get("ordering_end_date"),
            "highergov_url": v.get("path"),
        })

    return {
        "total_count": data.get("meta", {}).get("total_count", 0),
        "page": page_number,
        "vehicles": vehicles,
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
        related_key: The source_id_version or document_path from opportunity search

    Returns:
        List of documents with download URLs (expire in 60 min)
    """
    data = await hg_get("document", {
        "related_key": related_key,
        "page_number": page_number,
        "page_size": min(page_size, 100),
    })

    documents = []
    for doc in data.get("results", []):
        documents.append({
            "filename": doc.get("filename"),
            "file_type": doc.get("file_type"),
            "file_size": doc.get("file_size"),
            "download_url": doc.get("download_url"),
            "note": "URL expires in 60 minutes",
        })

    return {
        "total_count": data.get("meta", {}).get("total_count", 0),
        "documents": documents,
    }


@mcp.tool
async def search_agencies(
    agency_key: int | None = None,
    page_number: int = 1,
    page_size: int = 50,
) -> dict:
    """
    Search federal agencies (3K+ records).

    Args:
        agency_key: Specific HigherGov agency key
        page_number: Page number
        page_size: Results per page

    Returns:
        List of agencies with hierarchy
    """
    data = await hg_get("agency", {
        "agency_key": agency_key,
        "page_number": page_number,
        "page_size": min(page_size, 100),
    })

    agencies = []
    for a in data.get("results", []):
        parent = a.get("parent_agency") or {}
        agencies.append({
            "agency_key": a.get("agency_key"),
            "name": a.get("agency_name"),
            "abbreviation": a.get("agency_abbreviation"),
            "agency_type": a.get("agency_type"),
            "parent_agency": parent.get("agency_name") if isinstance(parent, dict) else parent,
            "highergov_url": a.get("path"),
        })

    return {
        "total_count": data.get("meta", {}).get("total_count", 0),
        "agencies": agencies,
    }


@mcp.tool
async def lookup_naics(
    naics_code: str | None = None,
    page_size: int = 50,
) -> dict:
    """
    Look up NAICS codes and descriptions.

    Args:
        naics_code: NAICS code to look up (partial match supported)
        page_size: Results per page

    Returns:
        List of NAICS codes with titles
    """
    data = await hg_get("naics", {
        "naics_code": naics_code,
        "page_size": min(page_size, 100),
    })

    codes = []
    for n in data.get("results", []):
        codes.append({
            "naics_code": n.get("naics_code"),
            "title": n.get("naics_title"),
        })

    return {"naics_codes": codes}


@mcp.tool
async def lookup_psc(
    psc_code: str | None = None,
    page_size: int = 50,
) -> dict:
    """
    Look up Product/Service Codes (PSC).

    Args:
        psc_code: PSC code to look up (partial match supported)
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
            "description": p.get("description"),
        })

    return {"psc_codes": codes}
