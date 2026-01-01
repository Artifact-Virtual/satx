#!/usr/bin/env python3
"""
Fetch latest TLE data from CelesTrak and other sources.
Downloads comprehensive satellite catalogs for pass prediction.
"""

import requests
import os
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# TLE sources from CelesTrak
TLE_SOURCES = {
    'active': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle',
    'stations': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle',
    'weather': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle',
    'noaa': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=noaa&FORMAT=tle',
    'cubesat': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=cubesat&FORMAT=tle',
    'amateur': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=amateur&FORMAT=tle',
    'cosmos': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=cosmos-2251-debris&FORMAT=tle',
    'iridium': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-33-debris&FORMAT=tle',
    'science': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=science&FORMAT=tle',
    'geodetic': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=geodetic&FORMAT=tle',
    'engineering': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=engineering&FORMAT=tle',
    'education': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=education&FORMAT=tle',
}

def download_tle(url, filename):
    """Download TLE file from URL."""
    try:
        logger.info(f"Downloading {filename}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Validate TLE format (basic check)
        content = response.text
        if not content or len(content) < 100:
            logger.warning(f"Downloaded file {filename} appears to be empty or too small")
            return False
            
        with open(filename, 'w') as f:
            f.write(content)
        
        # Count satellites
        lines = content.strip().split('\n')
        sat_count = len([l for l in lines if l.startswith('1 ')])
        logger.info(f"Successfully downloaded {filename} ({sat_count} satellites)")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {filename}: {e}")
        return False

def merge_tle_files(tle_dir, output_file):
    """Merge all downloaded TLE files into one master file."""
    logger.info("Merging TLE files...")
    
    satellites = {}  # Use dict to deduplicate by NORAD ID
    
    for tle_file in Path(tle_dir).glob('*.tle'):
        if tle_file.name == output_file:
            continue
            
        with open(tle_file, 'r') as f:
            lines = f.readlines()
        
        # Parse TLE sets (name, line1, line2)
        for i in range(0, len(lines) - 2, 3):
            if i + 2 < len(lines):
                name = lines[i].strip()
                line1 = lines[i + 1].strip()
                line2 = lines[i + 2].strip()
                
                # Extract NORAD ID from line 1
                if line1.startswith('1 '):
                    norad_id = line1.split()[1].rstrip('U')
                    satellites[norad_id] = (name, line1, line2)
    
    # Write merged file
    output_path = Path(tle_dir) / output_file
    with open(output_path, 'w') as f:
        for norad_id in sorted(satellites.keys()):
            name, line1, line2 = satellites[norad_id]
            f.write(f"{name}\n{line1}\n{line2}\n")
    
    logger.info(f"Merged {len(satellites)} unique satellites to {output_file}")
    return len(satellites)

def main():
    """Main execution function."""
    # Create TLE directory if it doesn't exist
    tle_dir = Path(__file__).parent.parent / 'data' / 'tles'
    tle_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting TLE download...")
    logger.info(f"TLE directory: {tle_dir}")
    
    # Download all TLE sources
    success_count = 0
    for name, url in TLE_SOURCES.items():
        filename = tle_dir / f'{name}.tle'
        if download_tle(url, filename):
            success_count += 1
    
    logger.info(f"Downloaded {success_count}/{len(TLE_SOURCES)} TLE files successfully")
    
    # Merge all TLE files
    total_sats = merge_tle_files(tle_dir, 'all-satellites.tle')
    
    # Create timestamp file
    timestamp_file = tle_dir / 'last_update.txt'
    with open(timestamp_file, 'w') as f:
        from datetime import timezone
        f.write(datetime.now(timezone.utc).isoformat() + ' UTC\n')
        f.write(f"Total satellites: {total_sats}\n")
    
    logger.info("TLE download complete!")
    logger.info(f"Use 'all-satellites.tle' for pass predictions")
    
    return 0

if __name__ == '__main__':
    exit(main())
