#!/usr/bin/env python3
"""
Process recorded I/Q files for signal detection and decoding.
Performs spectrogram analysis, ML-based signal detection, and protocol decoding.
"""

import logging
import json
import numpy as np
from pathlib import Path
from datetime import datetime
import argparse

try:
    import scipy.signal as signal
    from scipy.io import wavfile
except ImportError:
    logging.error("scipy not installed. Run: pip install scipy")
    exit(1)

try:
    import matplotlib.pyplot as plt
except ImportError:
    logging.error("matplotlib not installed. Run: pip install matplotlib")
    exit(1)

try:
    import torch
    from models.model_v1.model import SignalDetectorCNN
    ML_AVAILABLE = True
except ImportError:
    logging.warning("PyTorch or model not available. Using threshold detection only.")
    ML_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RecordingProcessor:
    def __init__(self, recording_path, metadata_path=None):
        """Initialize processor with recording file."""
        self.recording_path = Path(recording_path)
        
        if metadata_path:
            self.metadata_path = Path(metadata_path)
        else:
            self.metadata_path = self.recording_path.with_suffix('.iq.json')
        
        self.metadata = self.load_metadata()
        
        # Load ML model if available
        self.model = None
        if ML_AVAILABLE:
            try:
                self.model = SignalDetectorCNN()
                model_path = Path(__file__).parent.parent / 'models' / 'model_v1' / 'model.pth'
                if model_path.exists():
                    self.model.load_state_dict(torch.load(model_path, map_location='cpu'))
                    self.model.eval()
                    logger.info("ML model loaded successfully")
                else:
                    logger.warning(f"Model weights not found at {model_path}")
                    self.model = None
            except Exception as e:
                logger.warning(f"Failed to load ML model: {e}")
                self.model = None
        
    def load_metadata(self):
        """Load recording metadata."""
        if self.metadata_path.exists():
            with open(self.metadata_path, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"Metadata file not found: {self.metadata_path}")
            return {}
    
    def load_iq_data(self):
        """Load raw I/Q data from file."""
        logger.info(f"Loading I/Q data from {self.recording_path}")
        
        # Read raw I/Q samples (8-bit unsigned)
        samples = np.fromfile(self.recording_path, dtype=np.uint8)
        
        # Convert to complex float
        # RTL-SDR format: interleaved I,Q with 127.5 offset
        iq = (samples.astype(np.float32) - 127.5) / 127.5
        iq = iq[::2] + 1j * iq[1::2]
        
        logger.info(f"Loaded {len(iq)} complex samples")
        return iq
    
    def generate_spectrogram(self, iq, sample_rate):
        """Generate spectrogram from I/Q data."""
        logger.info("Generating spectrogram...")
        
        # Compute spectrogram
        nperseg = 1024
        noverlap = nperseg // 2
        
        f, t, Sxx = signal.spectrogram(
            iq, 
            fs=sample_rate,
            window='hann',
            nperseg=nperseg,
            noverlap=noverlap,
            return_onesided=False,
            scaling='density'
        )
        
        # Shift zero frequency to center
        Sxx = np.fft.fftshift(Sxx, axes=0)
        f = np.fft.fftshift(f)
        
        # Convert to dB
        Sxx_db = 10 * np.log10(Sxx + 1e-12)
        
        return f, t, Sxx_db
    
    def save_spectrogram_image(self, f, t, Sxx_db, output_path):
        """Save spectrogram as image."""
        logger.info(f"Saving spectrogram to {output_path}")
        
        plt.figure(figsize=(12, 6))
        plt.pcolormesh(t, f / 1e6, Sxx_db, shading='gouraud', cmap='viridis')
        plt.ylabel('Frequency (MHz)')
        plt.xlabel('Time (s)')
        plt.title(f'Spectrogram - NORAD {self.metadata.get("norad_id", "Unknown")}')
        plt.colorbar(label='Power (dB)')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
    
    def detect_signals(self, f, t, Sxx_db):
        """Detect candidate signals in spectrogram using ML model."""
        logger.info("Detecting signals...")
        
        candidates = []
        
        if self.model is not None:
            # Use ML-based detection
            candidates = self.detect_signals_ml(f, t, Sxx_db)
        else:
            # Fallback to threshold-based detection
            candidates = self.detect_signals_threshold(f, t, Sxx_db)
        
        logger.info(f"Found {len(candidates)} candidate signals")
        return candidates
    
    def detect_signals_ml(self, f, t, Sxx_db):
        """ML-based signal detection using CNN."""
        candidates = []
        
        # Normalize spectrogram to 0-1 range
        Sxx_norm = (Sxx_db - np.min(Sxx_db)) / (np.max(Sxx_db) - np.min(Sxx_db))
        
        # Create sliding window for tile extraction
        tile_size = 256
        stride = 128
        
        height, width = Sxx_norm.shape
        
        for y in range(0, height - tile_size + 1, stride):
            for x in range(0, width - tile_size + 1, stride):
                # Extract tile
                tile = Sxx_norm[y:y+tile_size, x:x+tile_size]
                
                # Convert to tensor
                tile_tensor = torch.from_numpy(tile).float().unsqueeze(0).unsqueeze(0)
                
                # Run inference
                with torch.no_grad():
                    output = self.model(tile_tensor)
                    prob_signal = torch.softmax(output, dim=1)[0, 1].item()
                
                # If signal probability > 0.5, consider it a candidate
                if prob_signal > 0.5:
                    # Calculate center frequency and time
                    center_freq_idx = y + tile_size // 2
                    center_time_idx = x + tile_size // 2
                    
                    if center_freq_idx < len(f) and center_time_idx < len(t):
                        freq_offset = f[center_freq_idx]
                        peak_time = t[center_time_idx]
                        
                        # Estimate SNR (simplified)
                        signal_power = np.max(tile)
                        noise_power = np.mean(tile)
                        snr = 10 * np.log10(signal_power / max(noise_power, 1e-12))
                        
                        candidates.append({
                            'frequency_offset': float(freq_offset),
                            'snr_db': float(snr),
                            'peak_time': float(peak_time),
                            'duration': float(t[-1]),
                            'confidence': float(prob_signal)
                        })
        
        return candidates
    
    def detect_signals_threshold(self, f, t, Sxx_db):
        """Simple threshold-based signal detection."""
        candidates = []
        
        # Calculate median power per frequency bin
        median_power = np.median(Sxx_db, axis=1)
        
        # Detection threshold: 6 dB above median
        threshold = median_power + 6
        
        # Find bins with power above threshold
        for i, freq in enumerate(f):
            if np.any(Sxx_db[i, :] > threshold[i]):
                # Calculate SNR estimate
                signal_power = np.max(Sxx_db[i, :])
                noise_power = median_power[i]
                snr = signal_power - noise_power
                
                # Find time of strongest signal
                peak_time_idx = np.argmax(Sxx_db[i, :])
                peak_time = t[peak_time_idx]
                
                candidates.append({
                    'frequency_offset': float(freq),
                    'snr_db': float(snr),
                    'peak_time': float(peak_time),
                    'duration': float(t[-1])
                })
        
        return candidates
    
    def process(self):
        """Main processing pipeline."""
        logger.info("="*60)
        logger.info("Starting recording processing")
        logger.info("="*60)
        
        # Load I/Q data
        iq = self.load_iq_data()
        
        sample_rate = self.metadata.get('sample_rate', 2400000)
        center_freq = self.metadata.get('center_frequency', 0)
        
        # Generate spectrogram
        f, t, Sxx_db = self.generate_spectrogram(iq, sample_rate)
        
        # Save spectrogram image
        spectrogram_path = self.recording_path.with_suffix('.png')
        self.save_spectrogram_image(f, t, Sxx_db, spectrogram_path)
        
        # Detect signals
        candidates = self.detect_signals(f, t, Sxx_db)
        
        # Save candidates
        candidates_path = self.recording_path.with_suffix('.candidates.json')
        with open(candidates_path, 'w') as f:
            json.dump({
                'recording': str(self.recording_path),
                'metadata': self.metadata,
                'candidates': candidates,
                'processed_time': datetime.utcnow().isoformat()
            }, f, indent=2)
        
        logger.info(f"Saved {len(candidates)} candidates to {candidates_path}")
        
        # Log to master candidates file
        self.log_candidates(candidates)
        
        logger.info("="*60)
        logger.info("Processing complete!")
        logger.info("="*60)
        
        return candidates
    
    def log_candidates(self, candidates):
        """Log candidates to master log file."""
        log_file = Path('logs/candidates.csv')
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create header if file doesn't exist
        if not log_file.exists():
            with open(log_file, 'w') as f:
                f.write('timestamp,norad_id,center_freq,freq_offset,snr_db,peak_time,recording_file\n')
        
        # Append candidates
        with open(log_file, 'a') as f:
            for c in candidates:
                line = f"{datetime.utcnow().isoformat()},{self.metadata.get('norad_id', 'N/A')}," \
                       f"{self.metadata.get('center_frequency', 0)},{c['frequency_offset']}," \
                       f"{c['snr_db']},{c['peak_time']},{self.recording_path}\n"
                f.write(line)

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Process satellite recording')
    parser.add_argument('recording', help='Path to .iq recording file')
    parser.add_argument('--metadata', help='Path to metadata JSON (optional)')
    
    args = parser.parse_args()
    
    processor = RecordingProcessor(args.recording, args.metadata)
    processor.process()
    
    return 0

if __name__ == '__main__':
    exit(main())
