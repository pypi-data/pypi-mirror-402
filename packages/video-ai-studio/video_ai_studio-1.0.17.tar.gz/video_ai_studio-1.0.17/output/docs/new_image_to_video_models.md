# New FAL AI Image-to-Video Models

Summary of 5 new image-to-video models to be implemented.

## Models Overview

| Model | Endpoint | Pricing | Max Duration | Key Features |
|-------|----------|---------|--------------|--------------|
| ByteDance Seedance v1.5 Pro | `fal-ai/bytedance/seedance/v1.5/pro/image-to-video` | ~$0.08/s | 10s | Seed control, motion synthesis |
| Kling Video v2.6 Pro | `fal-ai/kling-video/v2.6/pro/image-to-video` | ~$0.10/s | 10s | Professional tier, negative prompts |
| Sora 2 | `fal-ai/sora-2/image-to-video` | $0.10/s | 12s | 720p, aspect ratio control |
| Sora 2 Pro | `fal-ai/sora-2/image-to-video/pro` | $0.30-0.50/s | 12s | 720p-1080p, higher quality |
| Veo 3.1 Fast | `fal-ai/veo3.1/fast/image-to-video` | $0.10-0.15/s | 8s | Audio generation, fast |

---

## Sora 2

**Provider:** OpenAI (via FAL)
**Endpoint:** `fal-ai/sora-2/image-to-video`

### Parameters

| Parameter | Type | Default | Options |
|-----------|------|---------|---------|
| `prompt` | string | required | 1-5000 chars |
| `image_url` | string | required | URL |
| `resolution` | enum | "auto" | auto, 720p |
| `aspect_ratio` | enum | "auto" | auto, 9:16, 16:9 |
| `duration` | integer | 4 | 4, 8, 12 |
| `delete_video` | boolean | true | - |

### Example

```python
result = generator.generate_video(
    prompt="A woman walking through a field of flowers",
    image_url="https://example.com/image.jpg",
    model="sora_2",
    duration=8,
    aspect_ratio="16:9"
)
```

---

## Sora 2 Pro

**Provider:** OpenAI (via FAL)
**Endpoint:** `fal-ai/sora-2/image-to-video/pro`

### Parameters

| Parameter | Type | Default | Options |
|-----------|------|---------|---------|
| `prompt` | string | required | 1-5000 chars |
| `image_url` | string | required | URL |
| `resolution` | enum | "auto" | auto, 720p, 1080p |
| `aspect_ratio` | enum | "auto" | auto, 9:16, 16:9 |
| `duration` | integer | 4 | 4, 8, 12 |
| `delete_video` | boolean | true | - |

### Pricing

- **720p:** $0.30/second
- **1080p:** $0.50/second

### Example

```python
result = generator.generate_video(
    prompt="Cinematic shot of a sunset over mountains",
    image_url="https://example.com/image.jpg",
    model="sora_2_pro",
    duration=12,
    resolution="1080p"
)
```

---

## Veo 3.1 Fast

**Provider:** Google (via FAL)
**Endpoint:** `fal-ai/veo3.1/fast/image-to-video`

### Parameters

| Parameter | Type | Default | Options |
|-----------|------|---------|---------|
| `prompt` | string | required | - |
| `image_url` | string | required | 720p+, 16:9/9:16 |
| `aspect_ratio` | enum | "auto" | auto, 16:9, 9:16 |
| `duration` | enum | "8s" | 4s, 6s, 8s |
| `resolution` | enum | "720p" | 720p, 1080p |
| `generate_audio` | boolean | true | - |
| `auto_fix` | boolean | false | - |

### Pricing

- **Without audio:** $0.10/second
- **With audio:** $0.15/second

### Example

```python
result = generator.generate_video(
    prompt="Ocean waves crashing on rocks with seagulls",
    image_url="https://example.com/beach.jpg",
    model="veo_3_1_fast",
    duration="8s",
    generate_audio=True
)
```

---

## ByteDance Seedance v1.5 Pro

**Provider:** ByteDance
**Endpoint:** `fal-ai/bytedance/seedance/v1.5/pro/image-to-video`

### Parameters

| Parameter | Type | Default | Options |
|-----------|------|---------|---------|
| `prompt` | string | required | - |
| `image_url` | string | required | - |
| `duration` | string | "5" | 5, 10 |
| `seed` | integer | null | Optional for reproducibility |

### Example

```python
result = generator.generate_video(
    prompt="A dancer performing ballet moves",
    image_url="https://example.com/dancer.jpg",
    model="seedance_1_5_pro",
    duration="10",
    seed=42  # For reproducible results
)
```

---

## Kling Video v2.6 Pro

**Provider:** Kuaishou
**Endpoint:** `fal-ai/kling-video/v2.6/pro/image-to-video`

### Parameters

| Parameter | Type | Default | Options |
|-----------|------|---------|---------|
| `prompt` | string | required | - |
| `image_url` | string | required | - |
| `duration` | string | "5" | 5, 10 |
| `negative_prompt` | string | "blur, distort, low quality" | - |
| `cfg_scale` | float | 0.5 | 0.0-1.0 |

### Example

```python
result = generator.generate_video(
    prompt="A cat playing with yarn in slow motion",
    image_url="https://example.com/cat.jpg",
    model="kling_2_6_pro",
    duration="10",
    cfg_scale=0.7,
    negative_prompt="blur, noise, artifacts"
)
```

---

## Cost Comparison

| Model | 5s Video | 10s Video | Notes |
|-------|----------|-----------|-------|
| Seedance v1.5 Pro | $0.40 | $0.80 | Consistent pricing |
| Kling v2.6 Pro | $0.50 | $1.00 | Professional quality |
| Sora 2 | $0.50 | $1.00 | OpenAI quality |
| Sora 2 Pro (720p) | $1.50 | $3.00 | Higher quality |
| Sora 2 Pro (1080p) | $2.50 | $5.00 | Best quality |
| Veo 3.1 Fast (no audio) | $0.50 | - | Max 8s |
| Veo 3.1 Fast (audio) | $0.75 | - | Max 8s, includes audio |

---

## Implementation Status

Full implementation plan available at:
`issues/implement-new-image-to-video-models.md`

**Estimated Implementation Time:** ~2.5 hours (12 subtasks)

---

*Part of AI Content Pipeline*
