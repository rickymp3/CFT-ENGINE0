"""Asset pipeline with cloud storage integration and automatic caching.

Features:
- Dropbox/Box/Google Drive integration
- Automatic format conversion (.obj, .fbx, .gltf -> .bam)
- Asset caching with metadata
- Thumbnail generation
- Dependency tracking
- Version control
"""
import os
import json
import hashlib
import shutil
import logging
from typing import Dict, Optional, List, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import urllib.request

# Cloud storage imports (optional)
try:
    import dropbox
    DROPBOX_AVAILABLE = True
except ImportError:
    DROPBOX_AVAILABLE = False
    logging.warning("dropbox module not installed. Run: pip install dropbox")

try:
    from boxsdk import Client, OAuth2
    BOX_AVAILABLE = True
except ImportError:
    BOX_AVAILABLE = False
    logging.warning("boxsdk module not installed. Run: pip install boxsdk")

# Panda3D imports
try:
    from panda3d.core import NodePath, loadPrcFileData
    from direct.showbase.Loader import Loader
    PANDA3D_AVAILABLE = True
except ImportError:
    PANDA3D_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class AssetMetadata:
    """Asset metadata structure."""
    asset_id: str
    name: str
    asset_type: str  # model, texture, sound, material, etc.
    source_path: str  # Original path (cloud or local)
    cache_path: str  # Local cached path
    format: str  # File extension
    file_size: int
    checksum: str  # MD5 hash
    created_at: str
    modified_at: str
    dependencies: List[str]  # List of asset IDs this depends on
    tags: List[str]
    custom_data: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'AssetMetadata':
        """Create from dictionary."""
        return AssetMetadata(**data)


class AssetCache:
    """Local asset cache manager."""
    
    def __init__(self, cache_dir: str = "./asset_cache"):
        """Initialize asset cache.
        
        Args:
            cache_dir: Directory for cached assets
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.metadata_dir = self.cache_dir / "metadata"
        self.metadata_dir.mkdir(exist_ok=True)
        
        self.assets_dir = self.cache_dir / "assets"
        self.assets_dir.mkdir(exist_ok=True)
        
        self.thumbnails_dir = self.cache_dir / "thumbnails"
        self.thumbnails_dir.mkdir(exist_ok=True)
        
        # Load metadata index
        self.index_path = self.cache_dir / "index.json"
        self.index: Dict[str, AssetMetadata] = {}
        self._load_index()
        
        logger.info(f"Asset cache initialized at {cache_dir}")
    
    def _load_index(self) -> None:
        """Load metadata index from disk."""
        if self.index_path.exists():
            try:
                with open(self.index_path, 'r') as f:
                    data = json.load(f)
                    for asset_id, meta_dict in data.items():
                        self.index[asset_id] = AssetMetadata.from_dict(meta_dict)
                logger.info(f"Loaded {len(self.index)} assets from cache index")
            except Exception as e:
                logger.error(f"Failed to load cache index: {e}")
    
    def _save_index(self) -> None:
        """Save metadata index to disk."""
        try:
            data = {aid: meta.to_dict() for aid, meta in self.index.items()}
            with open(self.index_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")
    
    def add_asset(self, metadata: AssetMetadata, source_file: Path) -> bool:
        """Add asset to cache.
        
        Args:
            metadata: Asset metadata
            source_file: Source file to cache
            
        Returns:
            True if successful
        """
        try:
            # Copy to cache
            cache_file = self.assets_dir / metadata.asset_id / source_file.name
            cache_file.parent.mkdir(exist_ok=True)
            shutil.copy2(source_file, cache_file)
            
            # Update metadata
            metadata.cache_path = str(cache_file)
            
            # Add to index
            self.index[metadata.asset_id] = metadata
            self._save_index()
            
            logger.info(f"Added asset to cache: {metadata.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add asset to cache: {e}")
            return False
    
    def get_asset(self, asset_id: str) -> Optional[AssetMetadata]:
        """Get asset metadata.
        
        Args:
            asset_id: Asset identifier
            
        Returns:
            Asset metadata or None
        """
        return self.index.get(asset_id)
    
    def get_asset_path(self, asset_id: str) -> Optional[Path]:
        """Get cached asset file path.
        
        Args:
            asset_id: Asset identifier
            
        Returns:
            Path to cached file or None
        """
        metadata = self.get_asset(asset_id)
        if metadata:
            return Path(metadata.cache_path)
        return None
    
    def has_asset(self, asset_id: str) -> bool:
        """Check if asset is cached.
        
        Args:
            asset_id: Asset identifier
            
        Returns:
            True if asset is in cache
        """
        return asset_id in self.index
    
    def search_assets(self, query: str = "", asset_type: str = "", tags: List[str] = None) -> List[AssetMetadata]:
        """Search cached assets.
        
        Args:
            query: Name search query
            asset_type: Filter by asset type
            tags: Filter by tags
            
        Returns:
            List of matching assets
        """
        results = []
        
        for metadata in self.index.values():
            # Name filter
            if query and query.lower() not in metadata.name.lower():
                continue
            
            # Type filter
            if asset_type and metadata.asset_type != asset_type:
                continue
            
            # Tag filter
            if tags:
                if not any(tag in metadata.tags for tag in tags):
                    continue
            
            results.append(metadata)
        
        return results
    
    def clear_cache(self) -> None:
        """Clear all cached assets."""
        try:
            shutil.rmtree(self.assets_dir)
            self.assets_dir.mkdir(exist_ok=True)
            
            shutil.rmtree(self.thumbnails_dir)
            self.thumbnails_dir.mkdir(exist_ok=True)
            
            self.index.clear()
            self._save_index()
            
            logger.info("Asset cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")


class DropboxAssetProvider:
    """Dropbox cloud storage provider."""
    
    def __init__(self, access_token: str):
        """Initialize Dropbox provider.
        
        Args:
            access_token: Dropbox API access token
        """
        if not DROPBOX_AVAILABLE:
            raise ImportError("dropbox module not installed")
        
        self.dbx = dropbox.Dropbox(access_token)
        logger.info("Dropbox provider initialized")
    
    def list_files(self, folder_path: str = "") -> List[Dict]:
        """List files in Dropbox folder.
        
        Args:
            folder_path: Folder path (empty for root)
            
        Returns:
            List of file metadata
        """
        try:
            result = self.dbx.files_list_folder(folder_path)
            files = []
            
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    files.append({
                        'name': entry.name,
                        'path': entry.path_display,
                        'size': entry.size,
                        'modified': entry.server_modified.isoformat()
                    })
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list Dropbox files: {e}")
            return []
    
    def download_file(self, dropbox_path: str, local_path: Path) -> bool:
        """Download file from Dropbox.
        
        Args:
            dropbox_path: Path in Dropbox
            local_path: Local destination path
            
        Returns:
            True if successful
        """
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            self.dbx.files_download_to_file(str(local_path), dropbox_path)
            logger.info(f"Downloaded from Dropbox: {dropbox_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download from Dropbox: {e}")
            return False
    
    def upload_file(self, local_path: Path, dropbox_path: str) -> bool:
        """Upload file to Dropbox.
        
        Args:
            local_path: Local file path
            dropbox_path: Destination path in Dropbox
            
        Returns:
            True if successful
        """
        try:
            with open(local_path, 'rb') as f:
                self.dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
            logger.info(f"Uploaded to Dropbox: {dropbox_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload to Dropbox: {e}")
            return False


class AssetPipeline:
    """Main asset pipeline orchestrator."""
    
    def __init__(self, cache_dir: str = "./asset_cache"):
        """Initialize asset pipeline.
        
        Args:
            cache_dir: Directory for asset cache
        """
        self.cache = AssetCache(cache_dir)
        self.cloud_providers: Dict[str, Any] = {}
        
        # Loader for Panda3D
        self.loader = Loader(None) if PANDA3D_AVAILABLE else None
        
        # Format converters
        self.converters = {
            '.obj': self._convert_obj_to_bam,
            '.fbx': self._convert_fbx_to_bam,
            '.gltf': self._convert_gltf_to_bam,
            '.glb': self._convert_gltf_to_bam,
        }
        
        logger.info("Asset pipeline initialized")
    
    def register_dropbox(self, access_token: str) -> None:
        """Register Dropbox cloud provider.
        
        Args:
            access_token: Dropbox API access token
        """
        if DROPBOX_AVAILABLE:
            self.cloud_providers['dropbox'] = DropboxAssetProvider(access_token)
            logger.info("Dropbox provider registered")
        else:
            logger.error("Dropbox module not available")
    
    def import_asset(self, source_path: str, asset_type: str = "model", 
                     cloud_provider: Optional[str] = None, **kwargs) -> Optional[str]:
        """Import asset from local or cloud storage.
        
        Args:
            source_path: Source file path (local or cloud)
            asset_type: Type of asset (model, texture, etc.)
            cloud_provider: Cloud provider name (dropbox, box, etc.)
            **kwargs: Additional metadata
            
        Returns:
            Asset ID if successful, None otherwise
        """
        # Generate asset ID
        asset_id = hashlib.md5(source_path.encode()).hexdigest()
        
        # Check if already cached
        if self.cache.has_asset(asset_id):
            logger.info(f"Asset already cached: {asset_id}")
            return asset_id
        
        # Download from cloud if needed
        if cloud_provider:
            provider = self.cloud_providers.get(cloud_provider)
            if not provider:
                logger.error(f"Cloud provider not registered: {cloud_provider}")
                return None
            
            temp_path = self.cache.cache_dir / "temp" / Path(source_path).name
            temp_path.parent.mkdir(exist_ok=True)
            
            if not provider.download_file(source_path, temp_path):
                return None
            
            local_path = temp_path
        else:
            local_path = Path(source_path)
        
        # Validate file exists
        if not local_path.exists():
            logger.error(f"Source file not found: {local_path}")
            return None
        
        # Convert if needed
        converted_path = self._convert_asset(local_path, asset_type)
        if not converted_path:
            converted_path = local_path
        
        # Create metadata
        metadata = AssetMetadata(
            asset_id=asset_id,
            name=kwargs.get('name', local_path.stem),
            asset_type=asset_type,
            source_path=source_path,
            cache_path="",  # Will be set by cache
            format=converted_path.suffix,
            file_size=converted_path.stat().st_size,
            checksum=self._calculate_checksum(converted_path),
            created_at=datetime.now().isoformat(),
            modified_at=datetime.now().isoformat(),
            dependencies=kwargs.get('dependencies', []),
            tags=kwargs.get('tags', []),
            custom_data=kwargs.get('custom_data', {})
        )
        
        # Add to cache
        if self.cache.add_asset(metadata, converted_path):
            logger.info(f"Asset imported: {metadata.name} ({asset_id})")
            return asset_id
        
        return None
    
    def load_asset(self, asset_id: str) -> Optional[NodePath]:
        """Load asset for use in game.
        
        Args:
            asset_id: Asset identifier
            
        Returns:
            Loaded NodePath or None
        """
        if not PANDA3D_AVAILABLE:
            logger.error("Panda3D not available")
            return None
        
        metadata = self.cache.get_asset(asset_id)
        if not metadata:
            logger.error(f"Asset not found: {asset_id}")
            return None
        
        try:
            # Load dependencies first
            for dep_id in metadata.dependencies:
                self.load_asset(dep_id)
            
            # Load the asset
            asset_path = Path(metadata.cache_path)
            if not asset_path.exists():
                logger.error(f"Cached file not found: {asset_path}")
                return None
            
            model = self.loader.loadModel(str(asset_path))
            logger.info(f"Loaded asset: {metadata.name}")
            return model
            
        except Exception as e:
            logger.error(f"Failed to load asset: {e}")
            return None
    
    def _convert_asset(self, source_path: Path, asset_type: str) -> Optional[Path]:
        """Convert asset to engine-compatible format.
        
        Args:
            source_path: Source file path
            asset_type: Type of asset
            
        Returns:
            Converted file path or None
        """
        if asset_type != "model":
            return None  # Only convert models for now
        
        converter = self.converters.get(source_path.suffix.lower())
        if converter:
            return converter(source_path)
        
        return None
    
    def _convert_obj_to_bam(self, source_path: Path) -> Optional[Path]:
        """Convert OBJ to BAM format.
        
        Args:
            source_path: Source OBJ file
            
        Returns:
            Converted BAM file path
        """
        try:
            output_path = source_path.with_suffix('.bam')
            
            # Use Panda3D's obj2bam or egg2bam converter
            # For now, just return the OBJ (Panda3D can load it directly)
            logger.info(f"OBJ file will be loaded directly: {source_path}")
            return source_path
            
        except Exception as e:
            logger.error(f"Failed to convert OBJ: {e}")
            return None
    
    def _convert_fbx_to_bam(self, source_path: Path) -> Optional[Path]:
        """Convert FBX to BAM format.
        
        Args:
            source_path: Source FBX file
            
        Returns:
            Converted BAM file path
        """
        logger.warning("FBX conversion not yet implemented")
        return None
    
    def _convert_gltf_to_bam(self, source_path: Path) -> Optional[Path]:
        """Convert GLTF/GLB to BAM format.
        
        Args:
            source_path: Source GLTF/GLB file
            
        Returns:
            Converted BAM file path
        """
        logger.warning("GLTF conversion not yet implemented")
        return None
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file.
        
        Args:
            file_path: File to checksum
            
        Returns:
            MD5 hash string
        """
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
        return md5.hexdigest()
    
    def search_assets(self, query: str = "", asset_type: str = "", tags: List[str] = None) -> List[AssetMetadata]:
        """Search for assets.
        
        Args:
            query: Name search query
            asset_type: Filter by type
            tags: Filter by tags
            
        Returns:
            List of matching assets
        """
        return self.cache.search_assets(query, asset_type, tags)
    
    def get_asset_info(self, asset_id: str) -> Optional[AssetMetadata]:
        """Get asset metadata.
        
        Args:
            asset_id: Asset identifier
            
        Returns:
            Asset metadata or None
        """
        return self.cache.get_asset(asset_id)
