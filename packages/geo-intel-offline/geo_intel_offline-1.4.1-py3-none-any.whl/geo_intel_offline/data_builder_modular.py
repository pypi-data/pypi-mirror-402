"""
Modular data builder - generates country-wise data files.

Design:
- Each country in its own file
- Organized by continent directories
- Master index file for lookup
- Supports selective country/continent building
- Uses PIP validation for accurate geohash indexing
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from .geohash import encode
from .data_builder import simplify_polygon  # Uses improved simplify_polygon with validation
from .pip import point_in_polygon_with_holes
from .polygon_utils import (
    calculate_bounding_box,
    calculate_adaptive_step_size,
    calculate_safe_iteration_limits,
    get_polygon_centroid,
    convert_geojson_coords_to_latlon
)


# Continent mapping (normalize various continent name formats)
CONTINENT_MAPPING = {
    "Africa": "africa",
    "africa": "africa",
    "AFRICA": "africa",
    
    "Asia": "asia",
    "asia": "asia",
    "ASIA": "asia",
    
    "Europe": "europe",
    "europe": "europe",
    "EUROPE": "europe",
    
    "North America": "north_america",
    "north america": "north_america",
    "NorthAmerica": "north_america",
    "north_america": "north_america",
    
    "South America": "south_america",
    "south america": "south_america",
    "SouthAmerica": "south_america",
    "south_america": "south_america",
    
    "Oceania": "oceania",
    "oceania": "oceania",
    "OCEANIA": "oceania",
    "Australia": "oceania",
    
    "Antarctica": "antarctica",
    "antarctica": "antarctica",
    "ANTARCTICA": "antarctica",
}


def normalize_continent(continent: str) -> str:
    """Normalize continent name to directory format."""
    return CONTINENT_MAPPING.get(continent, continent.lower().replace(" ", "_"))


def build_country_geohash_index(
    polygon_exterior: List[Tuple[float, float]],
    polygon_holes: List[List[Tuple[float, float]]],
    country_id: int,
    geohash_precision: int = 6,
    validate_with_pip: bool = True
) -> Dict[str, List[int]]:
    """
    Build geohash index for a single country with PIP validation.
    
    Args:
        polygon_exterior: Exterior polygon coordinates
        polygon_holes: Interior rings (holes) if any
        country_id: Country ID
        geohash_precision: Geohash precision level
        validate_with_pip: If True, validate points are in polygon before indexing
    
    Returns:
        Dict mapping geohash strings to [country_id]
    """
    if not polygon_exterior:
        return {}
    
    # Calculate bounding box using shared utility
    min_lat, max_lat, min_lon, max_lon = calculate_bounding_box(polygon_exterior)
    
    lat_range = max_lat - min_lat
    lon_range = max_lon - min_lon
    
    # Calculate adaptive step size using shared utility
    step = calculate_adaptive_step_size(lat_range, lon_range)
    
    # For very small polygons, ensure we sample multiple points
    if lat_range < 0.001 or lon_range < 0.001:
        # Sample multiple points for tiny polygons
        sample_points = []
        sample_points.append(get_polygon_centroid(polygon_exterior))
        sample_points.append((min_lat, min_lon))
        sample_points.append((min_lat, max_lon))
        sample_points.append((max_lat, min_lon))
        sample_points.append((max_lat, max_lon))
        
        index = {}
        for point in sample_points:
            if validate_with_pip:
                if not point_in_polygon_with_holes(point, polygon_exterior, polygon_holes):
                    continue
            geohash = encode(point[0], point[1], geohash_precision)
            if geohash not in index:
                index[geohash] = []
            if country_id not in index[geohash]:
                index[geohash].append(country_id)
        return index
    
    # Sample points from bounding boxes with validation
    index = {}
    geohashes_added = set()
    lat = min_lat
    
    while lat <= max_lat:
        lon = min_lon
        while lon <= max_lon:
            point = (lat, lon)
            
            # Validate point is in polygon if enabled
            if validate_with_pip:
                if not point_in_polygon_with_holes(point, polygon_exterior, polygon_holes):
                    lon += step
                    continue
            
            # Add to index
            geohash = encode(lat, lon, geohash_precision)
            geohash_key = (geohash, country_id)
            
            if geohash_key not in geohashes_added:
                if geohash not in index:
                    index[geohash] = []
                if country_id not in index[geohash]:
                    index[geohash].append(country_id)
                geohashes_added.add(geohash_key)
            
            lon += step
        lat += step
    
    # Ensure at least one geohash for very small countries
    if len(geohashes_added) == 0 and validate_with_pip:
        centroid_lat, centroid_lon = get_polygon_centroid(polygon_exterior)
        centroid_point = (centroid_lat, centroid_lon)
        
        if point_in_polygon_with_holes(centroid_point, polygon_exterior, polygon_holes):
            geohash = encode(centroid_lat, centroid_lon, geohash_precision)
            if geohash not in index:
                index[geohash] = []
            if country_id not in index[geohash]:
                index[geohash].append(country_id)
    
    return index


def process_country(
    feature: Dict,
    country_id: int,
    geohash_precision: int = 6,
    polygon_tolerance: float = 0.005
) -> Optional[Dict]:
    """
    Process a single country feature into modular format.
    
    Returns:
        Dict with country data or None if invalid
    """
    geometry = feature.get('geometry', {})
    properties = feature.get('properties', {})
    
    if geometry.get('type') not in ('Polygon', 'MultiPolygon'):
        return None
    
    coords = geometry.get('coordinates', [])
    
    # Extract metadata
    metadata = {
        'name': properties.get('NAME', properties.get('name', f'Country {country_id}')),
        'iso2': properties.get('ISO_A2', properties.get('iso_a2', '')),
        'iso3': properties.get('ISO_A3', properties.get('iso_a3', '')),
        'continent': properties.get('CONTINENT', properties.get('continent', '')),
        'timezone': properties.get('TIMEZONE', properties.get('timezone', ''))
    }
    
    # Process polygon
    if geometry['type'] == 'Polygon':
        exterior_coords = coords[0] if coords else []
        hole_coords = coords[1:] if len(coords) > 1 else []
        
        # Convert GeoJSON [lon, lat] to [lat, lon]
        exterior = convert_geojson_coords_to_latlon(exterior_coords)
        holes = [convert_geojson_coords_to_latlon(hole) for hole in hole_coords] if hole_coords else []
        
        # Simplify with tighter tolerance for better accuracy
        exterior_simplified = simplify_polygon(exterior, tolerance=polygon_tolerance)
        
        # Ensure simplified polygon is still valid
        if len(exterior_simplified) < 3 and len(exterior) >= 3:
            exterior_simplified = exterior  # Use original if simplification made it invalid
        
        holes_simplified = []
        for hole in holes:
            if len(hole) >= 3:
                hole_simpl = simplify_polygon(hole, tolerance=polygon_tolerance)
                if len(hole_simpl) >= 3:
                    holes_simplified.append(hole_simpl)
                elif len(hole) >= 3:
                    holes_simplified.append(hole)  # Use original
        
        # Build geohash index for single polygon
        geohashes = build_country_geohash_index(
            exterior_simplified,
            holes_simplified if holes_simplified else [],
            country_id,
            geohash_precision,
            validate_with_pip=True
        )
        
        polygon_data = {
            'exterior': exterior_simplified,
            'holes': holes_simplified if holes_simplified else []
        }
    else:  # MultiPolygon - process ALL polygons
        all_exteriors = []
        all_holes = []
        all_geohashes = {}
        
        for poly_part in coords:
            if not poly_part or not poly_part[0]:
                continue
            
            exterior_coords = poly_part[0]
            hole_coords = poly_part[1:] if len(poly_part) > 1 else []
            
            exterior = convert_geojson_coords_to_latlon(exterior_coords)
            holes = [convert_geojson_coords_to_latlon(hole) for hole in hole_coords] if hole_coords else []
            
            exterior_simplified = simplify_polygon(exterior, tolerance=polygon_tolerance)
            
            if len(exterior_simplified) >= 3:  # Valid polygon
                all_exteriors.append(exterior_simplified)
            
            if holes:
                holes_simplified = [simplify_polygon(hole, tolerance=polygon_tolerance) for hole in holes]
                all_holes.extend(holes_simplified)
            
            # Build geohash index for each polygon part
            part_geohashes = build_country_geohash_index(
                exterior_simplified,
                holes_simplified if holes else [],
                country_id,
                geohash_precision,
                validate_with_pip=True
            )
            # Merge geohashes
            for gh, ids in part_geohashes.items():
                if gh not in all_geohashes:
                    all_geohashes[gh] = []
                all_geohashes[gh].extend(ids)
        
        if not all_exteriors:
            return None
        
        geohashes = all_geohashes
        
        # Store MultiPolygon structure
        polygon_data = {
            'exterior': all_exteriors[0],  # Primary exterior
            'holes': all_holes if all_holes else [],
            'multi': True,
            'exteriors': all_exteriors  # All exteriors for complete coverage
        }
    
    return {
        'country_id': country_id,
        'metadata': metadata,
        'geohashes': geohashes,
        'polygon': polygon_data
    }


def build_modular_data(
    geojson_path: Path,
    output_dir: Path,
    countries: Optional[List[str]] = None,
    continents: Optional[List[str]] = None,
    exclude_countries: Optional[List[str]] = None,
    geohash_precision: int = 6,
    polygon_tolerance: float = 0.005
) -> Dict:
    """
    Build modular country-wise data files.
    
    Args:
        geojson_path: Path to source GeoJSON file
        output_dir: Output directory for data files
        countries: List of ISO2 codes to include (None = all)
        continents: List of continent names to include (None = all)
        exclude_countries: List of ISO2 codes to exclude
        geohash_precision: Geohash precision level
        polygon_tolerance: Polygon simplification tolerance (0.005 = better accuracy)
    
    Returns:
        Dict with build statistics
    """
    # Load GeoJSON
    with open(geojson_path, 'r', encoding='utf-8') as f:
        geojson = json.load(f)
    
    features = geojson.get('features', [])
    
    # Normalize filters
    countries_set = set(c.upper() for c in (countries or []))
    exclude_set = set(c.upper() for c in (exclude_countries or []))
    continents_normalized = [normalize_continent(c) for c in (continents or [])]
    
    # Create output structure
    output_dir.mkdir(parents=True, exist_ok=True)
    continents_dir = output_dir / "continents"
    continents_dir.mkdir(exist_ok=True)
    
    # Process countries
    master_index = {
        'version': '1.0.0',
        'countries': {},
        'continents': {}
    }
    
    continent_countries = {}  # continent -> [iso2 codes]
    
    processed = 0
    skipped = 0
    
    print(f"Processing {len(features)} countries with PIP validation...")
    
    for idx, feature in enumerate(features):
        country_id = idx + 1
        properties = feature.get('properties', {})
        
        iso2 = properties.get('ISO_A2', properties.get('iso_a2', '')).upper()
        continent_raw = properties.get('CONTINENT', properties.get('continent', ''))
        continent = normalize_continent(continent_raw) if continent_raw else 'unknown'
        
        # Apply filters
        if countries_set and iso2 not in countries_set:
            skipped += 1
            continue
        
        if exclude_set and iso2 in exclude_set:
            skipped += 1
            continue
        
        if continents_normalized and continent not in continents_normalized:
            skipped += 1
            continue
        
        # Process country
        country_data = process_country(feature, country_id, geohash_precision, polygon_tolerance)
        if not country_data:
            skipped += 1
            continue
        
        # Create continent directory
        continent_dir = continents_dir / continent
        continent_dir.mkdir(exist_ok=True)
        
        # Save country file
        country_file = continent_dir / f"{iso2}.json"
        with open(country_file, 'w', encoding='utf-8') as f:
            json.dump(country_data, f, separators=(',', ':'))
        
        # Update master index
        relative_path = f"continents/{continent}/{iso2}.json"
        master_index['countries'][iso2] = {
            'id': country_id,
            'name': country_data['metadata']['name'],
            'iso2': iso2,
            'iso3': country_data['metadata'].get('iso3', ''),
            'continent': continent_raw,
            'file': relative_path,
            'size_bytes': country_file.stat().st_size
        }
        
        # Track continent membership
        if continent not in continent_countries:
            continent_countries[continent] = []
        continent_countries[continent].append(iso2)
        
        processed += 1
        
        # Progress indicator
        if processed % 20 == 0:
            print(f"  Processed {processed} countries...")
    
    # Update continent index
    master_index['continents'] = continent_countries
    
    # Save master index
    index_file = output_dir / "index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(master_index, f, indent=2, ensure_ascii=False)
    
    return {
        'processed': processed,
        'skipped': skipped,
        'countries': list(master_index['countries'].keys()),
        'continents': list(continent_countries.keys())
    }


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Build modular country-wise data files with high accuracy'
    )
    parser.add_argument('source', type=Path, help='Source GeoJSON file')
    parser.add_argument('output', type=Path, help='Output directory')
    parser.add_argument('--countries', help='Comma-separated ISO2 codes (e.g., US,CA,MX)')
    parser.add_argument('--continents', help='Comma-separated continent names')
    parser.add_argument('--exclude', help='Comma-separated ISO2 codes to exclude')
    parser.add_argument('--precision', type=int, default=6, help='Geohash precision (default: 6)')
    parser.add_argument('--tolerance', type=float, default=0.005, help='Polygon tolerance (default: 0.005 for high accuracy)')
    
    args = parser.parse_args()
    
    # Parse filters
    countries = [c.strip().upper() for c in args.countries.split(',')] if args.countries else None
    continents = [c.strip() for c in args.continents.split(',')] if args.continents else None
    exclude = [c.strip().upper() for c in args.exclude.split(',')] if args.exclude else None
    
    print(f"Building modular data from {args.source}...")
    print(f"  Polygon tolerance: {args.tolerance}° (smaller = more accurate)")
    print(f"  Geohash precision: {args.precision}")
    print(f"  PIP validation: Enabled")
    if countries:
        print(f"  Countries: {', '.join(countries)}")
    if continents:
        print(f"  Continents: {', '.join(continents)}")
    if exclude:
        print(f"  Exclude: {', '.join(exclude)}")
    print()
    
    stats = build_modular_data(
        args.source,
        args.output,
        countries=countries,
        continents=continents,
        exclude_countries=exclude,
        geohash_precision=args.precision,
        polygon_tolerance=args.tolerance
    )
    
    print(f"\n✓ Processed: {stats['processed']} countries")
    print(f"  Skipped: {stats['skipped']} countries")
    print(f"  Continents: {', '.join(stats['continents'])}")
    print(f"\nData saved to: {args.output}")
    print(f"Master index: {args.output / 'index.json'}")


if __name__ == '__main__':
    main()
