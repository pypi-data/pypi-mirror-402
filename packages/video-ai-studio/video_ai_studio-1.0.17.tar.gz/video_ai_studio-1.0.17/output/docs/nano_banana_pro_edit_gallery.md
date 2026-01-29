# Nano Banana Pro Edit Gallery: Character Reference Showcase

A visual showcase demonstrating the multi-image editing capabilities of `nano_banana_pro_edit` model using a character reference image.

**Reference Image:** `input/images/character/miranda.jpg`
**All images:** 16:9 aspect ratio | 1K resolution | PNG format
**Execution:** 4 parallel tasks for maximum speed

---

## Scene 1: Coffee Shop Morning
**Prompt:** "Woman from reference image sitting in a cozy coffee shop, morning light streaming through windows, holding a latte, casual elegant outfit, warm atmosphere, lifestyle photography"

**Output:** `miranda_coffee_shop_morning.png`

---

## Scene 2: Beach Sunset
**Prompt:** "Woman from reference image walking on beach at sunset, flowing summer dress, golden hour lighting, waves in background, hair blowing in wind, cinematic photography"

**Output:** `miranda_beach_sunset.png`

---

## Scene 3: Business Portrait
**Prompt:** "Woman from reference image in professional business attire, modern office background, confident pose, soft studio lighting, corporate headshot style, LinkedIn profile quality"

**Output:** `miranda_business_portrait.png`

---

## Scene 4: Garden Party
**Prompt:** "Woman from reference image at elegant garden party, wearing floral dress, surrounded by flowers, champagne glass in hand, natural daylight, editorial fashion photography"

**Output:** `miranda_garden_party.png`

---

## Generation Summary

| Scene | Description | Output Filename | Aspect Ratio |
|-------|-------------|-----------------|--------------|
| 1 | Coffee Shop Morning | miranda_coffee_shop_morning.png | 16:9 |
| 2 | Beach Sunset | miranda_beach_sunset.png | 16:9 |
| 3 | Business Portrait | miranda_business_portrait.png | 16:9 |
| 4 | Garden Party | miranda_garden_party.png | 16:9 |

## API Parameters Used

```json
{
  "model": "nano_banana_pro_edit",
  "endpoint": "fal-ai/nano-banana-pro/edit",
  "aspect_ratio": "16:9",
  "resolution": "1K",
  "output_format": "png",
  "num_images": 1,
  "sync_mode": true
}
```

## Cost Estimate

- **Per image:** $0.015
- **Total (4 images):** $0.060

---

*Generated with AI Content Pipeline using Nano Banana Pro Edit model with parallel execution*
