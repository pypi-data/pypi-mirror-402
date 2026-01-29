"""
Migration tool: Convert monolithic data format to modular format.

This tool reads existing monolithic data files and converts them to
the new modular country-wise format.
"""

import json
import sys
from pathlib import Path
from typing import Dict


def migrate_monolithic_to_modular(
    monolithic_dir: Path,
    output_dir: Path
) -> Dict:
    """
    Migrate monolithic data files to modular format.
    
    Args:
        monolithic_dir: Directory with monolithic files (geohash_index.json, etc.)
        output_dir: Output directory for modular format
    
    Returns:
        Dict with migration statistics
    """
    # Load monolithic files
    index_file = monolithic_dir / "geohash_index.json"
    polygons_file = monolithic_dir / "polygons.json"
    metadata_file = monolithic_dir / "metadata.json"
    
    if not all(f.exists() for f in [index_file, polygons_file, metadata_file]):
        raise FileNotFoundError(
            f"Monolithic data files not found in {monolithic_dir}. "
            "Expected: geohash_index.json, polygons.json, metadata.json"
        )
    
    with open(index_file, 'r') as f:
        geohash_index = json.load(f)
    
    with open(polygons_file, 'r') as f:
        polygons = json.load(f)
    
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    # Create output structure
    output_dir.mkdir(parents=True, exist_ok=True)
    continents_dir = output_dir / "continents"
    continents_dir.mkdir(exist_ok=True)
    
    # Organize by country
    master_index = {
        'version': '1.0.0',
        'countries': {},
        'continents': {}
    }
    
    continent_countries = {}
    
    # Process each country
    for country_id_str, country_metadata in metadata.items():
        country_id = int(country_id_str)
        iso2 = country_metadata.get('iso2', '').upper()
        continent_raw = country_metadata.get('continent', 'unknown')
        continent = continent_raw.lower().replace(' ', '_')
        
        if not iso2:
            # Skip countries without ISO2 code
            continue
        
        # Get polygon for this country
        country_polygon = polygons.get(country_id_str)
        if not country_polygon:
            continue
        
        # Extract geohashes for this country
        country_geohashes = {}
        for geohash, country_ids in geohash_index.items():
            if country_id in (country_ids if isinstance(country_ids, list) else [country_ids]):
                country_geohashes[geohash] = [country_id]
        
        # Create country data structure
        country_data = {
            'country_id': country_id,
            'metadata': country_metadata,
            'geohashes': country_geohashes,
            'polygon': country_polygon
        }
        
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
            'name': country_metadata.get('name', ''),
            'iso2': iso2,
            'iso3': country_metadata.get('iso3', ''),
            'continent': continent_raw,
            'file': relative_path,
            'size_bytes': country_file.stat().st_size
        }
        
        # Track continent membership
        if continent not in continent_countries:
            continent_countries[continent] = []
        continent_countries[continent].append(iso2)
    
    # Update continent index
    master_index['continents'] = continent_countries
    
    # Save master index
    index_output = output_dir / "index.json"
    with open(index_output, 'w', encoding='utf-8') as f:
        json.dump(master_index, f, indent=2, ensure_ascii=False)
    
    return {
        'countries_migrated': len(master_index['countries']),
        'continents': list(continent_countries.keys())
    }


def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print("Usage: python -m geo_intel_offline.migrate_to_modular <monolithic_dir> <output_dir>")
        print("\nExample:")
        print("  python -m geo_intel_offline.migrate_to_modular geo_intel_offline/data geo_intel_offline/data_modular")
        sys.exit(1)
    
    monolithic_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    
    print(f"Migrating monolithic data from {monolithic_dir} to {output_dir}...")
    
    try:
        stats = migrate_monolithic_to_modular(monolithic_dir, output_dir)
        print(f"\n✓ Migration complete!")
        print(f"  Countries migrated: {stats['countries_migrated']}")
        print(f"  Continents: {', '.join(stats['continents'])}")
        print(f"\nModular data saved to: {output_dir}")
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
