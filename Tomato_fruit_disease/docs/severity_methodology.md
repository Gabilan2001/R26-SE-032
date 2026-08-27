# Severity Methodology

## Leaf

Model: EfficientNet-B0 (`best_cnn_severity_model.pth`)

Outputs:

- `severity_score = P(HIGH)` in `[0, 1]`
- `severity_class = LOW | HIGH`
- `embedding` = 1280-d pre-classifier features

Labels used during training were **relative pseudo-severity labels** derived from YOLO affected-area information (P40 threshold). They are not expert ground truth.

**Reported performance:** test accuracy **81.42%**, F1 **81.60%** (not train accuracy 98.79%).  
See `docs/model_results.md` for the overfitting gap and model-replacement notes.

## Fruit

Integration adapter: `backend/severity/fruit/fruit_severity.py`

Set `FRUIT_SEVERITY_MODEL_PATH` when the updated Fruit CNN is available. Existing fruit model files are preserved and not overwritten by this migration.

## Future direction

Offline PCA/K-Means clustering on embeddings + measurable features is documented as a future research step (`scripts/run_severity_clustering.py`). No automatic retraining is performed by the active application.
