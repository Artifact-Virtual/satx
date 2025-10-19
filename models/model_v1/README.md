# Model v1 - Signal Detector CNN

## Overview

Simple CNN for binary classification of spectrogram tiles:
- **Input:** 256×256 grayscale spectrogram
- **Output:** Signal (1) or Noise (0)

## Architecture

```
Input (1, 256, 256)
    ↓
Conv2D(32) + BN + ReLU + MaxPool → (32, 128, 128)
    ↓
Conv2D(64) + BN + ReLU + MaxPool → (64, 64, 64)
    ↓
Conv2D(128) + BN + ReLU + MaxPool → (128, 32, 32)
    ↓
Conv2D(256) + BN + ReLU + MaxPool → (256, 16, 16)
    ↓
Flatten → (65536)
    ↓
FC(512) + ReLU + Dropout(0.5)
    ↓
FC(128) + ReLU + Dropout(0.3)
    ↓
FC(2) → Output
```

## Parameters

- Total parameters: ~17M
- Training epochs: 50
- Batch size: 32
- Learning rate: 0.001
- Optimizer: Adam

## Training Data

Train on labeled spectrograms from:
1. SatNOGS database (download observations)
2. Self-recorded passes (manually labeled)
3. Synthetic noise samples

**Required labels:**
- `signal`: Contains satellite transmission
- `noise`: Empty spectrum / background only

## Usage

```python
import torch
from model import create_model

# Load model
model = create_model()
model.load_state_dict(torch.load('model_weights.pth'))
model.eval()

# Prepare input (256x256 grayscale)
spectrogram = torch.randn(1, 1, 256, 256)

# Inference
with torch.no_grad():
    output = model(spectrogram)
    probabilities = torch.softmax(output, dim=1)
    prediction = torch.argmax(probabilities, dim=1)
    
print(f"Prediction: {'Signal' if prediction == 1 else 'Noise'}")
print(f"Confidence: {probabilities[0][prediction].item():.2%}")
```

## Training Script

See `train.py` for complete training pipeline.

## Performance Goals

- Accuracy: >95% on test set
- False positive rate: <5%
- Inference time: <100ms per tile

## Future Improvements

- Multi-class classification (AX.25, AFSK, BPSK, etc.)
- Add attention mechanism
- Use transfer learning from ImageNet
- Data augmentation
