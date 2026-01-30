"""
MBM Services Module

External service integrations for fetching data from legal,
public APIs (Wikipedia, Wikimedia Commons).
"""

from mbm.services.wikipedia import WikipediaService
from mbm.services.wikimedia import WikimediaService

__all__ = [
    "WikipediaService",
    "WikimediaService",
]
