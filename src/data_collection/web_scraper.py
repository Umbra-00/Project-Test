# Copyright (c) 2024 Umbra. All rights reserved.
import requests
from bs4 import BeautifulSoup

from src.utils.logging_utils import setup_logging # Import the new logging utility

# Setup logging for the scraper
logger = setup_logging(__name__) # Use the reusable setup_logging function

def fetch_html_content(url: str) -> str | None:
    """Fetches HTML content from a given URL."""
    logger.info(f"Attempting to fetch content from: {url}")
    try:
        response = requests.get(url, timeout=10) # 10 second timeout
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        logger.info(f"Successfully fetched content from: {url}")
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching content from {url}: {e}")
        return None

def parse_html_content(html_content: str) -> BeautifulSoup:
    """Parses HTML content using BeautifulSoup and lxml parser."""
    logger.info("Parsing HTML content...")
    return BeautifulSoup(html_content, 'lxml')


if __name__ == "__main__":
    # Example usage
    example_url = "https://www.example.com"
    logger.info(f"Running example web scraping for: {example_url}")
    html = fetch_html_content(example_url)
    if html:
        soup = parse_html_content(html)
        logger.info(f"Parsed title: {soup.title.string}")
        # You can add more parsing logic here, e.g., to extract specific data
    else:
        logger.error("Failed to fetch HTML content for example.") 