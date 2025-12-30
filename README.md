# HigherGov MCP Server

An MCP (Model Context Protocol) server for interacting with the HigherGov API - the most comprehensive source of U.S. federal government contract and grant data.

## Tools

### Opportunities & Awards
| Tool | Description | Records |
|------|-------------|---------|
| `search_opportunities` | Search contract & grant opportunities | 4M+ |
| `search_contracts` | Search federal contract awards | 61M+ |
| `search_grants` | Search federal grant awards | 4M+ |
| `get_documents` | Download opportunity documents (URLs expire in 60 min) | 3M+ |

### Entity Lookup (Enhanced)
| Tool | Description | Records |
|------|-------------|---------|
| `search_awardees` | Search contractors with full certifications, PSC codes, parent info | 1.5M+ |
| `search_awardees_by_name` | Search companies by name | 1.5M+ |
| `get_awardee_details` | Get comprehensive entity details (all codes, certs, contacts) | - |
| `get_awardee_certifications` | Get SBA-certified vs self-certified distinction | - |

### Reference Data
| Tool | Description | Records |
|------|-------------|---------|
| `search_agencies` | Search federal agencies | 3K+ |
| `search_contract_vehicles` | Search GWACs, BPAs, IDIQs, GSA Schedules | - |
| `search_people` | Search government contacts | 130K+ |
| `lookup_naics` | Look up NAICS codes | - |
| `lookup_psc` | Look up Product/Service Codes | - |

## Entity Lookup Features

The entity lookup tools now provide:
- **Full certification info** with SBA-certified vs self-certified distinction
- **All NAICS codes** (not just primary)
- **All PSC codes**
- **Parent company details**
- **Government POC contact info** (name, title, phone, email)
- **Registration dates** (initial, activation, expiration, last update)
- **Division info** for large contractors

## Setup

1. Get a HigherGov API key from your account settings (gear icon > API section)
2. Copy `.env.example` to `.env` and add your API key
3. Install dependencies: `pip install -r requirements.txt`

## Deployment

Deploy to FastMCP Cloud:

```bash
fastmcp deploy highergov_server.py
```

Set the `HIGHER_GOV_API_KEY` environment variable in FastMCP Cloud settings.

## Usage Limits

- Default: 10,000 records/month per subscription
- Rate limit: 10 requests/second, 100,000 requests/day
- Contact HigherGov for higher quotas

## API Reference

- [HigherGov API Docs](https://docs.highergov.com/import-and-export/api)
- [OpenAPI Specification](https://www.highergov.com/api-external/docs/)
- [GitHub Repository](https://github.com/HigherGov/API)
