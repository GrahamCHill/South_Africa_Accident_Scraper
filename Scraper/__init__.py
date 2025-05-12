"""
South African Accident Data Scraper package.

This package contains scrapers for various South African accident data sources.
"""
from .base_scraper import BaseScraper, AccidentRecord
from .ARRIVEALIVE_Scraper import ArriveAliveScraper
from .STATSSA_Scraper import StatsSAScraper
from .DOT_Scraper import DOTScraper
from .RTMC_Scraper import RTMCScraper

__all__ = [
    'BaseScraper',
    'AccidentRecord',
    'ArriveAliveScraper',
    'StatsSAScraper',
    'DOTScraper',
    'RTMCScraper',
]