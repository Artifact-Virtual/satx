#!/usr/bin/env python3
"""
Test utilities and fixtures for SATx system tests
"""

import os
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np

class TestFixtures:
    """Test fixtures and sample data for SATx tests"""

    @staticmethod
    def create_sample_tle_data():
        """Create sample TLE data for testing"""
        return """ISS (ZARYA)
1 25544U 98067A   24305.12345678  .00000000  00000-0  00000-0 0  9999
2 25544  51.6400 247.4627 0006703 130.5360 325.0288 15.5240 00000-0 0  9999
NOAA 15
1 25338U 98030A   24305.12345678  .00000000  00000-0  00000-0 0  9999
2 25338  98.7000 100.0000 0001000 000.0000 000.0000 14.2000 00000-0 0  9999"""

    @staticmethod
    def create_sample_station_config():
        """Create sample station configuration"""
        return """[station]
name = Test Station
latitude = 40.7128
longitude = -74.0060
altitude = 10
timezone = UTC

[sdr]
device = rtl=0
sample_rate = 2400000
gain = 40

[processing]
fft_size = 1024
overlap = 0.5
threshold = 0.8"""

    @staticmethod
    def create_sample_iq_data(filename, duration_seconds=1.0, sample_rate=2400000, frequency=437800000):
        """Create sample I/Q data file for testing"""
        # Generate noise with some signal-like characteristics
        num_samples = int(duration_seconds * sample_rate)

        # Create complex noise
        noise_real = np.random.normal(0, 0.1, num_samples)
        noise_imag = np.random.normal(0, 0.1, num_samples)
        iq_data = noise_real + 1j * noise_imag

        # Add a simple tone to simulate a signal
        t = np.arange(num_samples) / sample_rate
        signal_freq = 100000  # 100 kHz offset
        signal = 0.5 * np.exp(1j * 2 * np.pi * signal_freq * t)
        iq_data += signal

        # Convert to RTL-SDR format (uint8, I then Q, centered at 127.5)
        iq_int8 = np.empty(2 * num_samples, dtype=np.uint8)
        iq_int8[0::2] = np.clip(127.5 + 127.5 * iq_data.real, 0, 255).astype(np.uint8)
        iq_int8[1::2] = np.clip(127.5 + 127.5 * iq_data.imag, 0, 255).astype(np.uint8)

        # Write to file
        with open(filename, 'wb') as f:
            f.write(iq_int8.tobytes())

        # Create metadata
        metadata = {
            'norad_id': 25544,
            'center_frequency': frequency,
            'sample_rate': sample_rate,
            'duration_seconds': duration_seconds,
            'timestamp': '2024-01-01T12:00:00Z'
        }

        metadata_file = filename.with_suffix('.iq.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        return filename, metadata_file

    @staticmethod
    def create_sample_spectrogram_data():
        """Create sample spectrogram data for ML testing"""
        # Create a simple spectrogram-like 2D array
        time_steps = 100
        freq_bins = 256

        # Generate noise with some signal patterns
        spectrogram = np.random.rand(time_steps, freq_bins) * 0.1

        # Add horizontal lines to simulate signals
        signal_positions = [50, 100, 150, 200]
        for pos in signal_positions:
            spectrogram[:, pos] += np.random.rand(time_steps) * 0.8

        return spectrogram

class MockObjects:
    """Mock objects for testing"""

    @staticmethod
    def mock_skyfield_satellite():
        """Create a mock Skyfield satellite object"""
        mock_sat = Mock()
        mock_sat.name = "ISS (ZARYA)"

        # Mock position and velocity
        mock_pos = Mock()
        mock_pos.position = Mock()
        mock_pos.position.km = [4000, 2000, 3000]  # Example position
        mock_pos.velocity = Mock()
        mock_pos.velocity.km_per_s = [7.5, 6.2, 2.1]  # Example velocity

        mock_sat.at.return_value = mock_pos
        return mock_sat

    @staticmethod
    def mock_rtl_sdr():
        """Create a mock RTL-SDR device"""
        mock_sdr = Mock()
        mock_sdr.get_sample_rate.return_value = 2400000
        mock_sdr.get_center_freq.return_value = 437800000
        mock_sdr.get_gain.return_value = 40
        mock_sdr.read_samples.return_value = np.random.rand(1024) + 1j * np.random.rand(1024)
        return mock_sdr

    @staticmethod
    def mock_ml_model():
        """Create a mock ML model for testing"""
        mock_model = Mock()
        mock_model.eval.return_value = None
        mock_model.return_value = Mock()  # Mock tensor output
        mock_model.return_value.detach.return_value = Mock()
        mock_model.return_value.detach.return_value.numpy.return_value = np.array([[0.9, 0.1]])  # High confidence for signal
        return mock_model

class TestEnvironment:
    """Test environment management"""

    def __init__(self):
        self.temp_dir = None
        self.original_cwd = None

    def setup(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp(prefix='satx_test_'))
        self.original_cwd = os.getcwd()

        # Create test directory structure
        (self.temp_dir / 'data' / 'tles').mkdir(parents=True, exist_ok=True)
        (self.temp_dir / 'configs').mkdir(exist_ok=True)
        (self.temp_dir / 'recordings').mkdir(exist_ok=True)
        (self.temp_dir / 'logs').mkdir(exist_ok=True)
        (self.temp_dir / 'models' / 'model_v1').mkdir(parents=True, exist_ok=True)

        # Create sample files
        tle_file = self.temp_dir / 'data' / 'tles' / 'all-satellites.tle'
        with open(tle_file, 'w') as f:
            f.write(TestFixtures.create_sample_tle_data())

        config_file = self.temp_dir / 'configs' / 'station.ini'
        with open(config_file, 'w') as f:
            f.write(TestFixtures.create_sample_station_config())

        # Change to temp directory
        os.chdir(self.temp_dir)

        return self.temp_dir

    def teardown(self):
        """Clean up test environment"""
        if self.original_cwd:
            os.chdir(self.original_cwd)

        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.teardown()

class TestAssertions:
    """Custom test assertions for SATx-specific checks"""

    @staticmethod
    def assert_iq_file_valid(filename):
        """Assert that an I/Q file is valid"""
        assert filename.exists(), f"I/Q file {filename} does not exist"

        # Check file size is reasonable
        size = filename.stat().st_size
        assert size > 0, f"I/Q file {filename} is empty"
        assert size % 2 == 0, f"I/Q file {filename} has odd size (should be even)"

        # Check metadata file exists
        metadata_file = filename.with_suffix('.iq.json')
        assert metadata_file.exists(), f"Metadata file {metadata_file} does not exist"

        # Check metadata content
        with open(metadata_file) as f:
            metadata = json.load(f)

        required_keys = ['norad_id', 'center_frequency', 'sample_rate', 'duration_seconds']
        for key in required_keys:
            assert key in metadata, f"Metadata missing required key: {key}"

    @staticmethod
    def assert_spectrogram_valid(spectrogram):
        """Assert that a spectrogram is valid"""
        assert isinstance(spectrogram, np.ndarray), "Spectrogram must be a numpy array"
        assert spectrogram.ndim == 2, "Spectrogram must be 2D"
        assert spectrogram.shape[0] > 0, "Spectrogram must have time dimension > 0"
        assert spectrogram.shape[1] > 0, "Spectrogram must have frequency dimension > 0"
        assert np.all(np.isfinite(spectrogram)), "Spectrogram must contain finite values"

    @staticmethod
    def assert_tle_data_valid(tle_content):
        """Assert that TLE data is valid"""
        lines = tle_content.strip().split('\n')
        assert len(lines) >= 3, "TLE must have at least 3 lines"

        # Check TLE format (very basic)
        for i, line in enumerate(lines):
            if i % 3 == 0:  # Name line
                assert len(line.strip()) > 0, f"TLE name line {i//3 + 1} is empty"
            elif i % 3 == 1:  # Line 1
                assert line.startswith('1 '), f"TLE line {i//3 + 1} line 1 must start with '1 '"
            elif i % 3 == 2:  # Line 2
                assert line.startswith('2 '), f"TLE line {i//3 + 1} line 2 must start with '2 '"

    @staticmethod
    def assert_config_valid(config_content):
        """Assert that configuration content is valid"""
        assert len(config_content.strip()) > 0, "Configuration cannot be empty"

        # Check for required sections (basic check)
        lines = config_content.split('\n')
        sections_found = [line for line in lines if line.strip().startswith('[') and line.strip().endswith(']')]
        assert len(sections_found) > 0, "Configuration must have at least one section"

class PerformanceMonitor:
    """Monitor performance metrics during tests"""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.memory_start = None
        self.memory_end = None

    def start(self):
        """Start performance monitoring"""
        import psutil
        self.start_time = time.time()
        process = psutil.Process()
        self.memory_start = process.memory_info().rss

    def stop(self):
        """Stop performance monitoring"""
        import psutil
        self.end_time = time.time()
        process = psutil.Process()
        self.memory_end = process.memory_info().rss

    def get_metrics(self):
        """Get performance metrics"""
        if not all([self.start_time, self.end_time, self.memory_start, self.memory_end]):
            return {}

        execution_time = self.end_time - self.start_time
        memory_used = self.memory_end - self.memory_start

        return {
            'execution_time': execution_time,
            'memory_used': memory_used,
            'memory_used_mb': memory_used / (1024 * 1024)
        }
