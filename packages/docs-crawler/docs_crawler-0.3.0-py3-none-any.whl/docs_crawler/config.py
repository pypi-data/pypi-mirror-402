"""Configuration file support for docs-crawler."""

import os
import yaml
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "mode": "sitemap",
    "output_dir": "output",
    "path_filter": "/docs/",
    "max_depth": 100,
    "concurrency": 5,
}


def load_config(config_path):
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the YAML config file

    Returns:
        dict: Configuration dictionary merged with defaults
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        user_config = yaml.safe_load(f) or {}

    # Merge with defaults
    config = DEFAULT_CONFIG.copy()
    config.update(user_config)

    logger.info(f"Loaded config from {config_path}")
    return config


def find_config_file():
    """
    Find a config file in current directory or parent directories.

    Looks for: docs-crawler.yaml, docs-crawler.yml, .docs-crawler.yaml, .docs-crawler.yml

    Returns:
        str or None: Path to config file if found, None otherwise
    """
    config_names = [
        "docs-crawler.yaml",
        "docs-crawler.yml",
        ".docs-crawler.yaml",
        ".docs-crawler.yml",
    ]

    current_dir = os.getcwd()

    for name in config_names:
        config_path = os.path.join(current_dir, name)
        if os.path.exists(config_path):
            return config_path

    return None


def generate_example_config(output_path="docs-crawler.yaml"):
    """
    Generate an example configuration file.

    Args:
        output_path: Path to write the example config
    """
    example_config = """# docs-crawler configuration file
# See: https://github.com/neverbiasu/docs-crawler

# Base URL of the documentation site
base_url: https://example.com

# Mode: sitemap, discover, or list
mode: sitemap

# Starting URL for recursive discovery (optional)
# start_url: https://example.com/docs/

# Custom sitemap URL (optional, auto-detected from base_url)
# sitemap_url: https://example.com/sitemap.xml

# Output directory for markdown files
output_dir: output

# Custom folder name (optional, auto-detected from domain)
# folder: my-docs

# Path pattern to filter links
path_filter: /docs/

# Maximum URLs to discover in recursive mode
max_depth: 100

# Number of concurrent pages to process
concurrency: 5

# URL list file (for list mode)
# file: urls.txt
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(example_config)

    logger.info(f"Generated example config at {output_path}")
    return output_path
