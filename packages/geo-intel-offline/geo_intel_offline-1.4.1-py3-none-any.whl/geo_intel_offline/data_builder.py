"""
Data Builder - Process GeoJSON and generate optimized data files

Design Decisions:
1. Accept GeoJSON input (standard format, widely available)
2. Simplify polygons using Douglas-Peucker algorithm (reduces memory)
3. Build geohash index by sampling polygon coverage
4. Extract metadata from GeoJSON properties

Note: In production, you would download source data from Natural Earth
or similar authoritative sources. This script provides the processing pipeline.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from .geohash import encode
from .polygon_utils import (
    calculate_bounding_box,
    calculate_adaptive_step_size,
    calculate_safe_iteration_limits,
    get_polygon_centroid,
    convert_geojson_coords_to_latlon
)


def simplify_polygon(
    polygon: List[Tuple[float, float]],
    tolerance: float = 0.01
) -> List[Tuple[float, float]]:
    """
    Simplify polygon using Douglas-Peucker algorithm.
    
    For very small polygons, skip simplification to preserve validity.
    
    Args:
        polygon: List of (lat, lon) tuples
        tolerance: Simplification tolerance in degrees
    
    Returns:
        Simplified polygon (guaranteed to have at least 3 vertices)
    """
    if len(polygon) <= 2:
        return polygon
    
    # For very small polygons, skip simplification to preserve validity
    if len(polygon) <= 10:
        return polygon if len(polygon) >= 3 else []
    
    # Douglas-Peucker algorithm
    def douglas_peucker(points: List[Tuple[float, float]], tol: float) -> List[Tuple[float, float]]:
        if len(points) <= 3:
            return points if len(points) >= 3 else []
        
        # Find point with maximum distance
        max_dist = 0
        max_idx = 0
        end_idx = len(points) - 1
        
        for i in range(1, end_idx):
            dist = _point_to_line_distance(points[i], points[0], points[end_idx])
            if dist > max_dist:
                max_dist = dist
                max_idx = i
        
        # If max distance is greater than tolerance, recursively simplify
        if max_dist > tol:
            left = douglas_peucker(points[:max_idx + 1], tol)
            right = douglas_peucker(points[max_idx:], tol)
            
            if left and right:
                combined = left[:-1] + right
                if len(combined) < 3 and len(points) >= 3:
                    return points
                return combined
            elif left:
                return left if len(left) >= 3 else points
            elif right:
                return right if len(right) >= 3 else points
            return points
        else:
            if len(points) >= 3:
                mid_idx = len(points) // 2
                return [points[0], points[mid_idx], points[end_idx]]
            return points
    
    result = douglas_peucker(polygon, tolerance)
    
    # Final validation
    if len(result) < 3:
        return polygon if len(polygon) >= 3 else result
    
    return result


def _point_to_line_distance(
    point: Tuple[float, float],
    line_start: Tuple[float, float],
    line_end: Tuple[float, float]
) -> float:
    """Calculate perpendicular distance from point to line segment."""
    px, py = point
    sx, sy = line_start
    ex, ey = line_end
    
    dx = ex - sx
    dy = ey - sy
    
    if dx == 0 and dy == 0:
        # Degenerate line (point)
        return ((px - sx) ** 2 + (py - sy) ** 2) ** 0.5
    
    # Calculate t parameter
    t = ((px - sx) * dx + (py - sy) * dy) / (dx * dx + dy * dy)
    
    # Clamp to line segment
    t = max(0, min(1, t))
    
    # Projection point
    proj_x = sx + t * dx
    proj_y = sy + t * dy
    
    # Distance
    return ((px - proj_x) ** 2 + (py - proj_y) ** 2) ** 0.5


def build_geohash_index_from_polygons(
    polygons: Dict[int, Dict],
    geohash_precision: int = 6,
    validate_with_pip: bool = True
) -> Dict[str, List[int]]:
    """
    Build geohash index from processed polygons.
    
    Optimized version that uses already-processed polygon data.
    
    Args:
        polygons: Dict mapping country_id to polygon data
        geohash_precision: Geohash precision level
        validate_with_pip: If True, validate points are in polygon
    
    Returns:
        Dict mapping geohash strings to lists of country IDs
    """
    from .pip import point_in_polygon_with_holes
    
    index: Dict[str, List[int]] = {}
    total_countries = len(polygons)
    
    print(f"Building geohash index for {total_countries} countries...")
    
    for idx, (country_id, polygon_data) in enumerate(polygons.items(), 1):
        if (idx) % max(1, total_countries // 20) == 0 or idx == total_countries:
            progress = (idx / total_countries) * 100
            print(f"  Progress: {progress:.1f}% ({idx}/{total_countries})", end='\r')
        
        is_multi = polygon_data.get('multi', False)
        exteriors_data = polygon_data.get('exteriors', [])
        exterior = polygon_data.get('exterior', [])
        holes = polygon_data.get('holes', [])
        
        # Handle MultiPolygon
        if is_multi and exteriors_data:
            exteriors_to_process = exteriors_data
        else:
            exteriors_to_process = [exterior] if exterior else []
        
        geohashes_added = set()
        
        for exterior_coords in exteriors_to_process:
            if not exterior_coords or len(exterior_coords) < 3:
                continue
            
            # Calculate bounding box using shared utility
            min_lat, max_lat, min_lon, max_lon = calculate_bounding_box(exterior_coords)
            
            lat_range = max_lat - min_lat
            lon_range = max_lon - min_lon
            
            # Handle extremely small polygons - sample multiple points, not just centroid
            if lat_range < 0.001 or lon_range < 0.001:
                # For tiny polygons, sample multiple points (centroid + corners + midpoints)
                # to ensure better geohash coverage
                sample_points = []
                sample_points.append(get_polygon_centroid(exterior_coords))
                # Add bounding box corners and midpoints
                sample_points.append((min_lat, min_lon))
                sample_points.append((min_lat, max_lon))
                sample_points.append((max_lat, min_lon))
                sample_points.append((max_lat, max_lon))
                sample_points.append((min_lat, (min_lon + max_lon) / 2))
                sample_points.append((max_lat, (min_lon + max_lon) / 2))
                sample_points.append(((min_lat + max_lat) / 2, min_lon))
                sample_points.append(((min_lat + max_lat) / 2, max_lon))
                
                if validate_with_pip:
                    for point in sample_points:
                        if point_in_polygon_with_holes(point, exterior_coords, holes):
                            geohash = encode(point[0], point[1], geohash_precision)
                            if geohash not in index:
                                index[geohash] = []
                            if country_id not in index[geohash]:
                                index[geohash].append(country_id)
                continue
            
            # Calculate adaptive step size using shared utility
            step = calculate_adaptive_step_size(lat_range, lon_range)
            
            # Calculate safe iteration limits (may adjust step for very large countries)
            max_lat_iterations, max_lon_iterations, max_total_iterations, step = calculate_safe_iteration_limits(
                min_lat, max_lat, min_lon, max_lon, step
            )
            
            # Convert to tuples for PIP (already in lat,lon format)
            exterior_tuples = [(p[0], p[1]) for p in exterior_coords]
            holes_tuples = [[(p[0], p[1]) for p in hole] for hole in holes] if holes else None
            
            # Sample points
            lat = min_lat
            iterations = 0
            
            while lat <= max_lat and iterations < max_lat_iterations * 2:
                lon = min_lon
                lon_iterations = 0
                
                while lon <= max_lon and lon_iterations < max_lon_iterations * 2:
                    point = (lat, lon)
                    iterations += 1
                    lon_iterations += 1
                    
                    # Safety: prevent infinite loops
                    if iterations > max_total_iterations:
                        break
                    
                    # Validate point is in polygon
                    if validate_with_pip:
                        if not point_in_polygon_with_holes(point, exterior_tuples, holes_tuples):
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
                
                if iterations > max_total_iterations:
                    break
                lat += step
        
        # Fallback: ensure at least one geohash for very small countries
        if len(geohashes_added) == 0 and exterior:
            exterior_tuples = [(p[0], p[1]) for p in exterior]
            centroid_lat, centroid_lon = get_polygon_centroid(exterior)
            
            if not validate_with_pip or point_in_polygon_with_holes(
                (centroid_lat, centroid_lon), exterior_tuples, 
                [[(p[0], p[1]) for p in hole] for hole in holes] if holes else None
            ):
                geohash = encode(centroid_lat, centroid_lon, geohash_precision)
                if geohash not in index:
                    index[geohash] = []
                if country_id not in index[geohash]:
                    index[geohash].append(country_id)
    
    print()  # New line after progress
    print(f"✓ Completed: {total_countries} countries indexed")
    return index


def process_geojson(filepath: Path, polygon_tolerance: float = 0.005, geohash_precision: int = 6) -> Tuple[Dict[str, List[int]], Dict, Dict]:
    """
    Process GeoJSON file and generate data files.
    
    Returns:
        Tuple of (geohash_index, polygons_dict, metadata_dict)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        geojson = json.load(f)
    
    features = geojson.get('features', [])
    
    print(f"Loading {len(features)} countries from GeoJSON...")
    
    polygons: Dict[int, Dict] = {}
    metadata: Dict[int, Dict] = {}
    skipped_countries = []
    total_features = len(features)
    
    for idx, feature in enumerate(features):
        country_id = idx + 1
        progress_pct = ((idx + 1) / total_features) * 100
        
        if (idx + 1) % max(1, total_features // 20) == 0 or (idx + 1) == total_features:
            print(f"  Processing polygons: {progress_pct:.1f}% ({idx + 1}/{total_features})", end='\r')
        
        geometry = feature.get('geometry', {})
        properties = feature.get('properties', {})
        country_name = properties.get('NAME', properties.get('name', f'Country {country_id}'))
        
        if geometry.get('type') not in ('Polygon', 'MultiPolygon'):
            skipped_countries.append(f"{country_name} (type: {geometry.get('type', 'unknown')})")
            continue
        
        coords = geometry.get('coordinates', [])
        
        # Process coordinates
        if geometry['type'] == 'Polygon':
            exterior_coords = coords[0] if coords else []
            hole_coords = coords[1:] if len(coords) > 1 else []
            
            if not exterior_coords or len(exterior_coords) < 3:
                skipped_countries.append(f"{country_name} (invalid polygon: {len(exterior_coords) if exterior_coords else 0} vertices)")
                continue
            
            exterior = [(p[1], p[0]) for p in exterior_coords]
            holes = [[(p[1], p[0]) for p in hole] for hole in hole_coords] if hole_coords else []
            
            # Simplify (skip for small polygons)
            if len(exterior) <= 10:
                exterior_simplified = exterior
            else:
                exterior_simplified = simplify_polygon(exterior, tolerance=polygon_tolerance)
                if len(exterior_simplified) < 3:
                    exterior_simplified = exterior
            
            holes_simplified = []
            for hole in holes:
                if len(hole) <= 10:
                    holes_simplified.append(hole)
                else:
                    hole_simpl = simplify_polygon(hole, tolerance=polygon_tolerance)
                    if len(hole_simpl) >= 3:
                        holes_simplified.append(hole_simpl)
                    elif len(hole) >= 3:
                        holes_simplified.append(hole)
            
            if len(exterior_simplified) >= 3:
                polygons[country_id] = {
                    'exterior': exterior_simplified,
                    'holes': holes_simplified if holes_simplified else []
                }
            else:
                skipped_countries.append(f"{country_name} (polygon invalid after processing)")
        else:  # MultiPolygon
            all_exteriors = []
            all_holes = []
            
            for poly_part in coords:
                if not poly_part:
                    continue
                
                exterior_coords = poly_part[0] if poly_part else []
                hole_coords = poly_part[1:] if len(poly_part) > 1 else []
                
                if not exterior_coords or len(exterior_coords) < 3:
                    continue
                
                exterior = [(p[1], p[0]) for p in exterior_coords]
                
                if len(exterior) <= 10:
                    exterior_simplified = exterior
                else:
                    exterior_simplified = simplify_polygon(exterior, tolerance=polygon_tolerance)
                    if len(exterior_simplified) < 3:
                        exterior_simplified = exterior
                
                if len(exterior_simplified) >= 3:
                    all_exteriors.append(exterior_simplified)
                
                if hole_coords:
                    for hole_coord in hole_coords:
                        hole = [(p[1], p[0]) for p in hole_coord]
                        if len(hole) >= 3:
                            if len(hole) <= 10:
                                all_holes.append(hole)
                            else:
                                hole_simpl = simplify_polygon(hole, tolerance=polygon_tolerance)
                                if len(hole_simpl) >= 3:
                                    all_holes.append(hole_simpl)
                                elif len(hole) >= 3:
                                    all_holes.append(hole)
            
            if all_exteriors:
                polygons[country_id] = {
                    'exterior': all_exteriors[0],
                    'holes': all_holes if all_holes else [],
                    'multi': True,
                    'exteriors': all_exteriors
                }
        
        # Extract metadata
        metadata[country_id] = {
            'name': country_name,
            'iso2': properties.get('ISO_A2', properties.get('iso_a2', '')),
            'iso3': properties.get('ISO_A3', properties.get('iso_a3', '')),
            'continent': properties.get('CONTINENT', properties.get('continent', '')),
            'timezone': properties.get('TIMEZONE', properties.get('timezone', ''))
        }
        
        # Validate stored polygon
        if country_id in polygons:
            polygon_data = polygons[country_id]
            exterior = polygon_data.get('exterior', [])
            is_multi = polygon_data.get('multi', False)
            
            if is_multi:
                exteriors = polygon_data.get('exteriors', [])
                if not exteriors or all(len(ext) < 3 for ext in exteriors):
                    skipped_countries.append(f"{country_name} (invalid MultiPolygon)")
                    del polygons[country_id]
            elif not exterior or len(exterior) < 3:
                skipped_countries.append(f"{country_name} (invalid polygon: {len(exterior)} vertices)")
                del polygons[country_id]
    
    print()  # New line after progress
    if skipped_countries:
        print(f"\n⚠ Skipped {len(skipped_countries)} countries with invalid geometry:")
        for country in skipped_countries[:15]:
            print(f"  - {country}")
        if len(skipped_countries) > 15:
            print(f"  ... and {len(skipped_countries) - 15} more")
    
    print(f"\n✓ Processed {len(polygons)} countries with valid polygons")
    
    # Build geohash index from processed polygons (optimized)
    print("\nBuilding geohash index with PIP validation...")
    geohash_index = build_geohash_index_from_polygons(
        polygons,
        geohash_precision=geohash_precision,
        validate_with_pip=True
    )
    
    return geohash_index, polygons, metadata


def main():
    """CLI entry point for data builder."""
    if len(sys.argv) < 3:
        print("Usage: python -m geo_intel_offline.data_builder <source.geojson> <output_dir> [tolerance] [precision]")
        sys.exit(1)
    
    source_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    polygon_tolerance = float(sys.argv[3]) if len(sys.argv) > 3 else 0.005
    geohash_precision = int(sys.argv[4]) if len(sys.argv) > 4 else 6
    
    if not source_path.exists():
        print(f"Error: Source file not found: {source_path}")
        sys.exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("GEO_INTEL_OFFLINE - DATA BUILDER")
    print("=" * 70)
    print(f"Source: {source_path}")
    print(f"Output: {output_dir}")
    print(f"Polygon tolerance: {polygon_tolerance}°")
    print(f"Geohash precision: {geohash_precision}")
    print()
    
    # Process GeoJSON
    geohash_index, polygons, metadata = process_geojson(
        source_path,
        polygon_tolerance=polygon_tolerance,
        geohash_precision=geohash_precision
    )
    
    # Save data files (both uncompressed and compressed)
    print("\nSaving data files...")
    
    import gzip
    
    # Save uncompressed (for compatibility)
    print("  Saving uncompressed JSON files...")
    with open(output_dir / 'geohash_index.json', 'w', encoding='utf-8') as f:
        json.dump(geohash_index, f, separators=(',', ':'))
    
    with open(output_dir / 'polygons.json', 'w', encoding='utf-8') as f:
        json.dump(polygons, f, separators=(',', ':'))
    
    with open(output_dir / 'metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, separators=(',', ':'), ensure_ascii=False)
    
    # Save compressed versions (smaller file size)
    print("  Saving compressed JSON files (gzip)...")
    with gzip.open(output_dir / 'geohash_index.json.gz', 'wt', encoding='utf-8', compresslevel=9) as f:
        json.dump(geohash_index, f, separators=(',', ':'))
    
    with gzip.open(output_dir / 'polygons.json.gz', 'wt', encoding='utf-8', compresslevel=9) as f:
        json.dump(polygons, f, separators=(',', ':'))
    
    with gzip.open(output_dir / 'metadata.json.gz', 'wt', encoding='utf-8', compresslevel=9) as f:
        json.dump(metadata, f, separators=(',', ':'), ensure_ascii=False)
    
    # Show file sizes
    print()
    print("File sizes:")
    for filename in ['geohash_index.json', 'polygons.json', 'metadata.json']:
        json_file = output_dir / filename
        gzip_file = output_dir / f"{filename}.gz"
        if json_file.exists() and gzip_file.exists():
            json_size = json_file.stat().st_size / 1024 / 1024  # MB
            gzip_size = gzip_file.stat().st_size / 1024 / 1024  # MB
            ratio = (gzip_size / json_size) * 100 if json_size > 0 else 0
            print(f"  {filename}: {json_size:.2f} MB -> {gzip_size:.2f} MB ({ratio:.1f}%)")
    
    print()
    print("=" * 70)
    print("BUILD COMPLETE")
    print("=" * 70)
    print(f"✓ Generated {len(geohash_index)} geohashes")
    print(f"✓ Processed {len(polygons)} countries")
    print(f"✓ Files saved to: {output_dir}")
    print()


if __name__ == '__main__':
    main()
