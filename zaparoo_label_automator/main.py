from pathlib import Path
import sys
import argparse
from zaparoo_label_automator.igdb_scraper import IgdbScraper
from zaparoo_label_automator.label_generator import LabelGenerator
from zaparoo_label_automator.catalogue_generator import CatalogueGenerator

# Configuration variables
UPPER_BATCH_LIMIT = 500
PLATFORMS_FILE = "user_files/platforms.csv"
REFERENCE_GAMES_COUNT = 100
CATALOGUE_GAMES_COUNT = 20
OUTPUT_FOLDER = "output"
PATH_CONFIG = {
    "core_folder": Path(OUTPUT_FOLDER),
    "reference_data": Path(OUTPUT_FOLDER) / "reference_data",
    "labels_path": Path(OUTPUT_FOLDER) / "labels",
    "catalogue_path": Path(OUTPUT_FOLDER) / "catalogue",
}

CONFIG_PATH = "./.config"
IMAGE_CONFIG_PATH = "zaparoo_label_automator/image_config.json"
LABEL_DPI = 300  # DPI for PNG and PDF label generation
SVG_TEMPLATE_PATH = "user_files/fossHuCardLabel.svg"  # SVG template for label generation
LABEL_OUTPUT_FORMATS = ["pdf"] # allowed values are currently either "png", "pdf", or both

MEDIA_DOWNLOAD_CONFIG = {
    "cover": True,
    "platform_logo": True,
    "screenshot": True,
    "game_video": False # Only for future use, not currently implemented.
}

def parse_arguments():
    """Parse command line arguments to control which phases execute."""
    parser = argparse.ArgumentParser(
        description="Zaparoo Label Automator - Generate game labels and catalogues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Phase Control:
  By default, all phases run in sequence: gather → catalogues → labels
  Use phase flags to run specific phases only:
  
  --gather-only     Run information gathering phase only (collect reference data)
  --catalogues-only Run catalogue creation phase only (select games and generate JSON)
  --labels-only     Run label creation phase only (generate PNG/PDF labels)
  
  Or combine phases:
  --gather --catalogues    Run gathering and catalogue creation
  --catalogues --labels    Run catalogue and label creation
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
    
    scraper = IgdbScraper(
        platforms_file=PLATFORMS_FILE,
        games_count=REFERENCE_GAMES_COUNT,
        output_folder=PATH_CONFIG["reference_data"],
        config_path=CONFIG_PATH,
        image_config_path=IMAGE_CONFIG_PATH,
        upper_batch_limit=UPPER_BATCH_LIMIT,
        media_download_config=MEDIA_DOWNLOAD_CONFIG
    )
    scraper.run()
    
    print("Information gathering complete!")


def run_label_creation():
    """Run the label creation phase."""
    print("Starting label creation phase...")
    
    # Check for required dependencies
    if not PATH_CONFIG["reference_data"].exists():
        print(f"Error: Reference data path '{PATH_CONFIG["reference_data"]}' does not exist. Run information gathering phase first.")
        return False
    
    catalogue_json_path = PATH_CONFIG["catalogue_path"] / "game_selection_catalogue.json"
    if not catalogue_json_path.exists():
        print(f"Error: Catalogue JSON not found at '{catalogue_json_path}'. Run catalogue creation phase first.")
        return False
    
    # Create labels folder if it doesn't exist
    PATH_CONFIG["labels_path"].mkdir(parents=True, exist_ok=True)
    
    label_generator = LabelGenerator(
        template_path=SVG_TEMPLATE_PATH,
        dpi=LABEL_DPI,
        output_formats=LABEL_OUTPUT_FORMATS,
    )
    
    try:
        total_labels = label_generator.generate_labels_from_catalogue(
            catalogue_json_path=catalogue_json_path,
            reference_data_path=PATH_CONFIG["reference_data"],
            label_output_folder=PATH_CONFIG["labels_path"]
        )
        print(f"Label creation complete! Generated {total_labels} labels total.")
        return True
    except Exception as e:
        print(f"Error generating labels: {str(e)}")
        return False


def run_catalogue_creation():
    """Run the catalogue creation phase."""
    print("Starting catalogue creation phase...")
    
    if not PATH_CONFIG["reference_data"].exists():
        print(f"Error: Detail path '{PATH_CONFIG["reference_data"]}' does not exist. Run information gathering phase first.")
        return False
    
    # Create catalogue folder if it doesn't exist
    PATH_CONFIG["catalogue_path"].mkdir(parents=True, exist_ok=True)
    
    catalogue_generator = CatalogueGenerator(catalogue_games_count=CATALOGUE_GAMES_COUNT)
    platforms_processed = catalogue_generator.generate_catalogues_for_all_platforms(PATH_CONFIG["reference_data"], PATH_CONFIG["catalogue_path"])
    print(f"Processed {platforms_processed} platforms for catalogue selection")
    
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
    
    if run_catalogues:
        if not run_catalogue_creation():
            return 1
    
    if run_labels:
        if not run_label_creation():
            return 1
    
    print("Automation complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
