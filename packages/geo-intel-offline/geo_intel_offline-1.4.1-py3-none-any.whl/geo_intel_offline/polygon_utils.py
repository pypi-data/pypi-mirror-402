"""
Shared polygon processing utilities.
Consolidates duplicate code from data builders.
"""

from typing import List, Tuple, Dict


def calculate_bounding_box(polygon: List[Tuple[float, float]]) -> Tuple[float, float, float, float]:
    """Calculate bounding box for a polygon."""
    if not polygon:
        return 0.0, 0.0, 0.0, 0.0
    
    lats = [p[0] for p in polygon]
    lons = [p[1] for p in polygon]
    return min(lats), max(lats), min(lons), max(lons)


def calculate_adaptive_step_size(lat_range: float, lon_range: float) -> float:
    """
    Calculate adaptive step size for geohash sampling based on polygon size.
    
    Geohash precision 6 covers ~1.2km x 0.6km cells. We need step size small enough
    to ensure we sample multiple points within each geohash cell for reliable coverage.
    
    Returns:
        Step size in degrees
    """
    max_range = max(lat_range, lon_range)
    min_range = min(lat_range, lon_range)
    
    # For very small polygons, use very fine sampling to ensure geohash coverage
    # Geohash precision 6 = ~0.01° latitude, ~0.02° longitude
    if max_range < 0.001:
        return 0.001  # ~111m - very fine for tiny islands
    elif max_range < 0.01:
        return 0.002  # ~222m - fine sampling for small islands
    elif max_range < 0.05:
        return 0.005  # ~555m - good for small countries
    elif max_range < 0.1:
        return 0.008  # ~888m - ensure multiple samples per geohash
    elif max_range < 0.5:
        return 0.015  # ~1.6km - medium countries
    elif max_range < 2.0:
        return 0.025  # ~2.7km - large countries
    else:
        return 0.05  # ~5.5km - very large countries


def calculate_safe_iteration_limits(
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
    step: float
) -> Tuple[int, int, int, float]:
    """
    Calculate safe iteration limits to prevent infinite loops.
    
    These limits are only used as a safety net for truly infinite loops,
    not to reduce coverage. Returns very generous limits.
    
    Returns:
        Tuple of (max_lat_iterations, max_lon_iterations, max_total_iterations, adjusted_step)
    """
    lat_range = max_lat - min_lat
    lon_range = max_lon - min_lon
    
    max_lat_iter = int(lat_range / step) + 10 if step > 0 else 10000  # +10 buffer
    max_lon_iter = int(lon_range / step) + 10 if step > 0 else 10000  # +10 buffer
    max_total = max_lat_iter * max_lon_iter
    
    # Use original step (don't adjust - preserve full coverage)
    adjusted_step = step
    
    # Only apply a truly massive safety cap (10 million iterations) to prevent infinite loops
    # This should never be hit in normal operation
    if max_total > 10000000:
        max_total = 10000000
    
    return max_lat_iter, max_lon_iter, max_total, adjusted_step


def get_polygon_centroid(polygon: List[Tuple[float, float]]) -> Tuple[float, float]:
    """Calculate polygon centroid."""
    if not polygon:
        return 0.0, 0.0
    
    lats = [p[0] for p in polygon]
    lons = [p[1] for p in polygon]
    return sum(lats) / len(lats), sum(lons) / len(lons)


def convert_geojson_coords_to_latlon(coords_list: List) -> List[Tuple[float, float]]:
    """
    Convert GeoJSON coordinates [lon, lat] to internal format [(lat, lon), ...].
    
    Args:
        coords_list: GeoJSON coordinate list (each element is [lon, lat])
    
    Returns:
        List of (lat, lon) tuples
    """
    return [(p[1], p[0]) for p in coords_list]
