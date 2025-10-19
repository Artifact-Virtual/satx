#!/usr/bin/env python3
"""
Prepare training data for SATx signal detection model.
Creates spectrogram tiles from I/Q recordings and labels them.
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
import logging
from scipy import signal
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataPreparator:
    def __init__(self, output_dir='models/training_data'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.signal_dir = self.output_dir / 'signal'
        self.noise_dir = self.output_dir / 'noise'
        self.signal_dir.mkdir(exist_ok=True)
        self.noise_dir.mkdir(exist_ok=True)

    def load_iq_data(self, file_path):
        """Load I/Q data from file."""
        logger.info(f"Loading {file_path}")

        # Read raw I/Q samples
        samples = np.fromfile(file_path, dtype=np.uint8)

        # Convert to complex float
        iq = (samples.astype(np.float32) - 127.5) / 127.5
        iq = iq[::2] + 1j * iq[1::2]

        return iq

    def generate_spectrogram(self, iq, sample_rate=2400000, nperseg=1024):
        """Generate spectrogram from I/Q data."""
        # Compute spectrogram
        f, t, Sxx = signal.spectrogram(
            iq,
            fs=sample_rate,
            window='hann',
            nperseg=nperseg,
            noverlap=nperseg // 2,
            return_onesided=False,
            scaling='density'
        )

        # Shift zero frequency to center
        Sxx = np.fft.fftshift(Sxx, axes=0)
        f = np.fft.fftshift(f)

        # Convert to dB
        Sxx_db = 10 * np.log10(Sxx + 1e-12)

        return f, t, Sxx_db

    def extract_tiles(self, Sxx_db, tile_size=256, stride=128, threshold_db=-80):
        """Extract tiles from spectrogram."""
        tiles = []
        height, width = Sxx_db.shape

        for y in range(0, height - tile_size + 1, stride):
            for x in range(0, width - tile_size + 1, stride):
                tile = Sxx_db[y:y+tile_size, x:x+tile_size]

                # Skip tiles that are mostly noise
                if np.mean(tile) > threshold_db:
                    tiles.append(tile)

        return tiles

    def save_tiles(self, tiles, label, prefix):
        """Save tiles to disk."""
        output_dir = self.signal_dir if label == 'signal' else self.noise_dir

        for i, tile in enumerate(tiles):
            filename = f"{prefix}_{i:04d}.npy"
            filepath = output_dir / filename
            np.save(filepath, tile)

        logger.info(f"Saved {len(tiles)} {label} tiles")

    def process_recording(self, recording_path, metadata_path=None, sample_rate=2400000):
        """Process a single recording and extract training tiles."""
        recording_path = Path(recording_path)

        # Load metadata
        metadata = {}
        if metadata_path:
            metadata_file = Path(metadata_path)
        else:
            metadata_file = recording_path.with_suffix('.iq.json')

        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

        # Load I/Q data
        iq = self.load_iq_data(recording_path)

        # Generate spectrogram
        f, t, Sxx_db = self.generate_spectrogram(iq, sample_rate)

        # Extract tiles
        tiles = self.extract_tiles(Sxx_db)

        if not tiles:
            logger.warning(f"No tiles extracted from {recording_path}")
            return

        # Determine label
        norad_id = metadata.get('norad_id', 'unknown')
        has_candidates = len(metadata.get('candidates', [])) > 0

        if has_candidates or norad_id != 'unknown':
            label = 'signal'
        else:
            label = 'noise'

        # Create prefix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"{norad_id}_{timestamp}"

        # Save tiles
        self.save_tiles(tiles, label, prefix)

    def generate_synthetic_noise(self, num_tiles=1000, tile_size=256):
        """Generate synthetic noise tiles for training."""
        logger.info(f"Generating {num_tiles} synthetic noise tiles")

        tiles = []
        for i in range(num_tiles):
            # Generate random noise
            noise = np.random.normal(0, 1, (tile_size, tile_size))

            # Add some structure to make it more realistic
            # Apply some filtering
            from scipy import ndimage
            noise = ndimage.gaussian_filter(noise, sigma=1)

            tiles.append(noise)

        # Save noise tiles
        prefix = f"synthetic_noise_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.save_tiles(tiles, 'noise', prefix)

    def generate_synthetic_signals(self, num_tiles=500, tile_size=256):
        """Generate synthetic signal tiles for training."""
        logger.info(f"Generating {num_tiles} synthetic signal tiles")

        tiles = []
        for i in range(num_tiles):
            # Start with noise
            tile = np.random.normal(0, 1, (tile_size, tile_size))

            # Add synthetic signal
            # Create a narrowband signal
            freq = np.random.randint(tile_size // 4, 3 * tile_size // 4)
            time_start = np.random.randint(0, tile_size // 2)
            time_end = np.random.randint(time_start + 10, tile_size)

            # Add signal with some SNR
            signal_strength = np.random.uniform(2, 5)  # 2-5x noise level
            tile[freq-2:freq+2, time_start:time_end] += signal_strength

            # Add some frequency drift
            drift = np.random.normal(0, 0.5, time_end - time_start)
            for t in range(time_start, time_end):
                offset = int(drift[t - time_start])
                if 0 <= freq + offset < tile_size:
                    tile[freq + offset, t] += signal_strength

            tiles.append(tile)

        # Save signal tiles
        prefix = f"synthetic_signal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.save_tiles(tiles, 'signal', prefix)

def main():
    parser = argparse.ArgumentParser(description='Prepare training data for SATx model')
    parser.add_argument('--recordings-dir', default='recordings', help='Directory with I/Q recordings')
    parser.add_argument('--output-dir', default='models/training_data', help='Output directory')
    parser.add_argument('--generate-synthetic', action='store_true', help='Generate synthetic data')
    parser.add_argument('--synthetic-only', action='store_true', help='Only generate synthetic data')

    args = parser.parse_args()

    preparator = DataPreparator(args.output_dir)

    if args.synthetic_only:
        # Only generate synthetic data
        preparator.generate_synthetic_noise(2000)
        preparator.generate_synthetic_signals(1000)
    else:
        # Process real recordings
        recordings_dir = Path(args.recordings_dir)
        if recordings_dir.exists():
            iq_files = list(recordings_dir.glob('*.iq'))
            logger.info(f"Found {len(iq_files)} recordings")

            for iq_file in iq_files:
                try:
                    preparator.process_recording(iq_file)
                except Exception as e:
                    logger.error(f"Failed to process {iq_file}: {e}")
        else:
            logger.warning(f"Recordings directory {recordings_dir} not found")

        # Generate some synthetic data to supplement
        if args.generate_synthetic:
            preparator.generate_synthetic_noise(500)
            preparator.generate_synthetic_signals(250)

    # Print summary
    signal_count = len(list(preparator.signal_dir.glob('*.npy')))
    noise_count = len(list(preparator.noise_dir.glob('*.npy')))

    logger.info("Training data preparation complete!")
    logger.info(f"Signal tiles: {signal_count}")
    logger.info(f"Noise tiles: {noise_count}")
    logger.info(f"Total tiles: {signal_count + noise_count}")

if __name__ == '__main__':
    main()
