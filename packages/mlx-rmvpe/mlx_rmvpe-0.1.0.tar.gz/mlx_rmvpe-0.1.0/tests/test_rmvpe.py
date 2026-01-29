"""Tests for MLX RMVPE implementation."""

import numpy as np
import pytest

import mlx.core as mx


class TestModelArchitecture:
    """Test model architecture without weights."""

    def test_bigru_shape(self):
        """Test BiGRU output shape."""
        from mlx_rmvpe.model import BiGRU

        bigru = BiGRU(input_size=384, hidden_size=256)
        x = mx.random.normal((1, 100, 384))  # (batch, seq, features)
        out = bigru(x)

        assert out.shape == (1, 100, 512)  # hidden * 2 for bidirectional

    def test_conv_block_res_same_channels(self):
        """Test ConvBlockRes with same input/output channels."""
        from mlx_rmvpe.model import ConvBlockRes

        block = ConvBlockRes(16, 16)
        x = mx.random.normal((1, 32, 64, 16))  # (batch, H, W, C)
        out = block(x)

        assert out.shape == x.shape

    def test_conv_block_res_different_channels(self):
        """Test ConvBlockRes with different input/output channels."""
        from mlx_rmvpe.model import ConvBlockRes

        block = ConvBlockRes(16, 32)
        x = mx.random.normal((1, 32, 64, 16))
        out = block(x)

        assert out.shape == (1, 32, 64, 32)

    def test_e2e_forward(self):
        """Test E2E model forward pass."""
        from mlx_rmvpe.model import E2E

        model = E2E(n_blocks=4, n_gru=1, kernel_size=(2, 2))
        # Input: mel spectrogram (batch, n_mels, time)
        mel = mx.random.normal((1, 128, 64))
        out = model(mel)

        # Output: pitch probabilities (batch, time, 360)
        assert out.shape == (1, 64, 360)

    def test_e2e_variable_length(self):
        """Test E2E with different input lengths."""
        from mlx_rmvpe.model import E2E

        model = E2E(n_blocks=4, n_gru=1, kernel_size=(2, 2))

        for time_steps in [32, 64, 96, 128]:
            mel = mx.random.normal((1, 128, time_steps))
            out = model(mel)
            assert out.shape == (1, time_steps, 360)


class TestRMVPE:
    """Test RMVPE wrapper class."""

    def test_rmvpe_init(self):
        """Test RMVPE initialization."""
        from mlx_rmvpe import RMVPE

        model = RMVPE(hop_length=160)
        assert model.hop_length == 160
        assert model.cents_mapping.shape == (368,)

    def test_mel_spectrogram(self):
        """Test mel spectrogram computation."""
        from mlx_rmvpe import RMVPE

        model = RMVPE()

        # Generate test audio (1 second at 16kHz)
        audio = mx.array(np.random.randn(16000).astype(np.float32))
        mel = model.mel_spectrogram(audio)

        # Should be (batch, n_mels, time)
        assert mel.shape[0] == 1
        assert mel.shape[1] == 128  # n_mels
        # Time should be approximately samples / hop_length
        expected_frames = 16000 // 160 + 1
        assert abs(mel.shape[2] - expected_frames) <= 2

    def test_decode_voiced(self):
        """Test pitch decoding for voiced frames."""
        from mlx_rmvpe import RMVPE

        model = RMVPE()

        # Create fake pitch probabilities with clear peak at bin 180
        hidden = np.zeros((10, 360))
        for i in range(10):
            hidden[i, 180] = 0.9  # Strong peak
            hidden[i, 179] = 0.3
            hidden[i, 181] = 0.3

        f0 = model.decode(hidden, threshold=0.03)

        assert f0.shape == (10,)
        assert np.all(f0 > 0)  # All voiced

    def test_decode_unvoiced(self):
        """Test pitch decoding for unvoiced frames."""
        from mlx_rmvpe import RMVPE

        model = RMVPE()

        # Create pitch probabilities below threshold
        hidden = np.ones((10, 360)) * 0.01  # All below threshold

        f0 = model.decode(hidden, threshold=0.03)

        assert f0.shape == (10,)
        assert np.all(f0 == 0)  # All unvoiced


class TestIntegration:
    """Integration tests (require weights)."""

    @pytest.mark.skipif(True, reason="Requires HuggingFace weights")
    def test_from_pretrained(self):
        """Test loading pretrained model from HuggingFace."""
        from mlx_rmvpe import RMVPE

        model = RMVPE.from_pretrained()

        # Test inference
        audio = np.random.randn(16000).astype(np.float32)
        f0 = model.infer_from_audio(audio)

        assert f0.shape[0] > 0

    @pytest.mark.skipif(True, reason="Requires HuggingFace weights")
    def test_infer_from_audio(self):
        """Test full inference pipeline."""
        from mlx_rmvpe import RMVPE
        import librosa

        model = RMVPE.from_pretrained()

        # Generate sine wave at 440 Hz
        sr = 16000
        duration = 1.0
        t = np.linspace(0, duration, int(sr * duration))
        audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)

        f0 = model.infer_from_audio(audio)

        # Should detect pitch around 440 Hz
        voiced_f0 = f0[f0 > 0]
        if len(voiced_f0) > 0:
            mean_f0 = np.mean(voiced_f0)
            assert 400 < mean_f0 < 480, f"Expected ~440 Hz, got {mean_f0}"
