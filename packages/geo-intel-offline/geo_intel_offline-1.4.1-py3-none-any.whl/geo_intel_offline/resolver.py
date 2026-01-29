"""
Resolver orchestration - coordinates the resolution pipeline.

Resolution Pipeline:
1. Encode lat/lon to geohash
2. Query geohash index for candidate countries
3. For each candidate:
   a. Load polygon
   b. Test point-in-polygon
   c. If match, calculate confidence
4. Return best match or handle ambiguity

Edge Cases Handled:
- Points in oceans (no country match)
- Border points (multiple candidates)
- Geohash boundary cases (check neighbors)
- Countries with holes (islands, lakes)
"""

from typing import List, Tuple, Optional, Dict
from .geohash import encode, get_neighbors
from .pip import point_in_polygon_with_holes
from .confidence import calculate_confidence
from .data_loader import get_loader
from .modular_data_loader import ModularDataLoader


class ResolutionResult:
    """Result of a geo-intelligence resolution."""
    
    def __init__(
        self,
        country_id: Optional[int] = None,
        country_name: Optional[str] = None,
        iso2: Optional[str] = None,
        iso3: Optional[str] = None,
        continent: Optional[str] = None,
        timezone: Optional[str] = None,
        confidence: float = 0.0
    ):
        self.country_id = country_id
        self.country_name = country_name
        self.iso2 = iso2
        self.iso3 = iso3
        self.continent = continent
        self.timezone = timezone
        self.confidence = confidence
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "country": self.country_name,
            "iso2": self.iso2,
            "iso3": self.iso3,
            "continent": self.continent,
            "timezone": self.timezone,
            "confidence": self.confidence
        }
    
    def is_valid(self) -> bool:
        """Check if result is valid (has country)."""
        return self.country_id is not None


def resolve(
    lat: float,
    lon: float,
    data_dir: Optional[str] = None,
    countries: Optional[List[str]] = None,
    continents: Optional[List[str]] = None,
    exclude_countries: Optional[List[str]] = None,
    loader: Optional[ModularDataLoader] = None
) -> ResolutionResult:
    """
    Resolve latitude/longitude to geo-intelligence.
    
    Main resolution function that orchestrates the entire pipeline.
    
    Args:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)
        data_dir: Optional custom data directory
        countries: Optional list of ISO2 codes to load (modular format)
        continents: Optional list of continent names to load (modular format)
        exclude_countries: Optional list of ISO2 codes to exclude (modular format)
        loader: Optional pre-configured loader instance
    
    Returns:
        ResolutionResult with country information and confidence
    """
    if loader is None:
        # Use modular loader if filters specified, otherwise use default
        if countries or continents or exclude_countries:
            loader = ModularDataLoader(
                data_dir=data_dir,
                countries=countries,
                continents=continents,
                exclude_countries=exclude_countries
            )
        else:
            loader = get_loader(data_dir)
    point = (lat, lon)
    
    # Step 1: Encode to geohash
    geohash = encode(lat, lon)
    
    # Step 2: Get candidate countries
    candidates = loader.get_candidate_countries(geohash)
    
    # Step 3: If no candidates from primary geohash, try neighbors
    # This handles edge cases where point is on geohash boundaries
    if not candidates:
        neighbors = get_neighbors(geohash)
        for neighbor_hash in neighbors:
            neighbor_candidates = loader.get_candidate_countries(neighbor_hash)
            candidates.extend(neighbor_candidates)
        candidates = list(set(candidates))  # Deduplicate
    
    # Step 3b: If still no candidates, try extended neighbors (9x9 grid around point)
    # This improves accuracy for small countries/islands that may have sparse geohash coverage
    if not candidates:
        # Get all neighbors of neighbors (extended search)
        extended_neighbors = set()
        for neighbor_hash in neighbors:
            extended_neighbors.add(neighbor_hash)
            for extended_neighbor in get_neighbors(neighbor_hash):
                extended_neighbors.add(extended_neighbor)
        
        for extended_hash in extended_neighbors:
            if extended_hash != geohash:  # Skip primary (already checked)
                extended_candidates = loader.get_candidate_countries(extended_hash)
                candidates.extend(extended_candidates)
        candidates = list(set(candidates))  # Deduplicate
    
    # Step 3c: Final fallback - if still no candidates, try checking all loaded countries
    # This catches edge cases where geohash indexing missed coverage for small countries
    if not candidates:
        # Try to get all country IDs from the loader
        try:
            # For monolithic loader, we can iterate through metadata
            if hasattr(loader, 'metadata') and loader.metadata:
                candidates = list(loader.metadata.keys())
            # For modular loader, check if we can get all loaded countries
            elif hasattr(loader, '_loaded_countries'):
                candidates = list(loader._loaded_countries.keys())
        except:
            pass  # Fallback failed, continue with empty candidates
    
    if not candidates:
        # No country found (likely ocean or unsupported area)
        return ResolutionResult()
    
    # Step 4: Test point-in-polygon for each candidate
    matches = []
    
    for country_id in candidates:
        polygon_data = loader.get_polygon(country_id)
        if not polygon_data:
            continue
        
        # Handle MultiPolygon - check all exteriors
        is_multi = polygon_data.get('multi', False)
        exteriors_data = polygon_data.get('exteriors', [])
        
        if is_multi and exteriors_data:
            # MultiPolygon: check all exteriors
            for exterior in exteriors_data:
                exterior_tuples = [(p[0], p[1]) for p in exterior]
                holes = polygon_data.get('holes', [])
                holes_tuples = [[(p[0], p[1]) for p in hole] for hole in holes] if holes else None
                
                # Test point-in-polygon for this exterior
                if point_in_polygon_with_holes(point, exterior_tuples, holes_tuples):
                    metadata = loader.get_metadata(country_id)
                    if metadata:
                        # Calculate confidence
                        confidence = calculate_confidence(
                            point,
                            exterior_tuples,
                            holes_tuples,
                            candidate_count=len(candidates)
                        )
                        
                        matches.append({
                            'country_id': country_id,
                            'metadata': metadata,
                            'confidence': confidence,
                            'polygon': (exterior_tuples, holes_tuples)
                        })
                        break  # Found match, no need to check other exteriors
        else:
            # Single polygon
            exterior = polygon_data.get('exterior', [])
            holes = polygon_data.get('holes', [])
            
            # Convert coordinate lists to tuples
            exterior_tuples = [(p[0], p[1]) for p in exterior]
            holes_tuples = [[(p[0], p[1]) for p in hole] for hole in holes] if holes else None
            
            # Test point-in-polygon
            if point_in_polygon_with_holes(point, exterior_tuples, holes_tuples):
                metadata = loader.get_metadata(country_id)
                if metadata:
                    # Calculate confidence
                    confidence = calculate_confidence(
                        point,
                        exterior_tuples,
                        holes_tuples,
                        candidate_count=len(candidates)
                    )
                    
                    matches.append({
                        'country_id': country_id,
                        'metadata': metadata,
                        'confidence': confidence,
                        'polygon': (exterior_tuples, holes_tuples)
                    })
    
    # Step 5: If no matches from geohash candidates, try broader search
    # This handles cases where geohash index doesn't have complete coverage
    if not matches:
        # Fallback: Check all countries (expensive, but ensures accuracy)
        # This is a last resort when geohash indexing missed the country
        metadata_dict = loader.metadata
        polygons_dict = loader.polygons
        
        for country_id, meta in metadata_dict.items():
            # Skip if already checked as candidate
            if country_id in candidates:
                continue
            
            polygon_data = polygons_dict.get(country_id)
            if not polygon_data:
                continue
            
            # Handle MultiPolygon
            is_multi = polygon_data.get('multi', False)
            exteriors_data = polygon_data.get('exteriors', [])
            
            if is_multi and exteriors_data:
                for exterior in exteriors_data:
                    exterior_tuples = [(p[0], p[1]) for p in exterior]
                    holes = polygon_data.get('holes', [])
                    holes_tuples = [[(p[0], p[1]) for p in hole] for hole in holes] if holes else None
                    
                    if point_in_polygon_with_holes(point, exterior_tuples, holes_tuples):
                        confidence = calculate_confidence(
                            point,
                            exterior_tuples,
                            holes_tuples,
                            candidate_count=1  # Single match in fallback
                        )
                        
                        matches.append({
                            'country_id': country_id,
                            'metadata': meta,
                            'confidence': confidence * 0.95,  # Slightly lower confidence for fallback match
                            'polygon': (exterior_tuples, holes_tuples)
                        })
                        break
            else:
                exterior = polygon_data.get('exterior', [])
                holes = polygon_data.get('holes', [])
                
                if not exterior:
                    continue
                
                exterior_tuples = [(p[0], p[1]) for p in exterior]
                holes_tuples = [[(p[0], p[1]) for p in hole] for hole in holes] if holes else None
                
                if point_in_polygon_with_holes(point, exterior_tuples, holes_tuples):
                    confidence = calculate_confidence(
                        point,
                        exterior_tuples,
                        holes_tuples,
                        candidate_count=1
                    )
                    
                    matches.append({
                        'country_id': country_id,
                        'metadata': meta,
                        'confidence': confidence * 0.95,
                        'polygon': (exterior_tuples, holes_tuples)
                    })
    
    # Step 6: Return best match (highest confidence)
    if not matches:
        # No valid PIP matches found - return None
        return ResolutionResult()
    
    # Sort by confidence (descending)
    matches.sort(key=lambda x: x['confidence'], reverse=True)
    best_match = matches[0]
    
    metadata = best_match['metadata']
    return ResolutionResult(
        country_id=best_match['country_id'],
        country_name=metadata['name'],
        iso2=metadata.get('iso2'),
        iso3=metadata.get('iso3'),
        continent=metadata.get('continent'),
        timezone=metadata.get('timezone'),
        confidence=best_match['confidence']
    )


