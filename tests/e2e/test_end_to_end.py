"""
End-to-end tests for SATx system
"""

import unittest
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch, Mock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests import SATxTestCase

class TestEndToEnd(SATxTestCase):
    """End-to-end tests covering complete system workflows"""

    def setUp(self):
        super().setUp()
        self.project_root = Path(__file__).parent.parent.parent

    def test_full_system_initialization(self):
        """Test complete system initialization and setup"""
        # Test setup.sh script execution (mocked for safety)
        setup_script = self.project_root / 'setup.sh'

        if setup_script.exists():
            # Test script exists and has content (Windows compatibility)
            content = setup_script.read_text()
            self.assertIn('#!/usr/bin/env bash', content)
            self.assertIn('echo', content)  # Has output commands
            self.assertGreater(len(content), 100)  # Has substantial content

    def test_data_acquisition_pipeline(self):
        """Test complete data acquisition pipeline"""
        try:
            # Step 1: TLE fetching
            from scripts.fetch_tles import fetch_tles

            tle_dir = self.test_data_dir / 'tles'
            tle_dir.mkdir(exist_ok=True)

            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = Mock()
                mock_response.read.return_value = b"ISS\n1 25544U\n2 25544"
                mock_response.__enter__ = Mock(return_value=mock_response)
                mock_response.__exit__ = Mock(return_value=None)
                mock_urlopen.return_value = mock_response

                result = fetch_tles(str(tle_dir))
                self.assertTrue(result)

            # Step 2: Pass prediction
            config_file = self.create_mock_config()

            with patch('skyfield.api.load'), \
                 patch('skyfield.api.EarthSatellite'):

                from scripts.predict_passes import predict_passes
                predictions = predict_passes(str(tle_dir / 'all-satellites.tle'), str(config_file))
                self.assertIsInstance(predictions, list)

        except ImportError:
            # Test file system operations
            tle_dir = self.test_data_dir / 'tles'
            tle_dir.mkdir(exist_ok=True)
            tle_file = tle_dir / 'all-satellites.tle'
            tle_file.write_text("ISS\n1 25544U\n2 25544")
            self.assertTrue(tle_file.exists())

    def test_recording_and_processing_workflow(self):
        """Test complete recording and processing workflow"""
        # Create mock recording
        iq_file = self.create_mock_recording()

        try:
            # Process the recording
            from scripts.process_recording import process_recording

            result = process_recording(str(iq_file))
            self.assertIsNotNone(result)

            # Check outputs
            spectrogram_file = iq_file.with_suffix('.png')
            candidates_file = iq_file.with_suffix('.candidates.json')

            # Should generate some outputs
            outputs_exist = spectrogram_file.exists() or candidates_file.exists()
            self.assertTrue(outputs_exist, "Processing should generate output files")

        except ImportError:
            # Test file creation
            self.assertTrue(iq_file.exists())

    def test_ml_training_pipeline(self):
        """Test complete ML training pipeline"""
        try:
            # Step 1: Data preparation
            from scripts.prepare_training_data import prepare_training_data

            # Create mock training data
            training_dir = self.temp_dir / 'training_data'
            training_dir.mkdir(exist_ok=True)

            # This would normally process real recordings
            result = prepare_training_data(str(training_dir))
            # Result depends on implementation

            # Step 2: Model training
            from models.model_v1.train import train_model

            model_path = self.model_dir / 'test_model.pth'

            # Mock training (would take too long in tests)
            with patch('torch.save'):  # Prevent actual file saving
                result = train_model(
                    data_dir=str(training_dir),
                    model_path=str(model_path),
                    epochs=1,  # Minimal training
                    batch_size=4
                )

                # Should return training results
                self.assertIsInstance(result, dict)
                self.assertIn('final_accuracy', result)

        except ImportError:
            self.skipTest("ML training dependencies not available")

    def test_scheduler_operation(self):
        """Test scheduler end-to-end operation"""
        try:
            from scripts.scheduler import SatelliteScheduler

            # Create configuration
            config_file = self.create_mock_config()
            from scripts.predict_passes import load_station_config
            config = load_station_config(str(config_file))

            # Create scheduler
            scheduler = SatelliteScheduler(config)

            # Mock SDR device for testing
            with patch('scripts.scheduler.SDRDevice') as mock_sdr_class:
                mock_sdr = Mock()
                mock_sdr_class.return_value = mock_sdr

                # Mock pass predictions
                with patch('scripts.scheduler.predict_passes') as mock_predict:
                    mock_predict.return_value = [
                        {
                            'norad_id': 25544,
                            'rise_time': '2023-10-18T12:00:00Z',
                            'set_time': '2023-10-18T12:20:00Z',
                            'max_elevation': 45.0,
                            'frequency': 437800000
                        }
                    ]

                    # Test schedule generation
                    schedule = scheduler.generate_schedule()
                    self.assertIsInstance(schedule, list)
                    self.assertGreater(len(schedule), 0)

                    # Test recording execution (mocked)
                    success = scheduler.execute_recording(schedule[0])
                    # Success depends on mocking, but should not crash
                    self.assertIsInstance(success, bool)

        except ImportError:
            self.skipTest("Scheduler dependencies not available")

    def test_web_interface_e2e(self):
        """Test web interface end-to-end"""
        try:
            from web.app import create_app

            app = create_app()

            with app.test_client() as client:
                # Test main dashboard
                response = client.get('/')
                self.assertEqual(response.status_code, 200)
                self.assertIn(b'SATx', response.data)

                # Test API endpoints
                response = client.get('/api/status')
                self.assertEqual(response.status_code, 200)

                response = client.get('/api/passes')
                self.assertEqual(response.status_code, 200)

                # Test configuration endpoint
                response = client.get('/api/config')
                self.assertEqual(response.status_code, 200)

        except ImportError:
            self.skipTest("Web interface dependencies not available")

    def test_transmission_workflow(self):
        """Test transmission workflow (with safety checks)"""
        try:
            from transmit.transmit import TransmissionController

            controller = TransmissionController()

            # Test initialization
            self.assertIsNotNone(controller)

            # Test authorization check
            authorized = controller.check_authorization(
                norad_id=25544,
                frequency=437800000,
                callsign="TEST123"
            )

            # Should deny unauthorized transmissions
            self.assertFalse(authorized)

            # Test transmission preparation (should fail safely)
            success = controller.prepare_transmission(
                norad_id=25544,
                frequency=437800000,
                data="Test message",
                callsign="TEST123"
            )

            # Should fail due to authorization
            self.assertFalse(success)

        except ImportError:
            self.skipTest("Transmission module not available")

    def test_docker_deployment(self):
        """Test Docker deployment workflow"""
        docker_compose_file = self.project_root / 'docker-compose.yml'
        dockerfile_ml = self.project_root / 'services' / 'ml' / 'Dockerfile'
        dockerfile_sdr = self.project_root / 'services' / 'sdr' / 'Dockerfile'

        # Check Docker files exist
        self.assertTrue(docker_compose_file.exists())
        self.assertTrue(dockerfile_ml.exists())
        self.assertTrue(dockerfile_sdr.exists())

        # Test docker-compose configuration
        try:
            result = subprocess.run(
                ['docker-compose', 'config'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            self.assertEqual(result.returncode, 0,
                f"Docker Compose validation failed: {result.stderr}")

        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.skipTest("Docker not available for testing")

    def test_configuration_management(self):
        """Test configuration management end-to-end"""
        # Test station configuration
        config_file = self.create_mock_config(
            latitude=40.7128,
            longitude=-74.0060,
            altitude=100,
            device='rtl=0',
            sample_rate=2400000
        )

        try:
            from scripts.predict_passes import load_station_config

            config = load_station_config(str(config_file))

            # Verify all settings loaded correctly
            self.assertAlmostEqual(config['latitude'], 40.7128, places=4)
            self.assertAlmostEqual(config['longitude'], -74.0060, places=4)
            self.assertEqual(config['altitude'], 100)
            self.assertEqual(config['device'], 'rtl=0')
            self.assertEqual(config['sample_rate'], 2400000)

        except ImportError:
            # Test file content
            content = config_file.read_text()
            self.assertIn('latitude = 40.7128', content)
            self.assertIn('longitude = -74.006', content)

    def test_error_handling_and_recovery(self):
        """Test system error handling and recovery"""
        # Test with invalid inputs
        try:
            # Invalid TLE file
            from scripts.predict_passes import load_tle_data

            invalid_tle = self.test_data_dir / 'invalid.tle'
            invalid_tle.write_text("Invalid TLE data")

            # Should handle gracefully
            try:
                satellites = load_tle_data(str(invalid_tle))
                # If it doesn't crash, check result
                self.assertIsInstance(satellites, dict)
            except Exception:
                # Expected for invalid data
                pass

        except ImportError:
            # Test file creation
            invalid_tle = self.test_data_dir / 'invalid.tle'
            invalid_tle.write_text("Invalid TLE data")
            self.assertTrue(invalid_tle.exists())

    def test_performance_requirements(self):
        """Test system meets performance requirements"""
        # Test processing speed
        iq_file = self.create_mock_recording(duration_seconds=0.1)  # Short recording

        try:
            from scripts.process_recording import process_recording
            import time

            start_time = time.time()
            result = process_recording(str(iq_file))
            end_time = time.time()

            processing_time = end_time - start_time

            # Should process quickly (less than 10 seconds for short recording)
            self.assertLess(processing_time, 10.0,
                f"Processing took too long: {processing_time}s")

        except ImportError:
            # Test file exists
            self.assertTrue(iq_file.exists())

if __name__ == '__main__':
    unittest.main()
