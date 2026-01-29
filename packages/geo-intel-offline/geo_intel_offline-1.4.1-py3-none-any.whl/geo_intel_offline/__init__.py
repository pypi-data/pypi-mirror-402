"""
geo_intel_offline - Production-ready offline geo-intelligence library.

Unified API for both forward and reverse geocoding:

Forward Geocoding (Coordinates → Country):
    resolve(lat, lon) returns country, ISO codes, continent, timezone, confidence

Reverse Geocoding (Country → Coordinates):
    resolve(country="...") returns country centroid coordinates and metadata

Features:
- Country name, ISO2/ISO3 codes
- Continent and timezone information
- Confidence scores
- 99.92% accuracy across 258 countries
- 100% offline, no API keys required
"""

from .api import resolve, GeoIntelResult, resolve_by_country, ReverseGeoIntelResult

__version__ = "1.0.3"
__all__ = ["resolve", "GeoIntelResult", "resolve_by_country", "ReverseGeoIntelResult"]
