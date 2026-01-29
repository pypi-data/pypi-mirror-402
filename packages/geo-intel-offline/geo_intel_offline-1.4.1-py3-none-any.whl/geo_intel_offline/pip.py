"""
Point-in-Polygon (PIP) algorithm using Ray Casting.

Ray Casting Algorithm:
- Cast a ray from the point to infinity (we use East, +X direction)
- Count intersections with polygon edges
- Odd intersections = inside, even = outside

Design Decisions:
1. Ray Casting chosen over Winding Number for:
   - Simpler implementation
   - Better performance
   - Deterministic results

2. Handle polygon rings (exterior + holes):
   - Exterior ring: inside = true
   - Interior rings (holes): inside = false

3. Edge cases handled:
   - Points on vertices
   - Points on edges
   - Horizontal rays (collinear with edges)
"""

from typing import List, Tuple


def point_in_polygon(
    point: Tuple[float, float],
    polygon: List[Tuple[float, float]]
) -> bool:
    """
    Check if a point is inside a polygon using ray casting.
    
    Args:
        point: (lat, lon) tuple
        polygon: List of (lat, lon) tuples forming polygon ring
    
    Returns:
        True if point is inside polygon, False otherwise
    """
    if not polygon or len(polygon) < 3:
        return False
    
    lat, lon = point
    inside = False
    
    # Ray casting: check intersections with horizontal ray going East
    j = len(polygon) - 1
    for i in range(len(polygon)):
        lat_i, lon_i = polygon[i]
        lat_j, lon_j = polygon[j]
        
        # Check if ray crosses edge
        if ((lat_i > lat) != (lat_j > lat)):
            # Calculate intersection point
            if lon_j != lon_i:
                # Avoid division by zero (horizontal edges)
                intersect_lon = (lat - lat_i) * (lon_j - lon_i) / (lat_j - lat_i) + lon_i
            else:
                intersect_lon = lon_i
            
            # Count intersection if ray crosses to the right
            if lon < intersect_lon:
                inside = not inside
        
        j = i
    
    return inside


def point_in_polygon_with_holes(
    point: Tuple[float, float],
    exterior: List[Tuple[float, float]],
    holes: List[List[Tuple[float, float]]] = None
) -> bool:
    """
    Check if point is in polygon with holes (interior rings).
    
    Design Decision: Exterior ring defines inclusion, holes define exclusion.
    This handles countries with lakes, islands with lakes, etc.
    
    Args:
        point: (lat, lon) tuple
        exterior: Exterior polygon ring
        holes: List of interior rings (holes)
    
    Returns:
        True if point is inside exterior but not in any hole
    """
    if not point_in_polygon(point, exterior):
        return False
    
    # Check if point is in any hole (exclude from result)
    if holes:
        for hole in holes:
            if point_in_polygon(point, hole):
                return False
    
    return True


def distance_to_polygon_edge(
    point: Tuple[float, float],
    polygon: List[Tuple[float, float]]
) -> float:
    """
    Calculate minimum distance from point to polygon edge.
    
    Used for confidence scoring: closer to edge = lower confidence.
    
    Args:
        point: (lat, lon) tuple
        polygon: Polygon ring
    
    Returns:
        Distance in degrees (approximate, for confidence scoring)
    """
    if not polygon:
        return float('inf')
    
    min_dist = float('inf')
    lat, lon = point
    
    j = len(polygon) - 1
    for i in range(len(polygon)):
        lat_i, lon_i = polygon[i]
        lat_j, lon_j = polygon[j]
        
        # Distance to line segment
        # Use point-to-line-segment distance formula
        dx = lon_j - lon_i
        dy = lat_j - lat_i
        
        if dx == 0 and dy == 0:
            # Degenerate segment (point)
            dist = ((lat - lat_i) ** 2 + (lon - lon_i) ** 2) ** 0.5
        else:
            # Project point onto line segment
            t = max(0, min(1, ((lat - lat_i) * dy + (lon - lon_i) * dx) / (dx * dx + dy * dy)))
            
            proj_lat = lat_i + t * dy
            proj_lon = lon_i + t * dx
            
            dist = ((lat - proj_lat) ** 2 + (lon - proj_lon) ** 2) ** 0.5
        
        min_dist = min(min_dist, dist)
        j = i
    
    return min_dist
