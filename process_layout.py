
import os
import sys
import argparse
from pathlib import Path
from layout_model import LayoutProcessor, process_files, save_cropped_regions
from PIL import Image
import logging
import traceback
import json
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('layout_processing.log')
    ]
)
logger = logging.getLogger(__name__)

def get_files_interactive():
    """Get file paths from user input."""
    print("\nPlease enter the paths of the files to process:")
    print("1. Supported formats: PDF, PNG, JPG, JPEG, TIFF, BMP")
    print("2. You can paste multiple paths (one per line)")
    print("3. Press Enter twice when done\n")
    
    file_paths = []
    supported_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
    
    # Get initial input
    print("Paste your file paths below (press Enter twice when done):")
    lines = []
    while True:
        line = input().strip()
        if not line:
            break
        lines.append(line)
    
    # Process all pasted paths
    for path in lines:
        # Handle directory paths
        if os.path.isdir(path):
            print(f"\nProcessing directory: {path}")
            for ext in supported_extensions:
                for file in Path(path).glob(f"*{ext}"):
                    if file.is_file():
                        file_paths.append(file)
                        print(f"Added: {file}")
        # Handle single file paths
        else:
            file_path = Path(path)
            if not file_path.exists():
                print(f"Warning: File does not exist: {path}")
                continue
                
            if file_path.suffix.lower() not in supported_extensions:
                print(f"Warning: Unsupported file type: {file_path.suffix}")
                print("Supported types: PDF, PNG, JPG, JPEG, TIFF, BMP")
                continue
                
            file_paths.append(file_path)
            print(f"Added: {file_path}")
    
    if not file_paths:
        print("\nNo valid files found. Please try again.")
        return get_files_interactive()
    
    print(f"\nFound {len(file_paths)} valid files to process:")
    for i, path in enumerate(file_paths, 1):
        print(f"{i}. {path}")
    
    return file_paths

def get_output_directory():
    """Get output directory from user input."""
    print("\nPlease enter the output directory path:")
    print("1. Choose where to save the processed files")
    print("2. Press Enter to use default directory")
    print("3. You can paste the full path\n")
    
    while True:
        output_dir = input("Enter output directory path (or press Enter for default): ").strip()
        if not output_dir:
            return None
            
        dir_path = Path(output_dir)
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {dir_path}")
                return dir_path
            except Exception as e:
                print(f"Error creating directory: {e}")
                print("Please try again or press Enter for default directory")
                continue
        return dir_path

def process_single_file(file_path, processor, args):
    """Process a single file and return the results."""
    try:
        logger.info(f"Processing file: {file_path}")
        
        # Convert Path to string for process_files
        file_path_str = str(file_path)
        
        # Process the file
        images, updated_processor = process_files([file_path_str], dpi=args.dpi, processor=processor)
        processor = updated_processor
        
        if not hasattr(processor, 'regions_by_page') or not processor.regions_by_page:
            logger.error(f"No regions detected in {file_path}")
            return None, processor
        
        # Process each page
        results = []
        for i, (image, regions) in enumerate(zip(images, processor.regions_by_page)):
            page_result = {
                'page_number': i + 1,
                'file_name': file_path.name,
                'regions_with_captions': []
            }
            
            # Filter regions if specified
            if args.region_types:
                regions = [r for r in regions if r['label'].lower() in args.region_types]
            
            # Process each region
            for region in regions:
                # Only include regions that have captions
                if 'caption' in region and region['caption']:
                    region_info = {
                        'region_number': region['number'],
                        'region_type': region['label'],
                        'caption': {
                            'text': region['caption'],
                            'type': region.get('caption_type', 'unknown'),
                            'is_valid': region.get('caption_valid', True)
                        }
                    }
                    
                    # Add position information if needed
                    if 'position' in region:
                        region_info['position'] = region['position']
                    
                    page_result['regions_with_captions'].append(region_info)
            
            # Only add page if it has regions with captions
            if page_result['regions_with_captions']:
                results.append(page_result)
            
            # Save cropped regions if not skipped
            if not args.skip_cropping:
                try:
                    save_cropped_regions(image, regions, processor)
                    logger.info(f"Saved cropped regions for page {i + 1}")
                except Exception as e:
                    logger.error(f"Error saving cropped regions for page {i + 1}: {str(e)}")
        
        return results, processor
    
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        logger.error(traceback.format_exc())
        return None, processor

def interactive_mode():
    """Run the script in interactive mode."""
    print("\n=== Layout Analysis Tool ===")
    print("This tool will help you process images and PDFs to detect regions and captions.")
    
    # Get processing options
    print("\nProcessing Options:")
    print("1. Process all region types")
    print("2. Process specific region types")
    choice = input("Enter your choice (1/2): ").strip()
    
    region_types = None
    if choice == "2":
        print("\nAvailable region types: table, figure, image, map, text")
        types = input("Enter region types (comma-separated): ").strip()
        region_types = [t.strip().lower() for t in types.split(",")]
    
    # Get output format
    print("\nOutput Format:")
    print("1. Text (default)")
    print("2. JSON")
    format_choice = input("Enter your choice (1/2): ").strip()
    output_format = "json" if format_choice == "2" else "text"
    
    # Get files to process
    file_paths = get_files_interactive()
    if not file_paths:
        print("No files selected. Exiting...")
        return
    
    # Get output directory
    output_dir = get_output_directory()
    
    # Create args object
    class Args:
        def __init__(self):
            self.dpi = 200
            self.verbose = True
            self.format = output_format
            self.region_types = region_types
            self.caption_threshold = 0.8
            self.skip_cropping = False
            self.output_file = None
    
    args = Args()
    
    # Initialize processor
    processor = LayoutProcessor()
    if output_dir:
        processor.base_output_dir = output_dir
        processor.setup_output_directories()
    
    # Process files
    print(f"\nProcessing {len(file_paths)} files...")
    all_results = []
    total_pages = 0
    successful_pages = 0
    failed_pages = 0
    
    for file_path in file_paths:
        results, processor = process_single_file(file_path, processor, args)
        if results:
            all_results.extend(results)
            successful_pages += len(results)
        else:
            failed_pages += 1
        total_pages += 1
    
    # Prepare and display results
    output_data = {
        'summary': {
            'total_files': len(file_paths),
            'total_pages': total_pages,
            'successful_pages': successful_pages,
            'failed_pages': failed_pages,
            'timestamp': datetime.now().isoformat()
        },
        'results': all_results
    }
    
    if hasattr(processor, 'statistics'):
        # Only include relevant statistics
        stats = processor.statistics
        output_data['statistics'] = {
            'total_regions_with_captions': sum(len(page['regions_with_captions']) for page in all_results),
            'captions_by_type': stats.get('captions_by_type', {}),
            'valid_captions': sum(1 for page in all_results 
                                for region in page['regions_with_captions'] 
                                if region['caption']['is_valid'])
        }
    
    # Save or print output
    if args.format == 'json':
        output_file = output_dir / 'results.json' if output_dir else 'results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        print(f"\nResults saved to: {output_file}")
    else:
        print("\nProcessing Complete!")
        print("-" * 50)
        print(f"Total files processed: {output_data['summary']['total_files']}")
        print(f"Total pages processed: {output_data['summary']['total_pages']}")
        print(f"Successfully processed pages: {output_data['summary']['successful_pages']}")
        print(f"Failed pages: {output_data['summary']['failed_pages']}")
        
        if 'statistics' in output_data:
            print("\nOverall Statistics:")
            print(f"  Total Regions with Captions: {output_data['statistics']['total_regions_with_captions']}")
            print(f"  Valid Captions: {output_data['statistics']['valid_captions']}")
            print("\nCaptions by Type:")
            for caption_type, count in output_data['statistics']['captions_by_type'].items():
                print(f"  {caption_type}: {count}")
    
    print("\nPress Enter to exit...")
    input()

def main():
    try:
        parser = argparse.ArgumentParser(description='Process images and generate layout metadata')
        
        # Add interactive mode argument
        parser.add_argument('--interactive', '-i', action='store_true',
                          help='Run in interactive mode with file selection dialog')
        
        # Required arguments (only if not in interactive mode)
        parser.add_argument('input_path', nargs='?', help='Path to input image, PDF, or directory of files')
        
        # Optional arguments
        parser.add_argument('--output-dir', help='Custom output directory for results')
        parser.add_argument('--recursive', action='store_true', help='Process directories recursively')
        parser.add_argument('--dpi', type=int, default=200, help='DPI for rendering PDF pages')
        
        # Processing options
        parser.add_argument('--verbose', '-v', action='store_true', 
                          help='Enable verbose output with detailed processing information')
        parser.add_argument('--format', choices=['json', 'text'], default='text',
                          help='Output format for results (json or text)')
        parser.add_argument('--region-types', nargs='+', 
                          choices=['table', 'figure', 'image', 'map', 'text'],
                          help='Filter to process only specific region types')
        parser.add_argument('--caption-threshold', type=float, default=0.8,
                          help='Confidence threshold for caption validation (0.0 to 1.0)')
        parser.add_argument('--metadata-path', 
                          help='Custom path for saving the main metadata file')
        parser.add_argument('--skip-cropping', action='store_true',
                          help='Skip saving cropped regions, only generate metadata')
        parser.add_argument('--output-file',
                          help='Path to save the output JSON (if format is json)')
        
        args = parser.parse_args()
        
        # Check if interactive mode is requested
        if args.interactive or not args.input_path:
            interactive_mode()
            return
        
        # Set logging level based on verbose flag
        if args.verbose:
            logger.setLevel(logging.DEBUG)
            logger.debug("Verbose mode enabled")
        
        input_path = Path(args.input_path)
        
        if not input_path.exists():
            logger.error(f"Input path does not exist: {input_path}")
            sys.exit(1)
        
        # Create a list of files to process
        file_paths = []
        if input_path.is_file():
            file_paths.append(input_path)
        elif input_path.is_dir():
            # Include PDF and image extensions
            file_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
            if args.recursive:
                file_paths = [f for f in input_path.rglob('*') 
                              if f.is_file() and f.suffix.lower() in file_extensions]
            else:
                file_paths = [f for f in input_path.glob('*') 
                              if f.is_file() and f.suffix.lower() in file_extensions]
        
        if not file_paths:
            logger.error(f"No supported files found in {input_path}")
            sys.exit(1)

        # Initialize LayoutProcessor
        processor = LayoutProcessor()

        # Set custom output directory if provided
        if args.output_dir:
            processor.base_output_dir = Path(args.output_dir)
            processor.setup_output_directories()

        # Set custom metadata path if provided
        if args.metadata_path:
            processor.metadata_file = Path(args.metadata_path)

        # Set caption validation threshold
        processor.caption_threshold = args.caption_threshold

        logger.info(f"Starting processing for {len(file_paths)} files...")
        if args.region_types:
            logger.info(f"Filtering for region types: {', '.join(args.region_types)}")

        # Process all files
        all_results = []
        total_pages = 0
        successful_pages = 0
        failed_pages = 0

        for file_path in file_paths:
            results, processor = process_single_file(file_path, processor, args)
            if results:
                all_results.extend(results)
                successful_pages += len(results)
            else:
                failed_pages += 1
            total_pages += 1

        # Prepare output data
        output_data = {
            'summary': {
                'total_files': len(file_paths),
                'total_pages': total_pages,
                'successful_pages': successful_pages,
                'failed_pages': failed_pages,
                'timestamp': datetime.now().isoformat()
            },
            'results': all_results
        }

        if hasattr(processor, 'statistics'):
            output_data['statistics'] = processor.statistics

        # Save or print output based on format
        if args.format == 'json':
            if args.output_file:
                with open(args.output_file, 'w') as f:
                    json.dump(output_data, f, indent=4)
                logger.info(f"Results saved to {args.output_file}")
            else:
                print(json.dumps(output_data, indent=4))
        else:
            print("\nProcessing Complete!")
            print("-" * 50)
            print(f"Total files processed: {output_data['summary']['total_files']}")
            print(f"Total pages processed: {output_data['summary']['total_pages']}")
            print(f"Successfully processed pages: {output_data['summary']['successful_pages']}")
            print(f"Failed pages: {output_data['summary']['failed_pages']}")
            
            if 'statistics' in output_data:
                print("\nOverall Statistics:")
                print(f"  Total Regions: {output_data['statistics'].get('total_regions', 0)}")
                print(f"  Regions by Type: {output_data['statistics'].get('regions_by_type', {})}")
                print(f"  Captions by Type: {output_data['statistics'].get('captions_by_type', {})}")

        sys.exit(0 if failed_pages == 0 else 1)

    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 