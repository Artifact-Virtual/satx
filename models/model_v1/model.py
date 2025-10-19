"""
Simple CNN model for satellite signal detection.
Classifies spectrogram tiles as signal or noise.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class SignalDetectorCNN(nn.Module):
    """
    Convolutional Neural Network for signal detection in spectrograms.
    
    Input: (batch, 1, 256, 256) - Grayscale spectrogram tiles
    Output: (batch, 2) - Binary classification (signal/noise)
    """
    
    def __init__(self):
        super(SignalDetectorCNN, self).__init__()
        
        # Convolutional layers
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(2, 2)  # 256 -> 128
        
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d(2, 2)  # 128 -> 64
        
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.pool3 = nn.MaxPool2d(2, 2)  # 64 -> 32
        
        self.conv4 = nn.Conv2d(128, 256, kernel_size=3, padding=1)
        self.bn4 = nn.BatchNorm2d(256)
        self.pool4 = nn.MaxPool2d(2, 2)  # 32 -> 16
        
        # Fully connected layers
        self.fc1 = nn.Linear(256 * 16 * 16, 512)
        self.dropout1 = nn.Dropout(0.5)
        
        self.fc2 = nn.Linear(512, 128)
        self.dropout2 = nn.Dropout(0.3)
        
        self.fc3 = nn.Linear(128, 2)  # Binary classification
        
    def forward(self, x):
        # Conv block 1
        x = self.pool1(F.relu(self.bn1(self.conv1(x))))
        
        # Conv block 2
        x = self.pool2(F.relu(self.bn2(self.conv2(x))))
        
        # Conv block 3
        x = self.pool3(F.relu(self.bn3(self.conv3(x))))
        
        # Conv block 4
        x = self.pool4(F.relu(self.bn4(self.conv4(x))))
        
        # Flatten
        x = x.view(-1, 256 * 16 * 16)
        
        # Fully connected layers
        x = F.relu(self.fc1(x))
        x = self.dropout1(x)
        
        x = F.relu(self.fc2(x))
        x = self.dropout2(x)
        
        x = self.fc3(x)
        
        return x


def create_model():
    """Factory function to create model instance."""
    return SignalDetectorCNN()


if __name__ == '__main__':
    # Test model
    model = create_model()
    
    # Test input
    x = torch.randn(4, 1, 256, 256)
    
    # Forward pass
    output = model(x)
    
    print(f"Model created successfully")
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Total parameters: {sum(p.numel() for p in model.parameters())}")
