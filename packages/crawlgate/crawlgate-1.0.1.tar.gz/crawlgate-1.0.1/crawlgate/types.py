"""
CrawlGate SDK Type Definitions
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Literal, Union
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class Engine(str, Enum):
    """Scraping engine selection"""
    STATIC = "static"
    DYNAMIC = "dynamic"
    SMART = "smart"


class LLMProvider(str, Enum):
    """LLM provider for extraction"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class CrawlStatus(str, Enum):
    """Crawl/Batch job status"""
    SCRAPING = "scraping"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExtractStatus(str, Enum):
    """Extract job status"""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Type aliases
EngineType = Literal["static", "dynamic", "smart"]
FormatType = Literal["markdown", "html", "rawHtml", "text"]
LLMProviderType = Literal["openai", "anthropic"]


# =============================================================================
# Document Types
# =============================================================================

@dataclass
class DocumentMetadata:
    """Metadata from scraped page"""
    title: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    url: Optional[str] = None
    source_url: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None
    favicon: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["DocumentMetadata"]:
        if not data:
            return None
        return cls(
            title=data.get("title"),
            description=data.get("description"),
            language=data.get("language"),
            url=data.get("url") or data.get("sourceURL"),
            source_url=data.get("sourceURL"),
            og_title=data.get("ogTitle"),
            og_description=data.get("ogDescription"),
            og_image=data.get("ogImage"),
            favicon=data.get("favicon"),
            extra={k: v for k, v in data.items() if k not in [
                "title", "description", "language", "sourceURL", "url",
                "ogTitle", "ogDescription", "ogImage", "favicon"
            ]}
        )


@dataclass
class ExtractResult:
    """Result of LLM extraction"""
    data: Any
    provider: str
    model: str
    usage: Optional[Dict[str, int]] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["ExtractResult"]:
        if not data:
            return None
        return cls(
            data=data.get("data"),
            provider=data.get("provider", ""),
            model=data.get("model", ""),
            usage=data.get("usage")
        )


@dataclass
class Document:
    """Scraped document data"""
    url: str
    markdown: Optional[str] = None
    html: Optional[str] = None
    raw_html: Optional[str] = None
    text: Optional[str] = None
    metadata: Optional[DocumentMetadata] = None
    scrape_time: Optional[int] = None
    extract: Optional[ExtractResult] = None
    json: Optional[Any] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        return cls(
            url=data.get("url", ""),
            markdown=data.get("markdown"),
            html=data.get("html"),
            raw_html=data.get("rawHtml"),
            text=data.get("text"),
            metadata=DocumentMetadata.from_dict(data.get("metadata")),
            scrape_time=data.get("scrapeTime"),
            extract=ExtractResult.from_dict(data.get("extract")),
            json=data.get("json")
        )


# =============================================================================
# Options Types
# =============================================================================

@dataclass
class ExtractOptions:
    """Options for LLM-powered data extraction"""
    schema: Union[Dict[str, Any], Any]  # JSON Schema or Pydantic model
    system_prompt: Optional[str] = None
    provider: LLMProviderType = "openai"
    enable_fallback: bool = False

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        # Handle schema (convert Pydantic to JSON Schema if needed)
        if hasattr(self.schema, "model_json_schema"):
            result["schema"] = self.schema.model_json_schema()
        elif hasattr(self.schema, "schema"):
            result["schema"] = self.schema.schema()
        else:
            result["schema"] = self.schema

        if self.system_prompt:
            result["systemPrompt"] = self.system_prompt
        if self.provider:
            result["provider"] = self.provider
        if self.enable_fallback:
            result["enableFallback"] = self.enable_fallback

        return result


@dataclass
class ScrapeOptions:
    """Options for scraping a single URL"""
    engine: EngineType = "smart"
    formats: List[FormatType] = field(default_factory=lambda: ["markdown"])
    only_main_content: bool = True
    exclude_tags: Optional[List[str]] = None
    wait_for: Optional[int] = None
    timeout: Optional[int] = None
    proxy: Optional[str] = None
    extract: Optional[ExtractOptions] = None
    project_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "engine": self.engine,
            "formats": self.formats,
            "onlyMainContent": self.only_main_content,
        }
        if self.exclude_tags:
            result["excludeTags"] = self.exclude_tags
        if self.wait_for:
            result["waitFor"] = self.wait_for
        if self.timeout:
            result["timeout"] = self.timeout
        if self.proxy:
            result["proxy"] = self.proxy
        if self.extract:
            result["extract"] = self.extract.to_dict()
        if self.project_id:
            result["projectId"] = self.project_id
        return result


@dataclass
class CrawlOptions:
    """Options for crawling a website"""
    engine: EngineType = "dynamic"
    limit: int = 10
    formats: List[FormatType] = field(default_factory=lambda: ["markdown"])
    only_main_content: bool = True
    exclude_tags: Optional[List[str]] = None
    proxy: Optional[str] = None
    project_id: Optional[str] = None
    poll_interval: int = 2000  # ms
    timeout: int = 300  # seconds

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "engine": self.engine,
            "limit": self.limit,
            "formats": self.formats,
            "onlyMainContent": self.only_main_content,
        }
        if self.exclude_tags:
            result["excludeTags"] = self.exclude_tags
        if self.proxy:
            result["proxy"] = self.proxy
        if self.project_id:
            result["projectId"] = self.project_id
        return result


@dataclass
class MapOptions:
    """Options for mapping URLs on a website"""
    engine: EngineType = "dynamic"
    proxy: Optional[str] = None
    project_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"engine": self.engine}
        if self.proxy:
            result["proxy"] = self.proxy
        if self.project_id:
            result["projectId"] = self.project_id
        return result


@dataclass
class SearchOptions:
    """Options for web search"""
    limit: int = 10
    lang: str = "en"
    country: str = "us"
    engines: Optional[List[str]] = None
    scrape_options: Optional[Dict[str, Any]] = None
    engine: EngineType = "smart"
    extract: Optional[ExtractOptions] = None
    project_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "limit": self.limit,
            "lang": self.lang,
            "country": self.country,
        }
        if self.engines:
            result["engines"] = self.engines
        if self.scrape_options:
            result["scrapeOptions"] = self.scrape_options
        if self.engine:
            result["engine"] = self.engine
        if self.extract:
            result["extract"] = self.extract.to_dict()
        if self.project_id:
            result["projectId"] = self.project_id
        return result


@dataclass
class BatchScrapeOptions:
    """Options for batch scraping multiple URLs"""
    options: Optional[ScrapeOptions] = None
    webhook: Optional[Union[str, Dict[str, Any]]] = None
    ignore_invalid_urls: bool = False
    max_concurrency: Optional[int] = None
    project_id: Optional[str] = None
    poll_interval: int = 2000  # ms
    timeout: int = 300  # seconds

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        if self.options:
            result["options"] = self.options.to_dict()
        if self.webhook:
            result["webhook"] = self.webhook
        if self.ignore_invalid_urls:
            result["ignoreInvalidURLs"] = self.ignore_invalid_urls
        if self.max_concurrency:
            result["maxConcurrency"] = self.max_concurrency
        if self.project_id:
            result["projectId"] = self.project_id
        return result


# =============================================================================
# Response Types
# =============================================================================

@dataclass
class CrawlResponse:
    """Response from starting a crawl job"""
    success: bool
    id: str
    status: str
    engine: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CrawlResponse":
        return cls(
            success=data.get("success", False),
            id=data.get("id", data.get("jobId", "")),
            status=data.get("status", ""),
            engine=data.get("engine")
        )


@dataclass
class CrawlJob:
    """Crawl job status and data"""
    id: str
    status: str
    total: int
    completed: int
    data: List[Document]
    engine: Optional[str] = None
    error: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CrawlJob":
        return cls(
            id=data.get("id", ""),
            status=data.get("status", ""),
            total=data.get("total", 0),
            completed=data.get("completed", 0),
            data=[Document.from_dict(d) for d in data.get("data", [])],
            engine=data.get("engine"),
            error=data.get("error")
        )


@dataclass
class MapResponse:
    """Response from map endpoint"""
    success: bool
    links: List[str]
    count: int
    engine: Optional[str] = None
    error: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MapResponse":
        return cls(
            success=data.get("success", False),
            links=data.get("links", []),
            count=data.get("count", 0),
            engine=data.get("engine"),
            error=data.get("error")
        )


@dataclass
class SearchResult:
    """Individual search result"""
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    engine: Optional[str] = None
    score: Optional[float] = None
    position: Optional[int] = None
    markdown: Optional[str] = None
    html: Optional[str] = None
    metadata: Optional[DocumentMetadata] = None
    scrape_success: Optional[bool] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchResult":
        return cls(
            url=data.get("url", ""),
            title=data.get("title"),
            description=data.get("description"),
            engine=data.get("engine"),
            score=data.get("score"),
            position=data.get("position"),
            markdown=data.get("markdown"),
            html=data.get("html"),
            metadata=DocumentMetadata.from_dict(data.get("metadata")),
            scrape_success=data.get("scrapeSuccess")
        )


@dataclass
class SearchResponse:
    """Response from search endpoint"""
    success: bool
    data: List[SearchResult]
    query: str
    total_results: Optional[int] = None
    search_time: Optional[int] = None
    extract: Optional[ExtractResult] = None
    error: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchResponse":
        return cls(
            success=data.get("success", False),
            data=[SearchResult.from_dict(r) for r in data.get("data", [])],
            query=data.get("query", ""),
            total_results=data.get("totalResults"),
            search_time=data.get("searchTime"),
            extract=ExtractResult.from_dict(data.get("extract")),
            error=data.get("error")
        )


@dataclass
class BatchScrapeJob:
    """Batch scrape job status and data"""
    id: str
    status: str
    total: int
    completed: int
    data: List[Document]
    credits_used: Optional[int] = None
    expires_at: Optional[str] = None
    error: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchScrapeJob":
        return cls(
            id=data.get("id", ""),
            status=data.get("status", ""),
            total=data.get("total", 0),
            completed=data.get("completed", 0),
            data=[Document.from_dict(d) for d in data.get("data", [])],
            credits_used=data.get("creditsUsed"),
            expires_at=data.get("expiresAt"),
            error=data.get("error")
        )


@dataclass
class ExtractResponse:
    """Response from extract endpoint"""
    success: bool = True
    id: Optional[str] = None
    status: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[str] = None
    warning: Optional[str] = None
    sources: Optional[Dict[str, Any]] = None
    expires_at: Optional[str] = None
    credits_used: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractResponse":
        return cls(
            success=data.get("success", True),
            id=data.get("id"),
            status=data.get("status"),
            data=data.get("data"),
            error=data.get("error"),
            warning=data.get("warning"),
            sources=data.get("sources"),
            expires_at=data.get("expiresAt"),
            credits_used=data.get("creditsUsed")
        )


# =============================================================================
# Usage Types
# =============================================================================

@dataclass
class ConcurrencyInfo:
    """Concurrency usage information"""
    concurrency: int
    max_concurrency: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConcurrencyInfo":
        return cls(
            concurrency=data.get("concurrency", 0),
            max_concurrency=data.get("maxConcurrency", 0)
        )


@dataclass
class CreditUsage:
    """Credit usage information"""
    remaining_credits: int
    plan_credits: Optional[int] = None
    billing_period_start: Optional[str] = None
    billing_period_end: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CreditUsage":
        return cls(
            remaining_credits=data.get("remainingCredits", 0),
            plan_credits=data.get("planCredits"),
            billing_period_start=data.get("billingPeriodStart"),
            billing_period_end=data.get("billingPeriodEnd")
        )
