#!/usr/bin/env python3
"""
Train the SATx signal detection CNN model.
Trains on spectrogram tiles to classify signal vs noise.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import os
import argparse
import logging
from pathlib import Path
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
from datetime import datetime

from model import SignalDetectorCNN

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SpectrogramDataset(Dataset):
    """Dataset for spectrogram tiles."""

    def __init__(self, data_dir, transform=None):
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.samples = []

        # Load signal samples
        signal_dir = self.data_dir / 'signal'
        if signal_dir.exists():
            for file_path in signal_dir.glob('*.npy'):
                self.samples.append((file_path, 1))  # 1 = signal

        # Load noise samples
        noise_dir = self.data_dir / 'noise'
        if noise_dir.exists():
            for file_path in noise_dir.glob('*.npy'):
                self.samples.append((file_path, 0))  # 0 = noise

        logger.info(f"Loaded {len(self.samples)} samples")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        file_path, label = self.samples[idx]

        # Load spectrogram tile
        spectrogram = np.load(file_path)

        # Convert to tensor
        spectrogram = torch.from_numpy(spectrogram).float().unsqueeze(0)  # Add channel dimension

        if self.transform:
            spectrogram = self.transform(spectrogram)

        return spectrogram, label

def train_model(model, train_loader, val_loader, num_epochs=50, device='cpu'):
    """Train the model."""
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.1)

    best_accuracy = 0.0
    train_losses = []
    val_accuracies = []

    for epoch in range(num_epochs):
        # Training phase
        model.train()
        running_loss = 0.0

        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()

        epoch_loss = running_loss / len(train_loader)
        train_losses.append(epoch_loss)

        # Validation phase
        model.eval()
        correct = 0
        total = 0

        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

        accuracy = 100 * correct / total
        val_accuracies.append(accuracy)

        logger.info(f'Epoch {epoch+1}/{num_epochs}, Loss: {epoch_loss:.4f}, Accuracy: {accuracy:.2f}%')

        # Save best model
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            torch.save(model.state_dict(), 'model.pth')
            logger.info(f'Saved best model with accuracy: {accuracy:.2f}%')

        scheduler.step()

    return train_losses, val_accuracies

def evaluate_model(model, test_loader, device='cpu'):
    """Evaluate the model on test data."""
    model.eval()
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            _, predicted = torch.max(outputs.data, 1)

            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    # Print metrics
    logger.info("Classification Report:")
    logger.info(classification_report(all_labels, all_preds, target_names=['noise', 'signal']))

    logger.info("Confusion Matrix:")
    cm = confusion_matrix(all_labels, all_preds)
    logger.info(cm)

def plot_training_history(train_losses, val_accuracies, save_path='training_history.png'):
    """Plot training history."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    ax1.plot(train_losses, label='Training Loss')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.set_title('Training Loss')
    ax1.legend()

    ax2.plot(val_accuracies, label='Validation Accuracy', color='orange')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Accuracy (%)')
    ax2.set_title('Validation Accuracy')
    ax2.legend()

    plt.tight_layout()
    plt.savefig(save_path)
    logger.info(f"Saved training history to {save_path}")

def main():
    parser = argparse.ArgumentParser(description='Train SATx signal detection model')
    parser.add_argument('--data-dir', default='models/training_data', help='Training data directory')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    parser.add_argument('--epochs', type=int, default=50, help='Number of epochs')
    parser.add_argument('--val-split', type=float, default=0.2, help='Validation split ratio')
    parser.add_argument('--test-split', type=float, default=0.1, help='Test split ratio')
    parser.add_argument('--device', default='auto', help='Device to use (cpu/cuda/auto)')

    args = parser.parse_args()

    # Set device
    if args.device == 'auto':
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    else:
        device = torch.device(args.device)

    logger.info(f"Using device: {device}")

    # Load dataset
    dataset = SpectrogramDataset(args.data_dir)

    if len(dataset) == 0:
        logger.error(f"No training data found in {args.data_dir}")
        logger.error("Run prepare_training_data.py first")
        exit(1)

    # Split dataset
    total_size = len(dataset)
    test_size = int(args.test_split * total_size)
    val_size = int(args.val_split * total_size)
    train_size = total_size - val_size - test_size

    train_dataset, val_dataset, test_dataset = torch.utils.data.random_split(
        dataset, [train_size, val_size, test_size]
    )

    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False)

    logger.info(f"Train: {train_size}, Val: {val_size}, Test: {test_size}")

    # Initialize model
    model = SignalDetectorCNN()
    model.to(device)

    # Train model
    logger.info("Starting training...")
    train_losses, val_accuracies = train_model(model, train_loader, val_loader, args.epochs, device)

    # Plot training history
    plot_training_history(train_losses, val_accuracies)

    # Evaluate on test set
    logger.info("Evaluating on test set...")
    evaluate_model(model, test_loader, device)

    logger.info("Training complete!")

if __name__ == '__main__':
    main()
