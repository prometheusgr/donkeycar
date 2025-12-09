"""
Data utilities - handle data operations and TUB management.
"""

from pathlib import Path
from typing import List, Dict, Any
import json


class TubManager:
    """Manage TUB (Training/Telemetry data) files."""
    
    @staticmethod
    def get_tub_metadata(tub_dir: Path) -> Dict[str, Any]:
        """
        Get metadata for a TUB directory.
        
        Args:
            tub_dir: Path to TUB directory
            
        Returns:
            Dictionary with metadata (frame count, etc.)
        """
        metadata = {
            'path': str(tub_dir),
            'name': tub_dir.name,
            'exists': tub_dir.exists(),
            'frame_count': 0,
            'metadata_file': None,
        }
        
        if not tub_dir.exists():
            return metadata
        
        # Try to read metadata file
        meta_file = tub_dir / 'manifest.json'
        if meta_file.exists():
            try:
                with open(meta_file) as f:
                    manifest = json.load(f)
                    metadata['metadata_file'] = str(meta_file)
                    # Count records
                    if isinstance(manifest, dict) and 'records' in manifest:
                        metadata['frame_count'] = len(manifest['records'])
            except Exception:
                pass
        
        # Fallback: count image files
        if metadata['frame_count'] == 0:
            images = list(tub_dir.glob('*/image*.jpg'))
            metadata['frame_count'] = len(images)
        
        return metadata
    
    @staticmethod
    def list_tubs(parent_dir: Path) -> List[Dict[str, Any]]:
        """
        List all TUBs in a directory.
        
        Args:
            parent_dir: Parent directory containing TUBs
            
        Returns:
            List of TUB metadata dictionaries
        """
        tubs = []
        
        if not parent_dir.exists():
            return tubs
        
        for item in sorted(parent_dir.iterdir()):
            if item.is_dir():
                tubs.append(TubManager.get_tub_metadata(item))
        
        return tubs
    
    @staticmethod
    def merge_tubs(tub_dirs: List[Path], output_dir: Path) -> bool:
        """
        Merge multiple TUBs into one.
        
        Args:
            tub_dirs: List of TUB directories to merge
            output_dir: Output directory for merged TUB
            
        Returns:
            True if successful
        """
        # Placeholder for merge logic
        return True
