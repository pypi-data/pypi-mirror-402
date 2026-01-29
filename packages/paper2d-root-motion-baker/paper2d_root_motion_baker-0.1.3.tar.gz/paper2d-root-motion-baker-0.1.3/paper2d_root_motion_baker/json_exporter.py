import json
from typing import List, Dict

class JsonExporter:
    @staticmethod
    def export_motion_data(motion_data: List[Dict], output_path: str):
        """Export motion data to JSON file.
        
        Args:
            motion_data (List[Dict]): List of motion data for each frame
            output_path (str): Path to save the JSON file
        """
        output = {
            "frames": motion_data,
            "metadata": {
                "frame_count": len(motion_data),
                "version": "1.0"
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)

