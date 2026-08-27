# Legacy Treatment-Efficacy Architecture

Removed leaf-era modules (deleted):

- `routers/leaf_router.py`
- `services/leaf_service.py`
- `services/rule_engine.py`
- `schemas/leaf_schema.py`
- Old leaf U-Net models (`unet_leaf_A.pth`, `unet_leaf_B.pth`)
- Leaf gate/UNet training scripts and `datasets/leaf_disease/` CSVs

Still present for fruit legacy reference only (not mounted in active app):

| Module | Reason |
|--------|--------|
| `services/rag_engine.py` | Historical medicine KB |
| `services/fruit_service.py` | Old fruit Day pipeline |
| `services/fruit_rule_engine.py` | Old fruit treatment monitoring |
| `routers/fruit_router.py` | Old fruit upload API |

Active architecture uses `observation/` + `severity/leaf/efficientnet_severity.py`.
