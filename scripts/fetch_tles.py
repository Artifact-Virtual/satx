#!/usr/bin/env python3
"""
Fetch latest TLE data from CelesTrak and other sources.
Downloads comprehensive satellite catalogs for pass prediction.

Sovereignty: Supports full offline operation via local TLE cache.
  --offline    Use only cached TLEs (no network)
  Default:     Try network, fall back to cache silently
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

# Cache directory for offline sovereignty
CACHE_DIR = PROJECT_ROOT / 'data' / 'tle_cache'


def get_cache_path(name):
    """Get cache file path for a TLE catalog."""
    return CACHE_DIR / f'{name}.tle'


def get_cache_meta_path():
    """Get path for cache metadata."""
    return CACHE_DIR / 'cache_meta.txt'


def save_to_cache(name, content):
    """Save TLE content to local cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = get_cache_path(name)
    try:
        with open(cache_path, 'w') as f:
            f.write(content)
        logger.debug(f"Cached {name} → {cache_path}")
    except Exception as e:
        logger.warning(f"Failed to cache {name}: {e}")


def load_from_cache(name):
    """Load TLE content from local cache. Returns content or None."""
    cache_path = get_cache_path(name)
    if cache_path.exists():
        try:
            with open(cache_path, 'r') as f:
                content = f.read()
            if content and len(content) > 50:
                return content
        except Exception as e:
            logger.warning(f"Failed to read cache for {name}: {e}")
    return None


def update_cache_meta(success_count, total_count, source='network'):
    """Update cache metadata with timestamp."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    meta_path = get_cache_meta_path()
    try:
        with open(meta_path, 'w') as f:
            f.write(f"last_update: {datetime.now(timezone.utc).isoformat()}\n")
            f.write(f"source: {source}\n")
            f.write(f"catalogs: {success_count}/{total_count}\n")
    except Exception:
        pass


def get_cache_age():
    """Get cache age in hours. Returns None if no cache."""
    meta_path = get_cache_meta_path()
    if not meta_path.exists():
        return None
    try:
        with open(meta_path, 'r') as f:
            for line in f:
                if line.startswith('last_update:'):
                    ts = line.split(':', 1)[1].strip()
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    age = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
                    return age
    except Exception:
        pass
    return None


def download_tle(url, filename, catalog_name):
    """Download TLE file from URL and cache it."""
    try:
        logger.info(f"Downloading {catalog_name}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        content = response.text
        if not content or len(content) < 100:
            logger.warning(f"Downloaded file {catalog_name} appears to be empty or too small")
            return False

        # Save to target location
        with open(filename, 'w') as f:
            f.write(content)

        # Save to cache
        save_to_cache(catalog_name, content)

        # Count satellites
        lines = content.strip().split('\n')
        sat_count = len([l for l in lines if l.startswith('1 ')])
        logger.info(f"Downloaded {catalog_name} ({sat_count} satellites) → cached")
        return True

    except requests.exceptions.RequestException as e:
        logger.warning(f"Network failed for {catalog_name}: {e}")
        return False


def download_tle_with_fallback(url, filename, catalog_name):
    """Try network download, fall back to cache silently."""
    # Try network first
    if download_tle(url, filename, catalog_name):
        return True

    # Fall back to cache
    cached = load_from_cache(catalog_name)
    if cached:
        with open(filename, 'w') as f:
            f.write(cached)
        lines = cached.strip().split('\n')
        sat_count = len([l for l in lines if l.startswith('1 ')])
        logger.info(f"Using cached {catalog_name} ({sat_count} satellites)")
        return True

    logger.error(f"No network and no cache for {catalog_name}")
    return False


def load_tle_from_cache_only(filename, catalog_name):
    """Load TLE from cache only (offline mode)."""
    cached = load_from_cache(catalog_name)
    if cached:
        with open(filename, 'w') as f:
            f.write(cached)
        lines = cached.strip().split('\n')
        sat_count = len([l for l in lines if l.startswith('1 ')])
        logger.info(f"[OFFLINE] Loaded cached {catalog_name} ({sat_count} satellites)")
        return True
    else:
        logger.warning(f"[OFFLINE] No cache available for {catalog_name}")
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
    parser = argparse.ArgumentParser(description='Fetch TLE data (sovereign/offline-capable)')
    parser.add_argument('--offline', action='store_true',
                        help='Use only cached TLEs — no network access')
    parser.add_argument('--cache-only', action='store_true',
                        help='Alias for --offline')
    parser.add_argument('--force-network', action='store_true',
                        help='Force network download, skip cache fallback on failure')
    parser.add_argument('--cache-info', action='store_true',
                        help='Show cache status and exit')
    args = parser.parse_args()

    offline = args.offline or args.cache_only

    # Cache info mode
    if args.cache_info:
        age = get_cache_age()
        if age is not None:
            print(f"Cache age: {age:.1f} hours")
            cached_files = list(CACHE_DIR.glob('*.tle'))
            print(f"Cached catalogs: {len(cached_files)}")
            for f in sorted(cached_files):
                size = f.stat().st_size
                print(f"  {f.name}: {size:,} bytes")
        else:
            print("No cache found. Run without --offline to populate.")
        return 0

    # Create TLE directory
    tle_dir = PROJECT_ROOT / 'data' / 'tles'
    tle_dir.mkdir(parents=True, exist_ok=True)

    if offline:
        logger.info("=" * 60)
        logger.info("OFFLINE MODE — Using cached TLEs only (no network)")
        logger.info("=" * 60)
        age = get_cache_age()
        if age is not None:
            logger.info(f"Cache age: {age:.1f} hours")
        else:
            logger.warning("No cache metadata found — cache may be stale or missing")
    else:
        logger.info("Starting TLE download (network → cache fallback)...")

    logger.info(f"TLE directory: {tle_dir}")

    # Download/load all TLE sources
    success_count = 0
    for name, url in TLE_SOURCES.items():
        filename = tle_dir / f'{name}.tle'

        if offline:
            if load_tle_from_cache_only(filename, name):
                success_count += 1
        elif args.force_network:
            if download_tle(url, filename, name):
                success_count += 1
        else:
            if download_tle_with_fallback(url, filename, name):
                success_count += 1

    logger.info(f"Loaded {success_count}/{len(TLE_SOURCES)} TLE catalogs")

    if success_count == 0:
        logger.error("No TLE data available. Run with network access first to populate cache.")
        return 1

    # Merge all TLE files
    total_sats = merge_tle_files(tle_dir, 'all-satellites.tle')

    # Create timestamp file
    timestamp_file = tle_dir / 'last_update.txt'
    with open(timestamp_file, 'w') as f:
        source = 'cache' if offline else 'network+cache'
        f.write(f"{datetime.now(timezone.utc).isoformat()} UTC\n")
        f.write(f"Source: {source}\n")
        f.write(f"Total satellites: {total_sats}\n")

    if not offline:
        update_cache_meta(success_count, len(TLE_SOURCES), 'network')

    logger.info("TLE fetch complete!")
    logger.info(f"Use 'all-satellites.tle' for pass predictions ({total_sats} sats)")

    return 0


if __name__ == '__main__':
    exit(main())
