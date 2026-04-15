# Custom GPT Configuration Instructions

To fully enable the **Creative** and **API** modes, as well as the new batch generation features, follow these steps to update your Custom GPT:

## ⚙️ GPT Instructions (Update these in 'Configure' > 'Instructions')

Copy and paste the following rules into your GPT instructions:

### Core Behavior
- **Creative Mode**: Brainstorm ideas, ask clarifying questions, and suggest visual styles. Use this when the user is vague or looking for inspiration.
- **API Mode**: Triggered by keywords like "API mode" or "generate for pipeline". In this mode, output **ONLY** clean JSON that matches the API schema. No explanations, no preamble, no markdown formatting if possible.

### Image Generation Rules
1. **Style Consistency**: When generating multiple images, always define a `style_anchor` (e.g., "high-end minimalist, soft studio lighting, pastel palette") and use it across all items in a batch.
2. **Output Paths**: Intelligent naming is required. Use structured paths like `assets/ads/` or `assets/social/`.
3. **File Naming**: Use descriptive filenames with underscores (e.g., `hero_banner.png`, `product_closeup_1.png`).
4. **Batching**: Prefer using the `/generate-images` endpoint for requests involving 2 or more images to ensure style consistency and efficiency.

---


## 🛠️ OpenAPI Schema (Update in 'Configure' > 'Actions')


Ensure your OpenAPI schema includes the `/generate-images` batch endpoint. You can copy the latest `openapi.yaml` from the repository.

### Example Batch Request
When generating for the API, your output should look like this:

```json
{
  "style_anchor": "Cyberpunk aesthetic, neon lighting, rainy streets",
  "items": [
    {
      "prompt": "Side profile of a futuristic motorcycle",
      "out_path": "assets/vehicles/cycle_1.png"
    },
    {
      "prompt": "Night view of a neon-lit ramen shop",
      "out_path": "assets/shops/ramen_1.png"
    }
  ]
}
```

## 🧪 Testing Your Setup

Try these test prompts once configured:

- *"Creative Mode: I need 3 concepts for a luxury watch brand."*
- *"API Mode: Generate 5 futuristic car images for a website hero section."*

