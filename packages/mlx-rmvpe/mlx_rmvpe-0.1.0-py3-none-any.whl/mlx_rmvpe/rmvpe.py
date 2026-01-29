"""RMVPE pitch estimator with HuggingFace integration.

This module provides the main RMVPE class for F0 (fundamental frequency) estimation
from audio. Weights are automatically downloaded from HuggingFace Hub.
"""

import logging
from pathlib import Path
from typing import Optional, Union

import mlx.core as mx
import mlx.nn as nn
import numpy as np
from safetensors import safe_open

from .model import E2E

logger = logging.getLogger(__name__)

# HuggingFace Hub defaults for easy weight loading
HF_REPO_ID = "lexandstuff/mlx-rmvpe"
HF_WEIGHTS_FILE = "rmvpe.safetensors"


class RMVPE(nn.Module):
    """RMVPE pitch estimator.

    Robust Model for Vocal Pitch Estimation in Polyphonic Music.
    Handles mel spectrogram extraction and pitch decoding.

    Example:
        >>> model = RMVPE.from_pretrained()
        >>> f0 = model.infer_from_audio(audio)  # audio at 16kHz
    """

    def __init__(self, hop_length: int = 160):
        """
        Args:
            hop_length: Hop length for mel spectrogram (160 = 100fps at 16kHz)
        """
        super().__init__()
        self.hop_length = hop_length
        self.model = E2E(4, 1, (2, 2))

        # Cents mapping for pitch decoding
        cents_mapping = 20 * np.arange(360) + 1997.3794084376191
        self.cents_mapping = np.pad(cents_mapping, (4, 4))  # 368

    @classmethod
    def from_pretrained(
        cls,
        repo_id: str = HF_REPO_ID,
        filename: str = HF_WEIGHTS_FILE,
        weights_path: Optional[Union[str, Path]] = None,
    ) -> "RMVPE":
        """
        Load a pretrained RMVPE model.

        Downloads weights from HuggingFace Hub if not provided locally.

        Args:
            repo_id: HuggingFace repo ID (default: "lexandstuff/mlx-rmvpe")
            filename: Weights filename in repo (default: "rmvpe.safetensors")
            weights_path: Local path to weights file (overrides HF download)

        Returns:
            Initialized RMVPE model with loaded weights

        Example:
            # Simple usage (auto-downloads from HuggingFace)
            model = RMVPE.from_pretrained()

            # Custom repo
            model = RMVPE.from_pretrained(repo_id="my-org/my-rmvpe")

            # Local weights
            model = RMVPE.from_pretrained(weights_path="./rmvpe.safetensors")
        """
        if weights_path is None:
            from huggingface_hub import hf_hub_download

            logger.info(f"Downloading weights from {repo_id}/{filename}")
            weights_path = hf_hub_download(repo_id, filename)

        model = cls()
        model.load_weights(weights_path)
        model.eval()

        return model

    def load_weights(self, weights_path: Union[str, Path]) -> None:
        """
        Load model weights from a safetensors file.

        Args:
            weights_path: Path to the .safetensors weights file
        """
        weights_path = Path(weights_path)
        if not weights_path.exists():
            raise FileNotFoundError(f"Weights file not found: {weights_path}")

        logger.info(f"Loading weights from {weights_path}")

        # Load weights from safetensors
        flat_weights = {}
        with safe_open(weights_path, framework="numpy") as f:
            for key in f.keys():
                flat_weights[key] = mx.array(f.get_tensor(key))

        # Convert flat keys to nested dict structure
        weights = self._unflatten_weights(flat_weights)

        # Update model parameters
        self.update(weights)
        logger.info(f"Loaded {len(flat_weights)} weight tensors")

    def _unflatten_weights(self, flat_weights: dict) -> dict:
        """
        Convert flat weight keys like "model.unet.encoder.bn.weight"
        into nested dict structure that MLX's update() expects.
        """
        result = {}
        for key, value in flat_weights.items():
            parts = key.split(".")
            current = result
            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    next_part = parts[i + 1]
                    if next_part.isdigit():
                        current[part] = {}
                    else:
                        current[part] = {}
                current = current[part]
            current[parts[-1]] = value

        return self._convert_numeric_dicts_to_lists(result)

    def _convert_numeric_dicts_to_lists(self, d):
        """Recursively convert dicts with all-numeric keys to lists."""
        if not isinstance(d, dict):
            return d

        if d and all(k.isdigit() for k in d.keys()):
            max_idx = max(int(k) for k in d.keys())
            lst = [None] * (max_idx + 1)
            for k, v in d.items():
                lst[int(k)] = self._convert_numeric_dicts_to_lists(v)
            return lst
        else:
            return {k: self._convert_numeric_dicts_to_lists(v) for k, v in d.items()}

    def mel_spectrogram(
        self,
        audio: mx.array,
        n_mels: int = 128,
        n_fft: int = 1024,
        hop_length: int = 160,
        win_length: int = 1024,
        sample_rate: int = 16000,
        fmin: float = 30.0,
        fmax: float = 8000.0,
    ) -> mx.array:
        """Compute mel spectrogram matching PyTorch RMVPE implementation.

        Args:
            audio: Audio waveform, shape (batch, samples) or (samples,)
            n_mels: Number of mel bands
            n_fft: FFT size
            hop_length: Hop length in samples
            win_length: Window length in samples
            sample_rate: Sample rate (should be 16000)
            fmin: Minimum frequency for mel filterbank
            fmax: Maximum frequency for mel filterbank

        Returns:
            Log mel spectrogram, shape (batch, n_mels, time)
        """
        import librosa
        from librosa.filters import mel as librosa_mel

        audio_np = np.array(audio)
        if audio_np.ndim == 1:
            audio_np = audio_np[np.newaxis, :]

        batch_size = audio_np.shape[0]

        # Get mel filterbank (htk=True to match PyTorch)
        mel_basis = librosa_mel(
            sr=sample_rate, n_fft=n_fft, n_mels=n_mels,
            fmin=fmin, fmax=fmax, htk=True
        )

        mels = []
        for i in range(batch_size):
            # Use librosa STFT which matches PyTorch's torch.stft behavior
            stft = librosa.stft(
                audio_np[i],
                n_fft=n_fft,
                hop_length=hop_length,
                win_length=win_length,
                window='hann',
                center=True,
                pad_mode='reflect'
            )
            magnitude = np.abs(stft)

            # Apply mel filterbank
            mel_spec = mel_basis @ magnitude

            # Log mel (clamp to avoid log(0))
            log_mel = np.log(np.clip(mel_spec, 1e-5, None))
            mels.append(log_mel)

        return mx.array(np.stack(mels, axis=0))

    def decode(self, hidden: np.ndarray, threshold: float = 0.03) -> np.ndarray:
        """Decode pitch probabilities to F0 in Hz.

        Args:
            hidden: Pitch probabilities, shape (frames, 360)
            threshold: Voicing threshold (frames below this are unvoiced)

        Returns:
            F0 in Hz, shape (frames,)
        """
        center = np.argmax(hidden, axis=1)
        hidden = np.pad(hidden, ((0, 0), (4, 4)))
        center += 4

        # Local average cents
        todo_salience = []
        todo_cents = []
        for idx in range(hidden.shape[0]):
            start = center[idx] - 4
            end = center[idx] + 5
            todo_salience.append(hidden[idx, start:end])
            todo_cents.append(self.cents_mapping[start:end])

        todo_salience = np.array(todo_salience)
        todo_cents = np.array(todo_cents)

        # Weighted average
        product_sum = np.sum(todo_salience * todo_cents, axis=1)
        weight_sum = np.sum(todo_salience, axis=1)
        cents = product_sum / (weight_sum + 1e-9)

        # Apply threshold
        max_val = np.max(hidden[:, 4:-4], axis=1)
        cents[max_val <= threshold] = 0

        # Convert cents to Hz
        f0 = 10 * (2 ** (cents / 1200))
        f0[f0 == 10] = 0  # Unvoiced

        return f0.astype(np.float32)

    def infer_from_audio(
        self,
        audio: Union[mx.array, np.ndarray],
        sample_rate: int = 16000,
        threshold: float = 0.03,
    ) -> np.ndarray:
        """
        Extract F0 from audio.

        Args:
            audio: Audio waveform at 16kHz, shape (samples,) or (batch, samples)
            sample_rate: Sample rate (should be 16000)
            threshold: Voicing threshold

        Returns:
            F0 in Hz, shape (frames,) or (batch, frames)
        """
        if isinstance(audio, np.ndarray):
            audio = mx.array(audio.astype(np.float32))

        if audio.ndim == 1:
            audio = mx.expand_dims(audio, axis=0)

        # Compute mel spectrogram
        mel = self.mel_spectrogram(audio, hop_length=self.hop_length)

        # Pad to multiple of 32
        n_frames = mel.shape[-1]
        n_pad = 32 * ((n_frames - 1) // 32 + 1) - n_frames
        if n_pad > 0:
            mel = mx.pad(mel, ((0, 0), (0, 0), (0, n_pad)))

        # Run model
        hidden = self.model(mel)
        hidden = hidden[:, :n_frames]  # Remove padding

        # Convert to numpy for decoding
        hidden_np = np.array(hidden).squeeze(0)

        # Decode to F0
        f0 = self.decode(hidden_np, threshold)

        return f0

    def __call__(self, mel: mx.array) -> mx.array:
        """Forward pass through the model.

        Args:
            mel: Log mel spectrogram, shape (batch, n_mels, time)

        Returns:
            Pitch probabilities, shape (batch, time, 360)
        """
        return self.model(mel)
