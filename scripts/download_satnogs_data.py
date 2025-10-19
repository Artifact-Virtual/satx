#!/usr/bin/env python3
"""
Download training data from SatNOGS network.
Fetches observations and converts them to training tiles.
"""

import requests
import json
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import time
import zipfile
import io

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SatNOGSDataDownloader:
    def __init__(self, output_dir='models/training_data'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.api_base = "https://network.satnogs.org/api"
        self.session = requests.Session()

    def get_observations(self, satellite_id=None, transmitter_mode=None, limit=100):
        """Fetch observations from SatNOGS API."""
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
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            return data.get('results', [])
        except Exception as e:
            logger.error(f"Failed to fetch observations: {e}")
            return []

    def download_observation_data(self, observation_id, output_path):
        """Download I/Q data for an observation."""
        url = f"{self.api_base}/observations/{observation_id}/"

        try:
            response = self.session.get(url)
            response.raise_for_status()
            obs_data = response.json()

            # Check if data file exists
            if 'demoddata' in obs_data and obs_data['demoddata']:
                data_url = obs_data['demoddata'][0]  # Get first demod file

                logger.info(f"Downloading data from {data_url}")
                data_response = self.session.get(data_url)

                if data_response.status_code == 200:
                    # Save the data
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

        # Get observations for this satellite
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
            obs_id = obs['id']
            obs_filename = f"satnogs_{obs_id}.zip"
            obs_path = sat_dir / obs_filename

            if obs_path.exists():
                logger.info(f"Data for observation {obs_id} already exists")
                continue

            # Download data
            if self.download_observation_data(obs_id, obs_path):
                downloaded += 1

                # Add small delay to be respectful to the API
                time.sleep(1)

        logger.info(f"Downloaded {downloaded} new observations for NORAD {norad_id}")

    def get_popular_satellites(self, limit=20):
        """Get list of most observed satellites."""
        # This is a simplified version - in practice you'd query the API
        # for satellites with most observations
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

def main():
    parser = argparse.ArgumentParser(description='Download SatNOGS data for training')
    parser.add_argument('--output-dir', default='models/training_data', help='Output directory')
    parser.add_argument('--satellite', type=int, help='Specific NORAD ID to download')
    parser.add_argument('--max-observations', type=int, default=20, help='Max observations per satellite')
    parser.add_argument('--popular-only', action='store_true', help='Download from popular satellites only')

    args = parser.parse_args()

    downloader = SatNOGSDataDownloader(args.output_dir)

    if args.satellite:
        # Download data for specific satellite
        downloader.process_satellite_data(args.satellite, args.max_observations)
    elif args.popular_only:
        # Download from popular satellites
        satellites = downloader.get_popular_satellites()
        for sat_id in satellites:
            downloader.process_satellite_data(sat_id, args.max_observations)
            time.sleep(2)  # Be respectful to the API
    else:
        # Download from a few popular satellites
        satellites = downloader.get_popular_satellites(5)
        for sat_id in satellites:
            downloader.process_satellite_data(sat_id, args.max_observations)
            time.sleep(2)

    logger.info("SatNOGS data download complete!")
    logger.info("Next step: Run prepare_training_data.py to process the downloaded data")

if __name__ == '__main__':
    main()
