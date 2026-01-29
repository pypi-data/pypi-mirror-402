"""
Minimal test data generator for development/testing.

Creates a small test dataset with a few countries for testing without
requiring full Natural Earth data.

Usage:
    python -m geo_intel_offline.data_builder_minimal <output_dir>
"""

import json
import sys
from pathlib import Path
from .geohash import encode


def create_minimal_test_data():
    """
    Create minimal test data with a few countries.
    
    Returns:
        Tuple of (geohash_index, polygons, metadata)
    """
    # Define a few test countries with simple square polygons
    # Coordinates: (lat, lon)
    
    # United States (rough bounding box)
    usa_exterior = [
        (49.0, -125.0),  # NW
        (49.0, -66.0),   # NE
        (25.0, -66.0),   # SE
        (25.0, -125.0),  # SW
    ]
    
    # United Kingdom (rough bounding box)
    uk_exterior = [
        (60.0, -8.0),    # NW
        (60.0, 2.0),     # NE
        (50.0, 2.0),     # SE
        (50.0, -8.0),    # SW
    ]
    
    # Japan (rough bounding box)
    japan_exterior = [
        (45.0, 129.0),   # NW
        (45.0, 146.0),   # NE
        (31.0, 146.0),   # SE
        (31.0, 129.0),   # SW
    ]
    
    # France (rough bounding box)
    france_exterior = [
        (51.0, -5.0),    # NW
        (51.0, 10.0),    # NE
        (42.0, 10.0),    # SE
        (42.0, -5.0),    # SW
    ]
    
    # Germany (rough bounding box)
    germany_exterior = [
        (55.0, 6.0),     # NW
        (55.0, 15.0),    # NE
        (47.0, 15.0),    # SE
        (47.0, 6.0),     # SW
    ]
    
    polygons = {
        1: {"exterior": usa_exterior, "holes": []},
        2: {"exterior": uk_exterior, "holes": []},
        3: {"exterior": japan_exterior, "holes": []},
        4: {"exterior": france_exterior, "holes": []},
        5: {"exterior": germany_exterior, "holes": []},
    }
    
    metadata = {
        1: {
            "name": "United States",
            "iso2": "US",
            "iso3": "USA",
            "continent": "North America",
            "timezone": "America/New_York"
        },
        2: {
            "name": "United Kingdom",
            "iso2": "GB",
            "iso3": "GBR",
            "continent": "Europe",
            "timezone": "Europe/London"
        },
        3: {
            "name": "Japan",
            "iso2": "JP",
            "iso3": "JPN",
            "continent": "Asia",
            "timezone": "Asia/Tokyo"
        },
        4: {
            "name": "France",
            "iso2": "FR",
            "iso3": "FRA",
            "continent": "Europe",
            "timezone": "Europe/Paris"
        },
        5: {
            "name": "Germany",
            "iso2": "DE",
            "iso3": "DEU",
            "continent": "Europe",
            "timezone": "Europe/Berlin"
        },
    }
    
    # Build geohash index by sampling bounding boxes
    geohash_index = {}
    
    for country_id, poly_data in polygons.items():
        exterior = poly_data["exterior"]
        
        # Get bounding box
        lats = [p[0] for p in exterior]
        lons = [p[1] for p in exterior]
        
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        
        # Sample points
        step = 1.0  # Larger step for test data
        lat = min_lat
        while lat <= max_lat:
            lon = min_lon
            while lon <= max_lon:
                geohash = encode(lat, lon, precision=6)
                if geohash not in geohash_index:
                    geohash_index[geohash] = []
                if country_id not in geohash_index[geohash]:
                    geohash_index[geohash].append(country_id)
                lon += step
            lat += step
    
    return geohash_index, polygons, metadata


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m geo_intel_offline.data_builder_minimal <output_dir>")
        sys.exit(1)
    
    output_dir = Path(sys.argv[1])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating minimal test data...")
    geohash_index, polygons, metadata = create_minimal_test_data()
    
    # Save files
    print(f"Writing data files to {output_dir}...")
    
    with open(output_dir / "geohash_index.json", 'w', encoding='utf-8') as f:
        json.dump(geohash_index, f, separators=(',', ':'))
    
    with open(output_dir / "polygons.json", 'w', encoding='utf-8') as f:
        json.dump(polygons, f, separators=(',', ':'))
    
    with open(output_dir / "metadata.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f, separators=(',', ':'), ensure_ascii=False)
    
    print(f"Done! Generated {len(geohash_index)} geohashes, {len(polygons)} countries.")
    print("\nNote: This is minimal test data. For production, use data_builder.py")
    print("      with Natural Earth or similar authoritative source data.")


if __name__ == '__main__':
    main()
