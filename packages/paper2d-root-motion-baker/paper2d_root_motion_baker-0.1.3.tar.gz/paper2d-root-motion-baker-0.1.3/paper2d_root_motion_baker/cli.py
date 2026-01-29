import argparse
import os
from .image_processor import ImageSequence
from .marker_detector import MarkerDetector
from .motion_calculator import RootMotionCalculator
from .json_exporter import JsonExporter

def main():
    parser = argparse.ArgumentParser(description='Root Motion Baker for Paper2D')
    parser.add_argument('input_dir', help='Directory containing PNG sequence')
    parser.add_argument('output_json', help='Output JSON file path')
    parser.add_argument('--marker-color', nargs=3, type=int, default=[255, 0, 0],
                      help='Marker color in RGB format (default: 255 0 0 for red)')
    
    args = parser.parse_args()
    
    # Validate input directory
    if not os.path.isdir(args.input_dir):
        print(f"Error: Input directory '{args.input_dir}' does not exist")
        return 1
    
    try:
        # Initialize components
        image_sequence = ImageSequence(args.input_dir)
        marker_detector = MarkerDetector(tuple(args.marker_color))
        motion_calculator = RootMotionCalculator(marker_detector)
        
        # Load and validate images
        print("Loading and validating images...")
        image_paths = image_sequence.load_images()
        print(f"Found {len(image_paths)} images")
        
        # Process sequence
        print("Processing frames...")
        motion_data = motion_calculator.process_sequence(image_paths)
        
        # Export results
        print("Exporting motion data...")
        JsonExporter.export_motion_data(motion_data, args.output_json)
        
        print(f"Successfully exported motion data to {args.output_json}")
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())

