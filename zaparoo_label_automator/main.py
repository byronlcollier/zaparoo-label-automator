from pathlib import Path
import sys
import argparse
from zaparoo_label_automator.automator import ZaparooAutomator
from zaparoo_label_automator.label_generator import LabelGenerator
from zaparoo_label_automator.catalogue_generator import CatalogueGenerator

# Configuration variables
UPPER_BATCH_LIMIT = 500
PLATFORMS_FILE = "user_files/platforms.csv"
GAMES_COUNT = 50
OUTPUT_FOLDER = "output"
CONFIG_PATH = "./.config"
LABEL_DPI = 300  # DPI for PNG and PDF label generation
SVG_TEMPLATE_PATH = "user_files/fossHuCardLabel.svg"  # SVG template for label generation
LABEL_OUTPUT_FORMATS = ["png"] # allowed values are currently either "png", "pdf", or both

MEDIA_DOWNLOAD_CONFIG = {
    "cover": True,
    "platform_logo": True,
    "screenshot": False,
    "game_video": False # Only for future use, not currently implemented.
}

def parse_arguments():
    """Parse command line arguments to control which phases execute."""
    parser = argparse.ArgumentParser(
        description="Zaparoo Label Automator - Generate game labels and catalogues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Phase Control:
  By default, all phases run in sequence: gather → labels → catalogues
  Use phase flags to run specific phases only:
  
  --gather-only     Run information gathering phase only
  --labels-only     Run label creation phase only  
  --catalogues-only Run catalogue creation phase only
  
  Or combine phases:
  --gather --labels    Run gathering and label creation
  --labels --catalogues Run label and catalogue creation
        """
    )
    
    # Phase control arguments
    parser.add_argument('--gather', action='store_true', 
                       help='Run information gathering phase (collect game data from IGDB)')
    parser.add_argument('--labels', action='store_true',
                       help='Run label creation phase (generate PNG/PDF labels)')
    parser.add_argument('--catalogues', action='store_true', 
                       help='Run catalogue creation phase (generate PDF catalogues)')
    
    # Convenience flags for single phases
    parser.add_argument('--gather-only', action='store_true',
                       help='Run information gathering phase only')
    parser.add_argument('--labels-only', action='store_true', 
                       help='Run label creation phase only')
    parser.add_argument('--catalogues-only', action='store_true',
                       help='Run catalogue creation phase only')
    
    return parser.parse_args()


def run_information_gathering():
    """Run the information gathering phase."""
    print("Starting information gathering phase...")
    
    automator = ZaparooAutomator(
        platforms_file=PLATFORMS_FILE,
        games_count=GAMES_COUNT,
        output_folder=OUTPUT_FOLDER,
        config_path=CONFIG_PATH,
        upper_batch_limit=UPPER_BATCH_LIMIT,
        media_download_config=MEDIA_DOWNLOAD_CONFIG
    )
    automator.run()
    
    print("Information gathering complete!")


def run_label_creation():
    """Run the label creation phase."""
    print("Starting label creation phase...")
    
    output_path = Path(OUTPUT_FOLDER)
    detail_path = output_path / "detail"
    labels_path = output_path / "labels"
    
    if not detail_path.exists():
        print(f"Error: Detail path '{detail_path}' does not exist. Run information gathering phase first.")
        return False
    
    # Create labels folder if it doesn't exist
    labels_path.mkdir(parents=True, exist_ok=True)
    
    label_generator = LabelGenerator(
        template_path=SVG_TEMPLATE_PATH,
        dpi=LABEL_DPI,
        output_formats=LABEL_OUTPUT_FORMATS,
    )
    
    for platform_folder in detail_path.iterdir():
        if platform_folder.is_dir():
            try:
                label_generator.generate_labels_for_platform(platform_folder, labels_path)
            except Exception as e:
                print(f"Error generating labels for {platform_folder.name}: {str(e)}")
    
    print("Label creation complete!")
    return True


def run_catalogue_creation():
    """Run the catalogue creation phase."""
    print("Starting catalogue creation phase...")
    
    output_path = Path(OUTPUT_FOLDER)
    detail_path = output_path / "detail"
    catalogue_path = output_path / "catalogue"
    
    if not detail_path.exists():
        print(f"Error: Detail path '{detail_path}' does not exist. Run information gathering phase first.")
        return False
    
    # Create catalogue folder if it doesn't exist
    catalogue_path.mkdir(parents=True, exist_ok=True)
    
    catalogue_generator = CatalogueGenerator()
    catalogues_generated = catalogue_generator.generate_catalogues_for_all_platforms(detail_path, catalogue_path)
    print(f"Generated {catalogues_generated} catalogues")
    
    print("Catalogue creation complete!")
    return True


def main():
    args = parse_arguments()
    
    # Determine which phases to run
    run_gather = args.gather or args.gather_only
    run_labels = args.labels or args.labels_only  
    run_catalogues = args.catalogues or args.catalogues_only
    
    # If no phase flags specified, run all phases (default behavior)
    if not any([args.gather, args.labels, args.catalogues, 
                args.gather_only, args.labels_only, args.catalogues_only]):
        run_gather = run_labels = run_catalogues = True
    
    print("Starting Zaparoo Label Automator...")
    
    # Execute selected phases in order
    if run_gather:
        run_information_gathering()
    
    if run_labels:
        if not run_label_creation():
            return 1
    
    if run_catalogues:
        if not run_catalogue_creation():
            return 1
    
    print("Automation complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
