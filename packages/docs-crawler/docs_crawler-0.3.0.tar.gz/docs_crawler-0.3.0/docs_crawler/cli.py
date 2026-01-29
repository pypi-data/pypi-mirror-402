import os
import sys
import argparse
import logging
from urllib.parse import urlparse
from docs_crawler.crawler import Crawler
from docs_crawler.config import load_config, find_config_file, generate_example_config

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def extract_subdomain(url):
    """Extract subdomain from URL for file naming."""
    parsed = urlparse(url)
    hostname = parsed.hostname
    if hostname:
        parts = hostname.split(".")
        if len(parts) >= 2:
            return parts[-2]
        elif len(parts) == 1:
            return parts[0]
    return "default"


def main():
    """Main CLI entry point for docs-crawler."""
    parser = argparse.ArgumentParser(
        description="Crawl and convert documentation to Markdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Crawl from sitemap (tries sitemap first, falls back to recursive discovery)
  docs-crawler --base-url https://example.com

  # Discover links only and save to file
  docs-crawler --mode discover --base-url https://example.com

  # Crawl from a list of URLs in a file
  docs-crawler --mode list --file urls.txt

  # Specify custom output folder
  docs-crawler --base-url https://example.com --folder my-docs
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["sitemap", "discover", "list"],
        default="sitemap",
        help="Mode: 'sitemap' (crawl), 'discover' (find URLs), or 'list' (crawl from file).",
    )

    parser.add_argument(
        "--base-url", help="Base URL of the documentation site (e.g., https://example.com)"
    )

    parser.add_argument(
        "--start-url", help="Starting URL for recursive discovery (e.g., https://example.com/docs/)"
    )

    parser.add_argument(
        "--sitemap-url", help="URL of the sitemap (overrides auto-detected sitemap URL)"
    )

    parser.add_argument(
        "--file", help="Path to the text file containing URLs (required if mode is 'list')."
    )

    parser.add_argument(
        "--output-file",
        help="Output file for discovered URLs (discover mode, auto-generated if not specified)",
    )

    parser.add_argument(
        "--folder",
        help="Custom folder name under output directory (overrides auto-detection from domain).",
    )

    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory for markdown files (default: output)",
    )

    parser.add_argument(
        "--path-filter", default="/docs/", help="Path pattern to filter links (default: /docs/)"
    )

    parser.add_argument(
        "--max-depth",
        type=int,
        default=100,
        help="Maximum number of URLs to discover in recursive mode (default: 100)",
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Number of concurrent pages to process (default: 5, use 1 for sequential)",
    )

    parser.add_argument(
        "--config",
        help="Path to YAML config file (auto-detects docs-crawler.yaml if not specified)",
    )

    parser.add_argument(
        "--init-config",
        action="store_true",
        help="Generate an example config file (docs-crawler.yaml) and exit",
    )

    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Only crawl pages that have changed since last crawl (uses content hash)",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-crawl all pages, ignoring cache (opposite of --incremental)",
    )

    args = parser.parse_args()

    # Handle --init-config
    if args.init_config:
        generate_example_config()
        print("Generated docs-crawler.yaml")
        sys.exit(0)

    # Load config file if specified or auto-detect
    config = {}
    config_path = args.config or find_config_file()
    if config_path:
        try:
            config = load_config(config_path)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            sys.exit(1)

    # CLI args override config file (use config values as defaults)
    if not args.base_url and config.get("base_url"):
        args.base_url = config["base_url"]
    if not args.start_url and config.get("start_url"):
        args.start_url = config["start_url"]
    if not args.sitemap_url and config.get("sitemap_url"):
        args.sitemap_url = config["sitemap_url"]
    if not args.file and config.get("file"):
        args.file = config["file"]
    if not args.folder and config.get("folder"):
        args.folder = config["folder"]
    if args.output_dir == "output" and config.get("output_dir"):
        args.output_dir = config["output_dir"]
    if args.path_filter == "/docs/" and config.get("path_filter"):
        args.path_filter = config["path_filter"]
    if args.max_depth == 100 and config.get("max_depth"):
        args.max_depth = config["max_depth"]
    if args.concurrency == 5 and config.get("concurrency"):
        args.concurrency = config["concurrency"]
    if args.mode == "sitemap" and config.get("mode"):
        args.mode = config["mode"]
    if not args.incremental and config.get("incremental"):
        args.incremental = config["incremental"]

    # --force overrides --incremental
    if args.force:
        args.incremental = False

    # Validate arguments
    urls = None

    if args.mode == "discover":
        # Discover mode: find links and save to file
        if not args.base_url and not args.start_url:
            parser.error("--base-url or --start-url is required when mode is 'discover'")

        crawler = Crawler(
            base_url=args.base_url,
            sitemap_url=args.sitemap_url,
            output_dir=args.output_dir,
            custom_folder=args.folder,
        )

        try:
            # Discover links
            discovered_urls = crawler.discover_links(
                start_url=args.start_url, path_filter=args.path_filter, max_depth=args.max_depth
            )

            if not discovered_urls:
                logger.warning("No URLs discovered.")
                sys.exit(0)

            # Generate output filename
            if args.output_file:
                output_file = args.output_file
            else:
                # Use subdomain-based naming
                base = args.base_url or args.start_url
                subdomain = extract_subdomain(base)
                output_file = f"{subdomain}_urls.txt"

            # Show discovered URLs and ask for confirmation
            logger.info(f"\nDiscovered {len(discovered_urls)} URLs:")
            print("\nFirst 10 URLs:")
            for url in discovered_urls[:10]:
                print(f"  - {url}")
            if len(discovered_urls) > 10:
                print(f"  ... and {len(discovered_urls) - 10} more")

            # Ask for confirmation
            print(f"\nSave URLs to '{output_file}'? [Y/n]: ", end="", flush=True)
            response = input().strip().lower()

            if response in ["", "y", "yes"]:
                with open(output_file, "w", encoding="utf-8") as f:
                    for url in discovered_urls:
                        f.write(f"{url}\n")
                logger.info(f"Saved {len(discovered_urls)} URLs to {output_file}")
                logger.info(f"You can now run: docs-crawler --mode list --file {output_file}")
            else:
                logger.info("Cancelled. URLs not saved.")

        except KeyboardInterrupt:
            logger.info("\nDiscovery interrupted by user.")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error during discovery: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

    elif args.mode == "sitemap":
        # Sitemap mode (with fallback to recursive discovery)
        if not args.base_url and not args.sitemap_url:
            parser.error("--base-url or --sitemap-url is required when mode is 'sitemap'")

        crawler = Crawler(
            base_url=args.base_url,
            sitemap_url=args.sitemap_url,
            output_dir=args.output_dir,
            custom_folder=args.folder,
        )

        try:
            crawler.run(
                urls=None,
                start_url=args.start_url,
                path_filter=args.path_filter,
                max_depth=args.max_depth,
                concurrency=args.concurrency,
                incremental=args.incremental,
            )
        except KeyboardInterrupt:
            logger.info("\nCrawling interrupted by user.")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error during crawling: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

    elif args.mode == "list":
        # List mode: crawl from file
        if not args.file:
            parser.error("--file is required when mode is 'list'")

        if not os.path.exists(args.file):
            logger.error(f"File not found: {args.file}")
            sys.exit(1)

        try:
            with open(args.file, "r", encoding="utf-8") as f:
                urls = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(urls)} URLs from {args.file}")
        except Exception as e:
            logger.error(f"Failed to read file {args.file}: {e}")
            sys.exit(1)

        # Determine base_url from first URL if not provided
        if not args.base_url and urls:
            parsed = urlparse(urls[0])
            args.base_url = f"{parsed.scheme}://{parsed.netloc}"

        crawler = Crawler(
            base_url=args.base_url,
            sitemap_url=args.sitemap_url,
            output_dir=args.output_dir,
            custom_folder=args.folder,
        )

        try:
            crawler.run(urls=urls, concurrency=args.concurrency, incremental=args.incremental)
        except KeyboardInterrupt:
            logger.info("\nCrawling interrupted by user.")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error during crawling: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
