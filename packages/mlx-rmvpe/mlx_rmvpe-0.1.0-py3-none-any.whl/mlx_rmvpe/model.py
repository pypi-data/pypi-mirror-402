"""RMVPE (Robust Model for Vocal Pitch Estimation) implementation in MLX.

Based on the paper "RMVPE: A Robust Model for Vocal Pitch Estimation in Polyphonic Music"
and the RVC implementation.
"""

from typing import List, Optional

import mlx.core as mx
import mlx.nn as nn
import numpy as np


class BiGRU(nn.Module):
    """Bidirectional GRU layer.

    MLX's GRU is unidirectional, so we implement bidirectional by running
    two GRUs (forward and backward) and concatenating their outputs.
    """

    def __init__(self, input_size: int, hidden_size: int, num_layers: int = 1):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # For simplicity, we implement single-layer bidirectional GRU
        self.gru_forward = nn.GRU(input_size, hidden_size)
        self.gru_backward = nn.GRU(input_size, hidden_size)

    def __call__(self, x: mx.array) -> mx.array:
        """
        Args:
            x: Input tensor of shape (batch, seq_len, input_size)

        Returns:
            Output tensor of shape (batch, seq_len, hidden_size * 2)
        """
        # Forward pass
        out_forward = self.gru_forward(x)

        # Backward pass: reverse input, run GRU, reverse output
        x_reversed = x[:, ::-1, :]
        out_backward = self.gru_backward(x_reversed)
        out_backward = out_backward[:, ::-1, :]

        # Concatenate forward and backward
        return mx.concatenate([out_forward, out_backward], axis=-1)


class ConvBlockRes(nn.Module):
    """Residual convolutional block with two conv layers and optional shortcut."""

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()

        # First conv block: Conv2d -> BatchNorm -> ReLU
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm(out_channels)

        # Second conv block: Conv2d -> BatchNorm -> ReLU
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm(out_channels)

        # Shortcut if dimensions don't match
        self.shortcut = None
        if in_channels != out_channels:
            self.shortcut = nn.Conv2d(in_channels, out_channels, kernel_size=1)

    def __call__(self, x: mx.array) -> mx.array:
        # Main path
        out = self.conv1(x)
        out = self.bn1(out)
        out = nn.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)
        out = nn.relu(out)

        # Residual connection
        if self.shortcut is not None:
            x = self.shortcut(x)

        return out + x


class ResEncoderBlock(nn.Module):
    """Encoder block with residual conv blocks and optional pooling."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: Optional[tuple],
        n_blocks: int = 1,
    ):
        super().__init__()
        self.n_blocks = n_blocks
        self.kernel_size = kernel_size

        # Stack of ConvBlockRes
        self.conv_blocks = []
        self.conv_blocks.append(ConvBlockRes(in_channels, out_channels))
        for _ in range(n_blocks - 1):
            self.conv_blocks.append(ConvBlockRes(out_channels, out_channels))

    def __call__(self, x: mx.array) -> tuple:
        for conv_block in self.conv_blocks:
            x = conv_block(x)

        if self.kernel_size is not None:
            # Average pooling
            pooled = nn.AvgPool2d(self.kernel_size)(x)
            return x, pooled
        else:
            return x


class ResDecoderBlock(nn.Module):
    """Decoder block with transposed conv and residual blocks."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        stride: tuple,
        n_blocks: int = 1,
    ):
        super().__init__()
        self.n_blocks = n_blocks

        # Transposed convolution for upsampling
        self.conv_transpose = nn.ConvTranspose2d(
            in_channels, out_channels,
            kernel_size=3, stride=stride, padding=1,
        )
        self.bn = nn.BatchNorm(out_channels)

        # Conv blocks after concatenation (input is out_channels * 2 due to skip connection)
        self.conv_blocks = []
        self.conv_blocks.append(ConvBlockRes(out_channels * 2, out_channels))
        for _ in range(n_blocks - 1):
            self.conv_blocks.append(ConvBlockRes(out_channels, out_channels))

    def __call__(self, x: mx.array, skip: mx.array) -> mx.array:
        # Upsample
        x = self.conv_transpose(x)
        x = self.bn(x)
        x = nn.relu(x)

        # Handle size mismatch between upsampled tensor and skip connection
        # This can happen because ConvTranspose2d output size depends on input size
        # and MLX doesn't have output_padding parameter
        if x.shape[1] != skip.shape[1] or x.shape[2] != skip.shape[2]:
            # Crop or pad to match skip connection size
            target_h, target_w = skip.shape[1], skip.shape[2]
            curr_h, curr_w = x.shape[1], x.shape[2]

            # Crop if larger
            if curr_h > target_h:
                x = x[:, :target_h, :, :]
            if curr_w > target_w:
                x = x[:, :, :target_w, :]

            # Pad if smaller
            if curr_h < target_h:
                pad_h = target_h - curr_h
                x = mx.pad(x, ((0, 0), (0, pad_h), (0, 0), (0, 0)))
            if curr_w < target_w:
                pad_w = target_w - curr_w
                x = mx.pad(x, ((0, 0), (0, 0), (0, pad_w), (0, 0)))

        # Concatenate with skip connection
        x = mx.concatenate([x, skip], axis=-1)  # Channel-last in MLX

        # Process through conv blocks
        for conv_block in self.conv_blocks:
            x = conv_block(x)

        return x


class Encoder(nn.Module):
    """UNet encoder with multiple resolution levels."""

    def __init__(
        self,
        in_channels: int,
        in_size: int,
        n_encoders: int,
        kernel_size: tuple,
        n_blocks: int,
        out_channels: int = 16,
    ):
        super().__init__()
        self.n_encoders = n_encoders
        self.bn = nn.BatchNorm(in_channels)

        self.layers = []
        for i in range(n_encoders):
            self.layers.append(
                ResEncoderBlock(in_channels, out_channels, kernel_size, n_blocks)
            )
            in_channels = out_channels
            out_channels *= 2
            in_size //= 2

        self.out_size = in_size
        self.out_channel = out_channels

    def __call__(self, x: mx.array) -> tuple:
        skip_connections = []
        x = self.bn(x)

        for layer in self.layers:
            skip, x = layer(x)
            skip_connections.append(skip)

        return x, skip_connections


class Intermediate(nn.Module):
    """Intermediate blocks between encoder and decoder."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        n_inters: int,
        n_blocks: int,
    ):
        super().__init__()
        self.n_inters = n_inters

        self.layers = []
        self.layers.append(ResEncoderBlock(in_channels, out_channels, None, n_blocks))
        for _ in range(n_inters - 1):
            self.layers.append(ResEncoderBlock(out_channels, out_channels, None, n_blocks))

    def __call__(self, x: mx.array) -> mx.array:
        for layer in self.layers:
            x = layer(x)
        return x


class Decoder(nn.Module):
    """UNet decoder with skip connections."""

    def __init__(
        self,
        in_channels: int,
        n_decoders: int,
        stride: tuple,
        n_blocks: int,
    ):
        super().__init__()
        self.n_decoders = n_decoders

        self.layers = []
        for i in range(n_decoders):
            out_channels = in_channels // 2
            self.layers.append(ResDecoderBlock(in_channels, out_channels, stride, n_blocks))
            in_channels = out_channels

    def __call__(self, x: mx.array, skip_connections: List[mx.array]) -> mx.array:
        for i, layer in enumerate(self.layers):
            x = layer(x, skip_connections[-1 - i])
        return x


class DeepUnet(nn.Module):
    """Deep UNet architecture for RMVPE."""

    def __init__(
        self,
        kernel_size: tuple,
        n_blocks: int,
        en_de_layers: int = 5,
        inter_layers: int = 4,
        in_channels: int = 1,
        en_out_channels: int = 16,
    ):
        super().__init__()

        self.encoder = Encoder(
            in_channels, 128, en_de_layers, kernel_size, n_blocks, en_out_channels
        )
        self.intermediate = Intermediate(
            self.encoder.out_channel // 2,
            self.encoder.out_channel,
            inter_layers,
            n_blocks,
        )
        self.decoder = Decoder(
            self.encoder.out_channel, en_de_layers, kernel_size, n_blocks
        )

    def __call__(self, x: mx.array) -> mx.array:
        x, skip_connections = self.encoder(x)
        x = self.intermediate(x)
        x = self.decoder(x, skip_connections)
        return x


class E2E(nn.Module):
    """End-to-end RMVPE model.

    Combines DeepUnet, CNN projection, and BiGRU + Linear for pitch prediction.
    """

    def __init__(
        self,
        n_blocks: int,
        n_gru: int,
        kernel_size: tuple,
        en_de_layers: int = 5,
        inter_layers: int = 4,
        in_channels: int = 1,
        en_out_channels: int = 16,
    ):
        super().__init__()

        self.unet = DeepUnet(
            kernel_size, n_blocks, en_de_layers, inter_layers,
            in_channels, en_out_channels
        )

        # CNN projection: 16 -> 3 channels
        self.cnn = nn.Conv2d(en_out_channels, 3, kernel_size=3, padding=1)

        # FC layers: BiGRU + Linear
        if n_gru:
            self.bigru = BiGRU(3 * 128, 256, n_gru)
            self.linear = nn.Linear(512, 360)
            self.dropout = nn.Dropout(0.25)

        self.n_gru = n_gru

    def __call__(self, mel: mx.array) -> mx.array:
        """
        Args:
            mel: Mel spectrogram of shape (batch, n_mels, time)

        Returns:
            Pitch probabilities of shape (batch, time, 360)
        """
        # Transpose and add channel dim: (batch, n_mels, time) -> (batch, time, n_mels, 1)
        # MLX uses channels-last, so we need (batch, H, W, C)
        mel = mx.transpose(mel, (0, 2, 1))  # (batch, time, n_mels)
        mel = mx.expand_dims(mel, axis=-1)  # (batch, time, n_mels, 1)

        # UNet
        x = self.unet(mel)  # (batch, time, n_mels, 16)

        # CNN projection
        x = self.cnn(x)  # (batch, time, n_mels, 3)

        # Transpose to match PyTorch's order: (batch, time, n_mels, channels) -> (batch, time, channels, n_mels)
        # Then flatten: PyTorch does .transpose(1, 2).flatten(-2) which gives (batch, time, channels * n_mels)
        x = mx.transpose(x, (0, 1, 3, 2))  # (batch, time, 3, n_mels)

        # Flatten for GRU: (batch, time, channels * n_mels)
        batch, time, channels, mels = x.shape
        x = mx.reshape(x, (batch, time, channels * mels))

        # BiGRU + Linear
        if self.n_gru:
            x = self.bigru(x)  # (batch, time, 512)
            x = self.linear(x)  # (batch, time, 360)
            x = self.dropout(x)
            x = mx.sigmoid(x)

        return x
