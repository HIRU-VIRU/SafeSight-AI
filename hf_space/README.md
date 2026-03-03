---
title: SafeSight AI Inference
emoji: 🦺
colorFrom: yellow
colorTo: red
sdk: docker
pinned: false
---

# SafeSight AI – YOLO26m PPE Inference API

Gradio-powered inference endpoint for the SafeSight AI construction safety monitoring system.

## API Usage (machine-to-machine)

```
POST /run/infer
Content-Type: application/json

{"data": ["<base64-jpeg>", 0.3, 512]}
```

Response:
```json
{"data": ["[{\"class\":\"Person\", ...}]", 45.2]}
```

`data[0]` = JSON string of detections  
`data[1]` = inference latency in ms

## Model Classes

| ID | Class |
|----|-------|
| 0  | Person |
| 1  | helmet |
| 2  | gloves |
| 3  | vest   |
| 4  | boots  |
| 5  | goggles |

## Setup

Upload `best.pt` to this Space's root directory and restart.
