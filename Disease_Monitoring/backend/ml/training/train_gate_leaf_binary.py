"""
MobileNetV2-based Gate Model Training for Leaf Validation (Binary Classification)
- Classifies tomato leaf images as PASS (valid) or REJECT (corrupted/invalid)
- Training on mixed dataset: 16K real PASS + 1K synthetic REJECT samples
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, random_split
import torchvision.transforms as transforms
from torchvision.models import mobilenet_v2
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
import os
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd

# Configuration
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
BATCH_SIZE = 32
EPOCHS = 25
LEARNING_RATE = 0.001
IMAGE_SIZE = 224
MODEL_SAVE_PATH = Path(__file__).parent.parent / 'models' / 'gate_leaf_binary.pth'
RESULTS_PATH = Path(__file__).parent.parent / 'models' / 'gate_leaf_binary_results.txt'


class BinaryLeafDataset(Dataset):
    """
    Binary classification dataset for leaf validation.
    Labels:
    - 0 = REJECT (corrupted, invalid, low quality)
    - 1 = PASS (valid, healthy tomato leaf)
    """
    
    def __init__(self, csv_path, root_dir, transform=None, debug=False):
        self.data = pd.read_csv(csv_path)
        self.root_dir = Path(root_dir)
        self.transform = transform
        self.debug = debug
        
        # Map label strings to numeric values
        label_map = {
            'PASS': 1,
            'REJECT': 0
        }
        
        # Convert labels to numeric
        self.data['numeric_label'] = self.data['label'].map(label_map)
        
        # Remove any unmapped labels
        self.data = self.data.dropna(subset=['numeric_label'])
        self.data['numeric_label'] = self.data['numeric_label'].astype(int)
        
        if debug:
            print(f"[DEBUG] Dataset loaded: {len(self.data)} samples")
            print(f"[DEBUG] Label distribution:")
            for label_str in ['PASS', 'REJECT']:
                count = (self.data['label'] == label_str).sum()
                pct = (count / len(self.data)) * 100 if len(self.data) > 0 else 0
                print(f"        {label_str}: {count} ({pct:.1f}%)")
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        row = self.data.iloc[idx]
        img_path = self.root_dir / row['image_path']
        label = row['numeric_label']
        
        try:
            image = Image.open(img_path).convert('RGB')
            if self.transform:
                image = self.transform(image)
            return image, label
        except Exception as e:
            if self.debug and idx % 100 == 0:
                print(f"[SKIP] Skipping invalid image: {img_path}")
            return None


def collate_fn(batch):
    """Custom collate function to handle None samples"""
    batch = [sample for sample in batch if sample is not None]
    if len(batch) == 0:
        return None, None
    images, labels = zip(*batch)
    return torch.stack(images, 0), torch.tensor(labels)


class LeafGateModel(nn.Module):
    """MobileNetV2-based Binary Gate Model (PASS/REJECT)"""
    
    def __init__(self, num_classes=2):
        super(LeafGateModel, self).__init__()
        
        # Load pre-trained MobileNetV2
        self.mobilenet = mobilenet_v2(pretrained=True)
        
        # Freeze early layers for transfer learning
        for param in self.mobilenet.features[:12].parameters():
            param.requires_grad = False
        
        # Replace classifier for binary classification
        num_features = self.mobilenet.classifier[1].in_features
        self.mobilenet.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(num_features, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, num_classes)
        )
    
    def forward(self, x):
        return self.mobilenet(x)


def get_transforms():
    """Get data augmentation transforms"""
    train_transform = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                           std=[0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                           std=[0.229, 0.224, 0.225])
    ])
    
    return train_transform, val_transform


def create_datasets():
    """Create binary classification dataset from CSV"""
    print("[*] Loading mixed leaf dataset (PASS + REJECT)...")
    train_transform, val_transform = get_transforms()
    
    # Try different dataset CSV options
    csv_base = Path(__file__).parent.parent.parent / 'datasets' / 'leaf_disease'
    
    csv_options = [
        (csv_base / 'dataset_mixed.csv', 'Mixed (16K PASS + 1K REJECT)'),
        (csv_base / 'dataset_synthetic.csv', 'Synthetic (500 PASS only)'),
        (csv_base / 'dataset.csv', 'Real (16K PASS only)'),
    ]
    
    csv_path = None
    for path, desc in csv_options:
        if path.exists():
            csv_path = path
            print(f"   Using {desc}: {path.name}")
            break
    
    if csv_path is None:
        raise FileNotFoundError(
            f"No dataset found! Expected one of:\n"
            + "\n".join([f"  - {path}" for path, _ in csv_options])
        )
    
    # Root directory where images are stored
    root_dir = Path(__file__).parent.parent.parent / 'datasets'
    
    # Load dataset
    full_dataset = BinaryLeafDataset(csv_path, root_dir, transform=train_transform, debug=True)
    
    print(f"\n[OK] Dataset loaded: {len(full_dataset)} samples")
    
    # Split into train/val (80/20)
    val_size = int(0.2 * len(full_dataset))
    train_size = len(full_dataset) - val_size
    
    train_dataset, val_dataset = random_split(
        full_dataset, 
        [train_size, val_size], 
        generator=torch.Generator().manual_seed(42)
    )
    
    # Apply val_transform to validation set
    val_dataset.dataset.transform = val_transform
    
    print(f"   Train samples: {len(train_dataset)}")
    print(f"   Val samples:   {len(val_dataset)}")
    
    # Show class distribution
    train_labels = []
    for idx in train_dataset.indices:
        train_labels.append(full_dataset.data.iloc[idx]['numeric_label'])
    
    pass_count = sum(1 for l in train_labels if l == 1)
    reject_count = sum(1 for l in train_labels if l == 0)
    
    print(f"\n[*] Training Set Distribution:")
    print(f"    PASS:   {pass_count} ({100*pass_count/len(train_labels):.1f}%)")
    print(f"    REJECT: {reject_count} ({100*reject_count/len(train_labels):.1f}%)")
    
    return train_dataset, val_dataset


def train_epoch(model, train_loader, criterion, optimizer, device, epoch=0, debug_every=5):
    """Train for one epoch with per-class metrics"""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    batch_count = 0
    
    class_correct = [0, 0]  # [REJECT, PASS]
    class_total = [0, 0]
    
    for batch_idx, (images, labels) in enumerate(train_loader):
        if images is None or labels is None:
            continue
        
        images = images.to(device)
        labels = labels.to(device).long()
        
        # Forward pass
        outputs = model(images)
        loss = criterion(outputs, labels)
        
        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        # Statistics
        running_loss += loss.item()
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
        
        # Per-class accuracy
        for i in range(2):
            class_total[i] += (labels == i).sum().item()
            class_correct[i] += ((predicted == i) & (labels == i)).sum().item()
        
        batch_count += 1
        
        # Debug output
        if batch_count % debug_every == 0:
            batch_loss = loss.item()
            batch_acc = (predicted == labels).sum().item() / labels.size(0)
            label_counts = torch.bincount(labels.cpu(), minlength=2)
            print(f"  [Batch {batch_count}] Loss: {batch_loss:.4f}, Acc: {batch_acc:.4f}, "
                  f"Labels (REJECT/PASS): {label_counts[0]}/{label_counts[1]}")
    
    if total == 0:
        return 0.0, 0.0
    
    epoch_loss = running_loss / max(1, batch_count)
    epoch_acc = correct / total
    
    return epoch_loss, epoch_acc


def validate(model, val_loader, criterion, device):
    """Validate model"""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    batch_count = 0
    
    with torch.no_grad():
        for images, labels in val_loader:
            if images is None or labels is None:
                continue
            
            images = images.to(device)
            labels = labels.to(device).long()
            
            outputs = model(images)
            loss = criterion(outputs, labels)
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            batch_count += 1
    
    if total == 0:
        return 0.0, 0.0
    
    epoch_loss = running_loss / max(1, batch_count)
    epoch_acc = correct / total
    
    return epoch_loss, epoch_acc


def plot_results(train_losses, val_losses, train_accs, val_accs):
    """Plot training results"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Loss plot
    axes[0].plot(train_losses, label='Training Loss', marker='o')
    axes[0].plot(val_losses, label='Validation Loss', marker='s')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Training and Validation Loss')
    axes[0].legend()
    axes[0].grid(True)
    
    # Accuracy plot
    axes[1].plot(train_accs, label='Training Accuracy', marker='o')
    axes[1].plot(val_accs, label='Validation Accuracy', marker='s')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Accuracy')
    axes[1].set_title('Training and Validation Accuracy')
    axes[1].legend()
    axes[1].grid(True)
    
    plt.tight_layout()
    plt.savefig(
        Path(__file__).parent.parent / 'models' / 'gate_leaf_binary_training_results.png', 
        dpi=150
    )
    print("[OK] Training plot saved!")


def train_model():
    """Main training function"""
    print("\n" + "=" * 70)
    print("[START] MobileNetV2 Binary Gate Model Training (PASS/REJECT)")
    print("=" * 70 + "\n")
    
    # Create directories
    MODEL_SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Create datasets
    train_dataset, val_dataset = create_datasets()
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset, 
        batch_size=BATCH_SIZE, 
        shuffle=True, 
        collate_fn=collate_fn, 
        num_workers=0
    )
    val_loader = DataLoader(
        val_dataset, 
        batch_size=BATCH_SIZE, 
        shuffle=False, 
        collate_fn=collate_fn, 
        num_workers=0
    )
    
    print(f"\n[*] Device: {DEVICE}")
    print(f"[*] Batch Size: {BATCH_SIZE}")
    print(f"[*] Epochs: {EPOCHS}")
    print(f"[*] Learning Rate: {LEARNING_RATE}\n")
    
    # Create model
    print("[*] Creating MobileNetV2 model...")
    model = LeafGateModel(num_classes=2).to(DEVICE)
    
    # Print model info
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"   Total Parameters: {total_params:,}")
    print(f"   Trainable Parameters: {trainable_params:,}\n")
    
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, 
        mode='min', 
        factor=0.5, 
        patience=3
    )
    
    # Training loop
    train_losses = []
    val_losses = []
    train_accs = []
    val_accs = []
    best_val_acc = 0
    
    print("[START] Beginning Training Phase\n")
    print(f"{'Epoch':<8} {'Train Loss':<14} {'Train Acc':<12} {'Val Loss':<14} {'Val Acc':<12} Status")
    print("-" * 80)
    
    for epoch in range(EPOCHS):
        train_loss, train_acc = train_epoch(
            model, train_loader, criterion, optimizer, DEVICE, 
            epoch=epoch, debug_every=5
        )
        val_loss, val_acc = validate(model, val_loader, criterion, DEVICE)
        
        train_losses.append(train_loss)
        val_losses.append(val_loss)
        train_accs.append(train_acc)
        val_accs.append(val_acc)
        
        scheduler.step(val_loss)
        
        # Print progress
        status = ""
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), MODEL_SAVE_PATH)
            status = "[SAVE] Best Model"
        
        print(f"{epoch+1:<8} {train_loss:<14.4f} {train_acc:<12.4f} "
              f"{val_loss:<14.4f} {val_acc:<12.4f} {status}")
    
    print("\n" + "=" * 70)
    print("[DONE] Training Complete!")
    print("=" * 70 + "\n")
    
    # Plot results
    plot_results(train_losses, val_losses, train_accs, val_accs)
    
    # Save results to file
    with open(RESULTS_PATH, 'w') as f:
        f.write("MobileNetV2 Binary Gate Model - PASS/REJECT Classification\n")
        f.write("=" * 70 + "\n")
        f.write(f"Training Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Device: {DEVICE}\n")
        f.write(f"Total Parameters: {total_params:,}\n")
        f.write(f"Trainable Parameters: {trainable_params:,}\n\n")
        
        f.write("TRAINING CONFIGURATION\n")
        f.write(f"Batch Size: {BATCH_SIZE}\n")
        f.write(f"Epochs: {EPOCHS}\n")
        f.write(f"Learning Rate: {LEARNING_RATE}\n")
        f.write(f"Optimizer: Adam with ReduceLROnPlateau scheduler\n\n")
        
        f.write("FINAL RESULTS\n")
        f.write(f"Best Validation Accuracy: {best_val_acc:.4f}\n")
        f.write(f"Final Training Loss: {train_losses[-1]:.4f}\n")
        f.write(f"Final Training Accuracy: {train_accs[-1]:.4f}\n")
        f.write(f"Final Validation Loss: {val_losses[-1]:.4f}\n")
        f.write(f"Final Validation Accuracy: {val_accs[-1]:.4f}\n\n")
        
        f.write("MODEL CHECKPOINT\n")
        f.write(f"Saved at: {MODEL_SAVE_PATH}\n\n")
        
        f.write("USAGE\n")
        f.write("Load model:\n")
        f.write("  model = LeafGateModel()\n")
        f.write("  model.load_state_dict(torch.load('gate_leaf_binary.pth'))\n")
        f.write("  model.eval()\n")
    
    print(f"[OK] Results saved to: {RESULTS_PATH}")
    print(f"[OK] Model saved to: {MODEL_SAVE_PATH}")


if __name__ == "__main__":
    train_model()
