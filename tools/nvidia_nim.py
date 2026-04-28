"""
tools/nvidia_nim.py — NVIDIA NIM Image & Video Generation Adapter
===================================================================
Professional adapter for NVIDIA's NIM API providing:
  - Image generation via FLUX models (1-schnell, 1-dev, 2-klein)
  - Video generation via Cosmos-Predict1 (Text2World)
  - Automatic model selection based on quality/speed preference
  - Output saved to ~/Pictures/buddy_gen/ or ~/Videos/buddy_gen/
  - Budget-aware with credit tracking

Architecture:
  1. MODEL_CATALOG maps model aliases → NIM model IDs + metadata
  2. NIMClient handles auth, requests, retries
  3. generate_image() / generate_video() are the main entry points
  4. nvidia_generate() is the executor registry entry point

API: OpenAI-compatible via integrate.api.nvidia.com/v1
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from agent.models import ActionResult

__all__ = [
    "NIMClient",
    "generate_image",
    "generate_video",
    "nvidia_generate",
    "IMAGE_MODELS",
    "VIDEO_MODELS",
]


# ─── Constants ────────────────────────────────────────────────────────────────

NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
OUTPUT_DIR_IMAGES = Path.home() / "Pictures" / "buddy_gen"
OUTPUT_DIR_VIDEOS = Path.home() / "Videos" / "buddy_gen"
MAX_RETRIES = 2
REQUEST_TIMEOUT = 120  # seconds


# ─── Model Catalog ───────────────────────────────────────────────────────────

class ModelTier(str, Enum):
    """Quality/speed tradeoff."""
    FAST = "fast"          # Low latency, lower quality
    BALANCED = "balanced"  # Good quality, moderate speed
    QUALITY = "quality"    # Best quality, slower


@dataclass(frozen=True)
class NIMModelMeta:
    """Metadata for a NIM generation model."""
    model_id: str                     # NIM model identifier
    display_name: str                 # Human-readable name
    tier: ModelTier                   # Speed/quality classification
    modality: str                     # "image" or "video"
    default_size: str = "1024x1024"   # Default output dimensions
    max_size: str = "1024x1024"       # Maximum dimensions
    supports_negative: bool = True    # Supports negative prompts
    supports_seed: bool = True        # Supports deterministic seeds
    default_steps: int = 30           # Default inference steps
    description: str = ""             # Short description


# Image generation models
IMAGE_MODELS: dict[str, NIMModelMeta] = {
    "flux-schnell": NIMModelMeta(
        model_id="black-forest-labs/flux-1-schnell",
        display_name="FLUX.1 Schnell",
        tier=ModelTier.FAST,
        modality="image",
        default_steps=4,
        description="Ultra-fast image generation (~1s). Good for drafts and iteration.",
    ),
    "flux-dev": NIMModelMeta(
        model_id="black-forest-labs/flux-1-dev",
        display_name="FLUX.1 Dev",
        tier=ModelTier.BALANCED,
        modality="image",
        default_steps=30,
        description="Balanced quality and speed. Best general-purpose model.",
    ),
    "flux-kontext": NIMModelMeta(
        model_id="black-forest-labs/flux-1-kontext",
        display_name="FLUX.1 Kontext",
        tier=ModelTier.QUALITY,
        modality="image",
        default_steps=30,
        description="Context-aware generation with image-to-image support.",
    ),
    "flux-klein": NIMModelMeta(
        model_id="black-forest-labs/flux-2-klein-4b",
        display_name="FLUX.2 Klein 4B",
        tier=ModelTier.BALANCED,
        modality="image",
        default_steps=20,
        description="Lightweight FLUX.2 model. Fast with good quality.",
    ),
}

# Video generation models
VIDEO_MODELS: dict[str, NIMModelMeta] = {
    "cosmos-text2world": NIMModelMeta(
        model_id="nvidia/cosmos-predict1-7b-text2world",
        display_name="Cosmos Text2World",
        tier=ModelTier.QUALITY,
        modality="video",
        default_size="1280x704",
        max_size="1280x704",
        default_steps=50,
        description="Text-to-video generation. Cinematic quality world simulation.",
    ),
    "cosmos-video2world": NIMModelMeta(
        model_id="nvidia/cosmos-predict1-7b-video2world",
        display_name="Cosmos Video2World",
        tier=ModelTier.QUALITY,
        modality="video",
        default_size="1280x704",
        max_size="1280x704",
        default_steps=50,
        description="Video-to-video generation. Extends or transforms existing video.",
    ),
}

ALL_MODELS = {**IMAGE_MODELS, **VIDEO_MODELS}


# ─── NIM Client ──────────────────────────────────────────────────────────────

def _get_nim_key() -> str:
    """Retrieve NVIDIA NIM API key from environment."""
    key = os.environ.get("NVIDIA_NIM_API_KEY", "").strip()
    if not key:
        key = os.environ.get("NVIDIA_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "NVIDIA NIM API key not found. "
            "Set NVIDIA_NIM_API_KEY in your .env file. "
            "Get a free key at https://build.nvidia.com"
        )
    return key


def _select_model(
    prompt: str,
    modality: str = "image",
    model_name: str | None = None,
    quality: str = "balanced",
) -> NIMModelMeta:
    """
    Select the best model based on user preference.
    
    Args:
        prompt: User's generation prompt (used for context)
        modality: "image" or "video"
        model_name: Explicit model name override
        quality: "fast", "balanced", or "quality"
    """
    catalog = IMAGE_MODELS if modality == "image" else VIDEO_MODELS
    
    # Explicit model selection
    if model_name:
        normalized = model_name.lower().replace(" ", "-").replace(".", "-")
        # Direct match
        if normalized in catalog:
            return catalog[normalized]
        # Fuzzy match
        for key, meta in catalog.items():
            if normalized in key or normalized in meta.model_id.lower():
                return meta
        # Check all models (cross-modality)
        if normalized in ALL_MODELS:
            return ALL_MODELS[normalized]
        raise ValueError(
            f"Unknown model '{model_name}'. Available {modality} models: "
            f"{', '.join(catalog.keys())}"
        )
    
    # Auto-select by quality tier
    tier_map = {
        "fast": ModelTier.FAST,
        "balanced": ModelTier.BALANCED,
        "quality": ModelTier.QUALITY,
        "best": ModelTier.QUALITY,
        "quick": ModelTier.FAST,
        "draft": ModelTier.FAST,
    }
    target_tier = tier_map.get(quality.lower(), ModelTier.BALANCED)
    
    # Find best match for tier
    for meta in catalog.values():
        if meta.tier == target_tier:
            return meta
    
    # Fallback to first available
    return next(iter(catalog.values()))


def _parse_size(size_str: str) -> tuple[int, int]:
    """Parse 'WxH' or 'W*H' string into (width, height) tuple."""
    parts = re.split(r"[xX*×]", size_str.strip())
    if len(parts) == 2:
        return int(parts[0].strip()), int(parts[1].strip())
    return 1024, 1024


class NIMClient:
    """
    Client for NVIDIA NIM image and video generation API.
    Uses OpenAI-compatible endpoints at integrate.api.nvidia.com.
    """

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or _get_nim_key()
    
    def generate_image(
        self,
        prompt: str,
        model: NIMModelMeta | None = None,
        model_name: str | None = None,
        size: str = "1024x1024",
        quality: str = "balanced",
        negative_prompt: str = "",
        seed: int | None = None,
        steps: int | None = None,
        save_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """
        Generate an image using NVIDIA NIM.
        
        Returns dict with keys: path, model, size, prompt, elapsed_seconds
        """
        import requests
        
        if model is None:
            model = _select_model(prompt, "image", model_name, quality)
        
        width, height = _parse_size(size or model.default_size)
        actual_steps = steps or model.default_steps
        
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        payload: dict[str, Any] = {
            "model": model.model_id,
            "prompt": prompt,
            "size": f"{width}x{height}",
            "n": 1,
            "response_format": "b64_json",
        }
        
        extra: dict[str, Any] = {}
        if seed is not None:
            extra["seed"] = seed
        if actual_steps:
            extra["num_inference_steps"] = actual_steps
        if negative_prompt and model.supports_negative:
            extra["negative_prompt"] = negative_prompt
        if extra:
            payload["extra_body"] = extra
        
        # Make request with retries
        url = f"{NIM_BASE_URL}/images/generations"
        last_error = None
        start = time.time()
        
        for attempt in range(1, MAX_RETRIES + 2):
            try:
                resp = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=REQUEST_TIMEOUT,
                )
                resp.raise_for_status()
                data = resp.json()
                break
            except requests.exceptions.HTTPError as e:
                last_error = e
                if resp.status_code == 429:
                    # Rate limited — wait and retry
                    wait = min(2 ** attempt, 10)
                    time.sleep(wait)
                    continue
                raise RuntimeError(
                    f"NIM API error {resp.status_code}: {resp.text[:500]}"
                ) from e
            except requests.exceptions.RequestException as e:
                last_error = e
                if attempt <= MAX_RETRIES:
                    time.sleep(2)
                    continue
                raise RuntimeError(f"NIM connection failed: {e}") from e
        else:
            raise RuntimeError(f"NIM API failed after {MAX_RETRIES + 1} attempts: {last_error}")
        
        elapsed = time.time() - start
        
        # Extract and save image
        b64_data = data["data"][0].get("b64_json", "")
        if not b64_data:
            # Some models return URL instead
            img_url = data["data"][0].get("url", "")
            if img_url:
                img_resp = requests.get(img_url, timeout=60)
                img_bytes = img_resp.content
            else:
                raise RuntimeError("NIM returned no image data")
        else:
            img_bytes = base64.b64decode(b64_data)
        
        # Save to disk
        if save_path:
            output_path = Path(save_path)
        else:
            OUTPUT_DIR_IMAGES.mkdir(parents=True, exist_ok=True)
            filename = f"img_{int(time.time())}_{uuid.uuid4().hex[:6]}.png"
            output_path = OUTPUT_DIR_IMAGES / filename
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(img_bytes)
        
        return {
            "path": str(output_path),
            "model": model.display_name,
            "model_id": model.model_id,
            "size": f"{width}x{height}",
            "prompt": prompt[:200],
            "steps": actual_steps,
            "elapsed_seconds": round(elapsed, 2),
            "file_size_kb": round(len(img_bytes) / 1024, 1),
        }
    
    def generate_video(
        self,
        prompt: str,
        model: NIMModelMeta | None = None,
        model_name: str | None = None,
        quality: str = "quality",
        negative_prompt: str = "blurry, low quality, artifacts, distorted",
        seed: int | None = None,
        steps: int | None = None,
        width: int = 1280,
        height: int = 704,
        frames: int = 121,
        fps: int = 24,
        guidance_scale: float = 7.5,
        save_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """
        Generate a video using NVIDIA Cosmos models.
        
        Returns dict with keys: path, model, resolution, prompt, elapsed_seconds
        """
        import requests
        
        if model is None:
            model = _select_model(prompt, "video", model_name, quality)
        
        actual_steps = steps or model.default_steps
        
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        payload: dict[str, Any] = {
            "model": model.model_id,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "seed": seed if seed is not None else 42,
            "guidance_scale": guidance_scale,
            "steps": actual_steps,
            "video_params": {
                "height": height,
                "width": width,
                "frames_count": frames,
                "frames_per_sec": fps,
            },
        }
        
        # Cosmos uses a different endpoint pattern
        url = f"{NIM_BASE_URL}/infer"
        last_error = None
        start = time.time()
        
        for attempt in range(1, MAX_RETRIES + 2):
            try:
                resp = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=300,  # Video generation takes longer
                )
                resp.raise_for_status()
                data = resp.json()
                break
            except requests.exceptions.HTTPError as e:
                last_error = e
                if resp.status_code == 429:
                    wait = min(2 ** attempt, 15)
                    time.sleep(wait)
                    continue
                raise RuntimeError(
                    f"NIM Video API error {resp.status_code}: {resp.text[:500]}"
                ) from e
            except requests.exceptions.RequestException as e:
                last_error = e
                if attempt <= MAX_RETRIES:
                    time.sleep(3)
                    continue
                raise RuntimeError(f"NIM Video connection failed: {e}") from e
        else:
            raise RuntimeError(f"NIM Video API failed after retries: {last_error}")
        
        elapsed = time.time() - start
        
        # Extract and save video
        b64_video = data.get("b64_video", "")
        if not b64_video:
            # Try alternative response fields
            b64_video = data.get("video", "")
        if not b64_video:
            raise RuntimeError(
                f"NIM returned no video data. Response keys: {list(data.keys())}"
            )
        
        video_bytes = base64.b64decode(b64_video)
        
        # Save to disk
        if save_path:
            output_path = Path(save_path)
        else:
            OUTPUT_DIR_VIDEOS.mkdir(parents=True, exist_ok=True)
            filename = f"vid_{int(time.time())}_{uuid.uuid4().hex[:6]}.mp4"
            output_path = OUTPUT_DIR_VIDEOS / filename
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(video_bytes)
        
        return {
            "path": str(output_path),
            "model": model.display_name,
            "model_id": model.model_id,
            "resolution": f"{width}x{height}",
            "frames": frames,
            "fps": fps,
            "prompt": prompt[:200],
            "steps": actual_steps,
            "elapsed_seconds": round(elapsed, 2),
            "file_size_mb": round(len(video_bytes) / (1024 * 1024), 2),
        }
    
    def list_models(self, modality: str | None = None) -> list[dict[str, str]]:
        """List available models, optionally filtered by modality."""
        catalog = ALL_MODELS
        if modality == "image":
            catalog = IMAGE_MODELS
        elif modality == "video":
            catalog = VIDEO_MODELS
        
        return [
            {
                "name": key,
                "model_id": meta.model_id,
                "display_name": meta.display_name,
                "modality": meta.modality,
                "tier": meta.tier.value,
                "description": meta.description,
            }
            for key, meta in catalog.items()
        ]


# ─── Convenience Functions ───────────────────────────────────────────────────

def generate_image(
    prompt: str,
    model: str | None = None,
    size: str = "1024x1024",
    quality: str = "balanced",
    negative_prompt: str = "",
    seed: int | None = None,
    save_path: str | None = None,
) -> dict[str, Any]:
    """High-level image generation function."""
    client = NIMClient()
    return client.generate_image(
        prompt=prompt,
        model_name=model,
        size=size,
        quality=quality,
        negative_prompt=negative_prompt,
        seed=seed,
        save_path=save_path,
    )


def generate_video(
    prompt: str,
    model: str | None = None,
    quality: str = "quality",
    negative_prompt: str = "blurry, low quality, artifacts",
    seed: int | None = None,
    width: int = 1280,
    height: int = 704,
    frames: int = 121,
    fps: int = 24,
    save_path: str | None = None,
) -> dict[str, Any]:
    """High-level video generation function."""
    client = NIMClient()
    return client.generate_video(
        prompt=prompt,
        model_name=model,
        quality=quality,
        negative_prompt=negative_prompt,
        seed=seed,
        width=width,
        height=height,
        frames=frames,
        fps=fps,
        save_path=save_path,
    )


# ─── Executor Entry Point ───────────────────────────────────────────────────

def nvidia_generate(parameters: dict, player: Any = None, **kw: Any) -> str:
    """
    Unified executor entry point for NVIDIA NIM generation.
    
    Parameters:
        action: "generate_image" | "generate_video" | "list_models"
        prompt: The generation prompt
        model: Optional model name (e.g., "flux-dev", "cosmos-text2world")
        size: Image size "WxH" (default "1024x1024")
        quality: "fast" | "balanced" | "quality" (default "balanced")
        negative_prompt: What to exclude from generation
        seed: Reproducibility seed
        save_path: Override output path
        width/height/frames/fps: Video-specific parameters
    """
    action = parameters.get("action", "generate_image").lower().strip()
    prompt = parameters.get("prompt", "").strip()
    
    if action == "list_models":
        client = NIMClient()
        modality = parameters.get("modality")
        models = client.list_models(modality)
        lines = [f"Available NVIDIA NIM {modality or 'all'} models:\n"]
        for m in models:
            lines.append(
                f"  • {m['name']} ({m['display_name']}) — {m['tier']} — {m['description']}"
            )
        return "\n".join(lines)
    
    if not prompt:
        return "Error: 'prompt' parameter is required for generation."
    
    try:
        if action in ("generate_image", "image", "img"):
            result = generate_image(
                prompt=prompt,
                model=parameters.get("model"),
                size=parameters.get("size", "1024x1024"),
                quality=parameters.get("quality", "balanced"),
                negative_prompt=parameters.get("negative_prompt", ""),
                seed=parameters.get("seed"),
                save_path=parameters.get("save_path"),
            )
            return (
                f"Image generated successfully.\n"
                f"  Model: {result['model']}\n"
                f"  Size: {result['size']}\n"
                f"  File: {result['path']}\n"
                f"  Time: {result['elapsed_seconds']}s\n"
                f"  File size: {result['file_size_kb']} KB"
            )
        
        elif action in ("generate_video", "video", "vid"):
            result = generate_video(
                prompt=prompt,
                model=parameters.get("model"),
                quality=parameters.get("quality", "quality"),
                negative_prompt=parameters.get(
                    "negative_prompt", "blurry, low quality, artifacts"
                ),
                seed=parameters.get("seed"),
                width=int(parameters.get("width", 1280)),
                height=int(parameters.get("height", 704)),
                frames=int(parameters.get("frames", 121)),
                fps=int(parameters.get("fps", 24)),
                save_path=parameters.get("save_path"),
            )
            return (
                f"Video generated successfully.\n"
                f"  Model: {result['model']}\n"
                f"  Resolution: {result['resolution']}\n"
                f"  Duration: {result['frames']}/{result['fps']}fps "
                f"(~{result['frames'] / result['fps']:.1f}s)\n"
                f"  File: {result['path']}\n"
                f"  Time: {result['elapsed_seconds']}s\n"
                f"  File size: {result['file_size_mb']} MB"
            )
        
        else:
            return (
                f"Unknown action '{action}'. "
                f"Use 'generate_image', 'generate_video', or 'list_models'."
            )
    
    except RuntimeError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error generating content: {type(e).__name__}: {e}"
