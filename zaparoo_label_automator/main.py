from pathlib import Path
import sys
import argparse
from zaparoo_label_automator.scrapers.platforms import PlatformScraper
from zaparoo_label_automator.igdb_scraper import IgdbScraper
from zaparoo_label_automator.label_generator import LabelGenerator
from zaparoo_label_automator.catalogue_generator import CatalogueGenerator
from zaparoo_label_automator.wrappers.igdb import IgdbAPI

CONFIG = {
    "upper_batch_limit": 500,
    "reference_games_count": 100,
    "catalogue_games_count": 20,
    "api_timeout": 60,
    "label_dpi": 300 , # DPI for PNG and PDF label generation
    "output_path_config": {
        "core_folder": Path("output"),
        "reference_data": Path("output") / "reference_data",
        "labels_path": Path("output") / "labels",
        "catalogue_path": Path("output") / "catalogue",
    },
    "secrets_path": ".config",
    "image_config_path": "zaparoo_label_automator/config/image_config.json",
    "game_endpoint_config_path": "zaparoo_label_automator/config/game_endpoint.json",
    "platform_endpoint_config_path": "zaparoo_label_automator/config/platform_endpoint.json",
    "media_download_config": {
        "cover": True,
        "platform_logo": True,
        "screenshot": True,
        "game_video": False # Only for future use, not currently implemented.
    },
    "svg_template_path": "user_files/fossHuCardLabel.svg" , # SVG template for label generation
    "platforms_file": "user_files/platforms.csv",
    "label_output_formats": ["pdf"] # allowed values are currently either "png", "pdf", or both
}

# # init token manager and api rest client
# # TODO: make other methods use this - no, maybe not, init this in the scrapers instead
# api_client = IgdbAPI(CONFIG["secrets_path"])


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
        platforms_file=CONFIG["platforms_file"],
        games_count=CONFIG["reference_games_count"],
        output_folder=CONFIG["output_config_path"]["reference_data"],
        # config_path=CONFIG["secrets_path"],
        image_config_path=CONFIG["image_config_path"],
        upper_batch_limit=CONFIG["upper_batch_limit"],
        media_download_config=CONFIG["media_download_config"],
        game_endpoint_config = CONFIG["game_endpoint_config_path"],
        platform_endpoint_config = CONFIG["platform_endpoint_config_path"]
    )
    scraper.run()
    
    print("Information gathering complete!")


def run_label_creation():
    """Run the label creation phase."""
    print("Starting label creation phase...")
    
    # Check for required dependencies
    if not CONFIG["output_config_path"]["reference_data"].exists():
        print(f"Error: Reference data path '{CONFIG["output_config_path"]["reference_data"]}' does not exist. Run information gathering phase first.")
        return False
    
    catalogue_json_path = CONFIG["output_config_path"]["catalogue_path"] / "game_selection_catalogue.json"
    if not catalogue_json_path.exists():
        print(f"Error: Catalogue JSON not found at '{catalogue_json_path}'. Run catalogue creation phase first.")
        return False
    
    # Create labels folder if it doesn't exist
    CONFIG["output_config_path"]["labels_path"].mkdir(parents=True, exist_ok=True)
    
    label_generator = LabelGenerator(
        template_path=CONFIG["svg_template_path"],
        dpi=CONFIG["label_dpi"],
        output_formats=CONFIG["label_output_formats"],
    )
    
    try:
        total_labels = label_generator.generate_labels_from_catalogue(
            catalogue_json_path=catalogue_json_path,
            reference_data_path=CONFIG["output_config_path"]["reference_data"],
            label_output_folder=CONFIG["output_config_path"]["labels_path"]
        )
        print(f"Label creation complete! Generated {total_labels} labels total.")
        return True
    except Exception as e:
        print(f"Error generating labels: {str(e)}")
        return False


def run_catalogue_creation():
    """Run the catalogue creation phase."""
    print("Starting catalogue creation phase...")
    
    if not CONFIG["output_config_path"]["reference_data"].exists():
        print(f"Error: Detail path '{CONFIG["output_config_path"]["reference_data"]}' does not exist. Run information gathering phase first.")
        return False
    
    # Create catalogue folder if it doesn't exist
    CONFIG["output_config_path"]["catalogue_path"].mkdir(parents=True, exist_ok=True)
    
    catalogue_generator = CatalogueGenerator(catalogue_games_count=CONFIG["catalogue_games_count"])
    platforms_processed = catalogue_generator.generate_catalogues_for_all_platforms(CONFIG["output_config_path"]["reference_data"], CONFIG["output_config_path"]["catalogue_path"])
    print(f"Processed {platforms_processed} platforms for catalogue selection")
    
    # Generate PDF catalogues from the JSON
    print("\nGenerating PDF catalogues...")
    catalogue_json_path = CONFIG["output_config_path"]["catalogue_path"] / "game_selection_catalogue.json"
    pdfs_generated = catalogue_generator.generate_pdf_catalogues_from_json(
        catalogue_json_path=catalogue_json_path,
        reference_data_folder=CONFIG["output_config_path"]["reference_data"],
        pdf_output_folder=CONFIG["output_config_path"]["catalogue_path"]
    )
    print(f"Generated {pdfs_generated} PDF catalogues")
    
    print("Catalogue creation complete!")
    return True


def main():
    args = parse_arguments()

    # TODO: DEBUG: temporarily disrupting program flow in order to test refactoring

    platform_scraper = PlatformScraper(
        output_folder=CONFIG['output_path_config']['core_folder'],
        upper_batch_limit=CONFIG['upper_batch_limit'],
        secrets_path=CONFIG['secrets_path'],
        endpoint_config_file=CONFIG['platform_endpoint_config_path'],
        platforms_file=CONFIG['platforms_file'],
        api_timeout=CONFIG['api_timeout']
    )

    platform_scraper.scrape()
    
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
