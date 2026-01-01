#!/usr/bin/env python3
"""
Advanced Spectrum Scanner for SATx
Provides wide-band scanning and signal identification capabilities.
"""

import logging
import json
from pathlib import Path
from datetime import datetime, timezone
import configparser

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logging.warning("NumPy not available. Some features may be limited.")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SpectrumScanner:
    """
    Advanced spectrum scanner with signal identification.
    Scans frequency bands and identifies active signals.
    """
    
    def __init__(self, config_file='configs/station.ini'):
        """Initialize scanner with configuration."""
        self.config = configparser.ConfigParser()
        
        try:
            self.config.read(config_file)
            
            # Load scanner configuration with defaults
            if 'station' not in self.config:
                logger.warning(f"Config file {config_file} missing 'station' section. Using defaults.")
                self.config['station'] = {}
            
            self.device_id = self.config['station'].get('device_id', '0')
            self.sample_rate = int(self.config['station'].get('sample_rate', '2400000'))
            self.gain = float(self.config['station'].get('gain', '49.0'))
            
            # Parse frequency bands
            bands_str = self.config['station'].get('bands', '137.0-138.0, 435.0-438.0')
            self.bands = self._parse_bands(bands_str)
            
            logger.info(f"Scanner initialized with {len(self.bands)} frequency bands")
        except Exception as e:
            logger.error(f"Error initializing scanner: {e}")
            # Set defaults
            self.device_id = '0'
            self.sample_rate = 2400000
            self.gain = 49.0
            self.bands = [(137.0e6, 138.0e6), (435.0e6, 438.0e6)]
    
    def _parse_bands(self, bands_str):
        """Parse frequency bands from config."""
        bands = []
        try:
            for band in bands_str.split(','):
                band = band.strip()
                if '-' in band:
                    parts = band.split('-')
                    if len(parts) == 2:
                        try:
                            start = float(parts[0]) * 1e6
                            end = float(parts[1]) * 1e6
                            if start < end:  # Validate range
                                bands.append((start, end))
                            else:
                                logger.warning(f"Invalid band range: {band} (start >= end)")
                        except ValueError:
                            logger.warning(f"Invalid band format: {band}")
                    else:
                        logger.warning(f"Invalid band format: {band} (expected start-end)")
        except Exception as e:
            logger.error(f"Error parsing bands: {e}")
        
        # Return default if no valid bands
        if not bands:
            logger.warning("No valid bands found, using defaults")
            bands = [(137.0e6, 138.0e6), (435.0e6, 438.0e6)]
        
        return bands
    
    def scan_band(self, start_freq, end_freq, step_size=None, duration=5):
        """
        Scan a frequency band and detect active signals.
        
        Args:
            start_freq: Start frequency in Hz
            end_freq: End frequency in Hz
            step_size: Frequency step size (defaults to sample_rate)
            duration: Duration to scan each frequency in seconds
        
        Returns:
            List of detected signals with metadata
        """
        if step_size is None:
            step_size = self.sample_rate
        
        logger.info(f"Scanning {start_freq/1e6:.2f} - {end_freq/1e6:.2f} MHz")
        
        detections = []
        current_freq = start_freq
        
        while current_freq < end_freq:
            logger.info(f"Scanning {current_freq/1e6:.3f} MHz...")
            
            # Scan this frequency
            signals = self._scan_frequency(current_freq, duration)
            
            if signals:
                detections.extend(signals)
                logger.info(f"  → Found {len(signals)} signal(s)")
            
            current_freq += step_size
        
        logger.info(f"Scan complete. Total detections: {len(detections)}")
        return detections
    
    def _scan_frequency(self, center_freq, duration):
        """
        Scan a single frequency and analyze for signals.
        
        Args:
            center_freq: Center frequency in Hz
            duration: Duration to scan in seconds
        
        Returns:
            List of detected signals
        """
        # In a real implementation, this would use rtl_power or rtl_sdr
        # For now, we'll create a placeholder that demonstrates the concept
        
        signals = []
        
        try:
            # Simulate spectrum analysis (in real use, call rtl_power or similar)
            # Example command: rtl_power -f {center_freq} -i {duration} -g {gain} output.csv
            
            # For demonstration, we'll check if this looks like a satellite frequency
            satellite_freqs = {
                137.1e6: {"type": "NOAA APT", "modulation": "FM", "bandwidth": 40000},
                137.62e6: {"type": "NOAA APT", "modulation": "FM", "bandwidth": 40000},
                137.9125e6: {"type": "NOAA APT", "modulation": "FM", "bandwidth": 40000},
                145.8e6: {"type": "ISS SSTV", "modulation": "FM", "bandwidth": 15000},
                435.0e6: {"type": "Amateur Satellite", "modulation": "Various", "bandwidth": 30000},
                437.0e6: {"type": "CubeSat", "modulation": "FSK/AFSK", "bandwidth": 25000},
            }
            
            # Check if we're near a known satellite frequency
            for freq, info in satellite_freqs.items():
                if abs(center_freq - freq) < 50000:  # Within 50 kHz
                    signal = {
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'center_frequency': center_freq,
                        'detected_frequency': freq,
                        'signal_type': info['type'],
                        'modulation': info['modulation'],
                        'bandwidth': info['bandwidth'],
                        'snr_estimate': 'N/A',  # Would be calculated from actual scan
                        'strength': 'Medium',  # Would be calculated from actual scan
                    }
                    signals.append(signal)
        
        except Exception as e:
            logger.error(f"Error scanning {center_freq/1e6:.3f} MHz: {e}")
        
        return signals
    
    def identify_signal(self, frequency, bandwidth, iq_data=None):
        """
        Identify signal type based on characteristics.
        
        Args:
            frequency: Center frequency in Hz
            bandwidth: Signal bandwidth in Hz
            iq_data: Optional I/Q data for analysis
        
        Returns:
            Dictionary with signal identification
        """
        identification = {
            'frequency': frequency,
            'bandwidth': bandwidth,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'signal_class': 'Unknown',
            'modulation_type': 'Unknown',
            'protocol': 'Unknown',
            'confidence': 0.0
        }
        
        # Frequency-based identification
        freq_mhz = frequency / 1e6
        
        if 137.0 <= freq_mhz <= 138.0:
            identification['signal_class'] = 'Weather Satellite'
            identification['modulation_type'] = 'FM/APT'
            identification['protocol'] = 'NOAA APT'
            identification['confidence'] = 0.8
        
        elif 145.0 <= freq_mhz <= 146.0:
            identification['signal_class'] = 'Amateur Satellite'
            identification['modulation_type'] = 'FM/SSB'
            identification['protocol'] = 'Voice/Packet'
            identification['confidence'] = 0.7
        
        elif 435.0 <= freq_mhz <= 438.0:
            identification['signal_class'] = 'Amateur/CubeSat'
            identification['modulation_type'] = 'FSK/AFSK/BPSK'
            identification['protocol'] = 'AX.25/Custom'
            identification['confidence'] = 0.75
        
        elif 460.0 <= freq_mhz <= 470.0:
            identification['signal_class'] = 'Commercial LEO'
            identification['modulation_type'] = 'Unknown'
            identification['protocol'] = 'Proprietary'
            identification['confidence'] = 0.6
        
        # Bandwidth-based refinement
        if bandwidth < 5000:
            identification['modulation_type'] = 'Narrowband (CW/FSK)'
        elif bandwidth < 30000:
            identification['modulation_type'] = 'Medium bandwidth (AFSK/BPSK)'
        else:
            identification['modulation_type'] = 'Wideband (FM/Spread)'
        
        return identification
    
    def scan_all_bands(self, output_file=None):
        """
        Scan all configured frequency bands.
        
        Args:
            output_file: Optional path to save results
        
        Returns:
            List of all detections
        """
        logger.info("="*60)
        logger.info("WIDE-BAND SPECTRUM SCAN")
        logger.info("="*60)
        
        all_detections = []
        
        for start_freq, end_freq in self.bands:
            logger.info(f"\nScanning band: {start_freq/1e6:.2f} - {end_freq/1e6:.2f} MHz")
            detections = self.scan_band(start_freq, end_freq)
            all_detections.extend(detections)
        
        # Identify all detected signals
        logger.info("\n" + "="*60)
        logger.info("SIGNAL IDENTIFICATION")
        logger.info("="*60)
        
        for detection in all_detections:
            identified = self.identify_signal(
                detection['detected_frequency'],
                detection.get('bandwidth', 0)
            )
            detection['identification'] = identified
            
            logger.info(f"\nFrequency: {detection['detected_frequency']/1e6:.3f} MHz")
            logger.info(f"  Type: {identified['signal_class']}")
            logger.info(f"  Modulation: {identified['modulation_type']}")
            logger.info(f"  Protocol: {identified['protocol']}")
            logger.info(f"  Confidence: {identified['confidence']*100:.1f}%")
        
        # Save results
        if output_file or all_detections:
            if output_file is None:
                output_file = Path('logs') / f'scan_{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}.json'
            
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump({
                    'scan_time': datetime.now(timezone.utc).isoformat(),
                    'bands_scanned': [[s/1e6, e/1e6] for s, e in self.bands],
                    'total_detections': len(all_detections),
                    'detections': all_detections
                }, f, indent=2)
            
            logger.info(f"\nResults saved to: {output_file}")
        
        return all_detections


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='SATx Spectrum Scanner')
    parser.add_argument('--band', type=str, help='Specific band to scan (e.g., 137.0-138.0)')
    parser.add_argument('--output', type=str, help='Output file for results')
    parser.add_argument('--config', type=str, default='configs/station.ini', help='Configuration file')
    
    args = parser.parse_args()
    
    scanner = SpectrumScanner(config_file=args.config)
    
    if args.band:
        # Scan specific band - validate input
        try:
            parts = args.band.split('-')
            if len(parts) != 2:
                logger.error("Invalid band format. Use: start-end (e.g., 137.0-138.0)")
                return 1
            start, end = float(parts[0]), float(parts[1])
            if start >= end:
                logger.error("Invalid band: start frequency must be less than end frequency")
                return 1
            detections = scanner.scan_band(start * 1e6, end * 1e6)
        except ValueError as e:
            logger.error(f"Invalid band format: {e}")
            return 1
    else:
        # Scan all configured bands
        detections = scanner.scan_all_bands(output_file=args.output)
    
    logger.info(f"\nScan complete: {len(detections)} signals detected")
    return 0


if __name__ == '__main__':
    exit(main())
