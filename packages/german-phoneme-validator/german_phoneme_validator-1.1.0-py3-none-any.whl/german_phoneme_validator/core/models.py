"""
Model architectures for phoneme classification.
Extracted from hybrid_model_utils.py for standalone use.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math


# ============================================================================
# Model Architecture Components
# ============================================================================

class ResidualBlock2D(nn.Module):
    """Residual block for CNN branch"""
    def __init__(self, in_channels, out_channels, stride=1):
        super(ResidualBlock2D, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, stride=stride)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(out_channels)
        
        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride),
                nn.BatchNorm2d(out_channels)
            )
    
    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += self.shortcut(x)
        out = F.relu(out)
        return out


class EnhancedChannelAttention(nn.Module):
    """Enhanced Channel attention module with improved design"""
    def __init__(self, channels, reduction=8):
        super(EnhancedChannelAttention, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)
        
        # Use smaller reduction for better capacity
        reduced_dim = max(1, channels // reduction)
        
        self.fc = nn.Sequential(
            nn.Linear(channels, reduced_dim, bias=False),
            nn.ReLU(),
            nn.Linear(reduced_dim, channels, bias=False),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        b, c, _, _ = x.size()
        avg_out = self.fc(self.avg_pool(x).view(b, c))
        max_out = self.fc(self.max_pool(x).view(b, c))
        out = avg_out + max_out
        return x * out.view(b, c, 1, 1)


class FeatureAttention(nn.Module):
    """Squeeze-and-Excitation attention for feature vectors"""
    def __init__(self, n_features, reduction=8):
        super(FeatureAttention, self).__init__()
        self.reduction = reduction
        reduced_dim = max(1, n_features // reduction)
        
        self.fc = nn.Sequential(
            nn.Linear(n_features, reduced_dim, bias=False),
            nn.ReLU(),
            nn.Linear(reduced_dim, n_features, bias=False),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        attention_weights = self.fc(x)
        return x * attention_weights


class MultiScaleConvBlock(nn.Module):
    """Multi-scale convolution with parallel 3x3 and 5x5 kernels"""
    def __init__(self, in_channels, out_channels):
        super(MultiScaleConvBlock, self).__init__()
        self.conv3x3 = nn.Sequential(
            nn.Conv2d(in_channels, out_channels // 2, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels // 2),
            nn.ReLU()
        )
        self.conv5x5 = nn.Sequential(
            nn.Conv2d(in_channels, out_channels // 2, kernel_size=5, padding=2),
            nn.BatchNorm2d(out_channels // 2),
            nn.ReLU()
        )
    
    def forward(self, x):
        out3x3 = self.conv3x3(x)
        out5x5 = self.conv5x5(x)
        return torch.cat([out3x3, out5x5], dim=1)


class MultiHeadCrossAttentionFusion(nn.Module):
    """Multi-head cross-attention between CNN and MLP outputs with dropout"""
    def __init__(self, cnn_dim, mlp_dim, hidden_dim=256, num_heads=4, dropout=0.1):
        super(MultiHeadCrossAttentionFusion, self).__init__()
        self.cnn_dim = cnn_dim
        self.mlp_dim = mlp_dim
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads
        self.dropout = dropout
        
        assert hidden_dim % num_heads == 0, "hidden_dim must be divisible by num_heads"
        
        # Projections for multi-head attention
        self.cnn_to_qkv = nn.Linear(cnn_dim, hidden_dim * 3)
        self.mlp_to_qkv = nn.Linear(mlp_dim, hidden_dim * 3)
        
        self.norm1 = nn.LayerNorm(hidden_dim)
        self.norm2 = nn.LayerNorm(hidden_dim)
        self.dropout_layer = nn.Dropout(dropout)
        
        # Projections back to original dimensions
        self.cnn_proj = nn.Linear(hidden_dim, cnn_dim)
        self.mlp_proj = nn.Linear(hidden_dim, mlp_dim)
        
    def forward(self, cnn_out, mlp_out):
        # cnn_out: (batch, cnn_dim)
        # mlp_out: (batch, mlp_dim)
        batch_size = cnn_out.size(0)
        
        # CNN enhanced by MLP (multi-head attention)
        cnn_qkv = self.cnn_to_qkv(cnn_out).reshape(batch_size, 3, self.num_heads, self.head_dim).permute(1, 0, 2, 3)
        cnn_q, cnn_k, cnn_v = cnn_qkv[0], cnn_qkv[1], cnn_qkv[2]  # (batch, num_heads, head_dim)
        
        mlp_qkv = self.mlp_to_qkv(mlp_out).reshape(batch_size, 3, self.num_heads, self.head_dim).permute(1, 0, 2, 3)
        mlp_q, mlp_k, mlp_v = mlp_qkv[0], mlp_qkv[1], mlp_qkv[2]
        
        # Cross-attention: CNN queries attend to MLP keys/values
        scores = torch.matmul(cnn_q, mlp_k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout_layer(attn_weights)  # Add dropout
        cnn_attended = torch.matmul(attn_weights, mlp_v)  # (batch, num_heads, head_dim)
        cnn_attended = cnn_attended.transpose(1, 2).contiguous().view(batch_size, self.hidden_dim)
        cnn_enhanced = cnn_out + self.cnn_proj(self.norm1(cnn_attended))
        
        # MLP enhanced by CNN (multi-head attention)
        scores2 = torch.matmul(mlp_q, cnn_k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        attn_weights2 = F.softmax(scores2, dim=-1)
        attn_weights2 = self.dropout_layer(attn_weights2)  # Add dropout
        mlp_attended = torch.matmul(attn_weights2, cnn_v)
        mlp_attended = mlp_attended.transpose(1, 2).contiguous().view(batch_size, self.hidden_dim)
        mlp_enhanced = mlp_out + self.mlp_proj(self.norm2(mlp_attended))
        
        return cnn_enhanced, mlp_enhanced


class HybridCNNMLP_V4_3(nn.Module):
    """
    Enhanced Hybrid model: CNN for spectrograms + MLP for features
    Version 4.3 Improvements:
    - Multi-Head Cross-Attention Fusion (with dropout)
    - Residual connections in MLP branch
    - Enhanced SE blocks in CNN branch
    - Input validation
    """
    
    def __init__(self, n_features=129, num_classes=2, dropout=0.4):
        super(HybridCNNMLP_V4_3, self).__init__()
        self.n_features = n_features
        self.num_classes = num_classes
        
        # Multi-Scale CNN branch with enhanced attention
        self.cnn_initial = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2)  # (64, 64, 3)
        )
        
        # Multi-scale block
        self.multiscale = MultiScaleConvBlock(64, 128)
        
        self.cnn_branch = nn.Sequential(
            ResidualBlock2D(128, 128),
            EnhancedChannelAttention(128, reduction=8),
            nn.MaxPool2d(2, 2),  # (128, 32, 1)
            
            ResidualBlock2D(128, 256),
            EnhancedChannelAttention(256, reduction=8),
            ResidualBlock2D(256, 512),
            EnhancedChannelAttention(512, reduction=8),
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten()
        )
        
        # MLP branch with feature attention and residual connections
        self.feature_attention = FeatureAttention(n_features, reduction=8)
        
        # First layer
        self.mlp_layer1 = nn.Sequential(
            nn.Linear(n_features, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        # Second layer with residual
        self.mlp_layer2 = nn.Sequential(
            nn.Linear(256, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(dropout * 0.75)
        )
        self.mlp_residual1 = nn.Linear(256, 512)  # For residual connection
        
        # Third layer with residual
        self.mlp_layer3 = nn.Sequential(
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(dropout * 0.5)
        )
        self.mlp_residual2 = nn.Linear(512, 256)  # For residual connection
        
        # Final layer
        self.mlp_layer4 = nn.Linear(256, 128)
        
        # Multi-head cross-attention fusion (with dropout)
        self.cross_attention = MultiHeadCrossAttentionFusion(
            cnn_dim=512, mlp_dim=128, hidden_dim=256, num_heads=4, dropout=0.1
        )
        
        # Enhanced Fusion layer
        self.fusion = nn.Sequential(
            nn.Linear(512 + 128, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(dropout),
            
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(dropout * 0.75),
            
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(dropout * 0.5),
            
            nn.Linear(64, num_classes)
        )
        
    def forward(self, x):
        spectrogram, features = x
        
        # Input validation
        if len(spectrogram.shape) != 4:
            raise ValueError(f"Expected 4D spectrogram, got {len(spectrogram.shape)}D")
        if spectrogram.shape[1] != 1:
            raise ValueError(f"Expected 1 channel, got {spectrogram.shape[1]}")
        if len(features.shape) != 2:
            raise ValueError(f"Expected 2D features, got {len(features.shape)}D")
        if features.shape[1] != self.n_features:
            raise ValueError(f"Expected {self.n_features} features, got {features.shape[1]}")
        
        # CNN branch with multi-scale
        cnn_init = self.cnn_initial(spectrogram)
        cnn_multiscale = self.multiscale(cnn_init)
        cnn_out = self.cnn_branch(cnn_multiscale)  # (batch, 512)
        
        # MLP branch with feature attention and residual connections
        features_attended = self.feature_attention(features)
        
        mlp = self.mlp_layer1(features_attended)  # (batch, 256)
        mlp_input1 = mlp  # Save input for residual
        mlp = self.mlp_layer2(mlp) + self.mlp_residual1(mlp_input1)  # (batch, 512) with residual
        mlp_input2 = mlp  # Save input for residual
        mlp = self.mlp_layer3(mlp) + self.mlp_residual2(mlp_input2)  # (batch, 256) with residual
        mlp_out = self.mlp_layer4(mlp)  # (batch, 128)
        
        # Multi-head cross-attention fusion
        cnn_enhanced, mlp_enhanced = self.cross_attention(cnn_out, mlp_out)
        
        # Concatenate enhanced outputs
        fused = torch.cat([cnn_enhanced, mlp_enhanced], dim=1)  # (batch, 640)
        
        # Final classification
        out = self.fusion(fused)  # (batch, 2)
        
        return out
    
    def get_config(self):
        """Return model configuration"""
        return {
            'model_type': 'HybridCNNMLP_V4_3',
            'num_classes': 2,
            'n_features': self.n_features,
            'input_shapes': {
                'spectrogram': (1, 128, 7),
                'features': (self.n_features,)
            },
            'version': '4.3'
        }

