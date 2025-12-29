# HigherGov MCP Server

An MCP (Model Context Protocol) server for interacting with the HigherGov API - the most comprehensive source of U.S. federal government contract and grant data.

## Tools

| Tool | Description | Records |
|------|-------------|---------|
| `search_opportunities` | Search contract & grant opportunities | 4M+ |
| `search_contracts` | Search federal contract awards | 61M+ |
| `search_grants` | Search federal grant awards | 4M+ |
| `search_awardees` | Search contractors/companies | 1.5M+ |
| `get_documents` | Download opportunity documents | 3M+ |
| `search_agencies` | Search federal agencies | 3K+ |
| `search_contract_vehicles` | Search GWACs, BPAs, IDIQs | - |
| `search_people` | Search government contacts | 130K+ |
| `lookup_naics` | Look up NAICS codes | - |
| `lookup_psc` | Look up Product/Service Codes | - |

## Setup

1. Get a HigherGov API key from your account settings (gear icon > API section)
2. Copy `.env.example` to `.env` and add your API key
3. Install dependencies: `pip install -r requirements.txt`

## Deployment

Deploy to FastMCP Cloud:

```bash
fastmcp deploy highergov_server.py
```

Set the `HIGHERGOV_API_KEY` environment variable in FastMCP Cloud settings.

## Usage Limits

- Default: 10,000 records/month per subscription
- Rate limit: 10 requests/second, 100,000 requests/day
- Contact HigherGov for higher quotas

## API Reference

- [HigherGov API Docs](https://docs.highergov.com/import-and-export/api)
- [OpenAPI Specification](https://www.highergov.com/api-external/docs/)
- [GitHub Repository](https://github.com/HigherGov/API)
