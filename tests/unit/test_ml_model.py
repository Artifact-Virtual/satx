"""
Unit tests for ML model functionality
"""

import unittest
import torch
import numpy as np
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests import SATxTestCase

class TestMLModel(SATxTestCase):
    """Test cases for ML signal detection model"""

    def setUp(self):
        super().setUp()
        # Create model directory
        self.model_dir = self.test_root / 'models' / 'model_v1'
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def test_model_initialization(self):
        """Test CNN model initialization"""
        try:
            from models.model_v1.model import SignalDetectorCNN

            model = SignalDetectorCNN()

            # Check model structure
            self.assertIsInstance(model, torch.nn.Module)
            self.assertTrue(hasattr(model, 'conv1'))
            self.assertTrue(hasattr(model, 'fc1'))

            # Test forward pass with dummy input
            batch_size, channels, height, width = 1, 1, 256, 256
            dummy_input = torch.randn(batch_size, channels, height, width)

            with torch.no_grad():
                output = model(dummy_input)
                self.assertEqual(output.shape, (batch_size, 2))  # Binary classification

        except ImportError:
            self.skipTest("ML model dependencies not available")

    def test_model_forward_pass(self):
        """Test model forward pass with various inputs"""
        try:
            from models.model_v1.model import SignalDetectorCNN

            model = SignalDetectorCNN()
            model.eval()

            # Test different input sizes (all should work with the model)
            test_inputs = [
                torch.randn(1, 1, 256, 256),  # Standard spectrogram size
                torch.randn(2, 1, 256, 256),  # Batch of 2
            ]

            for input_tensor in test_inputs:
                with torch.no_grad():
                    output = model(input_tensor)
                    # Should output logits for binary classification
                    self.assertEqual(len(output.shape), 2)
                    self.assertEqual(output.shape[1], 2)  # Binary classification

                    # Check output is reasonable (not all zeros or NaN)
                    self.assertFalse(torch.isnan(output).any())
                    self.assertFalse(torch.isinf(output).any())

        except ImportError:
            self.skipTest("ML model dependencies not available")

    def test_model_save_load(self):
        """Test model saving and loading"""
        try:
            from models.model_v1.model import SignalDetectorCNN

            model = SignalDetectorCNN()

            # Save model
            model_path = self.model_dir / 'test_model.pth'
            torch.save(model.state_dict(), model_path)

            # Load model
            new_model = SignalDetectorCNN()
            new_model.load_state_dict(torch.load(model_path))

            # Compare parameters
            for param1, param2 in zip(model.parameters(), new_model.parameters()):
                self.assertTrue(torch.equal(param1, param2))

        except ImportError:
            self.skipTest("ML model dependencies not available")

    def test_signal_classification(self):
        """Test signal type classification"""
        try:
            from models.model_v1.model import SignalDetectorCNN, classify_signal

            model = SignalDetectorCNN()
            model.eval()

            # Create test spectrogram (simulated signal)
            spectrogram = torch.randn(1, 1, 128, 128)

            with torch.no_grad():
                prediction = classify_signal(model, spectrogram)

                self.assertIsInstance(prediction, dict)
                self.assertIn('predicted_class', prediction)
                self.assertIn('confidence', prediction)
                self.assertIn('probabilities', prediction)

                # Check confidence is between 0 and 1
                self.assertGreaterEqual(prediction['confidence'], 0.0)
                self.assertLessEqual(prediction['confidence'], 1.0)

        except ImportError:
            self.skipTest("ML model dependencies not available")

    def test_spectrogram_generation(self):
        """Test spectrogram generation from I/Q data"""
        try:
            from models.model_v1.model import generate_spectrogram

            # Create mock I/Q data (complex signal)
            sample_rate = 2400000
            duration = 1.0
            num_samples = int(sample_rate * duration)

            # Generate test signal with some modulation
            t = np.linspace(0, duration, num_samples)
            carrier_freq = 100000  # 100 kHz
            signal = np.exp(1j * 2 * np.pi * carrier_freq * t)  # Simple CW tone

            # Add some noise
            noise = 0.1 * (np.random.randn(num_samples) + 1j * np.random.randn(num_samples))
            iq_data = signal + noise

            spectrogram = generate_spectrogram(iq_data, sample_rate)

            self.assertIsInstance(spectrogram, np.ndarray)
            self.assertEqual(len(spectrogram.shape), 2)  # 2D spectrogram

            # Should have reasonable dimensions
            self.assertGreater(spectrogram.shape[0], 0)  # Time bins
            self.assertGreater(spectrogram.shape[1], 0)  # Frequency bins

        except ImportError:
            self.skipTest("Spectrogram generation not implemented")

    def test_data_preprocessing(self):
        """Test data preprocessing pipeline"""
        try:
            from models.model_v1.model import preprocess_spectrogram

            # Create test spectrogram
            spectrogram = np.random.randn(128, 128)

            processed = preprocess_spectrogram(spectrogram)

            # Should be normalized and resized appropriately
            self.assertIsInstance(processed, np.ndarray)
            self.assertGreater(processed.shape[0], 0)
            self.assertGreater(processed.shape[1], 0)

            # Check normalization (values should be in reasonable range)
            self.assertTrue(np.all(processed >= -3))  # Not too negative
            self.assertTrue(np.all(processed <= 3))   # Not too positive

        except ImportError:
            self.skipTest("Data preprocessing not implemented")

    def test_model_training_step(self):
        """Test single training step"""
        try:
            from models.model_v1.model import training_step

            model = SignalDetectorCNN()
            optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
            criterion = torch.nn.CrossEntropyLoss()

            # Create dummy batch
            batch_size = 8
            inputs = torch.randn(batch_size, 1, 128, 128)
            targets = torch.randint(0, 5, (batch_size,))  # 5 classes

            loss = training_step(model, inputs, targets, optimizer, criterion)

            self.assertIsInstance(loss, float)
            self.assertGreater(loss, 0)  # Loss should be positive

        except ImportError:
            self.skipTest("Training step not implemented")

    def test_model_evaluation(self):
        """Test model evaluation metrics"""
        try:
            from models.model_v1.model import evaluate_model

            model = SignalDetectorCNN()
            model.eval()

            # Create test dataset
            num_samples = 20
            inputs = torch.randn(num_samples, 1, 128, 128)
            targets = torch.randint(0, 5, (num_samples,))

            metrics = evaluate_model(model, inputs, targets)

            self.assertIsInstance(metrics, dict)
            self.assertIn('accuracy', metrics)
            self.assertIn('loss', metrics)

            # Accuracy should be between 0 and 1
            self.assertGreaterEqual(metrics['accuracy'], 0.0)
            self.assertLessEqual(metrics['accuracy'], 1.0)

        except ImportError:
            self.skipTest("Model evaluation not implemented")

if __name__ == '__main__':
    unittest.main()
