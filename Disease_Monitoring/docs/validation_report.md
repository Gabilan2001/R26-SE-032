# Leaf Validation Report — Observation-Based Monitoring

Date: 2026-08-23  
Scope: Leaf pipeline only (no Leaf CNN retrain, no Fruit CNN training, no YOLO changes)

## Automated tests

```text
28 passed
  tests/test_observation_monitoring.py
  tests/test_api_leaf_integration.py
  tests/test_leaf_e2e_suite.py
```

| Suite test | Coverage |
|------------|----------|
| Test 1 | Valid leaf → gate → severity → BASELINE saved |
| Test 2 | Second identical image → MATCH + trend |
| Test 3 | Different leaf → MISMATCH/POSSIBLE_MATCH, not saved |
| Test 4 | POSSIBLE_MATCH requires `confirm_same_case` |
| Test 5 | WORSENING → monitoring recommendation |
| Test 6 | IMPROVING/STABLE → no WORSENING recommendation |
| Test 7 | Invalid / REJECT image → gate rejection |
| Test 8 | Fruit without CNN → HTTP 503 |
| Test 9 | Weather context when lat/lon provided |
| Test 10 | `/cases/{id}/status` payload for frontend |

## Honest Leaf CNN metrics

| Metric | Value |
|--------|-------|
| Test accuracy | **81.42%** |
| Test F1 | **81.60%** |
| Best val accuracy | 86.02% |

Do not cite train accuracy 98.79% as performance. Labels are YOLO-derived relative pseudo-labels (P40), not expert GT.

## Gate

Retrained PlantVillage leaf vs REJECT. Holdout: leaf pass 500/500, reject false-accept 0/225. Backup: `ml/models/gate_leaf.pth.bak`.

## Frontend (Leaf)

`DiseaseDashboardScreen` supports:

- Case ID, Observation N / BASELINE  
- Previous vs current severity  
- Similarity + consistency language (“visual consistency evidence”)  
- Optional weather (demo Colombo coords)  
- Fruit pending messaging / 503 awareness  

## Manual demo (API)

```powershell
cd D:\Research\RP-COM-MY\R26-SE-032\Disease_Monitoring\backend
D:\Research\RP-COM-MY\venv\Scripts\uvicorn.exe main:app --reload --host 127.0.0.1 --port 8000
```

```powershell
# 1) Create case
curl -X POST http://127.0.0.1:8000/cases -H "Content-Type: application/json" -d "{\"crop_part\":\"LEAF\",\"label\":\"demo\"}"

# 2) Obs 1 (BASELINE) — replace CASE_ID and IMAGE path
curl -X POST "http://127.0.0.1:8000/cases/CASE_ID/observations" -F "file=@datasets/PlantVillage/Tomato_Early_blight/<image>.JPG" -F "crop_part=LEAF" -F "disease=early_blight"

# 3) Obs 2 same image (MATCH + trend)
# repeat upload with same file

# 4) Status
curl http://127.0.0.1:8000/cases/CASE_ID/status
```

## Manual demo (frontend)

```powershell
cd D:\Research\RP-COM-MY\R26-SE-032\Disease_Monitoring\frontend
# .env: EXPO_PUBLIC_API_HOST=<PC IP>, EXPO_PUBLIC_API_PORT=8000
npm install
npm start
```

1. Create LEAF case  
2. Select disease (external label)  
3. Toggle weather if desired  
4. Upload leaf → review BASELINE  
5. Re-upload same leaf → MATCH + trend  
6. Upload a different leaf → confirmation / rejection UX  

## Out of scope (intentional)

- Fruit severity CNN training  
- Leaf EfficientNet retrain  
- YOLO disease ID changes  
- Medicine / TRR / RAG as core product path  
