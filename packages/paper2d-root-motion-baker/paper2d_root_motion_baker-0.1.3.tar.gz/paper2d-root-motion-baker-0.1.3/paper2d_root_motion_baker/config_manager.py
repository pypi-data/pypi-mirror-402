import yaml
from typing import Dict, Any, List, Tuple
import os

# Try to use importlib.resources (Python 3.9+), fallback to pkg_resources or file-based approach
USE_IMPORTLIB = False
USE_PKGRESOURCES = False

try:
    from importlib.resources import files, as_file
    USE_IMPORTLIB = True
except ImportError:
    try:
        import pkg_resources
        USE_PKGRESOURCES = True
    except ImportError:
        pass

class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from YAML file."""
        config_path = None
        
        # Try importlib.resources first (Python 3.9+)
        if USE_IMPORTLIB:
            try:
                config_file = files('paper2d_root_motion_baker').joinpath('config.yaml')
                with as_file(config_file) as path:
                    config_path = str(path)
            except Exception:
                pass
        
        # Fallback to pkg_resources
        if not config_path and USE_PKGRESOURCES:
            try:
                config_path = pkg_resources.resource_filename('paper2d_root_motion_baker', 'config.yaml')
            except Exception:
                pass
        
        # Fallback to file-based approach (for development)
        if not config_path:
            # Get the package directory
            package_dir = os.path.dirname(__file__)
            config_path = os.path.join(package_dir, 'config.yaml')
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found at {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
    
    @property
    def marker_color(self) -> Tuple[int, int, int]:
        """Get the marker color."""
        return tuple(self.config['marker']['color'])
    
    @property
    def color_tolerance(self) -> int:
        """Get the color matching tolerance."""
        return self.config['marker']['tolerance']
    
    @property
    def supported_extensions(self) -> List[str]:
        """Get supported image extensions."""
        return self.config['image']['supported_extensions']
    
    @property
    def json_version(self) -> str:
        """Get JSON export version."""
        return self.config['export']['json']['version']
    
    @property
    def json_indent(self) -> int:
        """Get JSON export indentation."""
        return self.config['export']['json']['indent']
    
    @property
    def motion_error_threshold(self) -> float:
        """Get motion error threshold."""
        return self.config['motion']['error_threshold']

