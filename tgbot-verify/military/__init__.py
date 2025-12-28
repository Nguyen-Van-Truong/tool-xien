"""Military verification module for ChatGPT Military discount"""

from .config import (
    SHEERID_BASE_URL,
    PROGRAM_ID,
    MILITARY_STATUSES,
    ORGANIZATIONS,
    EMAIL_DOMAINS,
)
from .sheerid_verifier import (
    MilitaryVerifier,
    BulkMilitaryVerifier,
)
from .vlm_scraper import (
    VLMScraper,
    scrape_veterans_sync,
    scrape_veterans_bulk_sync,
)

__all__ = [
    'SHEERID_BASE_URL',
    'PROGRAM_ID', 
    'MILITARY_STATUSES',
    'ORGANIZATIONS',
    'EMAIL_DOMAINS',
    'MilitaryVerifier',
    'BulkMilitaryVerifier',
    'VLMScraper',
    'scrape_veterans_sync',
    'scrape_veterans_bulk_sync',
]
