from PIL import Image
import os
from typing import List, Tuple

class ImageSequence:
    def __init__(self, directory: str):
        """Initialize the image sequence processor.
        
        Args:
            directory (str): Directory containing PNG sequence
        """
        self.directory = directory
        self.images = []
        self.reference_size = None

    def load_images(self) -> List[str]:
        """Load and validate all PNG images in the directory.
        
        Returns:
            List[str]: Sorted list of valid image paths
        """
        # Get all PNG files
        png_files = [f for f in os.listdir(self.directory) if f.lower().endswith('.png')]
        png_files.sort()  # Sort by name
        
        if not png_files:
            raise ValueError(f"No PNG files found in {self.directory}")
        
        # Validate first image and set reference size
        first_image = Image.open(os.path.join(self.directory, png_files[0]))
        self.reference_size = first_image.size
        first_image.close()
        
        # Validate all images have same dimensions
        for png_file in png_files[1:]:
            img_path = os.path.join(self.directory, png_file)
            with Image.open(img_path) as img:
                if img.size != self.reference_size:
                    raise ValueError(f"Image {png_file} size mismatch. Expected {self.reference_size}, got {img.size}")
        
        self.images = [os.path.join(self.directory, f) for f in png_files]
        return self.images

    def get_image_dimensions(self) -> Tuple[int, int]:
        """Get the dimensions of images in the sequence.
        
        Returns:
            Tuple[int, int]: Width and height of images
        """
        if not self.reference_size:
            raise RuntimeError("Images not loaded yet")
        return self.reference_size

