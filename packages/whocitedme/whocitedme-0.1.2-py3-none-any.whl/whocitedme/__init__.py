"""
WhoCitedMe - Google Scholar Citation Analysis Library

A Python library for scraping Google Scholar citations, enriching author information,
and analyzing high-impact citations for academic purposes.
"""

__version__ = "0.1.2"
__author__ = "WhoCitedMe Contributors"

from whocitedme.scrapers.citing_papers import CitingPapersScraper
from whocitedme.scrapers.author_enricher import AuthorEnricher
from whocitedme.scrapers.author_info import AuthorInfoFetcher
from whocitedme.processors.id_matcher import IDMatcher
from whocitedme.processors.top_scholar import TopScholarProcessor

__all__ = [
    "CitingPapersScraper",
    "AuthorEnricher",
    "AuthorInfoFetcher",
    "IDMatcher",
    "TopScholarProcessor",
    "__version__",
]
