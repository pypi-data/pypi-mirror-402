import os
import logging
import asyncio
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from tqdm import tqdm
import requests
from docs_crawler.cache import CrawlCache

# Configuration
MAX_RETRIES = 3
PAGE_LOAD_TIMEOUT = 30000  # 30秒超时
MAX_DISCOVERY_DEPTH = 1000  # 最大递归深度（默认值，可通过参数覆盖）
DEFAULT_CONCURRENCY = 5  # 默认并发数

# Setup logging
logger = logging.getLogger(__name__)


class Crawler:
    def __init__(self, base_url=None, sitemap_url=None, output_dir="output", custom_folder=None):
        """
        Initialize the crawler.

        Args:
            base_url: Base URL of the documentation site
            sitemap_url: URL of the sitemap
            output_dir: Output directory for markdown files
            custom_folder: Custom folder name under output_dir
        """
        self.base_url = base_url
        self.sitemap_url = sitemap_url or (f"{base_url}/sitemap.xml" if base_url else None)
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (compatible; Bot/1.0; +http://example.com)"}
        )
        self.results = []
        self.failed = []  # 记录失败的 URL 及原因
        self.skipped = []  # 记录跳过的 URL（未变化）
        self.subdomain = None
        self.custom_folder = custom_folder
        self.cache = None  # 延迟初始化，等 output_subdir 确定后

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

    def extract_subdomain(self, url):
        """从URL中提取二级域名（主域名）作为文件夹名。"""
        parsed = urlparse(url)
        hostname = parsed.hostname
        if hostname:
            parts = hostname.split(".")

            # 提取二级域名（主域名）的逻辑：
            # code.claude.com -> parts[-2] = 'claude'
            # antigravity.google -> parts[-2] = 'antigravity'
            # example.com -> parts[-2] = 'example'
            # localhost -> parts[-1] = 'localhost'

            if len(parts) >= 2:
                # 取倒数第二个部分作为二级域名
                return parts[-2]
            elif len(parts) == 1:
                # 只有一个部分，如 localhost
                return parts[0]

        return "default"

    def fetch_sitemap(self):
        """Fetches and parses the sitemap to extract /docs/ URLs."""
        if not self.sitemap_url:
            logger.error("No sitemap URL configured")
            return []

        try:
            logger.info(f"Fetching sitemap from {self.sitemap_url}")
            response = self.session.get(self.sitemap_url)
            response.raise_for_status()

            # XML parsing (using lxml if available, else html.parser)
            # sitemap files are often just text/xml
            soup = BeautifulSoup(response.content, "xml")
            urls = [loc.text for loc in soup.find_all("loc")]

            # Filter for /docs/
            doc_urls = [url for url in urls if "/docs/" in urlparse(url).path]
            logger.info(f"Found {len(doc_urls)} pages under /docs/")
            return doc_urls
        except Exception as e:
            logger.error(f"Failed to fetch sitemap: {e}")
            return []

    def extract_links_from_page(self, page, current_url, path_filter="/docs/"):
        """
        Extract all links from a page that match the path filter.

        Args:
            page: Playwright page object
            current_url: Current page URL
            path_filter: Path pattern to filter links (default: '/docs/')

        Returns:
            Set of discovered URLs
        """
        links = set()

        try:
            # Get all <a> tags
            link_elements = page.query_selector_all("a[href]")

            parsed_base = urlparse(current_url)
            base_domain = parsed_base.netloc

            for element in link_elements:
                href = element.get_attribute("href")
                if not href:
                    continue

                # Convert relative URLs to absolute
                absolute_url = urljoin(current_url, href)
                parsed_url = urlparse(absolute_url)

                # Filter: same domain and contains path_filter
                if parsed_url.netloc == base_domain and path_filter in parsed_url.path:
                    # Remove fragment and normalize
                    clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                    if parsed_url.query:
                        clean_url += f"?{parsed_url.query}"
                    links.add(clean_url)

        except Exception as e:
            logger.warning(f"Error extracting links from {current_url}: {e}")

        return links

    def discover_links_recursive(
        self, start_url, path_filter="/docs/", max_depth=MAX_DISCOVERY_DEPTH
    ):
        """
        Recursively discover documentation links starting from a URL.

        Args:
            start_url: Starting URL for discovery
            path_filter: Path pattern to filter links (default: '/docs/')
            max_depth: Maximum number of URLs to discover

        Returns:
            List of discovered URLs
        """
        discovered = set()
        to_visit = {start_url}
        visited = set()

        logger.info(f"Starting recursive link discovery from {start_url}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            pbar = tqdm(desc="Discovering links", unit="page")

            while to_visit and len(discovered) < max_depth:
                current_url = to_visit.pop()

                if current_url in visited:
                    continue

                visited.add(current_url)
                discovered.add(current_url)
                pbar.update(1)
                pbar.set_postfix({"found": len(discovered), "queue": len(to_visit)})

                try:
                    # Load the page
                    page.goto(current_url, timeout=PAGE_LOAD_TIMEOUT)
                    page.wait_for_load_state("networkidle", timeout=15000)

                    # Extract links from this page
                    new_links = self.extract_links_from_page(page, current_url, path_filter)

                    # Add new unvisited links to the queue
                    for link in new_links:
                        if link not in visited and link not in discovered:
                            to_visit.add(link)

                except Exception as e:
                    logger.warning(f"Failed to process {current_url}: {e}")

            pbar.close()
            browser.close()

        logger.info(f"Discovery complete. Found {len(discovered)} URLs")
        return sorted(list(discovered))

    def discover_links(self, start_url=None, path_filter="/docs/", max_depth=MAX_DISCOVERY_DEPTH):
        """
        Discover documentation links. Try sitemap first, fallback to recursive discovery.

        Args:
            start_url: Starting URL for recursive discovery (if sitemap fails)
            path_filter: Path pattern to filter links (default: '/docs/')
            max_depth: Maximum number of URLs to discover in recursive mode

        Returns:
            List of discovered URLs
        """
        # Try sitemap first
        urls = self.fetch_sitemap()

        if urls:
            logger.info(f"Successfully found {len(urls)} URLs from sitemap")
            return urls

        # Fallback to recursive discovery
        logger.info("Sitemap not available, using recursive link discovery")

        if not start_url:
            # Try to construct a starting URL
            if self.base_url:
                start_url = (
                    f"{self.base_url}/docs/"
                    if not self.base_url.endswith("/")
                    else f"{self.base_url}docs/"
                )
            else:
                logger.error("No start URL provided and no base_url configured")
                return []

        return self.discover_links_recursive(start_url, path_filter, max_depth)

    def process_url_with_playwright(self, page, url, incremental=False):
        """Downloads and converts a single URL using Playwright."""
        # 如果还没有设置subdomain，从当前URL提取或使用custom_folder
        if self.subdomain is None:
            if self.custom_folder:
                self.subdomain = self.custom_folder
                logger.info(f"Using custom folder: {self.subdomain}")
            else:
                self.subdomain = self.extract_subdomain(url)
                logger.info(f"Using auto-detected folder (domain): {self.subdomain}")
            # 创建子文件夹
            self.output_subdir = os.path.join(self.output_dir, self.subdomain)
            os.makedirs(self.output_subdir, exist_ok=True)

        slug = urlparse(url).path.strip("/").replace("/", "_")
        if not slug:
            slug = "index"
        filename = f"{slug}.md"
        filepath = os.path.join(self.output_subdir, filename)

        content = None
        title = None

        for attempt in range(MAX_RETRIES):
            try:
                # 导航到页面
                page.goto(url, timeout=PAGE_LOAD_TIMEOUT)

                # 等待主内容加载完成
                # 尝试等待文章内容或主区域
                try:
                    page.wait_for_selector('article, main, [role="main"]', timeout=10000)
                except Exception:
                    pass

                # 额外等待确保JS完全渲染
                page.wait_for_load_state("networkidle", timeout=15000)

                # 获取渲染后的HTML
                content = page.content()
                break
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == MAX_RETRIES - 1:
                    error_msg = str(e)
                    logger.error(f"Failed to download {url} after {MAX_RETRIES} attempts")
                    return {"url": url, "error": error_msg, "failed": True}

        if content:
            try:
                markdown_content, page_title = self.convert_to_markdown(content)
                title = page_title

                # Check if content changed (incremental mode)
                content_hash = CrawlCache.compute_hash(markdown_content)
                if incremental and self.cache:
                    if not self.cache.is_changed(url, content_hash):
                        return {"url": url, "skipped": True, "reason": "unchanged"}

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                # Update cache
                if self.cache:
                    self.cache.update_page(url, content_hash)

                return {"title": title, "url": url, "file": filename}
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error converting {url}: {e}")
                return {"url": url, "error": error_msg, "failed": True}

        return {"url": url, "error": "Empty content", "failed": True}

    def convert_to_markdown(self, html_content):
        """Extracts content and converts to Markdown."""
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract title
        title_tag = soup.find("title")
        title = title_tag.text.strip() if title_tag else "No Title"

        # Remove unwanted elements
        for tag in soup.find_all(
            ["nav", "footer", "script", "style", "noscript", "iframe", "header"]
        ):
            tag.decompose()

        # Common classes/IDs for unwanted elements
        unwanted_selectors = [
            ".sidebar",
            "#sidebar",
            ".toc",
            "#toc",
            ".breadcrumbs",
            ".breadcrumb",
            ".footer",
            ".header",
            ".nav",
            '[role="navigation"]',
            ".navigation",
            ".menu",
        ]
        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()

        # Prioritize content extraction - 尝试更具体的选择器
        content_element = None

        # 尝试找到文档内容区域
        content_selectors = [
            "article",
            '[role="main"]',
            ".docs-content",
            ".content",
            ".markdown-body",
            "main",
            ".main-content",
        ]

        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element and len(content_element.get_text(strip=True)) > 100:
                break

        if not content_element:
            content_element = soup.find("body")

        if not content_element:
            return "", title

        # Convert to Markdown
        markdown = md(str(content_element), heading_style="ATX", strip=["img"])

        # 清理多余的空行
        lines = markdown.split("\n")
        cleaned_lines = []
        prev_empty = False
        for line in lines:
            is_empty = not line.strip()
            if is_empty and prev_empty:
                continue
            cleaned_lines.append(line)
            prev_empty = is_empty

        return "\n".join(cleaned_lines).strip(), title

    def generate_index(self):
        """Generates the index.md file."""
        index_path = os.path.join(self.output_subdir, "index.md")
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("# Documentation Index\n\n")
            f.write("| Title | Original URL | Local File |\n")
            f.write("|-------|--------------|------------|\n")
            for item in sorted(self.results, key=lambda x: x["title"]):
                title = item["title"]
                url = item["url"]
                file = item["file"]
                f.write(f"| {title} | [{url}]({url}) | [{file}]({file}) |\n")
        logger.info(f"Generated index at {index_path}")

    def generate_failure_report(self):
        """Generates a failure report if there are failed URLs."""
        if not self.failed:
            return

        report_path = os.path.join(self.output_subdir, "failed_urls.txt")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# Failed URLs Report\n\n")
            f.write(f"Total failed: {len(self.failed)}\n\n")
            for item in self.failed:
                url = item["url"]
                error = item.get("error", "Unknown error")
                f.write(f"URL: {url}\n")
                f.write(f"Error: {error}\n\n")
        logger.warning(f"Generated failure report at {report_path}")

    def _print_summary(self, total_urls):
        """Print crawl summary statistics."""
        success_count = len(self.results)
        failed_count = len(self.failed)
        skipped_count = len(self.skipped)
        logger.info("=" * 50)
        logger.info("Crawl Summary:")
        logger.info(f"  Total URLs: {total_urls}")
        logger.info(f"  Successful: {success_count}")
        logger.info(f"  Skipped (unchanged): {skipped_count}")
        logger.info(f"  Failed: {failed_count}")
        if total_urls > 0:
            success_rate = (success_count / total_urls) * 100
            logger.info(f"  Success Rate: {success_rate:.1f}%")
        logger.info("=" * 50)

    def _setup_output_dir(self, url):
        """Setup output subdirectory based on URL or custom folder."""
        if self.subdomain is None:
            if self.custom_folder:
                self.subdomain = self.custom_folder
                logger.info(f"Using custom folder: {self.subdomain}")
            else:
                self.subdomain = self.extract_subdomain(url)
                logger.info(f"Using auto-detected folder (domain): {self.subdomain}")
            self.output_subdir = os.path.join(self.output_dir, self.subdomain)
            os.makedirs(self.output_subdir, exist_ok=True)
            # Initialize cache after output_subdir is set
            self.cache = CrawlCache(self.output_subdir)

    async def _process_url_async(self, context, url, semaphore, pbar, incremental=False):
        """Async version of process_url_with_playwright."""
        async with semaphore:
            page = await context.new_page()
            try:
                slug = urlparse(url).path.strip("/").replace("/", "_")
                if not slug:
                    slug = "index"
                filename = f"{slug}.md"
                filepath = os.path.join(self.output_subdir, filename)

                content = None
                title = None

                for attempt in range(MAX_RETRIES):
                    try:
                        await page.goto(url, timeout=PAGE_LOAD_TIMEOUT)
                        try:
                            await page.wait_for_selector(
                                'article, main, [role="main"]', timeout=10000
                            )
                        except Exception:
                            pass
                        await page.wait_for_load_state("networkidle", timeout=15000)
                        content = await page.content()
                        break
                    except Exception as e:
                        logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                        if attempt == MAX_RETRIES - 1:
                            error_msg = str(e)
                            logger.error(f"Failed to download {url} after {MAX_RETRIES} attempts")
                            pbar.update(1)
                            return {"url": url, "error": error_msg, "failed": True}

                if content:
                    try:
                        markdown_content, page_title = self.convert_to_markdown(content)
                        title = page_title

                        # Check if content changed (incremental mode)
                        content_hash = CrawlCache.compute_hash(markdown_content)
                        if incremental and self.cache:
                            if not self.cache.is_changed(url, content_hash):
                                pbar.update(1)
                                return {"url": url, "skipped": True, "reason": "unchanged"}

                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(markdown_content)

                        # Update cache
                        if self.cache:
                            self.cache.update_page(url, content_hash)

                        pbar.update(1)
                        return {"title": title, "url": url, "file": filename}
                    except Exception as e:
                        error_msg = str(e)
                        logger.error(f"Error converting {url}: {e}")
                        pbar.update(1)
                        return {"url": url, "error": error_msg, "failed": True}

                pbar.update(1)
                return {"url": url, "error": "Empty content", "failed": True}
            finally:
                await page.close()

    async def _run_async(self, urls, concurrency=DEFAULT_CONCURRENCY, incremental=False):
        """Async implementation of the crawler."""
        logger.info(
            f"Starting concurrent download of {len(urls)} pages (concurrency={concurrency})..."
        )
        if incremental:
            logger.info("Incremental mode: skipping unchanged pages")

        semaphore = asyncio.Semaphore(concurrency)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            pbar = tqdm(total=len(urls), unit="page")

            tasks = [
                self._process_url_async(context, url, semaphore, pbar, incremental) for url in urls
            ]
            results = await asyncio.gather(*tasks)

            pbar.close()
            await browser.close()

        # 分离成功、失败和跳过的结果
        for r in results:
            if r is not None:
                if r.get("failed"):
                    self.failed.append(r)
                elif r.get("skipped"):
                    self.skipped.append(r)
                else:
                    self.results.append(r)

        # Save cache after crawling
        if self.cache:
            self.cache.save()

    def run(
        self,
        urls=None,
        start_url=None,
        path_filter="/docs/",
        max_depth=MAX_DISCOVERY_DEPTH,
        concurrency=None,
        incremental=False,
    ):
        """
        Run the crawler.

        Args:
            urls: List of URLs to crawl. If None, uses discover_links method.
            start_url: Starting URL for recursive discovery (if needed)
            path_filter: Path pattern to filter links (default: '/docs/')
            max_depth: Maximum number of URLs to discover in recursive mode
            concurrency: Number of concurrent pages to process (default: 5, use 1 for sequential)
            incremental: If True, skip unchanged pages (based on content hash)
        """
        if urls is None:
            urls = self.discover_links(start_url, path_filter, max_depth)

        if not urls:
            logger.warning("No URLs found to process.")
            return

        # Setup output directory from first URL
        self._setup_output_dir(urls[0])

        if concurrency is None:
            concurrency = DEFAULT_CONCURRENCY

        if concurrency == 1:
            # Use original synchronous mode
            logger.info(f"Starting download of {len(urls)} pages using Playwright (sequential)...")
            if incremental:
                logger.info("Incremental mode: skipping unchanged pages")

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()

                for url in tqdm(urls, unit="page"):
                    result = self.process_url_with_playwright(page, url, incremental)
                    if result:
                        if result.get("failed"):
                            self.failed.append(result)
                        elif result.get("skipped"):
                            self.skipped.append(result)
                        else:
                            self.results.append(result)

                browser.close()

            # Save cache after crawling
            if self.cache:
                self.cache.save()
        else:
            # Use async concurrent mode
            asyncio.run(self._run_async(urls, concurrency, incremental))

        self.generate_index()
        self.generate_failure_report()
        self._print_summary(len(urls))
        logger.info("Done.")
