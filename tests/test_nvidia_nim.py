"""
tests/test_nvidia_nim.py — Tests for NVIDIA NIM Image & Video Generation
=========================================================================
Tests model selection, client construction, parameter parsing, registry
integration, and mock API interactions.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.nvidia_nim import (
    ALL_MODELS,
    IMAGE_MODELS,
    VIDEO_MODELS,
    ModelTier,
    NIMClient,
    NIMModelMeta,
    _get_nim_key,
    _parse_size,
    _select_model,
    generate_image,
    generate_video,
    nvidia_generate,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_api_key():
    """Set a mock NVIDIA API key for testing."""
    with patch.dict(os.environ, {"NVIDIA_NIM_API_KEY": "nvapi-test-key-123"}):
        yield "nvapi-test-key-123"


@pytest.fixture
def nim_client(mock_api_key):
    """Create a NIMClient with mock API key."""
    return NIMClient()


@pytest.fixture
def mock_image_response():
    """Create a mock successful image generation response."""
    # Create a tiny 1x1 PNG
    tiny_png = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100).decode()
    return {
        "data": [{"b64_json": tiny_png}]
    }


@pytest.fixture
def mock_video_response():
    """Create a mock successful video generation response."""
    tiny_video = base64.b64encode(b"\x00\x00\x00\x1cftypisom" + b"\x00" * 200).decode()
    return {
        "b64_video": tiny_video
    }


# ─── Model Catalog Tests ─────────────────────────────────────────────────────

class TestModelCatalog:
    """Tests for model catalog completeness and structure."""

    def test_image_models_exist(self):
        assert len(IMAGE_MODELS) >= 4
        assert "flux-schnell" in IMAGE_MODELS
        assert "flux-dev" in IMAGE_MODELS
        assert "flux-kontext" in IMAGE_MODELS
        assert "flux-klein" in IMAGE_MODELS

    def test_video_models_exist(self):
        assert len(VIDEO_MODELS) >= 2
        assert "cosmos-text2world" in VIDEO_MODELS
        assert "cosmos-video2world" in VIDEO_MODELS

    def test_all_models_combined(self):
        assert len(ALL_MODELS) == len(IMAGE_MODELS) + len(VIDEO_MODELS)

    def test_image_models_have_correct_modality(self):
        for name, meta in IMAGE_MODELS.items():
            assert meta.modality == "image", f"{name} should be image modality"

    def test_video_models_have_correct_modality(self):
        for name, meta in VIDEO_MODELS.items():
            assert meta.modality == "video", f"{name} should be video modality"

    def test_all_models_have_required_fields(self):
        for name, meta in ALL_MODELS.items():
            assert meta.model_id, f"{name} missing model_id"
            assert meta.display_name, f"{name} missing display_name"
            assert meta.tier in ModelTier, f"{name} has invalid tier"
            assert meta.modality in ("image", "video"), f"{name} has invalid modality"
            assert meta.description, f"{name} missing description"

    def test_flux_schnell_is_fast_tier(self):
        assert IMAGE_MODELS["flux-schnell"].tier == ModelTier.FAST

    def test_flux_dev_is_balanced(self):
        assert IMAGE_MODELS["flux-dev"].tier == ModelTier.BALANCED

    def test_cosmos_is_quality_tier(self):
        assert VIDEO_MODELS["cosmos-text2world"].tier == ModelTier.QUALITY

    def test_model_ids_are_valid_format(self):
        for name, meta in ALL_MODELS.items():
            assert "/" in meta.model_id, f"{name} model_id should be org/model format"


# ─── Model Selection Tests ───────────────────────────────────────────────────

class TestModelSelection:
    """Tests for automatic and explicit model selection."""

    def test_select_fast_image_model(self):
        model = _select_model("test prompt", "image", quality="fast")
        assert model.tier == ModelTier.FAST

    def test_select_balanced_image_model(self):
        model = _select_model("test prompt", "image", quality="balanced")
        assert model.tier == ModelTier.BALANCED

    def test_select_quality_image_model(self):
        model = _select_model("test prompt", "image", quality="quality")
        assert model.tier == ModelTier.QUALITY

    def test_select_quality_video_model(self):
        model = _select_model("test prompt", "video", quality="quality")
        assert model.tier == ModelTier.QUALITY

    def test_select_explicit_model_by_name(self):
        model = _select_model("test", "image", model_name="flux-dev")
        assert model.model_id == "black-forest-labs/flux-1-dev"

    def test_select_explicit_model_by_partial_match(self):
        model = _select_model("test", "image", model_name="schnell")
        assert "schnell" in model.model_id

    def test_select_unknown_model_raises(self):
        with pytest.raises(ValueError, match="Unknown model"):
            _select_model("test", "image", model_name="nonexistent-model-xyz")

    def test_select_with_alias_quick(self):
        model = _select_model("test", "image", quality="quick")
        assert model.tier == ModelTier.FAST

    def test_select_with_alias_best(self):
        model = _select_model("test", "image", quality="best")
        assert model.tier == ModelTier.QUALITY

    def test_select_with_alias_draft(self):
        model = _select_model("test", "image", quality="draft")
        assert model.tier == ModelTier.FAST

    def test_default_quality_is_balanced(self):
        model = _select_model("test", "image")
        assert model.tier == ModelTier.BALANCED


# ─── Size Parsing Tests ──────────────────────────────────────────────────────

class TestSizeParsing:
    """Tests for dimension string parsing."""

    def test_standard_format(self):
        assert _parse_size("1024x1024") == (1024, 1024)

    def test_uppercase_x(self):
        assert _parse_size("1024X768") == (1024, 768)

    def test_asterisk_format(self):
        assert _parse_size("1280*720") == (1280, 720)

    def test_multiplication_sign(self):
        assert _parse_size("512×512") == (512, 512)

    def test_with_whitespace(self):
        assert _parse_size("  1024 x 768  ") == (1024, 768)

    def test_invalid_format_returns_default(self):
        assert _parse_size("invalid") == (1024, 1024)


# ─── API Key Tests ────────────────────────────────────────────────────────────

class TestAPIKey:
    """Tests for API key retrieval."""

    def test_get_key_from_primary_env(self):
        with patch.dict(os.environ, {"NVIDIA_NIM_API_KEY": "nvapi-primary"}):
            assert _get_nim_key() == "nvapi-primary"

    def test_get_key_from_fallback_env(self):
        with patch.dict(
            os.environ,
            {"NVIDIA_NIM_API_KEY": "", "NVIDIA_API_KEY": "nvapi-fallback"},
            clear=False,
        ):
            assert _get_nim_key() == "nvapi-fallback"

    def test_missing_key_raises(self):
        with patch.dict(
            os.environ,
            {"NVIDIA_NIM_API_KEY": "", "NVIDIA_API_KEY": ""},
            clear=False,
        ):
            with patch("config.runtime.load_env_file", return_value={}):
                with pytest.raises(RuntimeError, match="API key not found"):
                    _get_nim_key()


# ─── NIMClient Tests ─────────────────────────────────────────────────────────

class TestNIMClient:
    """Tests for the NIMClient class."""

    def test_client_construction(self, mock_api_key):
        client = NIMClient()
        assert client._api_key == "nvapi-test-key-123"

    def test_client_with_explicit_key(self):
        client = NIMClient(api_key="nvapi-explicit")
        assert client._api_key == "nvapi-explicit"

    def test_list_all_models(self, nim_client):
        models = nim_client.list_models()
        assert len(models) >= 6
        assert all("name" in m for m in models)
        assert all("model_id" in m for m in models)

    def test_list_image_models_only(self, nim_client):
        models = nim_client.list_models(modality="image")
        assert all(m["modality"] == "image" for m in models)
        assert len(models) == len(IMAGE_MODELS)

    def test_list_video_models_only(self, nim_client):
        models = nim_client.list_models(modality="video")
        assert all(m["modality"] == "video" for m in models)
        assert len(models) == len(VIDEO_MODELS)

    @patch("requests.post")
    def test_generate_image_success(self, mock_post, nim_client, mock_image_response):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_image_response
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "test_img.png"
            result = nim_client.generate_image(
                prompt="A sunset over mountains",
                save_path=str(save_path),
            )
            assert result["path"] == str(save_path)
            assert "model" in result
            assert "elapsed_seconds" in result
            assert save_path.exists()

    @patch("requests.post")
    def test_generate_image_with_negative_prompt(self, mock_post, nim_client, mock_image_response):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_image_response
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "test.png"
            result = nim_client.generate_image(
                prompt="A cat",
                negative_prompt="blurry, low quality",
                save_path=str(save_path),
            )
            # Verify negative_prompt was included in the request
            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert "negative_prompt" in payload.get("extra_body", {})

    @patch("requests.post")
    def test_generate_image_with_seed(self, mock_post, nim_client, mock_image_response):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_image_response
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "test.png"
            result = nim_client.generate_image(
                prompt="A cat",
                seed=42,
                save_path=str(save_path),
            )
            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert payload["extra_body"]["seed"] == 42

    @patch("requests.post")
    def test_generate_video_success(self, mock_post, nim_client, mock_video_response):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_video_response
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "test_vid.mp4"
            result = nim_client.generate_video(
                prompt="A car driving through a city",
                save_path=str(save_path),
            )
            assert result["path"] == str(save_path)
            assert "resolution" in result
            assert "frames" in result
            assert "fps" in result
            assert save_path.exists()

    @patch("requests.post")
    def test_rate_limit_retry(self, mock_post, nim_client, mock_image_response):
        """Test that 429 rate limit triggers retry."""
        import requests as req_mod

        rate_limited = MagicMock()
        rate_limited.status_code = 429
        rate_limited.raise_for_status.side_effect = req_mod.exceptions.HTTPError(
            response=rate_limited
        )
        rate_limited.text = "Rate limited"

        success = MagicMock()
        success.status_code = 200
        success.json.return_value = mock_image_response
        success.raise_for_status.return_value = None

        mock_post.side_effect = [rate_limited, success]

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "test.png"
            result = nim_client.generate_image(
                prompt="test",
                save_path=str(save_path),
            )
            assert result["path"] == str(save_path)
            assert mock_post.call_count == 2


# ─── Executor Entry Point Tests ──────────────────────────────────────────────

class TestExecutorEntryPoint:
    """Tests for the nvidia_generate() executor function."""

    @patch("tools.nvidia_nim._get_nim_key", return_value="nvapi-test")
    def test_list_models_action(self, mock_key):
        result = nvidia_generate({"action": "list_models"})
        assert "Available NVIDIA NIM" in result
        assert "flux" in result.lower()

    @patch("tools.nvidia_nim._get_nim_key", return_value="nvapi-test")
    def test_list_models_image_only(self, mock_key):
        result = nvidia_generate({"action": "list_models", "modality": "image"})
        assert "flux" in result.lower()

    @patch("tools.nvidia_nim._get_nim_key", return_value="nvapi-test")
    def test_list_models_video_only(self, mock_key):
        result = nvidia_generate({"action": "list_models", "modality": "video"})
        assert "cosmos" in result.lower()

    def test_missing_prompt_returns_error(self):
        result = nvidia_generate({"action": "generate_image", "prompt": ""})
        assert "Error" in result

    def test_unknown_action_returns_error(self):
        with patch.dict(os.environ, {"NVIDIA_NIM_API_KEY": "nvapi-test"}):
            result = nvidia_generate({"action": "unknown_action", "prompt": "test"})
            assert "Unknown action" in result

    @patch("tools.nvidia_nim.generate_image")
    def test_image_action_calls_generate(self, mock_gen):
        mock_gen.return_value = {
            "path": "/tmp/test.png",
            "model": "FLUX.1 Dev",
            "size": "1024x1024",
            "elapsed_seconds": 3.5,
            "file_size_kb": 450.2,
        }
        result = nvidia_generate({
            "action": "generate_image",
            "prompt": "A beautiful landscape",
        })
        assert "Image generated successfully" in result
        assert "FLUX.1 Dev" in result
        mock_gen.assert_called_once()

    @patch("tools.nvidia_nim.generate_video")
    def test_video_action_calls_generate(self, mock_gen):
        mock_gen.return_value = {
            "path": "/tmp/test.mp4",
            "model": "Cosmos Text2World",
            "resolution": "1280x704",
            "frames": 121,
            "fps": 24,
            "elapsed_seconds": 45.2,
            "file_size_mb": 12.5,
        }
        result = nvidia_generate({
            "action": "generate_video",
            "prompt": "A car driving through the city",
        })
        assert "Video generated successfully" in result
        assert "Cosmos Text2World" in result
        mock_gen.assert_called_once()

    @patch("tools.nvidia_nim.generate_image")
    def test_image_shorthand_action(self, mock_gen):
        mock_gen.return_value = {
            "path": "/tmp/test.png",
            "model": "FLUX.1 Dev",
            "size": "1024x1024",
            "elapsed_seconds": 2.0,
            "file_size_kb": 300.0,
        }
        result = nvidia_generate({"action": "img", "prompt": "test"})
        assert "Image generated" in result

    @patch("tools.nvidia_nim.generate_video")
    def test_video_shorthand_action(self, mock_gen):
        mock_gen.return_value = {
            "path": "/tmp/test.mp4",
            "model": "Cosmos Text2World",
            "resolution": "1280x704",
            "frames": 121,
            "fps": 24,
            "elapsed_seconds": 30.0,
            "file_size_mb": 8.0,
        }
        result = nvidia_generate({"action": "vid", "prompt": "test"})
        assert "Video generated" in result

    @patch("tools.nvidia_nim.generate_image", side_effect=RuntimeError("API down"))
    def test_error_handling(self, mock_gen):
        with patch.dict(os.environ, {"NVIDIA_NIM_API_KEY": "nvapi-test"}):
            result = nvidia_generate({
                "action": "generate_image",
                "prompt": "test",
            })
            assert "Error" in result


# ─── Registry Integration Tests ──────────────────────────────────────────────

class TestRegistryIntegration:
    """Tests for executor registry registration."""

    def test_nvidia_generate_in_registry(self):
        from agent.executor import _TOOL_REGISTRY
        assert "nvidia_generate" in _TOOL_REGISTRY

    def test_registry_entry_is_callable(self):
        from agent.executor import _TOOL_REGISTRY
        handler = _TOOL_REGISTRY["nvidia_generate"]
        assert callable(handler)


# ─── Model Metadata Tests ────────────────────────────────────────────────────

class TestModelMetadata:
    """Tests for NIMModelMeta correctness."""

    def test_flux_schnell_steps(self):
        assert IMAGE_MODELS["flux-schnell"].default_steps == 4

    def test_flux_dev_steps(self):
        assert IMAGE_MODELS["flux-dev"].default_steps == 30

    def test_cosmos_video_default_size(self):
        assert VIDEO_MODELS["cosmos-text2world"].default_size == "1280x704"

    def test_models_are_frozen(self):
        """Ensure NIMModelMeta is immutable."""
        meta = IMAGE_MODELS["flux-dev"]
        with pytest.raises(AttributeError):
            meta.model_id = "changed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
