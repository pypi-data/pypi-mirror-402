"""
Modular data loader - supports selective country/continent loading.

Features:
- Load specific countries or continents
- Lazy loading of country files
- Efficient memory usage
- Backward compatible with monolithic format
- Supports gzip-compressed data files
"""

import json
import gzip
from pathlib import Path
from typing import Dict, List, Optional
from .data_loader import DataLoader as MonolithicLoader


class ModularDataLoader:
    """
    Modular data loader that supports selective loading.
    
    Can load:
    - All countries (backward compatible)
    - Specific countries (by ISO2 codes)
    - Specific continents
    - All except excluded countries
    """
    
    def __init__(
        self,
        data_dir: Optional[str] = None,
        countries: Optional[List[str]] = None,
        continents: Optional[List[str]] = None,
        exclude_countries: Optional[List[str]] = None
    ):
        """
        Initialize modular data loader.
        
        Args:
            data_dir: Data directory (defaults to package data)
            countries: List of ISO2 codes to load (None = all)
            continents: List of continent names to load (None = all)
            exclude_countries: List of ISO2 codes to exclude
        """
        if data_dir is None:
            package_dir = Path(__file__).parent
            data_dir = package_dir / "data"
        
        self.data_dir = Path(data_dir)
        self.countries_filter = set(c.upper() for c in (countries or []))
        self.continents_filter = set(c.lower().replace(" ", "_") for c in (continents or [])) if continents else None
        self.exclude_filter = set(c.upper() for c in (exclude_countries or []))
        
        # Check if modular format exists
        self.index_path = self.data_dir / "index.json"
        self.is_modular = self.index_path.exists()
        
        if not self.is_modular:
            # Fallback to monolithic loader
            self.monolithic_loader = MonolithicLoader(data_dir)
            return
        
        # Load master index (supports gzip compression)
        index_gzip_path = self.index_path.with_suffix(self.index_path.suffix + '.gz')
        if index_gzip_path.exists():
            with gzip.open(index_gzip_path, 'rt', encoding='utf-8') as f:
                self.index = json.load(f)
        else:
            with open(self.index_path, 'r', encoding='utf-8') as f:
                self.index = json.load(f)
        
        # Determine which countries to load
        self._determine_countries_to_load()
        
        # Cache for loaded country data
        self._loaded_countries: Dict[str, Dict] = {}
        self._geohash_index: Dict[str, List[int]] = {}
        self._polygons: Dict[int, Dict] = {}
        self._metadata: Dict[int, Dict] = {}
    
    def _determine_countries_to_load(self):
        """Determine which countries should be loaded based on filters."""
        available_countries = set(self.index['countries'].keys())
        
        if self.countries_filter:
            # Specific countries requested
            to_load = available_countries & self.countries_filter
        elif self.continents_filter:
            # Specific continents requested
            to_load = set()
            for continent in self.continents_filter:
                if continent in self.index.get('continents', {}):
                    to_load.update(self.index['continents'][continent])
        else:
            # Load all countries
            to_load = available_countries
        
        # Apply exclusion filter
        to_load -= self.exclude_filter
        
        self.countries_to_load = to_load
    
    def _load_country(self, iso2: str) -> Optional[Dict]:
        """Load a single country file."""
        if iso2 in self._loaded_countries:
            return self._loaded_countries[iso2]
        
        if iso2 not in self.index['countries']:
            return None
        
        country_info = self.index['countries'][iso2]
        country_file = self.data_dir / country_info['file']
        
        # Try compressed version first, fallback to uncompressed
        country_gzip_file = country_file.with_suffix(country_file.suffix + '.gz')
        if country_gzip_file.exists():
            with gzip.open(country_gzip_file, 'rt', encoding='utf-8') as f:
                country_data = json.load(f)
        elif country_file.exists():
            with open(country_file, 'r', encoding='utf-8') as f:
                country_data = json.load(f)
        else:
            return None
        
        self._loaded_countries[iso2] = country_data
        
        # Update caches
        country_id = country_data['country_id']
        
        # Add to geohash index
        for geohash, ids in country_data['geohashes'].items():
            if geohash not in self._geohash_index:
                self._geohash_index[geohash] = []
            if country_id not in self._geohash_index[geohash]:
                self._geohash_index[geohash].append(country_id)
        
        # Add to polygons and metadata
        self._polygons[country_id] = country_data['polygon']
        self._metadata[country_id] = country_data['metadata']
        
        return country_data
    
    def _load_all_countries(self):
        """Load all countries that match filters."""
        for iso2 in self.countries_to_load:
            self._load_country(iso2)
    
    @property
    def geohash_index(self) -> Dict[str, List[int]]:
        """Get geohash index (lazy-loaded)."""
        if not self.is_modular:
            return self.monolithic_loader.geohash_index
        
        if not self._geohash_index:
            self._load_all_countries()
        return self._geohash_index
    
    @property
    def polygons(self) -> Dict[int, Dict]:
        """Get polygons (lazy-loaded)."""
        if not self.is_modular:
            return self.monolithic_loader.polygons
        
        if not self._polygons:
            self._load_all_countries()
        return self._polygons
    
    @property
    def metadata(self) -> Dict[int, Dict]:
        """Get metadata (lazy-loaded)."""
        if not self.is_modular:
            return self.monolithic_loader.metadata
        
        if not self._metadata:
            self._load_all_countries()
        return self._metadata
    
    def get_candidate_countries(self, geohash: str) -> List[int]:
        """Get candidate country IDs for a geohash."""
        index = self.geohash_index
        
        # Try full geohash first
        candidates = index.get(geohash, [])
        
        # If no exact match, try prefixes
        if not candidates:
            for prefix_len in range(len(geohash), 0, -1):
                prefix = geohash[:prefix_len]
                if prefix in index:
                    candidates.extend(index[prefix])
                    break
        
        return list(set(candidates))
    
    def get_polygon(self, country_id: int) -> Optional[Dict]:
        """Get polygon for a country."""
        return self.polygons.get(country_id)
    
    def get_metadata(self, country_id: int) -> Optional[Dict]:
        """Get metadata for a country."""
        return self.metadata.get(country_id)
    
    def get_loaded_countries(self) -> List[str]:
        """Get list of loaded country ISO2 codes."""
        if not self.is_modular:
            return list(self.monolithic_loader.metadata.keys())
        return list(self.countries_to_load)
    
    def get_loaded_count(self) -> int:
        """Get count of loaded countries."""
        return len(self.countries_to_load) if self.is_modular else len(self.monolithic_loader.metadata)
