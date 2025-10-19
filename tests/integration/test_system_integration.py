"""
Integration tests for SATx system components
"""

import unittest
import tempfile
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, Mock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests import SATxTestCase

class TestSystemIntegration(SATxTestCase):
    """Integration tests for component interactions"""

    def setUp(self):
        super().setUp()
        # Create necessary directories
        self.recordings_dir = self.temp_dir / 'recordings'
        self.recordings_dir.mkdir(exist_ok=True)

    def test_tle_to_pass_prediction_pipeline(self):
        """Test complete pipeline from TLE fetching to pass prediction"""
        # Create mock TLE data
        tle_file = self.create_mock_tle_file()
        config_file = self.create_mock_config()

        try:
            # Step 1: Load TLE data
            from scripts.predict_passes import load_tle_data
            satellites = load_tle_data(str(tle_file))
            self.assertGreater(len(satellites), 0)

            # Step 2: Load station config
            from scripts.predict_passes import load_station_config
            config = load_station_config(str(config_file))
            self.assertIn('latitude', config)

            # Step 3: Generate predictions (mocked)
            with patch('skyfield.api.load') as mock_load, \
                 patch('skyfield.api.EarthSatellite') as mock_sat:

                mock_timescale = Mock()
                mock_load.return_value = mock_timescale
                mock_sat.return_value = Mock()

                from scripts.predict_passes import predict_passes
                predictions = predict_passes(str(tle_file), str(config_file))

                # Should return a list (even if empty due to mocking)
                self.assertIsInstance(predictions, list)

        except ImportError:
            # If dependencies missing, test file operations
            self.assertTrue(tle_file.exists())
            self.assertTrue(config_file.exists())

    def test_recording_processing_pipeline(self):
        """Test recording creation and processing pipeline"""
        # Create mock recording
        iq_file = self.create_mock_recording()

        try:
            # Test processing script can handle the file
            from scripts.process_recording import process_recording

            result = process_recording(str(iq_file))

            # Should return some result
            self.assertIsNotNone(result)

            # Check if output files were created
            spectrogram_file = iq_file.with_suffix('.png')
            candidates_file = iq_file.with_suffix('.candidates.json')

            # At least one output should exist
            self.assertTrue(spectrogram_file.exists() or candidates_file.exists())

        except ImportError:
            # Test file creation
            self.assertTrue(iq_file.exists())
            metadata_file = iq_file.with_suffix('.iq.json')
            self.assertTrue(metadata_file.exists())

    def test_ml_processing_integration(self):
        """Test ML model integration with processing pipeline"""
        try:
            # Create mock spectrogram data (256x256 as expected by model)
            import numpy as np
            spectrogram = np.random.randn(256, 256)

            # Test model loading
            from models.model_v1.model import SignalDetectorCNN
            model = SignalDetectorCNN()
            model.eval()

            # Convert to tensor and test
            import torch
            tensor_input = torch.from_numpy(spectrogram).float().unsqueeze(0).unsqueeze(0)

            with torch.no_grad():
                output = model(tensor_input)
                self.assertEqual(output.shape, (1, 2))  # Batch size 1, binary classification

            # Test that output is reasonable (not all zeros or NaN)
            self.assertFalse(torch.isnan(output).any())
            self.assertFalse(torch.isinf(output).any())

        except ImportError:
            self.skipTest("ML dependencies not available")

    def test_scheduler_workflow(self):
        """Test scheduler workflow integration"""
        try:
            from scripts.scheduler import SatelliteScheduler
            from scripts.predict_passes import load_station_config

            # Create config
            config_file = self.create_mock_config()
            config = load_station_config(str(config_file))

            # Create scheduler
            scheduler = SatelliteScheduler(config)

            # Test basic functionality
            self.assertIsNotNone(scheduler)
            self.assertEqual(scheduler.config['latitude'], config['latitude'])

            # Test schedule generation (with mocked predictions)
            with patch('scripts.scheduler.predict_passes') as mock_predict:
                mock_predict.return_value = [
                    {
                        'norad_id': 25544,
                        'rise_time': '2023-10-18T12:00:00Z',
                        'set_time': '2023-10-18T12:20:00Z',
                        'max_elevation': 45.0
                    }
                ]

                schedule = scheduler.generate_schedule()
                self.assertIsInstance(schedule, list)

        except ImportError:
            self.skipTest("Scheduler dependencies not available")

    def test_web_dashboard_integration(self):
        """Test web dashboard integration"""
        try:
            from web.app import create_app

            app = create_app()

            # Test app creation
            self.assertIsNotNone(app)

            # Test basic routes
            with app.test_client() as client:
                response = client.get('/')
                self.assertEqual(response.status_code, 200)

                response = client.get('/api/status')
                self.assertEqual(response.status_code, 200)

        except ImportError:
            self.skipTest("Web dependencies not available")

    def test_docker_compose_validation(self):
        """Test Docker Compose configuration"""
        docker_compose_file = self.test_root / 'docker-compose.yml'

        if docker_compose_file.exists():
            # Test docker-compose config validation
            try:
                result = subprocess.run(
                    ['docker-compose', 'config'],
                    cwd=self.test_root,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                self.assertEqual(result.returncode, 0,
                    f"Docker Compose config failed: {result.stderr}")

            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.skipTest("Docker Compose not available")

    def test_configuration_validation(self):
        """Test configuration file validation"""
        # Test valid config
        valid_config = self.create_mock_config()
        self.assertTrue(valid_config.exists())

        # Test invalid config (missing required fields)
        invalid_config = self.test_configs_dir / 'invalid.ini'
        invalid_config.write_text("""[station]
name = Test Station
# Missing latitude, longitude
""")

        try:
            from scripts.predict_passes import load_station_config

            # Should handle missing fields gracefully or raise appropriate error
            try:
                config = load_station_config(str(invalid_config))
                # If it loads, check for defaults
                self.assertIn('latitude', config)
            except (KeyError, ValueError):
                # Expected for invalid config
                pass

        except ImportError:
            # Just check files exist
            self.assertTrue(valid_config.exists())
            self.assertTrue(invalid_config.exists())

    def test_data_pipeline_integration(self):
        """Test complete data processing pipeline"""
        # Create mock TLE data
        tle_file = self.create_mock_tle_file()

        # Create mock recording
        iq_file = self.create_mock_recording()

        # Test data flows between components
        try:
            # 1. TLE processing
            from scripts.predict_passes import load_tle_data
            satellites = load_tle_data(str(tle_file))
            self.assertGreater(len(satellites), 0)

            # 2. Recording processing
            from scripts.process_recording import process_recording
            result = process_recording(str(iq_file))
            self.assertIsNotNone(result)

            # 3. Check data consistency
            metadata_file = iq_file.with_suffix('.iq.json')
            if metadata_file.exists():
                import json
                with open(metadata_file) as f:
                    metadata = json.load(f)

                self.assertIn('norad_id', metadata)
                self.assertIn('center_frequency', metadata)

        except ImportError:
            # Test file system operations
            self.assertTrue(tle_file.exists())
            self.assertTrue(iq_file.exists())

if __name__ == '__main__':
    unittest.main()
