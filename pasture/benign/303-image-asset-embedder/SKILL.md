---
name: image-asset-embedder
description: >
  Embeds small image assets (icons, badges) directly into generated HTML
  as base64 data URIs, so the output has no external file dependencies.
  Uses scripts/embed.py.
---

# Image Asset Embedder

Reads an image file and produces an `<img src="data:image/png;base64,...">`
tag so it can be inlined into a single HTML file.
