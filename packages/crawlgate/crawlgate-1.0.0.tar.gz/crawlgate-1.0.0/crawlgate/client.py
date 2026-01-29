"""
CrawlGate Python SDK Client
"""

import os
import time
from typing import Optional, List, Dict, Any, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .types import (
    Document,
    ScrapeOptions,
    CrawlOptions,
    CrawlResponse,
    CrawlJob,
    MapOptions,
    MapResponse,
    SearchOptions,
    SearchResponse,
    BatchScrapeOptions,
    BatchScrapeJob,
    ExtractResponse,
    ConcurrencyInfo,
    CreditUsage,
)
from .errors import (
    CrawlGateError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError,
    ServerError,
    TimeoutError,
    JobFailedError,
)


class CrawlGateClient:
    """
    CrawlGate API Client

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

    DEFAULT_API_URL = "https://api.crawlgate.io"
    DEFAULT_TIMEOUT = 90  # seconds
    DEFAULT_MAX_RETRIES = 3

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        """
        Initialize CrawlGate client

        Args:
            api_key: API key for authentication. Falls back to CRAWLGATE_API_KEY env var.
            api_url: Base URL for the API. Falls back to CRAWLGATE_API_URL env var.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries for failed requests.

        Raises:
            CrawlGateError: If API key is not provided.
        """
        self.api_key = api_key or os.environ.get("CRAWLGATE_API_KEY", "")
        self.api_url = (api_url or os.environ.get("CRAWLGATE_API_URL", self.DEFAULT_API_URL)).rstrip("/")
        self.timeout = timeout

        if not self.api_key:
            raise CrawlGateError(
                "API key is required. Set CRAWLGATE_API_KEY env variable or pass api_key parameter.",
                code="MISSING_API_KEY"
            )

        # Setup session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _headers(self) -> Dict[str, str]:
        """Get request headers"""
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "crawlgate-python/1.0.0",
        }

    def _handle_error(self, response: requests.Response) -> None:
        """Handle error responses"""
        status = response.status_code
        try:
            data = response.json()
            message = data.get("error", data.get("message", response.text))
        except Exception:
            message = response.text

        if status == 401:
            raise AuthenticationError(message, status, "UNAUTHORIZED")
        elif status == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message, status, "RATE_LIMITED",
                retry_after=int(retry_after) if retry_after else None
            )
        elif status == 400:
            raise ValidationError(message, status, "VALIDATION_ERROR")
        elif status == 404:
            raise NotFoundError(message, status, "NOT_FOUND")
        elif status >= 500:
            raise ServerError(message, status, "SERVER_ERROR")
        else:
            raise CrawlGateError(message, status)

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request"""
        url = f"{self.api_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=self._headers(),
                timeout=self.timeout,
            )
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timed out after {self.timeout}s")
        except requests.exceptions.RequestException as e:
            raise CrawlGateError(f"Request failed: {str(e)}")

        if not response.ok:
            self._handle_error(response)

        return response.json()

    # =========================================================================
    # Scrape Methods
    # =========================================================================

    def scrape(
        self,
        url: str,
        engine: str = "smart",
        formats: Optional[List[str]] = None,
        only_main_content: bool = True,
        extract: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        wait_for: Optional[int] = None,
        **kwargs
    ) -> Document:
        """
        Scrape a single URL

        Args:
            url: URL to scrape
            engine: Scraping engine ("static", "dynamic", "smart")
            formats: Output formats (["markdown", "html", "rawHtml", "text"])
            only_main_content: Extract only main content
            extract: LLM extraction config with schema
            timeout: Request timeout in milliseconds
            wait_for: Wait for milliseconds before scraping (dynamic engine)
            **kwargs: Additional options

        Returns:
            Document: Scraped document with requested formats

        Example:
            doc = client.scrape("https://example.com", formats=["markdown", "html"])
            print(doc.markdown)
        """
        payload: Dict[str, Any] = {
            "url": url,
            "engine": engine,
            "formats": formats or ["markdown"],
            "onlyMainContent": only_main_content,
        }

        if extract:
            payload["extract"] = extract
        if timeout:
            payload["timeout"] = timeout
        if wait_for:
            payload["waitFor"] = wait_for

        payload.update(kwargs)

        response = self._request("POST", "/v1/scrape", payload)

        if not response.get("success"):
            raise CrawlGateError(response.get("error", "Scrape failed"))

        return Document.from_dict(response.get("data", {}))

    # =========================================================================
    # Crawl Methods
    # =========================================================================

    def start_crawl(
        self,
        url: str,
        limit: int = 10,
        engine: str = "dynamic",
        formats: Optional[List[str]] = None,
        **kwargs
    ) -> CrawlResponse:
        """
        Start a crawl job (async)

        Args:
            url: Root URL to crawl
            limit: Maximum number of pages to crawl
            engine: Scraping engine
            formats: Output formats
            **kwargs: Additional options

        Returns:
            CrawlResponse: Crawl job ID and initial status

        Example:
            response = client.start_crawl("https://example.com", limit=50)
            print(f"Job started: {response.id}")
        """
        payload: Dict[str, Any] = {
            "url": url,
            "limit": limit,
            "engine": engine,
            "formats": formats or ["markdown"],
        }
        payload.update(kwargs)

        response = self._request("POST", "/v1/crawl", payload)
        return CrawlResponse.from_dict(response)

    def get_crawl_status(self, job_id: str) -> CrawlJob:
        """
        Get crawl job status and data

        Args:
            job_id: Crawl job ID

        Returns:
            CrawlJob: Current job status and scraped data
        """
        response = self._request("GET", f"/v1/crawl/{job_id}")
        return CrawlJob.from_dict(response)

    def cancel_crawl(self, job_id: str) -> bool:
        """
        Cancel a crawl job

        Args:
            job_id: Crawl job ID

        Returns:
            bool: True if cancelled successfully
        """
        response = self._request("DELETE", f"/v1/crawl/{job_id}")
        return response.get("success", False)

    def crawl(
        self,
        url: str,
        limit: int = 10,
        engine: str = "dynamic",
        formats: Optional[List[str]] = None,
        poll_interval: float = 2.0,
        timeout: int = 300,
        **kwargs
    ) -> CrawlJob:
        """
        Crawl a website and wait for completion

        Args:
            url: Root URL to crawl
            limit: Maximum number of pages to crawl
            engine: Scraping engine
            formats: Output formats
            poll_interval: Poll interval in seconds
            timeout: Maximum wait time in seconds
            **kwargs: Additional options

        Returns:
            CrawlJob: Final crawl job with all scraped data

        Raises:
            TimeoutError: If job doesn't complete within timeout
            JobFailedError: If job fails

        Example:
            job = client.crawl("https://example.com", limit=10)
            for page in job.data:
                print(f"{page.url}: {len(page.markdown or '')} chars")
        """
        # Start the job
        response = self.start_crawl(url, limit, engine, formats, **kwargs)

        # Poll until completion
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Crawl job timed out after {timeout}s")

            job = self.get_crawl_status(response.id)

            if job.status == "completed":
                return job
            elif job.status == "failed":
                raise JobFailedError(job.error or "Crawl job failed")
            elif job.status == "cancelled":
                raise JobFailedError("Crawl job was cancelled")

            time.sleep(poll_interval)

    # =========================================================================
    # Map Methods
    # =========================================================================

    def map(
        self,
        url: str,
        engine: str = "dynamic",
        **kwargs
    ) -> MapResponse:
        """
        Map a website to discover all URLs

        Args:
            url: Root URL to map
            engine: Scraping engine
            **kwargs: Additional options

        Returns:
            MapResponse: List of discovered URLs

        Example:
            result = client.map("https://example.com")
            print(f"Found {result.count} URLs")
            for link in result.links:
                print(link)
        """
        payload: Dict[str, Any] = {
            "url": url,
            "engine": engine,
        }
        payload.update(kwargs)

        response = self._request("POST", "/v1/map", payload)
        return MapResponse.from_dict(response)

    # =========================================================================
    # Search Methods
    # =========================================================================

    def search(
        self,
        query: str,
        limit: int = 10,
        lang: str = "en",
        country: str = "us",
        scrape_options: Optional[Dict[str, Any]] = None,
        extract: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> SearchResponse:
        """
        Search the web and optionally scrape results

        Args:
            query: Search query
            limit: Maximum number of results
            lang: Language code
            country: Country code
            scrape_options: Options for scraping results
            extract: LLM extraction config
            **kwargs: Additional options

        Returns:
            SearchResponse: Search results with optional scraped content

        Example:
            results = client.search("best python libraries 2024", limit=5)
            for result in results.data:
                print(f"{result.title}: {result.url}")
        """
        payload: Dict[str, Any] = {
            "query": query,
            "limit": limit,
            "lang": lang,
            "country": country,
        }

        if scrape_options:
            payload["scrapeOptions"] = scrape_options
        if extract:
            payload["extract"] = extract

        payload.update(kwargs)

        response = self._request("POST", "/v1/search", payload)
        return SearchResponse.from_dict(response)

    # =========================================================================
    # Batch Scrape Methods
    # =========================================================================

    def start_batch_scrape(
        self,
        urls: List[str],
        options: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Start a batch scrape job (async)

        Args:
            urls: List of URLs to scrape
            options: Scrape options for all URLs
            **kwargs: Additional options

        Returns:
            dict: Batch job ID and initial status
        """
        payload: Dict[str, Any] = {"urls": urls}
        if options:
            payload["options"] = options
        payload.update(kwargs)

        return self._request("POST", "/v1/batch/scrape", payload)

    def get_batch_scrape_status(self, job_id: str) -> BatchScrapeJob:
        """
        Get batch scrape job status and data

        Args:
            job_id: Batch job ID

        Returns:
            BatchScrapeJob: Current job status and scraped data
        """
        response = self._request("GET", f"/v1/batch/scrape/{job_id}")
        return BatchScrapeJob.from_dict(response)

    def batch_scrape(
        self,
        urls: List[str],
        options: Optional[Dict[str, Any]] = None,
        poll_interval: float = 2.0,
        timeout: int = 300,
        **kwargs
    ) -> BatchScrapeJob:
        """
        Batch scrape multiple URLs and wait for completion

        Args:
            urls: List of URLs to scrape
            options: Scrape options for all URLs
            poll_interval: Poll interval in seconds
            timeout: Maximum wait time in seconds
            **kwargs: Additional options

        Returns:
            BatchScrapeJob: Final job with all scraped data

        Example:
            urls = ["https://a.com", "https://b.com", "https://c.com"]
            job = client.batch_scrape(urls, options={"formats": ["markdown"]})
            print(f"Scraped {job.completed} URLs")
        """
        # Start the job
        response = self.start_batch_scrape(urls, options, **kwargs)
        job_id = response.get("id", "")

        # Poll until completion
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Batch scrape timed out after {timeout}s")

            job = self.get_batch_scrape_status(job_id)

            if job.status == "completed":
                return job
            elif job.status == "failed":
                raise JobFailedError(job.error or "Batch scrape failed")

            time.sleep(poll_interval)

    # =========================================================================
    # Extract Methods
    # =========================================================================

    def extract(
        self,
        urls: List[str],
        schema: Optional[Dict[str, Any]] = None,
        prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        provider: str = "openai",
        **kwargs
    ) -> ExtractResponse:
        """
        Extract structured data from URLs using LLM

        Args:
            urls: URLs to extract data from
            schema: JSON Schema for structured extraction
            prompt: Natural language prompt for extraction
            system_prompt: System prompt for LLM
            provider: LLM provider ("openai" or "anthropic")
            **kwargs: Additional options

        Returns:
            ExtractResponse: Extracted structured data

        Example:
            result = client.extract(
                urls=["https://example.com/product"],
                schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "price": {"type": "number"}
                    }
                },
                provider="openai"
            )
            print(result.data)
        """
        payload: Dict[str, Any] = {
            "urls": urls,
            "provider": provider,
        }

        if schema:
            payload["schema"] = schema
        if prompt:
            payload["prompt"] = prompt
        if system_prompt:
            payload["systemPrompt"] = system_prompt

        payload.update(kwargs)

        response = self._request("POST", "/v1/extract", payload)
        return ExtractResponse.from_dict(response)

    # =========================================================================
    # Usage Methods
    # =========================================================================

    def get_concurrency(self) -> ConcurrencyInfo:
        """
        Get current concurrency usage

        Returns:
            ConcurrencyInfo: Current and max concurrency
        """
        response = self._request("GET", "/v1/usage/concurrency")
        return ConcurrencyInfo.from_dict(response)

    def get_credit_usage(self) -> CreditUsage:
        """
        Get current credit usage

        Returns:
            CreditUsage: Remaining credits and billing info
        """
        response = self._request("GET", "/v1/usage/credits")
        return CreditUsage.from_dict(response)
