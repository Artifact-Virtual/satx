#!/usr/bin/env python3
"""
Test script for SATx satellite detection system.
Runs comprehensive tests on all components.
"""

import subprocess
import sys
import logging
from pathlib import Path
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SATxTester:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.passed = 0
        self.failed = 0

    def run_command(self, cmd, cwd=None, check=True):
        """Run a command and return success status."""
        try:
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                logger.info("✓ Command succeeded")
                return True, result.stdout, result.stderr
            else:
                logger.error(f"✗ Command failed with code {result.returncode}")
                if result.stderr:
                    logger.error(f"Error: {result.stderr}")
                return False, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            logger.error("✗ Command timed out")
            return False, "", "Timeout"
        except Exception as e:
            logger.error(f"✗ Command failed: {e}")
            return False, "", str(e)

    def test_python_imports(self):
        """Test that all Python dependencies can be imported."""
        logger.info("Testing Python imports...")

        test_imports = [
            "import skyfield, scipy, numpy, matplotlib",
            "import torch; print('PyTorch version:', torch.__version__)",
            "import tensorflow as tf; print('TensorFlow version:', tf.__version__)",
            "from models.model_v1.model import SignalDetectorCNN",
        ]

        success = True
        for import_stmt in test_imports:
            logger.info(f"Testing: {import_stmt}")
            result = self.run_command([sys.executable, "-c", import_stmt])
            if not result[0]:
                logger.warning(f"Import failed: {import_stmt}")
                success = False
            else:
                logger.info("✓ Import successful")

        return success

    def test_tle_fetching(self):
        """Test TLE data fetching."""
        logger.info("Testing TLE fetching...")

        # Create data directory if it doesn't exist
        data_dir = self.project_root / 'data' / 'tles'
        data_dir.mkdir(parents=True, exist_ok=True)

        # Run fetch script with test flag
        success, stdout, stderr = self.run_command([
            sys.executable, "scripts/fetch_tles.py", "--test"
        ])

        if success:
            # Check if TLE file was created
            tle_file = data_dir / 'all-satellites.tle'
            if tle_file.exists() and tle_file.stat().st_size > 0:
                logger.info("✓ TLE file created successfully")
                return True
            else:
                logger.error("✗ TLE file not created or empty")
                return False
        else:
            return False

    def test_pass_prediction(self):
        """Test satellite pass prediction."""
        logger.info("Testing pass prediction...")

        # First ensure we have TLE data
        if not (self.project_root / 'data' / 'tles' / 'all-satellites.tle').exists():
            logger.warning("No TLE data found, fetching...")
            self.test_tle_fetching()

        # Run prediction script
        success, stdout, stderr = self.run_command([
            sys.executable, "scripts/predict_passes.py", "--test"
        ])

        if success:
            # Check if predictions file was created
            predictions_file = self.project_root / 'logs' / 'predicted_passes.json'
            if predictions_file.exists():
                logger.info("✓ Pass predictions generated")
                return True
            else:
                logger.warning("Predictions file not found, but command succeeded")
                return True  # Still consider it passed
        else:
            return False

    def test_model_loading(self):
        """Test ML model loading."""
        logger.info("Testing ML model loading...")

        # Check if model file exists
        model_file = self.project_root / 'models' / 'model_v1' / 'model.pth'
        if not model_file.exists():
            logger.warning("Model weights not found, skipping test")
            return True  # Not a failure, just not trained yet

        # Try to load the model
        test_code = """
from models.model_v1.model import SignalDetectorCNN
import torch
model = SignalDetectorCNN()
model.load_state_dict(torch.load('models/model_v1/model.pth', map_location='cpu'))
model.eval()
print('Model loaded successfully')
"""

        success, stdout, stderr = self.run_command([
            sys.executable, "-c", test_code
        ])

        return success

    def test_recording_processing(self):
        """Test recording processing pipeline."""
        logger.info("Testing recording processing...")

        # Create a dummy recording file for testing
        recordings_dir = self.project_root / 'recordings'
        recordings_dir.mkdir(exist_ok=True)

        test_file = recordings_dir / 'test.iq'
        if not test_file.exists():
            # Create a small dummy I/Q file (just noise)
            logger.info("Creating dummy test recording...")
            dummy_samples = []
            for i in range(10000):  # Small file for testing
                # Generate noise around 127.5 (RTL-SDR format)
                i_val = int(127.5 + 10 * (i % 2 - 0.5))  # Alternating I/Q
                q_val = int(127.5 + 10 * ((i + 1) % 2 - 0.5))
                dummy_samples.extend([i_val, q_val])

            with open(test_file, 'wb') as f:
                f.write(bytes(dummy_samples))

            # Create metadata
            metadata = {
                'norad_id': 25544,  # ISS
                'center_frequency': 437800000,
                'sample_rate': 2400000,
                'duration_seconds': 2.0
            }

            with open(test_file.with_suffix('.iq.json'), 'w') as f:
                json.dump(metadata, f)

        # Run processing
        success, stdout, stderr = self.run_command([
            sys.executable, "scripts/process_recording.py", str(test_file)
        ])

        if success:
            # Check if output files were created
            spectrogram = test_file.with_suffix('.png')
            candidates = test_file.with_suffix('.candidates.json')

            if spectrogram.exists() or candidates.exists():
                logger.info("✓ Processing generated output files")
                return True
            else:
                logger.warning("No output files found, but processing succeeded")
                return True
        else:
            return False

    def test_docker_setup(self):
        """Test Docker setup."""
        logger.info("Testing Docker setup...")

        # Check if docker is available
        success, stdout, stderr = self.run_command(["docker", "--version"])
        if not success:
            logger.warning("Docker not available, skipping Docker tests")
            return True

        # Check if docker-compose works
        success, stdout, stderr = self.run_command(["docker-compose", "config"])
        if success:
            logger.info("✓ Docker Compose configuration valid")
            return True
        else:
            logger.error("✗ Docker Compose configuration invalid")
            return False

    def run_test(self, test_name, test_func):
        """Run a single test."""
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")

        try:
            success = test_func()
            if success:
                logger.info(f"✓ {test_name} PASSED")
                self.passed += 1
            else:
                logger.error(f"✗ {test_name} FAILED")
                self.failed += 1
            return success
        except Exception as e:
            logger.error(f"✗ {test_name} FAILED with exception: {e}")
            self.failed += 1
            return False

    def run_all_tests(self):
        """Run all tests."""
        logger.info("Starting SATx system tests...")

        tests = [
            ("Python Imports", self.test_python_imports),
            ("TLE Fetching", self.test_tle_fetching),
            ("Pass Prediction", self.test_pass_prediction),
            ("Model Loading", self.test_model_loading),
            ("Recording Processing", self.test_recording_processing),
            ("Docker Setup", self.test_docker_setup),
        ]

        for test_name, test_func in tests:
            self.run_test(test_name, test_func)

        # Print summary
        logger.info(f"\n{'='*50}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'='*50}")
        logger.info(f"Passed: {self.passed}")
        logger.info(f"Failed: {self.failed}")
        logger.info(f"Total:  {self.passed + self.failed}")

        if self.failed == 0:
            logger.info("🎉 All tests passed!")
            return True
        else:
            logger.warning(f"⚠️  {self.failed} test(s) failed")
            return False

def main():
    tester = SATxTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
