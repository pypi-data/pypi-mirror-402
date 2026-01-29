"""
Data compression utilities for reducing dataset file size.

Supports multiple compression formats:
1. gzip - Standard library, good compression ratio
2. msgpack - Binary format, smaller than JSON + faster parsing

All compression is lossless - no data is modified, only encoded differently.
"""

import gzip
import json
from pathlib import Path
from typing import Dict, Any, Optional

# msgpack is optional - only needed if using MessagePack format
HAS_MSGPACK = False
try:
    import msgpack  # type: ignore
    HAS_MSGPACK = True
except ImportError:
    pass


def compress_json_to_gzip(json_file: Path, output_file: Optional[Path] = None) -> Path:
    """
    Compress a JSON file using gzip.
    
    Args:
        json_file: Path to source JSON file
        output_file: Optional output path (defaults to json_file + '.gz')
    
    Returns:
        Path to compressed file
    """
    if output_file is None:
        output_file = json_file.with_suffix(json_file.suffix + '.gz')
    
    with open(json_file, 'rb') as f_in:
        with gzip.open(output_file, 'wb', compresslevel=9) as f_out:
            f_out.writelines(f_in)
    
    return output_file


def decompress_gzip_to_json(gzip_file: Path, output_file: Optional[Path] = None) -> Path:
    """
    Decompress a gzip file to JSON.
    
    Args:
        gzip_file: Path to compressed file
        output_file: Optional output path (defaults to gzip_file without .gz)
    
    Returns:
        Path to decompressed JSON file
    """
    if output_file is None:
        output_file = gzip_file.with_suffix('')
        if output_file.suffix == '.gz':
            output_file = output_file.with_suffix('')
    
    with gzip.open(gzip_file, 'rb') as f_in:
        with open(output_file, 'wb') as f_out:
            f_out.write(f_in.read())
    
    return output_file


def load_json_gzip(gzip_file: Path) -> Dict[str, Any]:
    """
    Load JSON data directly from a gzip-compressed file.
    
    Args:
        gzip_file: Path to compressed JSON file
    
    Returns:
        Parsed JSON data
    """
    with gzip.open(gzip_file, 'rt', encoding='utf-8') as f:
        return json.load(f)


def save_json_gzip(data: Dict[str, Any], output_file: Path, compresslevel: int = 9) -> Path:
    """
    Save JSON data directly to a gzip-compressed file.
    
    Args:
        data: Data to save (will be JSON-serialized)
        output_file: Output file path (will be .json.gz)
        compresslevel: gzip compression level (1-9, 9 = maximum)
    
    Returns:
        Path to saved file
    """
    with gzip.open(output_file, 'wt', encoding='utf-8', compresslevel=compresslevel) as f:
        json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
    
    return output_file


def load_msgpack(msgpack_file: Path) -> Dict[str, Any]:
    """
    Load data from MessagePack binary file.
    
    Args:
        msgpack_file: Path to .msgpack file
    
    Returns:
        Parsed data
    """
    if not HAS_MSGPACK:
        raise ImportError("msgpack library required. Install with: pip install msgpack")
    with open(msgpack_file, 'rb') as f:
        return msgpack.unpackb(f.read(), raw=False)


def save_msgpack(data: Dict[str, Any], output_file: Path) -> Path:
    """
    Save data to MessagePack binary file.
    
    Args:
        data: Data to save
        output_file: Output file path (should be .msgpack)
    
    Returns:
        Path to saved file
    """
    if not HAS_MSGPACK:
        raise ImportError("msgpack library required. Install with: pip install msgpack")
    with open(output_file, 'wb') as f:
        f.write(msgpack.packb(data, use_bin_type=True))
    return output_file


def verify_data_integrity(original_file: Path, compressed_file: Path, format: str = 'gzip') -> bool:
    """
    Verify that compressed data matches original data exactly.
    
    Args:
        original_file: Original JSON file
        compressed_file: Compressed file
        format: Compression format ('gzip' or 'msgpack')
    
    Returns:
        True if data matches, False otherwise
    """
    # Load original
    with open(original_file, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    # Load compressed
    if format == 'gzip':
        if compressed_file.suffix == '.gz':
            decompressed_data = load_json_gzip(compressed_file)
        else:
            # Assume it's compressed
            decompressed_data = load_json_gzip(compressed_file)
    elif format == 'msgpack':
        decompressed_data = load_msgpack(compressed_file)
    else:
        raise ValueError(f"Unknown format: {format}")
    
    # Compare (convert to JSON strings for comparison to handle ordering)
    original_json = json.dumps(original_data, sort_keys=True, separators=(',', ':'))
    decompressed_json = json.dumps(decompressed_data, sort_keys=True, separators=(',', ':'))
    
    return original_json == decompressed_json


def get_compression_ratio(original_file: Path, compressed_file: Path) -> float:
    """
    Calculate compression ratio.
    
    Returns:
        Compression ratio (compressed_size / original_size)
    """
    original_size = original_file.stat().st_size
    compressed_size = compressed_file.stat().st_size
    return compressed_size / original_size


def compress_all_data_files(data_dir: Path, use_msgpack: bool = False) -> Dict[str, Any]:
    """
    Compress all JSON data files in a directory.
    
    Args:
        data_dir: Directory containing JSON files
        use_msgpack: If True, use MessagePack format; otherwise use gzip
    
    Returns:
        Dict with compression statistics
    """
    results = {
        'compressed_files': [],
        'total_original_size': 0,
        'total_compressed_size': 0,
        'compression_ratio': 0.0,
        'files': {}
    }
    
    json_files = list(data_dir.glob('*.json'))
    
    for json_file in json_files:
        original_size = json_file.stat().st_size
        results['total_original_size'] += original_size
        
        if use_msgpack:
            # Save as MessagePack
            msgpack_file = json_file.with_suffix('.msgpack')
            save_msgpack(json.load(open(json_file, 'r', encoding='utf-8')), msgpack_file)
            compressed_size = msgpack_file.stat().st_size
            results['compressed_files'].append(str(msgpack_file))
        else:
            # Compress with gzip
            gzip_file = compress_json_to_gzip(json_file)
            compressed_size = gzip_file.stat().st_size
            results['compressed_files'].append(str(gzip_file))
        
        results['total_compressed_size'] += compressed_size
        ratio = compressed_size / original_size
        results['files'][json_file.name] = {
            'original_size': original_size,
            'compressed_size': compressed_size,
            'ratio': ratio
        }
        
        # Verify integrity
        if use_msgpack:
            verified = verify_data_integrity(json_file, msgpack_file, 'msgpack')
        else:
            verified = verify_data_integrity(json_file, gzip_file, 'gzip')
        
        if not verified:
            raise ValueError(f"Data integrity check failed for {json_file.name}")
    
    results['compression_ratio'] = results['total_compressed_size'] / results['total_original_size']
    
    return results
