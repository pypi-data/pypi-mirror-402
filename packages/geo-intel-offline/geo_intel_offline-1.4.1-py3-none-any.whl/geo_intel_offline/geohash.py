"""
Geohash encoding and decoding for spatial indexing.

Geohash is a geocoding system that encodes latitude/longitude into a string.
We use it to create a spatial index for fast candidate country filtering.

Design Decision: Using precision level 6 (32-bit geohash) as a balance:
- Precision ~1.2km × 0.6km (sufficient for country-level resolution)
- Small index size (~200 countries × few geohashes each)
- Fast encoding/decoding operations
"""

from typing import Tuple

# Base32 encoding used by geohash
BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"

# Geohash precision for indexing (6 chars = ~1.2km precision)
GEOHASH_PRECISION = 6


def encode(lat: float, lon: float, precision: int = GEOHASH_PRECISION) -> str:
    """
    Encode latitude/longitude to geohash string.
    
    Args:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)
        precision: Number of geohash characters (default 6)
    
    Returns:
        Geohash string
    """
    if not (-90 <= lat <= 90):
        raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
    if not (-180 <= lon <= 180):
        raise ValueError(f"Longitude must be between -180 and 180, got {lon}")
    
    lat_range = (-90.0, 90.0)
    lon_range = (-180.0, 180.0)
    bits = 0
    bits_per_char = 5
    geohash = []
    
    ch = 0
    
    for i in range(precision * bits_per_char):
        if i % 2 == 0:
            # Longitude bit
            mid = (lon_range[0] + lon_range[1]) / 2
            if lon >= mid:
                ch |= (1 << (bits_per_char - 1 - (i // 2) % bits_per_char))
                lon_range = (mid, lon_range[1])
            else:
                lon_range = (lon_range[0], mid)
        else:
            # Latitude bit
            mid = (lat_range[0] + lat_range[1]) / 2
            if lat >= mid:
                ch |= (1 << (bits_per_char - 1 - (i // 2) % bits_per_char))
                lat_range = (mid, lat_range[1])
            else:
                lat_range = (lat_range[0], mid)
        
        if (i + 1) % bits_per_char == 0:
            geohash.append(BASE32[ch])
            ch = 0
    
    return ''.join(geohash)


def decode(geohash: str) -> Tuple[float, float, Tuple[float, float], Tuple[float, float]]:
    """
    Decode geohash string to latitude/longitude with bounding box.
    
    Args:
        geohash: Geohash string
    
    Returns:
        Tuple of (lat, lon, lat_range, lon_range)
    """
    if not geohash:
        raise ValueError("Geohash cannot be empty")
    
    lat_range = (-90.0, 90.0)
    lon_range = (-180.0, 180.0)
    is_even = True
    
    for char in geohash:
        if char not in BASE32:
            raise ValueError(f"Invalid geohash character: {char}")
        
        idx = BASE32.index(char)
        
        for j in range(5):
            bit = (idx >> (4 - j)) & 1
            if is_even:
                mid = (lon_range[0] + lon_range[1]) / 2
                if bit:
                    lon_range = (mid, lon_range[1])
                else:
                    lon_range = (lon_range[0], mid)
            else:
                mid = (lat_range[0] + lat_range[1]) / 2
                if bit:
                    lat_range = (mid, lat_range[1])
                else:
                    lat_range = (lat_range[0], mid)
            is_even = not is_even
    
    lat = (lat_range[0] + lat_range[1]) / 2
    lon = (lon_range[0] + lon_range[1]) / 2
    
    return lat, lon, lat_range, lon_range


def get_neighbors(geohash: str) -> list[str]:
    """
    Get 8 neighboring geohashes (for border cases).
    
    Design Decision: Check neighbors when point-in-polygon fails.
    This handles edge cases where a point is near geohash boundaries.
    
    Args:
        geohash: Geohash string
    
    Returns:
        List of 8 neighboring geohashes plus the original
    """
    lat, lon, lat_range, lon_range = decode(geohash)
    
    # Calculate step size from precision
    lat_step = lat_range[1] - lat_range[0]
    lon_step = lon_range[1] - lon_range[0]
    
    neighbors = []
    for dlat in [-lat_step, 0, lat_step]:
        for dlon in [-lon_step, 0, lon_step]:
            if dlat == 0 and dlon == 0:
                continue
            new_lat = lat + dlat
            new_lon = lon + dlon
            
            # Clamp to valid ranges
            new_lat = max(-90, min(90, new_lat))
            new_lon = max(-180, min(180, new_lon))
            
            neighbors.append(encode(new_lat, new_lon, len(geohash)))
    
    return neighbors
