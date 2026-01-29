"""
Data loading and binary format handling.

Binary Format Design:
1. geohash_index.json(.gz) - Geohash → country_id mappings (compressed)
2. polygons.json(.gz) - Country polygons (simplified, coordinate arrays)
3. metadata.json(.gz) - Country metadata (ISO codes, continent, timezone)

Design Decisions:
- JSON for simplicity (can be compressed/gzipped in production)
- Supports gzip compression for reduced file size
- Alternative: msgpack/binary for even smaller size
- Lazy loading: Load only when needed
- In-memory caching: Keep in memory after first load

For production with < 15 MB constraint:
- Simplify polygons (reduce vertices using Douglas-Peucker)
- Compress geohash index (sparse representation)
- Use efficient coordinate storage (fixed-point integers)
- Gzip compression reduces file size by ~60-80%
"""

import json
import gzip
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class DataLoader:
    """Loads and caches geo-intelligence data."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize data loader.
        
        Args:
            data_dir: Directory containing data files. If None, uses package data directory.
        """
        if data_dir is None:
            # Default to package data directory
            package_dir = Path(__file__).parent
            data_dir = package_dir / "data"
        
        self.data_dir = Path(data_dir)
        self._geohash_index: Optional[Dict[str, List[int]]] = None
        self._polygons: Optional[Dict[int, Dict]] = None
        self._metadata: Optional[Dict[int, Dict]] = None
    
    def _load_json(self, filename: str) -> dict:
        """
        Load JSON file from data directory.
        
        Automatically detects and handles gzip-compressed files (.json.gz).
        Falls back to uncompressed .json in data_dev/ for development if needed.
        """
        filepath = self.data_dir / filename
        gzip_filepath = self.data_dir / f"{filename}.gz"
        dev_data_dir = self.data_dir.parent / "data_dev"
        dev_filepath = dev_data_dir / filename
        
        # Try compressed version first (smaller, preferred - for distribution)
        if gzip_filepath.exists():
            with gzip.open(gzip_filepath, 'rt', encoding='utf-8') as f:
                return json.load(f)
        
        # Fallback to uncompressed in data directory (development)
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Fallback to dev directory (uncompressed files moved here)
        if dev_filepath.exists():
            with open(dev_filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # None found
        raise FileNotFoundError(
            f"Data file not found: {gzip_filepath} or {filepath} or {dev_filepath}\n"
            f"Please run data_builder.py to generate data files."
        )
    
    @property
    def geohash_index(self) -> Dict[str, List[int]]:
        """Get geohash index (lazy-loaded)."""
        if self._geohash_index is None:
            data = self._load_json("geohash_index.json")
            self._geohash_index = {
                k: v if isinstance(v, list) else [v]
                for k, v in data.items()
            }
        return self._geohash_index
    
    @property
    def polygons(self) -> Dict[int, Dict]:
        """Get country polygons (lazy-loaded)."""
        if self._polygons is None:
            self._polygons = self._load_json("polygons.json")
            # Convert list keys to int (JSON doesn't support int keys)
            self._polygons = {
                int(k): v for k, v in self._polygons.items()
            }
        return self._polygons
    
    @property
    def metadata(self) -> Dict[int, Dict]:
        """Get country metadata (lazy-loaded)."""
        if self._metadata is None:
            self._metadata = self._load_json("metadata.json")
            # Convert list keys to int
            self._metadata = {
                int(k): v for k, v in self._metadata.items()
            }
        return self._metadata
    
    def get_candidate_countries(self, geohash: str) -> List[int]:
        """
        Get candidate country IDs for a geohash.
        
        Args:
            geohash: Geohash string
        
        Returns:
            List of country IDs that may contain this geohash
        """
        index = self.geohash_index
        
        # Try full geohash first
        candidates = index.get(geohash, [])
        
        # If no exact match, try prefixes (geohash can overlap borders)
        if not candidates:
            for prefix_len in range(len(geohash), 0, -1):
                prefix = geohash[:prefix_len]
                if prefix in index:
                    candidates.extend(index[prefix])
                    break
        
        return list(set(candidates))  # Deduplicate
    
    def get_polygon(self, country_id: int) -> Optional[Dict]:
        """
        Get polygon data for a country.
        
        Returns:
            Dict with 'exterior' and optionally 'holes' keys,
            or None if country not found
        """
        return self.polygons.get(country_id)
    
    def get_metadata(self, country_id: int) -> Optional[Dict]:
        """
        Get metadata for a country.
        
        Returns:
            Dict with 'name', 'iso2', 'iso3', 'continent', 'timezone',
            or None if country not found
        """
        return self.metadata.get(country_id)


# Global instance (lazy-loaded)
_loader: Optional[DataLoader] = None


def get_loader(data_dir: Optional[str] = None) -> DataLoader:
    """Get or create global data loader instance."""
    global _loader
    if _loader is None:
        _loader = DataLoader(data_dir)
    return _loader
