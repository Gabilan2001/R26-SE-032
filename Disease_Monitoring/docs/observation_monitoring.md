# Observation-Based Disease Severity and Recovery Monitoring

## Component responsibility

This component monitors **repeated leaf (and later fruit) observations** to estimate
**relative pseudo-severity**, visual consistency evidence, weather context, and
observation-based recovery trend status.

It is **not** the disease identification component (external YOLO).  
It is **not** a treatment recommendation / medicine system.

## Leaf observation architecture

```text
Upload Leaf Image
 → Leaf Gate
 → External disease label (client / future YOLO API)
 → EfficientNet-B0 relative severity (P(HIGH) + embedding)
 → Consistency vs previous accepted observation
 → MATCH / POSSIBLE_MATCH / MISMATCH
 → Save append-only observation
 → Weather context (optional coords)
 → Trend: BASELINE / STABLE / IMPROVING / WORSENING / RECOVERED
 → Monitoring guidance only when WORSENING
```

## Leaf gate

- Model: MobileNetV2 (`ml/models/gate_leaf.pth`)
- Retrained on PlantVillage tomato leaves vs REJECT
- Reported holdout behaviour on PlantVillage: leaf pass 500/500, reject false-accept 0/225
- Backup: `ml/models/gate_leaf.pth.bak`

## Severity CNN

- EfficientNet-B0 via `LEAF_SEVERITY_MODEL_PATH` (default `datasets/best_cnn_severity_model.pth`)
- Outputs: `severity_score = P(HIGH)`, `severity_class`, 1280-d embedding
- **Reported performance: Test accuracy 81.42%, F1 81.60%**
- Do **not** report train accuracy 98.79% as model performance

## Visual consistency

Cosine similarity on embeddings. Thresholds: MATCH ≥ 0.85, POSSIBLE_MATCH ≥ 0.65, else MISMATCH.  
POSSIBLE_MATCH and MISMATCH require `confirm_same_case` to enter history.  
This is **visual consistency evidence**, not guaranteed plant identity.

## Weather

Contextual only. Optional lat/lon on upload. Never determines disease identity or replaces severity.

## Fruit status

Fruit adapter uses `FRUIT_SEVERITY_MODEL_PATH` (default `datasets/fruit_severity_cnn.pth`).
Same observation APIs as Leaf. If the checkpoint is missing, Fruit uploads return **HTTP 503**.

## Model replacement

Set `LEAF_SEVERITY_MODEL_PATH` to a new checkpoint that exposes the same
`severity_score` / `severity_class` / `embedding` interface. Observation APIs and frontend stay the same.

## Frontend workflow

1. Create LEAF case  
2. Select external disease label  
3. Optionally attach weather (demo coords)  
4. Upload leaf image  
5. Review BASELINE / MATCH / confirmation / trend / weather / guidance  

See also: `docs/severity_methodology.md`, `docs/model_results.md`, `docs/image_consistency.md`.
