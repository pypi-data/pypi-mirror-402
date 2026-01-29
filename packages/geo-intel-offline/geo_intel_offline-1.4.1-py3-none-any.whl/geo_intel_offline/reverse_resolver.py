"""
Reverse geocoding - resolve country name/ISO code to coordinates.

Given a country name or ISO code, returns:
- Latitude/Longitude (centroid of country)
- Country metadata (name, ISO codes, continent, timezone)
"""

from typing import Optional, Dict, Tuple
from .data_loader import get_loader
from .polygon_utils import get_polygon_centroid


class ReverseResolutionResult:
    """Result of reverse geo-intelligence resolution."""
    
    def __init__(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        country_name: Optional[str] = None,
        iso2: Optional[str] = None,
        iso3: Optional[str] = None,
        continent: Optional[str] = None,
        timezone: Optional[str] = None,
        confidence: float = 1.0  # Always 1.0 for exact country match
    ):
        self.latitude = latitude
        self.longitude = longitude
        self.country_name = country_name
        self.iso2 = iso2
        self.iso3 = iso3
        self.continent = continent
        self.timezone = timezone
        self.confidence = confidence
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'country': self.country_name,
            'iso2': self.iso2,
            'iso3': self.iso3,
            'continent': self.continent,
            'timezone': self.timezone,
            'confidence': self.confidence
        }
    
    def __repr__(self) -> str:
        return (
            f"ReverseResolutionResult("
            f"country={self.country_name!r}, "
            f"lat={self.latitude}, "
            f"lon={self.longitude}, "
            f"iso2={self.iso2!r}"
            f")"
        )


def _normalize_country_name(name: str) -> str:
    """Normalize country name for matching."""
    return name.strip().lower().replace('_', ' ').replace('-', ' ')


def _find_country_by_name_or_iso(
    country_input: str,
    data_dir: Optional[str] = None
) -> Optional[Tuple[int, Dict]]:
    """
    Find country ID and metadata by name or ISO code.
    
    Args:
        country_input: Country name, ISO2 code, or ISO3 code
        data_dir: Optional custom data directory
    
    Returns:
        Tuple of (country_id, metadata) or None if not found
    """
    loader = get_loader(data_dir)
    metadata = loader.metadata
    polygons = loader.polygons
    
    normalized_input = country_input.strip().upper()
    normalized_name = _normalize_country_name(country_input)
    
    # Search through all countries
    for country_id, country_meta in metadata.items():
        # Check ISO2
        iso2 = country_meta.get('iso2', '').upper()
        if iso2 == normalized_input:
            return country_id, country_meta
        
        # Check ISO3
        iso3 = country_meta.get('iso3', '').upper()
        if iso3 == normalized_input:
            return country_id, country_meta
        
        # Check country name (exact match)
        country_name = country_meta.get('name', '')
        normalized_meta_name = _normalize_country_name(country_name)
        if normalized_meta_name == normalized_name:
            return country_id, country_meta
        
        # Check country name (contains match - for partial names)
        if normalized_name in normalized_meta_name or normalized_meta_name in normalized_name:
            # Prefer exact match, but return if found
            if normalized_meta_name == normalized_name:
                return country_id, country_meta
    
    # Try partial match (case-insensitive)
    for country_id, country_meta in metadata.items():
        country_name = country_meta.get('name', '')
        normalized_meta_name = _normalize_country_name(country_name)
        
        # Check if input is contained in country name or vice versa
        if normalized_name in normalized_meta_name or normalized_meta_name in normalized_name:
            return country_id, country_meta
    
    return None


def resolve_by_country(
    country_input: str,
    data_dir: Optional[str] = None
) -> ReverseResolutionResult:
    """
    Resolve country name or ISO code to coordinates and metadata.
    
    This function performs reverse geocoding - given a country name or ISO code,
    it returns the country's centroid coordinates along with all metadata.
    
    Args:
        country_input: Country name (e.g., "United States", "USA", "US") or ISO code (e.g., "US", "USA")
        data_dir: Optional custom data directory path
    
    Returns:
        ReverseResolutionResult object with:
        - latitude: Country centroid latitude
        - longitude: Country centroid longitude
        - country: Country name
        - iso2: ISO 3166-1 alpha-2 code
        - iso3: ISO 3166-1 alpha-3 code
        - continent: Continent name
        - timezone: IANA timezone identifier
        - confidence: Always 1.0 for exact country match
    
    Example:
        >>> result = resolve_by_country("United States")
        >>> print(result.latitude, result.longitude)
        39.8283 -98.5795
        >>> print(result.iso2)
        'US'
        
        >>> result = resolve_by_country("US")  # ISO2 code
        >>> print(result.country)
        'United States of America'
        
        >>> result = resolve_by_country("USA")  # ISO3 code
        >>> print(result.latitude, result.longitude)
        39.8283 -98.5795
    
    Raises:
        ValueError: If country not found
        FileNotFoundError: If data files are missing
    """
    # Find country
    country_match = _find_country_by_name_or_iso(country_input, data_dir)
    
    if not country_match:
        raise ValueError(
            f"Country not found: '{country_input}'. "
            f"Please provide a valid country name or ISO code (ISO2/ISO3)."
        )
    
    country_id, metadata = country_match
    
    # Get polygon to calculate centroid
    loader = get_loader(data_dir)
    polygons = loader.polygons
    
    if country_id not in polygons:
        raise ValueError(f"Polygon data not found for country ID {country_id}")
    
    polygon_data = polygons[country_id]
    
    # Handle MultiPolygon (multiple exteriors) or single Polygon
    exteriors = []
    if polygon_data.get('multi', False):
        # MultiPolygon - get all exteriors
        exteriors_list = polygon_data.get('exteriors', [])
        if exteriors_list:
            exteriors = exteriors_list
        else:
            # Fallback: try single exterior
            exterior = polygon_data.get('exterior', [])
            if exterior:
                exteriors = [exterior]
    else:
        # Single Polygon
        exterior = polygon_data.get('exterior', [])
        if exterior:
            exteriors = [exterior]
    
    if not exteriors:
        raise ValueError(f"Invalid polygon data for country ID {country_id}")
    
    # Calculate centroid from all exteriors (weighted by area)
    # For simplicity, use the largest exterior's centroid
    # Or calculate weighted average of all centroids
    all_centroids = []
    for ext in exteriors:
        if ext:
            centroid = get_polygon_centroid(ext)
            all_centroids.append(centroid)
    
    if not all_centroids:
        raise ValueError(f"No valid exteriors found for country ID {country_id}")
    
    # Use average of all centroids (simple approach)
    # For MultiPolygon countries, this gives a reasonable center point
    centroid_lat = sum(c[0] for c in all_centroids) / len(all_centroids)
    centroid_lon = sum(c[1] for c in all_centroids) / len(all_centroids)
    
    # Build result
    return ReverseResolutionResult(
        latitude=centroid_lat,
        longitude=centroid_lon,
        country_name=metadata.get('name'),
        iso2=metadata.get('iso2'),
        iso3=metadata.get('iso3'),
        continent=metadata.get('continent'),
        timezone=metadata.get('timezone'),
        confidence=1.0  # Exact match
    )
