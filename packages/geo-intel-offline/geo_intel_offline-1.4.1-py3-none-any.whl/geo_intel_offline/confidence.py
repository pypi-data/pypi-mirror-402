"""
Confidence scoring for geo-intelligence results.

Confidence is based on:
1. Distance to polygon edge (closer = lower confidence)
2. Geohash ambiguity (multiple candidates = lower confidence)
3. Border proximity threshold

Design Decision: Use distance-based scoring with thresholds:
- > 0.1° from edge: 0.98-1.0 confidence (high)
- 0.01°-0.1° from edge: 0.85-0.98 confidence (medium)
- < 0.01° from edge: 0.70-0.85 confidence (low)
- Multiple candidates: Reduce by 0.1-0.2

This gives users actionable confidence metrics without over-promising accuracy.
"""

from typing import List, Tuple
from .pip import distance_to_polygon_edge


def calculate_confidence(
    point: Tuple[float, float],
    polygon: List[Tuple[float, float]],
    holes: List[List[Tuple[float, float]]] = None,
    candidate_count: int = 1
) -> float:
    """
    Calculate confidence score for geo-intelligence result.
    
    Args:
        point: (lat, lon) tuple
        polygon: Exterior polygon ring
        holes: Interior rings (holes) if any
        candidate_count: Number of candidate countries found (ambiguity penalty)
    
    Returns:
        Confidence score between 0.0 and 1.0
    """
    # Calculate distance to nearest edge (exterior or holes)
    dist_exterior = distance_to_polygon_edge(point, polygon)
    
    min_dist = dist_exterior
    
    if holes:
        for hole in holes:
            dist_hole = distance_to_polygon_edge(point, hole)
            min_dist = min(min_dist, dist_hole)
    
    # Convert distance (degrees) to confidence
    # 0.1° ≈ 11km at equator, good threshold for "far from border"
    if min_dist >= 0.1:
        base_confidence = 0.98
    elif min_dist >= 0.05:
        # Linear interpolation between 0.05° and 0.1°
        base_confidence = 0.88 + (min_dist - 0.05) / 0.05 * 0.10
    elif min_dist >= 0.01:
        # Linear interpolation between 0.01° and 0.05°
        base_confidence = 0.75 + (min_dist - 0.01) / 0.04 * 0.13
    else:
        # Very close to border
        base_confidence = 0.70 + min_dist / 0.01 * 0.05
    
    # Apply ambiguity penalty
    if candidate_count > 1:
        # Multiple candidates reduce confidence
        penalty = min(0.2, (candidate_count - 1) * 0.05)
        base_confidence -= penalty
    
    # Clamp to valid range
    return max(0.5, min(1.0, base_confidence))


def get_confidence_label(confidence: float) -> str:
    """
    Get human-readable confidence label.
    
    Args:
        confidence: Confidence score (0.0-1.0)
    
    Returns:
        Label: "high", "medium", or "low"
    """
    if confidence >= 0.90:
        return "high"
    elif confidence >= 0.75:
        return "medium"
    else:
        return "low"
