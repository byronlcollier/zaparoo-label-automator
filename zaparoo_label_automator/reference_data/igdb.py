"""
IGDB Reference Data Collector

This module orchestrates the collection of reference data from the IGDB API.
Reference data includes platforms, platform types, logos, and other lookup/metadata
that serves as a foundation for user-specific data collection operations.
"""

import json
import os
import re
from typing import List, Dict, Any, Set, cast, Literal
from datetime import datetime

from zaparoo_label_automator.wrapper.twitch import TokenManager
from zaparoo_label_automator.wrapper.generic import GenericRestAPI
from zaparoo_label_automator.reference_data.endpoint_config import ConfigManager

class DataCollector:
    """
    Main orchestrator for collecting reference data from the IGDB API.

    Reference data includes platforms, platform types, logos, families, and other
    metadata that serves as lookup information for user-specific operations.

    This class coordinates:
    - Loading reference endpoint configurations
    - Querying APIs with proper batching
    - Collecting and deduplicating reference data
    - Managing reference data output files
    """

    def __init__(
        self,
        config_path: str,
        endpoints_file: str,
        output_dir: str,
        batch_limit: int,
    ):
        """
        Initialize the IGDB reference data collector.

        Args:
            config_path: Path to authentication configuration
            endpoints_file: Path to reference endpoints configuration file
            output_dir: Directory for reference data output files
            batch_limit: Maximum records per API batch
        """
        self._config_path = config_path
        self._endpoints_file = endpoints_file
        self._output_dir = output_dir
        self._batch_limit = batch_limit

        # Initialize components
        self._token_manager = TokenManager(config_path=config_path)
        self._token_manager.initialise_token()
        self._api_client = GenericRestAPI()
        self._config_manager = ConfigManager(config_file_path=endpoints_file)

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Track collected data and statistics
        self._collection_stats = {}

    def collect_all_reference_data(self) -> Dict[str, Any]:
        """
        Collect reference data from all configured endpoints.

        Returns:
            Dictionary containing collection statistics and results
        """
        print("Starting IGDB reference data collection...")

        # Load endpoint configurations
        endpoints = self._config_manager.load_endpoints(self._batch_limit)

        print(f"Loaded {len(endpoints)} endpoint configurations")

        collection_results = {}
        overall_stats = {
            'start_time': datetime.now().isoformat(),
            'endpoints_processed': 0,
            'total_records_collected': 0,
            'successful_endpoints': [],
            'failed_endpoints': [],
            'warnings': []
        }

        # Process each endpoint
        for endpoint_config in endpoints:
            endpoint_name = endpoint_config.get('name')

            try:
                print(f"\nProcessing endpoint: {endpoint_name}")

                # Validate endpoint configuration
                if not self._config_manager.validate_endpoint_config(endpoint_config):
                    warning_msg = f"Invalid configuration for endpoint '{endpoint_name}', skipping"
                    print(f"WARNING: {warning_msg}")
                    overall_stats['warnings'].append(warning_msg)
                    continue

                # Collect data for this endpoint
                endpoint_data, endpoint_stats = self._collect_endpoint_data(endpoint_config)

                # Store results
                collection_results[endpoint_name] = {
                    'data': endpoint_data,
                    'stats': endpoint_stats
                }

                # Update overall stats
                overall_stats['endpoints_processed'] += 1
                overall_stats['total_records_collected'] += endpoint_stats.get('total_records', 0)
                overall_stats['successful_endpoints'].append(endpoint_name)

                print(f"✓ Collected {endpoint_stats.get('total_records', 0)} records from {endpoint_name}")

            except (ValueError, KeyError, ConnectionError) as e:
                error_msg = f"Failed to process endpoint '{endpoint_name}': {str(e)}"
                print(f"ERROR: {error_msg}")
                overall_stats['failed_endpoints'].append({
                    'endpoint': endpoint_name,
                    'error': str(e)
                })

        overall_stats['end_time'] = datetime.now().isoformat()

        print("\nReference data collection completed!")
        print(f"Processed: {overall_stats['endpoints_processed']} endpoints")
        print(f"Total reference records: {overall_stats['total_records_collected']}")
        print(f"Successful: {len(overall_stats['successful_endpoints'])}")
        print(f"Failed: {len(overall_stats['failed_endpoints'])}")

        # Save results to output files
        self._save_results_to_files(collection_results, overall_stats)

        return {
            'results': collection_results,
            'stats': overall_stats
        }

    def _collect_endpoint_data(self, endpoint_config: Dict[str, Any]) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Collect data from a single endpoint.

        Args:
            endpoint_config: Configuration for the endpoint

        Returns:
            Tuple of (collected_data, collection_stats)
        """
        endpoint_name = endpoint_config['name']
        properties = endpoint_config['properties']

        # Extract endpoint properties directly from configuration
        body_template = properties['body']

        stats = {
            'endpoint_name': endpoint_name,
            'endpoint_url': properties['endpoint_url'],
            'batches_required': 0,
            'total_records': 0,
            'start_time': datetime.now().isoformat()
        }

        try:
            # Use batching functionality with URLs from configuration
            collected_data, batches_used = self._query_with_batching(
                endpoint_config=properties,
                body_template=body_template,
                batch_limit=self._batch_limit
            )

            # Deduplicate records based on ID
            deduplicated_data = self._deduplicate_records(collected_data)

            stats.update({
                'batches_required': batches_used,
                'total_records': len(deduplicated_data),
                'duplicates_removed': len(collected_data) - len(deduplicated_data),
                'end_time': datetime.now().isoformat()
            })

            return deduplicated_data, stats

        except Exception as e:
            stats.update({
                'error': str(e),
                'end_time': datetime.now().isoformat()
            })
            raise

    def _deduplicate_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate records based on their ID field.

        Args:
            records: List of records to deduplicate

        Returns:
            List of deduplicated records
        """
        if not records:
            return records

        seen_ids: Set[int] = set()
        deduplicated = []

        for record in records:
            record_id = record.get('id')
            if record_id is not None and record_id not in seen_ids:
                seen_ids.add(record_id)
                deduplicated.append(record)
            elif record_id is None:
                # Keep records without IDs (shouldn't happen with IGDB but safety first)
                deduplicated.append(record)

        return deduplicated

    def _get_headers(self) -> Dict[str, str]:
        """
        Get the required headers for IGDB API requests.

        Returns:
            Dictionary containing required headers
        """
        return self._token_manager.get_header()

    def _query_count(self, count_endpoint_url: str, body: str = "") -> int:
        """
        Query the count endpoint to determine how many records are available.

        Args:
            count_endpoint_url: The full count endpoint URL
            body: Optional query body for filtering

        Returns:
            Number of records available

        Raises:
            Exception: If the API request fails
        """
        headers = self._get_headers()

        try:
            response = self._api_client.request(
                method="POST",
                url=count_endpoint_url,
                headers=headers,
                body=body
            )

            # The count endpoint returns a dictionary with a 'count' key
            if isinstance(response, dict) and 'count' in response:
                return response['count']
            if isinstance(response, list) and len(response) > 0 and 'count' in response[0]:
                return response[0]['count']
            raise ValueError(f"Unexpected response format from count endpoint: {response}")

        except (ValueError, KeyError, ConnectionError) as e:
            raise ValueError(f"Failed to query count for endpoint {count_endpoint_url}: {str(e)}") from e

    def _query_data(
        self,
        endpoint_url: str,
        body: str,
        http_method: str = "POST"
    ) -> List[Dict[str, Any]]:
        """
        Query the IGDB API for data.

        Args:
            endpoint_url: The full API endpoint URL
            body: The query body (in IGDB's Apicalypse format)
            http_method: HTTP method to use (default: POST)

        Returns:
            List of records returned by the API

        Raises:
            Exception: If the API request fails
        """
        headers = self._get_headers()

        try:
            # Type cast to ensure compatibility with GenericRestAPI
            method_literal = cast(Literal['GET', 'POST', 'PUT', 'DELETE', 'PATCH'], http_method)
            response = self._api_client.request(
                method=method_literal,
                url=endpoint_url,
                headers=headers,
                body=body
            )

            # Ensure we always return a list
            if isinstance(response, list):
                return response
            if isinstance(response, dict):
                return [response]
            return []

        except (ValueError, KeyError, ConnectionError) as e:
            raise ValueError(f"Failed to query endpoint {endpoint_url}: {str(e)}") from e

    def _query_with_batching(
        self,
        endpoint_config: Dict[str, str],
        body_template: str,
        batch_limit: int
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Query an endpoint with automatic batching if needed.

        This method:
        1. Queries the count endpoint to determine total records
        2. If total > batch_limit, performs batched queries with offset
        3. Returns all collected records and batch count

        Args:
            endpoint_url: The full API endpoint URL
            count_endpoint_url: The full count endpoint URL
            body_template: The query body template with limit placeholder
            batch_limit: Maximum records per batch
            http_method: HTTP method to use

        Returns:
            Tuple of (all_records, batches_used)
        """
        # Extract values from endpoint config
        endpoint_url = endpoint_config['endpoint_url']
        count_endpoint_url = endpoint_config['count_endpoint_url']
        http_method = endpoint_config.get('http_method', 'POST')

        # First, get the total count
        total_count = self._query_count(count_endpoint_url)

        if total_count == 0:
            return [], 0

        all_records = []
        batches_used = 0

        if total_count <= batch_limit:
            # No batching needed - single request
            # The body already has the limit appended by ConfigManager
            records = self._query_data(endpoint_url, body_template, http_method)
            all_records.extend(records)
            batches_used = 1
        else:
            # Batching needed
            offset = 0

            while offset < total_count:
                # Calculate limit for this batch
                remaining = total_count - offset
                current_limit = min(batch_limit, remaining)

                # Replace the existing limit with the calculated current_limit
                # Look for the limit statement that was appended by ConfigManager
                body = self._replace_limit_in_body(body_template, current_limit)

                # Add offset after the limit statement
                if f"limit {current_limit};" in body:
                    body = body.replace(
                        f"limit {current_limit};",
                        f"limit {current_limit}; offset {offset};"
                    )
                else:
                    # Fallback: append offset at the end
                    body = f"{body.rstrip(';')}; offset {offset};"

                # Query this batch
                batch_records = self._query_data(endpoint_url, body, http_method)
                all_records.extend(batch_records)
                batches_used += 1

                # Move to next batch
                offset += current_limit

                # Safety check to prevent infinite loops
                if len(batch_records) == 0:
                    print(f"Warning: No records returned for offset {offset}, stopping batching")
                    break

        return all_records, batches_used

    def _replace_limit_in_body(self, body: str, new_limit: int) -> str:
        """
        Replace the existing limit statement in a query body with a new limit value.

        Args:
            body: The query body with an existing limit statement
            new_limit: The new limit value to use

        Returns:
            Body with the limit value replaced
        """        # Use regex to find and replace the limit statement
        # Pattern matches "limit" followed by whitespace and a number, followed by semicolon
        pattern = r'limit\s+\d+;'
        replacement = f'limit {new_limit};'

        # Replace the limit statement
        modified_body = re.sub(pattern, replacement, body, count=1)

        return modified_body

    def _save_results_to_files(
        self,
        collection_results: Dict[str, Any],
        overall_stats: Dict[str, Any]
    ) -> None:
        """
        Save collection results to JSON files in the output directory.

        Args:
            collection_results: Dictionary of endpoint results
            overall_stats: Overall collection statistics
        """
        print(f"\nSaving results to {self._output_dir}/...")

        # Save individual endpoint data files
        for endpoint_name, endpoint_result in collection_results.items():
            data = endpoint_result['data']

            if data:  # Only save if there's data
                filename = f"{endpoint_name}.json"
                filepath = os.path.join(self._output_dir, filename)

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                print(f"✓ Saved {len(data)} records to {filename}")

        # Save collection statistics
        stats_filename = "collection_stats.json"
        stats_filepath = os.path.join(self._output_dir, stats_filename)

        # Prepare comprehensive stats
        comprehensive_stats = {
            'overall': overall_stats,
            'endpoints': {}
        }

        for endpoint_name, endpoint_result in collection_results.items():
            comprehensive_stats['endpoints'][endpoint_name] = endpoint_result['stats']

        with open(stats_filepath, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_stats, f, indent=2, ensure_ascii=False)

        print(f"✓ Saved collection statistics to {stats_filename}")

        # Save summary report
        self._save_summary_report(overall_stats)

    def _save_summary_report(self, overall_stats: Dict[str, Any]) -> None:
        """
        Save a human-readable summary report.

        Args:
            overall_stats: Overall collection statistics
        """
        summary_filename = "collection_summary.txt"
        summary_filepath = os.path.join(self._output_dir, summary_filename)

        with open(summary_filepath, 'w', encoding='utf-8') as f:
            f.write("IGDB Reference Data Collection Summary\n")
            f.write("=" * 40 + "\n\n")

            f.write(f"Collection started: {overall_stats['start_time']}\n")
            f.write(f"Collection ended: {overall_stats['end_time']}\n\n")

            f.write(f"Endpoints processed: {overall_stats['endpoints_processed']}\n")
            f.write(f"Total records collected: {overall_stats['total_records_collected']}\n\n")

            f.write(f"Successful endpoints ({len(overall_stats['successful_endpoints'])}):\n")
            for endpoint in overall_stats['successful_endpoints']:
                f.write(f"  ✓ {endpoint}\n")

            if overall_stats['failed_endpoints']:
                f.write(f"\nFailed endpoints ({len(overall_stats['failed_endpoints'])}):\n")
                for failed in overall_stats['failed_endpoints']:
                    f.write(f"  ✗ {failed['endpoint']}: {failed['error']}\n")

            if overall_stats['warnings']:
                f.write(f"\nWarnings ({len(overall_stats['warnings'])}):\n")
                for warning in overall_stats['warnings']:
                    f.write(f"  ⚠ {warning}\n")


        print(f"✓ Saved summary report to {summary_filename}")
