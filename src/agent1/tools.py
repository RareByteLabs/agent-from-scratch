"""Tools the agent can call. Each tool is a plain function plus a schema the model reads."""

import httpx
from anthropic.types import ToolParam

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TIMEOUT = 15.0
MAX_CHARS = 8000  # cap what we hand back to the model, so cost stays bounded


def search_pubmed(query: str, max_results: int = 5) -> str:
    """Search PubMed and return the abstracts of the top matches as plain text."""

    max_results = max(1, min(max_results, 10))  # cap max resutls to limit token cost later

    with httpx.Client(timeout=TIMEOUT) as client:
        found = client.get(
            f"{EUTILS}/esearch.fcgi",
            params={
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance",
            },
        )
        found.raise_for_status()
        ids = found.json()["esearchresult"]["idlist"]
        if not ids:
            return "No results found."
        abstracts = client.get(
            f"{EUTILS}/efetch.fcgi",
            params={
                "db": "pubmed",
                "id": ",".join(ids),
                "rettype": "abstract",
                "retmode": "text",
            },
        )
        abstracts.raise_for_status()
    return abstracts.text[:MAX_CHARS]


SEARCH_PUBMED_SCHEMA: ToolParam = {
    "name": "search_pubmed",
    "description": (
        "Search PubMed for biomedical literature. Returns the abstracts of the most "
        "relevant papers, each with its PMID. Use this for any question about medical evidence."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "PubMed query, e.g. "
                    "'colorectal cancer screening AND randomized controlled trial'"
                ),
            },
            "max_results": {
                "type": "integer",
                "description": "Number of papers to fetch (1 to 10)",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}
