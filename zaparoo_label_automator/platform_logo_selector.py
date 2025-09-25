"""
Platform logo selector module for selecting the best platform logo based on release date and region preferences.
"""


class PlatformLogoSelector:
    """Handles selection of the best platform logo based on release date and region preferences."""
    
    @staticmethod
    def select_best_platform_logo(platform_info):
        """
        Select the best platform logo based on release date and region preferences.
        
        Args:
            platform_info (dict): Platform information from JSON
            
        Returns:
            dict or None: Best platform logo object, or None if no logo found
        """
        versions = platform_info.get('versions', [])
        if not versions:
            return None
        
        # Collect all versions that have platform logos
        logo_candidates = []
        fallback_logos = []  # For versions without release dates
        
        for version in versions:
            platform_logo = version.get('platform_logo')
            if not platform_logo or not platform_logo.get('image_id'):
                continue
            
            # Get release dates for this version
            release_dates = version.get('platform_version_release_dates', [])
            
            if release_dates:
                # Process versions with release dates
                for release_date in release_dates:
                    # Date should already be processed by automator
                    date_value = release_date.get('date')
                    region = release_date.get('release_region', {}).get('region', '').lower()
                    
                    logo_candidates.append({
                        'platform_logo': platform_logo,
                        'date': date_value,
                        'region': region,
                        'version_name': version.get('name', 'unknown')
                    })
            else:
                # Collect versions without release dates as fallback
                fallback_logos.append({
                    'platform_logo': platform_logo,
                    'date': None,
                    'region': 'unknown',
                    'version_name': version.get('name', 'unknown')
                })
        
        # If we have candidates with release dates, use the existing logic
        if logo_candidates:
            # First preference: earliest Europe release
            europe_releases = [c for c in logo_candidates if c['region'] == 'europe']
            if europe_releases:
                # Sort by date (string format YYYY-MM-DD works for sorting)
                europe_releases.sort(key=lambda x: x['date'] or '9999-12-31')
                selected = europe_releases[0]
                return selected['platform_logo']
            
            # Second preference: earliest Japan release
            japan_releases = [c for c in logo_candidates if c['region'] == 'japan']
            if japan_releases:
                # Sort by date (string format YYYY-MM-DD works for sorting)
                japan_releases.sort(key=lambda x: x['date'] or '9999-12-31')
                selected = japan_releases[0]
                return selected['platform_logo']
            
            # Third preference: earliest release overall
            logo_candidates.sort(key=lambda x: x['date'] or '9999-12-31')
            selected = logo_candidates[0]
            return selected['platform_logo']
        
        # If no candidates with release dates, use fallback logos (versions without dates)
        if fallback_logos:
            # Just return the first available logo
            return fallback_logos[0]['platform_logo']
        
        # No logo found at all
        return None
    
    @staticmethod
    def find_platform_logo_path(platform_info, platform_folder):
        """
        Find the best platform logo file path using selection logic.
        
        Args:
            platform_info (dict): Platform information from JSON
            platform_folder (Path): Platform folder path
            
        Returns:
            Path or None: Path to platform logo file
        """
        # Use the selection logic to find the best logo
        best_logo = PlatformLogoSelector.select_best_platform_logo(platform_info)
        
        if best_logo and best_logo.get('local_file_path'):
            logo_path = platform_folder / best_logo['local_file_path']
            if logo_path.exists():
                return logo_path
        
        # Fallback: look for any webp file in platform folder that might be logo
        for file_path in platform_folder.glob('*platform_logo*.webp'):
            return file_path
        
        return None
    
    @staticmethod
    def sort_versions_chronologically(versions):
        """
        Sort platform versions in chronological order based on earliest release date.
        
        Args:
            versions (list): List of platform version objects
            
        Returns:
            list: Sorted list of platform versions
        """
        def get_earliest_date(version):
            """Get the earliest release date for a version."""
            release_dates = version.get('platform_version_release_dates', [])
            if not release_dates:
                return '9999-12-31'  # Put versions without dates at the end
            
            dates = [rd.get('date', '9999-12-31') for rd in release_dates]
            return min(dates)
        
        return sorted(versions, key=get_earliest_date)