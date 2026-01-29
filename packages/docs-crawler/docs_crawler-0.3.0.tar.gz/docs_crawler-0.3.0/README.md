# Docs Crawler

A powerful documentation crawler that converts web documentation to Markdown format using Playwright for JavaScript-rendered content.

## Features

- **Smart Link Discovery**: Tries sitemap first, automatically falls back to recursive link discovery
- **Discover Mode**: Find and save documentation URLs before crawling
- Crawls documentation from sitemaps or URL lists
- Uses Playwright to handle JavaScript-rendered Single Page Applications (SPAs)
- Converts HTML to clean Markdown format
- Auto-detects domain-based folder structure
- Generates an index of all crawled pages
- Progress tracking with tqdm
- Retry logic for failed requests

## Requirements

- Python 3.8+
- Poetry (for dependency management)

## Installation

### Using Poetry (Recommended)

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Clone the repository
git clone https://github.com/neverbiasu/docs-crawler.git
cd docs-crawler

# Install dependencies
poetry install

# Install Playwright browsers
poetry run playwright install chromium
```

### Using pip

```bash
pip install docs-crawler
playwright install chromium
```

## Usage

### Command Line Interface

The package provides a `docs-crawler` command with three modes:

#### 1. Sitemap Mode (Default)
Tries to fetch URLs from sitemap first, automatically falls back to recursive link discovery if sitemap is not available.

```bash
# Crawl from sitemap (with automatic fallback)
poetry run docs-crawler --base-url https://example.com

# Specify custom sitemap URL
poetry run docs-crawler --sitemap-url https://example.com/custom-sitemap.xml

# Customize path filter and max URLs to discover
poetry run docs-crawler --base-url https://example.com --path-filter /docs/ --max-depth 200
```

#### 2. Discover Mode
Discover all documentation URLs and save them to a file for review before crawling.

```bash
# Discover links and save to auto-generated file (e.g., example_urls.txt)
poetry run docs-crawler --mode discover --base-url https://example.com

# Specify custom output file
poetry run docs-crawler --mode discover --base-url https://example.com --output-file my-urls.txt

# Start from a specific URL
poetry run docs-crawler --mode discover --start-url https://example.com/docs/intro

# Customize discovery settings
poetry run docs-crawler --mode discover --base-url https://example.com --path-filter /api/ --max-depth 50
```

The discover mode will:
1. Find all documentation links (using sitemap or recursive discovery)
2. Display the first 10 URLs as a preview
3. Ask for your confirmation before saving
4. Save URLs to a file named `{subdomain}_urls.txt` (e.g., `example_urls.txt`)

#### 3. List Mode
Crawl from a list of URLs in a text file.

```bash
# Crawl from URL list
poetry run docs-crawler --mode list --file urls.txt

# Specify custom output folder
poetry run docs-crawler --mode list --file urls.txt --folder my-docs
```

#### Common Options

```bash
# Custom output directory
--output-dir custom-output

# Custom folder name
--folder my-docs

# Path filter for link discovery (default: /docs/)
--path-filter /documentation/

# Maximum URLs to discover (default: 100)
--max-depth 500

# Starting URL for recursive discovery
--start-url https://example.com/docs/
```

### Python API

```python
from docs_crawler import Crawler

# Create crawler instance
crawler = Crawler(
    base_url="https://antigravity.google",
    output_dir="output",
    custom_folder="antigravity"
)

# Run with automatic link discovery (sitemap first, then recursive)
crawler.run()

# Discover links only
urls = crawler.discover_links(
    start_url="https://example.com/docs/",
    path_filter="/docs/",
    max_depth=100
)
print(f"Found {len(urls)} URLs")

# Run with custom URLs
crawler.run(urls=[
    "https://example.com/docs/page1",
    "https://example.com/docs/page2"
])

# Run with custom discovery settings
crawler.run(
    start_url="https://example.com/docs/intro",
    path_filter="/documentation/",
    max_depth=200
)
```

## Output

- The downloaded Markdown files will be saved in the `output/` directory (or custom directory).
- An index of all downloaded pages is available at `output/{folder}/index.md`.
- Files are organized by domain or custom folder name.

## Development

```bash
# Install development dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Format code
poetry run black .

# Lint code
poetry run flake8

# Type checking
poetry run mypy docs_crawler
```

## Configuration

The crawler can be configured through:
- Command-line arguments
- Python API parameters
- Environment variables (coming soon)

## How It Works

### Link Discovery

The crawler uses a smart two-step approach:

1. **Sitemap First**: Attempts to fetch URLs from the sitemap.xml file
2. **Recursive Discovery Fallback**: If sitemap is unavailable or empty, automatically discovers links by:
   - Starting from a base URL (e.g., `/docs/`)
   - Extracting all internal links matching the path filter
   - Recursively crawling pages to find more documentation links
   - Respecting the max-depth limit to avoid excessive crawling

### Workflow Example

```bash
# Step 1: Discover links and save for review
poetry run docs-crawler --mode discover --base-url https://example.com
# Output: example_urls.txt

# Step 2: Review and edit urls.txt if needed
# (Remove unwanted URLs, add missing ones, etc.)

# Step 3: Crawl the URLs
poetry run docs-crawler --mode list --file example_urls.txt
```

## Notes

- The crawler uses Playwright to handle JavaScript-rendered content, making it suitable for modern SPAs.
- Default path filter is `/docs/` but can be customized with `--path-filter`
- Respects retry limits and timeouts to be polite to servers.
- Auto-detects domain-based folder structure or uses custom folder names.
- Recursive discovery avoids infinite loops by tracking visited URLs
- URL files are named using the subdomain for easy identification (e.g., `github_urls.txt`, `example_urls.txt`)

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
