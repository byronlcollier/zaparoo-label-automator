import sys
from zaparoo_label_automator.automator import ZaparooAutomator

# Configuration variables
UPPER_BATCH_LIMIT = 500
PLATFORMS_FILE = "user_files/platforms.csv"
GAMES_COUNT = 20
OUTPUT_FOLDER = "output"
CONFIG_PATH = "./.config"

def main():
    print("Starting Zaparoo Label Automator...")
    
    # Initialize components
    automator = ZaparooAutomator(
        platforms_file=PLATFORMS_FILE,
        games_count=GAMES_COUNT,
        output_folder=OUTPUT_FOLDER,
        config_path=CONFIG_PATH,
        upper_batch_limit=UPPER_BATCH_LIMIT
    )
    automator.run()
    
    print("Automation complete!")


if __name__ == "__main__":
    sys.exit(main())