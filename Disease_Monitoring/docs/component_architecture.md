# Component Architecture — Observation-Based Disease Severity and Recovery Monitoring

## Active pipeline

```text
Farmer → Upload → Crop-part gate → Severity CNN + embedding
→ Visual consistency → Observation store → Weather context
→ Trend → WORSENING monitoring guidance (optional)
```

Disease identification is **external**. Treatment medicine RAG is **out of scope**.

## Leaf vs Fruit

| | Leaf | Fruit |
|--|------|-------|
| Gate | `gate_leaf.pth` | `gate_fruit.pth` |
| Severity | EfficientNet-B0 (`LEAF_SEVERITY_MODEL_PATH`) | EfficientNet-B0 (`FRUIT_SEVERITY_MODEL_PATH`, default `datasets/fruit_severity_cnn.pth`) |
| Status | Active | Active when checkpoint present; HTTP 503 if path missing |

Shared: monitoring cases, observations, consistency, trend, weather, recommendation trigger.

## Configuration

```env
LEAF_SEVERITY_MODEL_PATH=...
FRUIT_SEVERITY_MODEL_PATH=...
WEATHER_API_KEY=...   # or OPENWEATHER_API_KEY
LEAF_GATE_THRESHOLD=0.5
YOLO_DISEASE_API_URL=   # optional future
```

## APIs

`POST /cases`, `GET /cases/{id}`, `POST /cases/{id}/observations`,  
`GET /cases/{id}/observations`, `GET /cases/{id}/status`, `GET /health`
