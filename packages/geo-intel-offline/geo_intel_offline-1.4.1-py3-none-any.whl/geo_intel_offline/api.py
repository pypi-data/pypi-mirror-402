"""
Public API for geo_intel_offline library.

Clean, simple interface that hides implementation details.
"""

from typing import Dict, Optional, List, Union, TYPE_CHECKING
from .resolver import resolve as _resolve, ResolutionResult
from .reverse_resolver import resolve_by_country as _resolve_by_country, ReverseResolutionResult

if TYPE_CHECKING:
    from typing import TypeVar


class GeoIntelResult:
    """
    Result object for geo-intelligence resolution.
    
    Provides both dictionary-like access and attribute access.
    """
    
    def __init__(self, result: ResolutionResult):
        self._result = result
    
    @property
    def country(self) -> Optional[str]:
        """Country name."""
        return self._result.country_name
    
    @property
    def iso2(self) -> Optional[str]:
        """ISO 3166-1 alpha-2 code."""
        return self._result.iso2
    
    @property
    def iso3(self) -> Optional[str]:
        """ISO 3166-1 alpha-3 code."""
        return self._result.iso3
    
    @property
    def continent(self) -> Optional[str]:
        """Continent name."""
        return self._result.continent
    
    @property
    def timezone(self) -> Optional[str]:
        """IANA timezone identifier."""
        return self._result.timezone
    
    @property
    def confidence(self) -> float:
        """Confidence score (0.0-1.0)."""
        return self._result.confidence
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return self._result.to_dict()
    
    def __repr__(self) -> str:
        return (
            f"GeoIntelResult("
            f"country={self.country!r}, "
            f"iso2={self.iso2!r}, "
            f"iso3={self.iso3!r}, "
            f"confidence={self.confidence:.2f}"
            f")"
        )


def resolve(
    *args,
    data_dir: Optional[str] = None,
    countries: Optional[List[str]] = None,
    continents: Optional[List[str]] = None,
    exclude_countries: Optional[List[str]] = None,
    **kwargs
):
    """
    Resolve coordinates to geo-intelligence (forward geocoding) or country to coordinates (reverse geocoding).
    
    This unified function automatically detects the mode based on parameters:
    
    **Forward Geocoding** (Coordinates → Country):
        Pass two numeric arguments: resolve(lat, lon)
        Example: resolve(40.7128, -74.0060)
    
    **Reverse Geocoding** (Country → Coordinates):
        Pass one string argument: resolve("United States") or resolve("US")
        Example: resolve("United States")
    
    Args:
        *args: 
            - For forward geocoding: (lat: float, lon: float)
            - For reverse geocoding: (country: str)
        data_dir: Optional custom data directory path
        countries: Optional list of ISO2 codes to load (modular format only, forward geocoding)
        continents: Optional list of continent names to load (modular format only, forward geocoding)
        exclude_countries: Optional list of ISO2 codes to exclude (modular format only, forward geocoding)
        **kwargs: Reserved for future use
    
    Returns:
        - GeoIntelResult for forward geocoding (when lat/lon provided)
        - ReverseGeoIntelResult for reverse geocoding (when country string provided)
    
    Examples:
        Forward geocoding (coordinates → country):
        >>> result = resolve(40.7128, -74.0060)  # New York
        >>> print(result.country)
        'United States of America'
        >>> print(result.iso2)
        'US'
        
        Reverse geocoding (country → coordinates):
        >>> result = resolve("United States")
        >>> print(result.latitude, result.longitude)
        39.8283 -98.5795
        >>> print(result.iso2)
        'US'
        
        >>> result = resolve("US")   # ISO2 code
        >>> result = resolve("USA")  # ISO3 code
        
        Forward geocoding with filters:
        >>> result = resolve(40.7128, -74.0060, countries=["US", "CA"])
        >>> result = resolve(40.7128, -74.0060, continents=["North America"])
    
    Raises:
        ValueError: If parameters are invalid or missing
        FileNotFoundError: If data files are missing
    """
    # Auto-detect mode based on arguments
    if len(args) == 2:
        # Forward geocoding: two numeric arguments (lat, lon)
        lat, lon = args[0], args[1]
        
        # Validate types
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            raise ValueError(
                f"Forward geocoding requires two numeric arguments (lat, lon). "
                f"Got: lat={type(lat).__name__}, lon={type(lon).__name__}\n"
                f"For reverse geocoding, use: resolve('Country Name')"
            )
        
        # Forward geocoding mode
        resolution_result = _resolve(
            float(lat), float(lon), data_dir,
            countries=countries,
            continents=continents,
            exclude_countries=exclude_countries
        )
        return GeoIntelResult(resolution_result)
    
    elif len(args) == 1:
        # Reverse geocoding: one string argument (country)
        country_input = args[0]
        
        # Validate type
        if not isinstance(country_input, str):
            raise ValueError(
                f"Reverse geocoding requires one string argument (country name or ISO code). "
                f"Got: {type(country_input).__name__}\n"
                f"For forward geocoding, use: resolve(lat, lon)"
            )
        
        # Check if forward geocoding parameters were passed as keyword args (backward compatibility)
        if 'lat' in kwargs or 'lon' in kwargs:
            raise ValueError(
                "Cannot mix positional and keyword arguments for coordinates. "
                "Use resolve(lat, lon) for forward geocoding or resolve('Country') for reverse geocoding."
            )
        
        # Reverse geocoding mode
        reverse_result = _resolve_by_country(country_input, data_dir)
        return ReverseGeoIntelResult(reverse_result)
    
    elif len(args) == 0:
        # Check if country was passed as keyword argument (backward compatibility)
        if 'country' in kwargs:
            country_input = kwargs.pop('country')
            if not isinstance(country_input, str):
                raise ValueError("country parameter must be a string")
            reverse_result = _resolve_by_country(country_input, data_dir)
            return ReverseGeoIntelResult(reverse_result)
        
        # Check if lat/lon were passed as keyword arguments (backward compatibility)
        if 'lat' in kwargs and 'lon' in kwargs:
            lat, lon = kwargs.pop('lat'), kwargs.pop('lon')
            if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
                raise ValueError("lat and lon must be numeric")
            resolution_result = _resolve(
                float(lat), float(lon), data_dir,
                countries=countries,
                continents=continents,
                exclude_countries=exclude_countries
            )
            return GeoIntelResult(resolution_result)
        
        raise ValueError(
            "Must provide either:\n"
            "  - Two numeric arguments for forward geocoding: resolve(lat, lon)\n"
            "  - One string argument for reverse geocoding: resolve('Country Name')\n"
            "Examples:\n"
            "  Forward:  resolve(40.7128, -74.0060)\n"
            "  Reverse:  resolve('United States')"
        )
    
    else:
        raise ValueError(
            f"Invalid number of arguments: {len(args)}. "
            f"Expected 1 (reverse) or 2 (forward) positional arguments.\n"
            f"Examples:\n"
            f"  Forward:  resolve(40.7128, -74.0060)\n"
            f"  Reverse:  resolve('United States')"
        )


class ReverseGeoIntelResult:
    """
    Result object for reverse geo-intelligence resolution.
    
    Provides both dictionary-like access and attribute access.
    """
    
    def __init__(self, result: ReverseResolutionResult):
        self._result = result
    
    @property
    def latitude(self) -> Optional[float]:
        """Latitude of country centroid."""
        return self._result.latitude
    
    @property
    def longitude(self) -> Optional[float]:
        """Longitude of country centroid."""
        return self._result.longitude
    
    @property
    def country(self) -> Optional[str]:
        """Country name."""
        return self._result.country_name
    
    @property
    def iso2(self) -> Optional[str]:
        """ISO 3166-1 alpha-2 code."""
        return self._result.iso2
    
    @property
    def iso3(self) -> Optional[str]:
        """ISO 3166-1 alpha-3 code."""
        return self._result.iso3
    
    @property
    def continent(self) -> Optional[str]:
        """Continent name."""
        return self._result.continent
    
    @property
    def timezone(self) -> Optional[str]:
        """IANA timezone identifier."""
        return self._result.timezone
    
    @property
    def confidence(self) -> float:
        """Confidence score (always 1.0 for exact country match)."""
        return self._result.confidence
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return self._result.to_dict()
    
    def __repr__(self) -> str:
        return (
            f"ReverseGeoIntelResult("
            f"country={self.country!r}, "
            f"lat={self.latitude}, "
            f"lon={self.longitude}, "
            f"iso2={self.iso2!r}"
            f")"
        )


def resolve_by_country(
    country_input: str,
    data_dir: Optional[str] = None
) -> ReverseGeoIntelResult:
    """
    Resolve country name or ISO code to coordinates and metadata.
    
    **Deprecated**: Use `resolve(country=country_input)` instead for consistency.
    This function is kept for backward compatibility.
    
    This function performs reverse geocoding - given a country name or ISO code,
    it returns the country's centroid coordinates along with all metadata.
    
    Args:
        country_input: Country name (e.g., "United States", "USA", "US") or ISO code (e.g., "US", "USA")
        data_dir: Optional custom data directory path
    
    Returns:
        ReverseGeoIntelResult object with:
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
        
        # Recommended: Use unified resolve() function instead
        >>> result = resolve(country="United States")
    
    Raises:
        ValueError: If country not found
        FileNotFoundError: If data files are missing
    """
    reverse_result = _resolve_by_country(country_input, data_dir)
    return ReverseGeoIntelResult(reverse_result)
