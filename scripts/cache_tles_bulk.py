#!/usr/bin/env python3
"""
Bulk TLE Cache Downloader for SATx Sovereignty.

Downloads ALL major TLE catalogs from CelesTrak for offline/air-gapped use.
Run this while you have network access to prepare for sovereign operation.

Usage:
    python scripts/cache_tles_bulk.py          # Download everything
    python scripts/cache_tles_bulk.py --status  # Show cache status
    python scripts/cache_tles_bulk.py --verify  # Verify cache integrity
"""

import requests
import os
import sys
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
CACHE_DIR = PROJECT_ROOT / 'data' / 'tle_cache'

# Comprehensive TLE catalog sources from CelesTrak
# Covers ALL major categories for maximum offline coverage
TLE_CATALOGS = {
    # ========== OPERATIONAL SATELLITES ==========
    'stations': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle',
        'desc': 'Space Stations (ISS, Tiangong, etc.)',
    },
    'active': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle',
        'desc': 'Active Satellites (full catalog)',
    },

    # ========== WEATHER & EARTH OBSERVATION ==========
    'weather': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle',
        'desc': 'Weather Satellites',
    },
    'noaa': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=noaa&FORMAT=tle',
        'desc': 'NOAA Satellites',
    },
    'goes': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=goes&FORMAT=tle',
        'desc': 'GOES Satellites',
    },
    'resource': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=resource&FORMAT=tle',
        'desc': 'Earth Resources Satellites',
    },

    # ========== SEARCH & RESCUE ==========
    'sarsat': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=sarsat&FORMAT=tle',
        'desc': 'Search & Rescue (SARSAT)',
    },
    'disaster-monitoring': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=dmc&FORMAT=tle',
        'desc': 'Disaster Monitoring Constellation',
    },

    # ========== COMMUNICATIONS ==========
    'geo': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=geo&FORMAT=tle',
        'desc': 'Geostationary Satellites',
    },
    'intelsat': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=intelsat&FORMAT=tle',
        'desc': 'Intelsat Satellites',
    },
    'ses': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=ses&FORMAT=tle',
        'desc': 'SES Satellites',
    },
    'iridium': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=iridium&FORMAT=tle',
        'desc': 'Iridium Satellites',
    },
    'iridium-next': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-NEXT&FORMAT=tle',
        'desc': 'Iridium NEXT Satellites',
    },
    'orbcomm': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=orbcomm&FORMAT=tle',
        'desc': 'ORBCOMM Satellites',
    },
    'globalstar': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=globalstar&FORMAT=tle',
        'desc': 'Globalstar Satellites',
    },
    'starlink': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle',
        'desc': 'Starlink Satellites',
    },
    'oneweb': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=tle',
        'desc': 'OneWeb Satellites',
    },
    'swarm': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=swarm&FORMAT=tle',
        'desc': 'Swarm Satellites',
    },

    # ========== AMATEUR RADIO ==========
    'amateur': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=amateur&FORMAT=tle',
        'desc': 'Amateur Radio Satellites',
    },

    # ========== NAVIGATION ==========
    'gps-ops': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=gps-ops&FORMAT=tle',
        'desc': 'GPS Operational',
    },
    'glonass': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=glo-ops&FORMAT=tle',
        'desc': 'GLONASS Operational',
    },
    'galileo': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=galileo&FORMAT=tle',
        'desc': 'Galileo',
    },
    'beidou': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=beidou&FORMAT=tle',
        'desc': 'BeiDou',
    },

    # ========== SCIENCE ==========
    'science': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=science&FORMAT=tle',
        'desc': 'Science Satellites',
    },
    'geodetic': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=geodetic&FORMAT=tle',
        'desc': 'Geodetic Satellites',
    },
    'engineering': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=engineering&FORMAT=tle',
        'desc': 'Engineering Satellites',
    },
    'education': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=education&FORMAT=tle',
        'desc': 'Education Satellites',
    },

    # ========== CUBESATS ==========
    'cubesat': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=cubesat&FORMAT=tle',
        'desc': 'CubeSats',
    },

    # ========== MILITARY & SPECIAL ==========
    'military': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=military&FORMAT=tle',
        'desc': 'Military Satellites',
    },
    'radar': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=radar&FORMAT=tle',
        'desc': 'Radar Calibration Satellites',
    },
    'other-comm': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=other-comm&FORMAT=tle',
        'desc': 'Other Communications Satellites',
    },
    'x-comm': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=x-comm&FORMAT=tle',
        'desc': 'Experimental Communications',
    },

    # ========== NOTABLE DEBRIS ==========
    'cosmos-2251-debris': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=cosmos-2251-debris&FORMAT=tle',
        'desc': 'Cosmos 2251 Debris',
    },
    'iridium-33-debris': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-33-debris&FORMAT=tle',
        'desc': 'Iridium 33 Debris',
    },

    # ========== SUPPLEMENTAL ==========
    'planet': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=planet&FORMAT=tle',
        'desc': 'Planet Labs',
    },
    'spire': {
        'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=spire&FORMAT=tle',
        'desc': 'Spire Global',
    },
}


def download_catalog(name, url, cache_dir):
    """Download a single TLE catalog and cache it."""
    cache_path = cache_dir / f'{name}.tle'
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        content = response.text
        if not content or len(content) < 50:
            logger.warning(f"  {name}: Empty or too small response")
            return False, 0

        with open(cache_path, 'w') as f:
            f.write(content)

        lines = content.strip().split('\n')
        sat_count = len([l for l in lines if l.startswith('1 ')])
        logger.info(f"  ✓ {name}: {sat_count} satellites ({len(content):,} bytes)")
        return True, sat_count

    except requests.exceptions.RequestException as e:
        logger.warning(f"  ✗ {name}: {e}")
        return False, 0


def merge_all_cached(cache_dir):
    """Merge all cached TLE files into a single master file."""
    satellites = {}

    for tle_file in sorted(cache_dir.glob('*.tle')):
        if tle_file.name == 'all-satellites.tle':
            continue

        try:
            with open(tle_file, 'r') as f:
                lines = f.readlines()

            for i in range(0, len(lines) - 2, 3):
                if i + 2 < len(lines):
                    name = lines[i].strip()
                    line1 = lines[i + 1].strip()
                    line2 = lines[i + 2].strip()

                    if line1.startswith('1 '):
                        norad_id = line1.split()[1].rstrip('U')
                        satellites[norad_id] = (name, line1, line2)
        except Exception as e:
            logger.warning(f"Error reading {tle_file.name}: {e}")

    # Write merged file
    merged_path = cache_dir / 'all-satellites.tle'
    with open(merged_path, 'w') as f:
        for norad_id in sorted(satellites.keys()):
            name, line1, line2 = satellites[norad_id]
            f.write(f"{name}\n{line1}\n{line2}\n")

    return len(satellites)


def show_status(cache_dir):
    """Show detailed cache status."""
    print("\n" + "=" * 70)
    print("SATx TLE CACHE STATUS")
    print("=" * 70)

    if not cache_dir.exists():
        print("Cache directory does not exist. Run without --status to populate.")
        return

    meta_path = cache_dir / 'cache_meta.txt'
    if meta_path.exists():
        with open(meta_path, 'r') as f:
            print(f.read())
        print("-" * 70)

    total_sats = 0
    total_bytes = 0
    catalogs = []

    for tle_file in sorted(cache_dir.glob('*.tle')):
        if tle_file.name == 'all-satellites.tle':
            continue

        size = tle_file.stat().st_size
        with open(tle_file, 'r') as f:
            content = f.read()
        lines = content.strip().split('\n')
        sat_count = len([l for l in lines if l.startswith('1 ')])

        name = tle_file.stem
        desc = TLE_CATALOGS.get(name, {}).get('desc', '')
        catalogs.append((name, sat_count, size, desc))
        total_sats += sat_count
        total_bytes += size

    print(f"{'Catalog':<25} {'Sats':>6} {'Size':>10}  Description")
    print("-" * 70)
    for name, sats, size, desc in catalogs:
        print(f"{name:<25} {sats:>6} {size:>9,}B  {desc}")

    print("-" * 70)
    print(f"{'TOTAL':<25} {total_sats:>6} {total_bytes:>9,}B")

    merged = cache_dir / 'all-satellites.tle'
    if merged.exists():
        with open(merged, 'r') as f:
            lines = f.readlines()
        unique = len([l for l in lines if l.startswith('1 ')])
        print(f"\nMerged (deduplicated): {unique} unique satellites")
    else:
        print("\nNo merged file yet — will be created on next download")

    print("=" * 70)


def verify_cache(cache_dir):
    """Verify cache integrity."""
    print("\nVerifying TLE cache integrity...")
    issues = 0

    for tle_file in sorted(cache_dir.glob('*.tle')):
        if tle_file.name == 'all-satellites.tle':
            continue

        with open(tle_file, 'r') as f:
            lines = f.readlines()

        # Basic TLE format validation
        errors = 0
        for i in range(0, len(lines) - 2, 3):
            if i + 2 < len(lines):
                line1 = lines[i + 1].strip()
                line2 = lines[i + 2].strip()

                if not line1.startswith('1 '):
                    errors += 1
                if not line2.startswith('2 '):
                    errors += 1
                if len(line1) < 69 or len(line2) < 69:
                    errors += 1

        if errors > 0:
            print(f"  ✗ {tle_file.name}: {errors} format errors")
            issues += 1
        else:
            sats = len([l for l in lines if l.startswith('1 ')])
            print(f"  ✓ {tle_file.name}: {sats} satellites OK")

    if issues == 0:
        print("\n✓ All cached TLE files are valid")
    else:
        print(f"\n⚠️  {issues} files have issues — re-download recommended")


def main():
    parser = argparse.ArgumentParser(
        description='Bulk download ALL TLE catalogs for offline sovereignty'
    )
    parser.add_argument('--status', action='store_true', help='Show cache status')
    parser.add_argument('--verify', action='store_true', help='Verify cache integrity')
    parser.add_argument('--catalogs', nargs='+',
                        help='Download specific catalogs only (e.g., --catalogs noaa goes military)')
    args = parser.parse_args()

    if args.status:
        show_status(CACHE_DIR)
        return

    if args.verify:
        verify_cache(CACHE_DIR)
        return

    # Download mode
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("SATx BULK TLE CACHE DOWNLOAD")
    print(f"Target: {CACHE_DIR}")
    print(f"Catalogs: {len(TLE_CATALOGS)}")
    print("=" * 70)

    # Filter catalogs if specified
    catalogs = TLE_CATALOGS
    if args.catalogs:
        catalogs = {k: v for k, v in TLE_CATALOGS.items() if k in args.catalogs}
        if not catalogs:
            print(f"No matching catalogs found. Available: {', '.join(TLE_CATALOGS.keys())}")
            return

    success = 0
    total_sats = 0
    failed = []

    for name, info in catalogs.items():
        ok, count = download_catalog(name, info['url'], CACHE_DIR)
        if ok:
            success += 1
            total_sats += count
        else:
            failed.append(name)

    print("\n" + "-" * 70)
    print(f"Downloaded: {success}/{len(catalogs)} catalogs")
    print(f"Total satellites (with duplicates): {total_sats}")

    if failed:
        print(f"Failed: {', '.join(failed)}")

    # Merge all into master file
    if success > 0:
        unique = merge_all_cached(CACHE_DIR)
        print(f"Merged: {unique} unique satellites → all-satellites.tle")

        # Write metadata
        meta_path = CACHE_DIR / 'cache_meta.txt'
        with open(meta_path, 'w') as f:
            f.write(f"last_update: {datetime.now(timezone.utc).isoformat()}\n")
            f.write(f"catalogs_downloaded: {success}/{len(catalogs)}\n")
            f.write(f"unique_satellites: {unique}\n")
            f.write(f"source: CelesTrak bulk download\n")

    print("\n✓ Cache ready for offline/air-gapped operation")
    print("  Use: python scripts/fetch_tles.py --offline")
    print("  Or:  python scripts/predict_passes.py --offline")


if __name__ == '__main__':
    main()
