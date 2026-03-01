#!/usr/bin/env python3
"""
Download training data from SatNOGS network.
Fetches observations and converts them to training tiles.

Sovereignty: Full offline support.
  --offline    Use only locally cached data (no network)
  Default:     Try network, cache everything for offline use
"""

import requests
import json
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
import argparse
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Cache directories
SATNOGS_CACHE_DIR = PROJECT_ROOT / 'data' / 'satnogs_cache'
OBS_CACHE_DIR = SATNOGS_CACHE_DIR / 'observations'
SAT_CACHE_DIR = SATNOGS_CACHE_DIR / 'satellites'


class SatNOGSDataDownloader:
    def __init__(self, output_dir='models/training_data', offline=False):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.offline = offline

        self.api_base = "https://network.satnogs.org/api"
        self.session = requests.Session()

        # Ensure cache dirs exist
        OBS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        SAT_CACHE_DIR.mkdir(parents=True, exist_ok=True)

        if self.offline:
            logger.info("=" * 60)
            logger.info("OFFLINE MODE — Using cached SatNOGS data only")
            logger.info("=" * 60)

    def _cache_key(self, satellite_id=None, transmitter_mode=None, limit=100):
        """Generate a cache key for observation queries."""
        parts = ['obs']
        if satellite_id:
            parts.append(f'sat{satellite_id}')
        if transmitter_mode:
            parts.append(f'mode{transmitter_mode}')
        parts.append(f'limit{limit}')
        return '_'.join(parts) + '.json'

    def _save_obs_cache(self, cache_key, data):
        """Save observation data to cache."""
        cache_path = OBS_CACHE_DIR / cache_key
        try:
            with open(cache_path, 'w') as f:
                json.dump({
                    'cached_at': datetime.now(timezone.utc).isoformat(),
                    'results': data
                }, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to cache observations: {e}")

    def _load_obs_cache(self, cache_key):
        """Load observation data from cache."""
        cache_path = OBS_CACHE_DIR / cache_key
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    cached = json.load(f)
                results = cached.get('results', [])
                cached_at = cached.get('cached_at', 'unknown')
                logger.info(f"[CACHE] Loaded {len(results)} observations (cached {cached_at})")
                return results
            except Exception as e:
                logger.warning(f"Failed to read observation cache: {e}")
        return None

    def get_observations(self, satellite_id=None, transmitter_mode=None, limit=100):
        """Fetch observations from SatNOGS API or cache."""
        cache_key = self._cache_key(satellite_id, transmitter_mode, limit)

        # Offline mode: cache only
        if self.offline:
            cached = self._load_obs_cache(cache_key)
            if cached is not None:
                return cached
            logger.warning(f"[OFFLINE] No cached observations for query {cache_key}")
            return []

        # Online mode: try network, cache results, fall back to cache
        params = {
            'format': 'json',
            'limit': limit
        }
        if satellite_id:
            params['satellite__norad_cat_id'] = satellite_id
        if transmitter_mode:
            params['transmitter_mode'] = transmitter_mode

        url = f"{self.api_base}/observations/"
        logger.info(f"Fetching observations from {url}")

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            results = data.get('results', [])

            # Cache the results
            self._save_obs_cache(cache_key, results)
            return results

        except Exception as e:
            logger.warning(f"Network failed for observations: {e}")
            # Fall back to cache
            cached = self._load_obs_cache(cache_key)
            if cached is not None:
                logger.info("Using cached observations as fallback")
                return cached
            logger.error("No network and no cache for observations")
            return []

    def download_observation_data(self, observation_id, output_path):
        """Download I/Q data for an observation."""
        # Check if already downloaded
        if Path(output_path).exists():
            logger.info(f"Data for observation {observation_id} already exists locally")
            return True

        if self.offline:
            logger.info(f"[OFFLINE] Skipping download for observation {observation_id}")
            return False

        url = f"{self.api_base}/observations/{observation_id}/"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            obs_data = response.json()

            # Cache observation metadata
            meta_path = SAT_CACHE_DIR / f'obs_{observation_id}_meta.json'
            with open(meta_path, 'w') as f:
                json.dump(obs_data, f, indent=2, default=str)

            # Check if data file exists
            if 'demoddata' in obs_data and obs_data['demoddata']:
                data_url = obs_data['demoddata'][0]

                logger.info(f"Downloading data from {data_url}")
                data_response = self.session.get(data_url, timeout=60)

                if data_response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(data_response.content)
                    logger.info(f"Saved data to {output_path}")
                    return True
                else:
                    logger.warning(f"Failed to download data: {data_response.status_code}")
            else:
                logger.info(f"No demod data available for observation {observation_id}")

        except Exception as e:
            logger.error(f"Failed to download observation {observation_id}: {e}")

        return False

    def process_satellite_data(self, norad_id, max_observations=50):
        """Process data for a specific satellite."""
        logger.info(f"Processing data for NORAD ID {norad_id}")

        observations = self.get_observations(satellite_id=norad_id, limit=max_observations)

        if not observations:
            logger.warning(f"No observations found for NORAD ID {norad_id}")
            return

        logger.info(f"Found {len(observations)} observations")

        # Create satellite directory
        sat_dir = self.output_dir / 'satellites' / str(norad_id)
        sat_dir.mkdir(parents=True, exist_ok=True)

        downloaded = 0
        for obs in observations:
            obs_id = obs.get('id', obs.get('observation_id', 'unknown'))
            obs_filename = f"satnogs_{obs_id}.zip"
            obs_path = sat_dir / obs_filename

            if obs_path.exists():
                logger.info(f"Data for observation {obs_id} already exists")
                downloaded += 1
                continue

            if self.download_observation_data(obs_id, obs_path):
                downloaded += 1
                if not self.offline:
                    time.sleep(1)  # Be respectful to the API

        logger.info(f"Available: {downloaded} observations for NORAD {norad_id}")

    def get_popular_satellites(self, limit=20):
        """Get list of most observed satellites."""
        popular_satellites = [
            25544,  # ISS
            28654,  # NOAA 18
            33591,  # NOAA 19
            40069,  # FOX-1A (AO-85)
            40967,  # FUNCUBE-1
            42766,  # FOX-1D (AO-92)
            43803,  # FOX-1B (AO-91)
            44832,  # AO-7
            7530,   # AO-7
            24278,  # FO-29
        ]
        return popular_satellites[:limit]

    def cache_status(self):
        """Print cache status information."""
        print("\n" + "=" * 60)
        print("SATNOGS CACHE STATUS")
        print("=" * 60)

        obs_files = list(OBS_CACHE_DIR.glob('*.json'))
        meta_files = list(SAT_CACHE_DIR.glob('*_meta.json'))
        sat_dirs = [d for d in (self.output_dir / 'satellites').iterdir() if d.is_dir()] \
            if (self.output_dir / 'satellites').exists() else []

        print(f"Observation query cache: {len(obs_files)} queries")
        print(f"Observation metadata cache: {len(meta_files)} observations")
        print(f"Satellite data directories: {len(sat_dirs)}")

        total_data = 0
        for sat_dir in sat_dirs:
            data_files = list(sat_dir.glob('*.zip'))
            total_data += len(data_files)
            if data_files:
                print(f"  NORAD {sat_dir.name}: {len(data_files)} data files")

        print(f"\nTotal cached data files: {total_data}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Download SatNOGS data (offline-capable)')
    parser.add_argument('--output-dir', default='models/training_data', help='Output directory')
    parser.add_argument('--satellite', type=int, help='Specific NORAD ID to download')
    parser.add_argument('--max-observations', type=int, default=20, help='Max observations per satellite')
    parser.add_argument('--popular-only', action='store_true', help='Download from popular satellites only')
    parser.add_argument('--offline', action='store_true',
                        help='Offline mode — use only cached data, no network')
    parser.add_argument('--cache-status', action='store_true',
                        help='Show cache status and exit')

    args = parser.parse_args()

    downloader = SatNOGSDataDownloader(args.output_dir, offline=args.offline)

    if args.cache_status:
        downloader.cache_status()
        return

    if args.satellite:
        downloader.process_satellite_data(args.satellite, args.max_observations)
    elif args.popular_only:
        satellites = downloader.get_popular_satellites()
        for sat_id in satellites:
            downloader.process_satellite_data(sat_id, args.max_observations)
            if not args.offline:
                time.sleep(2)
    else:
        satellites = downloader.get_popular_satellites(5)
        for sat_id in satellites:
            downloader.process_satellite_data(sat_id, args.max_observations)
            if not args.offline:
                time.sleep(2)

    logger.info("SatNOGS data processing complete!")
    if not args.offline:
        logger.info("All downloaded data has been cached for offline use")
    logger.info("Next step: Run prepare_training_data.py to process the data")


if __name__ == '__main__':
    main()
