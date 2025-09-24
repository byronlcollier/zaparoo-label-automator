import sys
from zaparoo_label_automator.automator import ZaparooAutomator
from zaparoo_label_automator.label_generator import LabelGenerator

# Configuration variables
UPPER_BATCH_LIMIT = 500
PLATFORMS_FILE = "user_files/platforms.csv"
GAMES_COUNT = 20
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

def main():
    print("Starting Zaparoo Label Automator...")
    
    # Initialize components
    automator = ZaparooAutomator(
        platforms_file=PLATFORMS_FILE,
        games_count=GAMES_COUNT,
        output_folder=OUTPUT_FOLDER,
        config_path=CONFIG_PATH,
        upper_batch_limit=UPPER_BATCH_LIMIT,
        media_download_config=MEDIA_DOWNLOAD_CONFIG
    )
    automator.run()

    label_output_folder = OUTPUT_FOLDER + "/labels"
    
    print("Data collection complete! Generating labels...")
    
    # Generate labels for all platforms
    label_generator = LabelGenerator(template_path=SVG_TEMPLATE_PATH, dpi=LABEL_DPI, output_formats=LABEL_OUTPUT_FORMATS)
    
    from pathlib import Path
    output_path = Path(OUTPUT_FOLDER)
    label_output_path = Path(label_output_folder)
    
    for platform_folder in output_path.iterdir():
        if platform_folder.is_dir():
            try:
                label_generator.generate_labels_for_platform(platform_folder, label_output_path)
            except Exception as e:
                print(f"Error generating labels for {platform_folder.name}: {str(e)}")
    
    print("Label generation complete!")
    print("Automation complete!")


if __name__ == "__main__":
    sys.exit(main())