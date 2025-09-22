"""
Zaparoo Label Automator - IGDB Data Collection

This script collects data from the IGDB API for use in creating Zaparoo labels.
It processes all endpoints defined in the api_endpoints.json.j2 configuration file.
"""

import json
import sys
from zaparoo_label_automator.reference_data.igdb import DataCollector

# UPPER_BATCH_LIMIT = 500
UPPER_BATCH_LIMIT = 100


def main():
    """
    Main entry point for the IGDB data collection process.
    """
    try:
        print("Zaparoo Label Automator - IGDB Data Collection")
        print("=" * 55)

        # Initialize the IGDB reference data collector
        platform_collector = DataCollector(
            config_path="./.config",
            endpoints_file="./reference_data/igdb_platform_endpoints.json",
            output_dir="./output/reference_data/",
            batch_limit=UPPER_BATCH_LIMIT
        )

        # Collect all configured reference data
        results = platform_collector.collect_all_reference_data()

        # Display summary
        stats = results['stats']
        print("\n" + "=" * 55)
        print("COLLECTION COMPLETE")
        print("=" * 55)
        print(f"Endpoints processed: {stats['endpoints_processed']}")
        print(f"Total records collected: {stats['total_records_collected']}")
        print(f"Successful endpoints: {len(stats['successful_endpoints'])}")

        if stats['failed_endpoints']:
            print(f"Failed endpoints: {len(stats['failed_endpoints'])}")
            for failed in stats['failed_endpoints']:
                print(f"  ✗ {failed['endpoint']}: {failed['error']}")

        if stats['warnings']:
            print(f"Warnings: {len(stats['warnings'])}")

        print("\nResults saved to: output/")
        print("Check collection_summary.txt for detailed report.")

        return 0

    except KeyboardInterrupt:
        print("\n\nCollection interrupted by user.")
        return 1

    except (FileNotFoundError, ValueError, ConnectionError, json.JSONDecodeError) as e:
        print(f"\nERROR: {str(e)}")
        print("Check your configuration and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
