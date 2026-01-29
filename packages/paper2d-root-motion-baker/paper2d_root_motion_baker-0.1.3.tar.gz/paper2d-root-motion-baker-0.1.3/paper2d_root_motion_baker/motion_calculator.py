from typing import List, Tuple, Dict
from .marker_detector import MarkerDetector

class RootMotionCalculator:
    def __init__(self, marker_detector: MarkerDetector):
        """Initialize the root motion calculator.
        
        Args:
            marker_detector (MarkerDetector): Marker detector instance
        """
        self.marker_detector = marker_detector
        self.reference_point = None
        self.motion_data = []

    def process_sequence(self, image_paths: List[str]) -> List[Dict]:
        """Process a sequence of images and calculate root motion.
        
        Args:
            image_paths (List[str]): List of image paths to process
            
        Returns:
            List[Dict]: List of motion data for each frame
        """
        if not image_paths:
            raise ValueError("No images provided")

        # Get reference point from first frame
        self.reference_point = self.marker_detector.find_marker(image_paths[0])
        if not self.reference_point:
            raise ValueError("Could not find marker in reference frame")

        self.motion_data = []
        ref_x, ref_y = self.reference_point

        # Process each frame
        for i, image_path in enumerate(image_paths):
            marker_pos = self.marker_detector.find_marker(image_path)
            if not marker_pos:
                raise ValueError(f"Could not find marker in frame {i}")
            print(f"Frame {i}: Found marker at position {marker_pos}")

            # Calculate delta from reference point
            # Flip Y coordinate (positive Y is up)
            delta_x = marker_pos[0] - ref_x
            delta_y = -(marker_pos[1] - ref_y)  # Negate Y delta so positive is up

            frame_data = {
                "frame": i,
                "position": {
                    "x": delta_x,
                    "y": delta_y
                }
            }
            self.motion_data.append(frame_data)

        return self.motion_data

