"""
CrawlGate Python SDK - Official Python SDK for CrawlGate Search Engine API

Usage:
    from crawlgate import CrawlGateClient

    client = CrawlGateClient(api_key="sk_live_...")

    # Scrape a single URL
    doc = client.scrape("https://example.com")
    print(doc.markdown)

    # Crawl a website
    job = client.crawl("https://example.com", limit=10)
    for page in job.data:
        print(page.url)
"""

from .client import CrawlGateClient
from .types import (
    Document,
    DocumentMetadata,
    ScrapeOptions,
    CrawlOptions,
    CrawlJob,
    CrawlResponse,
    MapOptions,
    MapResponse,
    SearchOptions,
    SearchResult,
    SearchResponse,
    BatchScrapeOptions,
    BatchScrapeJob,
    ExtractOptions,
    ExtractResponse,
)
from .errors import (
    CrawlGateError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError,
    ServerError,
    TimeoutError,
)

__version__ = "1.0.1"
__all__ = [
    "CrawlGateClient",
    # Types
    "Document",
    "DocumentMetadata",
    "ScrapeOptions",
    "CrawlOptions",
    "CrawlJob",
    "CrawlResponse",
    "MapOptions",
    "MapResponse",
    "SearchOptions",
    "SearchResult",
    "SearchResponse",
    "BatchScrapeOptions",
    "BatchScrapeJob",
    "ExtractOptions",
    "ExtractResponse",
    # Errors
    "CrawlGateError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "NotFoundError",
    "ServerError",
    "TimeoutError",
]
