"""
SATx Test Configuration and Base Classes
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
import logging
from unittest.mock import Mock, patch
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure test logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SATxTestCase(unittest.TestCase):
    """Base test case for SATx tests"""

    def setUp(self):
        """Set up test environment"""
        self.test_root = Path(__file__).parent.parent
        self.temp_dir = Path(tempfile.mkdtemp(prefix='satx_test_'))

        # Create test directories
        self.test_data_dir = self.temp_dir / 'data'
        self.test_data_dir.mkdir()

        self.test_configs_dir = self.temp_dir / 'configs'
        self.test_configs_dir.mkdir()

        self.test_logs_dir = self.temp_dir / 'logs'
        self.test_logs_dir.mkdir()

        # Mock paths for testing
        self.mock_paths = {
            'data_dir': self.test_data_dir,
            'configs_dir': self.test_configs_dir,
            'logs_dir': self.test_logs_dir,
            'models_dir': self.temp_dir / 'models',
            'recordings_dir': self.temp_dir / 'recordings'
        }

        # Create mock directories
        for path in self.mock_paths.values():
            path.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_mock_config(self, **kwargs):
        """Create a mock station configuration file"""
        config_path = self.test_configs_dir / 'station.ini'
        config_content = f"""[station]
name = Test Station
latitude = {kwargs.get('latitude', 40.7128)}
longitude = {kwargs.get('longitude', -74.0060)}
altitude = {kwargs.get('altitude', 10)}
timezone = {kwargs.get('timezone', 'UTC')}

[sdr]
device = {kwargs.get('device', 'rtl=0')}
sample_rate = {kwargs.get('sample_rate', 2400000)}
gain = {kwargs.get('gain', 40)}

[ml]
model_path = {kwargs.get('model_path', 'models/model_v1/model.pth')}
confidence_threshold = {kwargs.get('confidence_threshold', 0.8)}
"""
        config_path.write_text(config_content)
        return config_path

    def create_mock_tle_file(self, satellites=None):
        """Create a mock TLE file for testing"""
        if satellites is None:
            satellites = [
                ("ISS", "1 25544U 98067A   23165.12345678  .00000000  00000-0  00000-0 0  9999", "2 25544  51.6400  12.3456 0001000  45.6789 314.3211 15.48900000123456"),
                ("NOAA 15", "1 25338U 98030A   23165.12345678  .00000000  00000-0  00000-0 0  9998", "2 25338  98.7000  12.3456 0001000  45.6789 314.3211 14.20000000123456")
            ]

        tle_path = self.test_data_dir / 'tles' / 'test.tle'
        tle_path.parent.mkdir(exist_ok=True)

        content = ""
        for name, line1, line2 in satellites:
            content += f"{name}\n{line1}\n{line2}\n"

        tle_path.write_text(content)
        return tle_path

    def create_mock_recording(self, duration_seconds=1.0, sample_rate=2400000, frequency=437800000):
        """Create a mock I/Q recording file"""
        recordings_dir = self.temp_dir / 'recordings'
        recordings_dir.mkdir(exist_ok=True)

        filename = f"test_sat_{int(frequency)}.iq"
        iq_path = recordings_dir / filename

        # Create simple noise signal (alternating I/Q values)
        samples = []
        for i in range(int(sample_rate * duration_seconds)):
            # Generate simple alternating pattern
            i_val = int(127.5 + 20 * ((i % 2) - 0.5))
            q_val = int(127.5 + 20 * (((i + 1) % 2) - 0.5))
            samples.extend([i_val, q_val])

        # Write as bytes
        with open(iq_path, 'wb') as f:
            f.write(bytes(samples))

        # Create metadata file
        metadata = {
            'norad_id': 25544,
            'center_frequency': frequency,
            'sample_rate': sample_rate,
            'duration_seconds': duration_seconds,
            'timestamp': '2023-10-18T12:00:00Z'
        }

        import json
        metadata_path = iq_path.with_suffix('.iq.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)

        return iq_path

class MockSDRDevice:
    """Mock SDR device for testing"""

    def __init__(self, sample_rate=2400000, gain=40):
        self.sample_rate = sample_rate
        self.gain = gain
        self.center_freq = 437800000
        self.is_recording = False

    def set_center_freq(self, freq):
        self.center_freq = freq

    def set_sample_rate(self, rate):
        self.sample_rate = rate

    def set_gain(self, gain):
        self.gain = gain

    def start_recording(self, duration, filename):
        self.is_recording = True
        # Simulate recording by creating a file
        Path(filename).touch()
        return True

    def stop_recording(self):
        self.is_recording = False
        return True

def run_tests_with_coverage(test_module):
    """Run tests with coverage reporting"""
    try:
        import coverage
        cov = coverage.Coverage(source=['scripts', 'models', 'web'])
        cov.start()

        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_module)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        cov.stop()
        cov.report()

        return result.wasSuccessful()

    except ImportError:
        # Coverage not available, run without it
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_module)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()

if __name__ == '__main__':
    unittest.main()
