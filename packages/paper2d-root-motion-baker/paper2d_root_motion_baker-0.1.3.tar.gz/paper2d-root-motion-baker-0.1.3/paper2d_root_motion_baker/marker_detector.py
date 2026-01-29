from PIL import Image
import numpy as np
from typing import Tuple, Optional
from .config_manager import ConfigManager

class MarkerDetector:
    def __init__(self, marker_color: Optional[Tuple[int, int, int]] = None):
        """Initialize the marker detector.
        
        Args:
            marker_color (Optional[Tuple[int, int, int]], optional): RGB color tuple of the marker.
                If not provided, uses the default from config.
        """
        config = ConfigManager()
        self.marker_color = marker_color if marker_color is not None else config.marker_color
        self.tolerance = config.color_tolerance

    def find_marker(self, image_path: str) -> Optional[Tuple[int, int]]:
        """Find the marker coordinates in the image.
        Scans from left to right, top to bottom and returns the first matching pixel.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            Optional[Tuple[int, int]]: Marker coordinates (x, y) or None if not found
        """
        with Image.open(image_path) as img:
            # Convert to RGBA to handle transparency
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Convert to numpy array for faster processing
            img_data = np.array(img)
            height, width = img_data.shape[:2]
            
            # Scan each pixel from left to right, bottom to top
            for y in range(height - 1, -1, -1):  # Start from bottom (height-1) to top (0)
                for x in range(width):
                    pixel = img_data[y, x]
                    # Check if pixel matches marker color within tolerance, ignoring alpha channel
                    if (abs(pixel[0] - self.marker_color[0]) <= self.tolerance and
                        abs(pixel[1] - self.marker_color[1]) <= self.tolerance and
                        abs(pixel[2] - self.marker_color[2]) <= self.tolerance):
                        return (x, y)
            
            return None

