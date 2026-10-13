# TomatoDoc — Project Unit Tests

Cross-module unit tests for **R26-SE-032** (Nutrient, Fruit, Disease Monitoring, Price Prediction).

## Setup (one time)

```bash
cd /Users/gabilansivanesan/Documents/RP_PP2/PROJECT/R26-SE-032/tests
python3 -m pip install -r requirements.txt
```

Or use an existing backend venv that already has `pytest` and `flask`.

## Run all unit tests

```bash
cd /Users/gabilansivanesan/Documents/RP_PP2/PROJECT/R26-SE-032
pytest tests/unit -v
```

## Run by component

```bash
pytest tests/unit/test_nutrient_deficiency.py -v
pytest tests/unit/test_tomato_fruit_disease.py -v
pytest tests/unit/test_disease_monitoring.py -v
pytest tests/unit/test_price_prediction.py -v
```

## Test coverage map

| File | Component | What is tested |
|------|-----------|----------------|
| `test_nutrient_deficiency.py` | Nutrient Deficiency | API response helpers, class names config |
| `test_tomato_fruit_disease.py` | Fruit Disease | API response helpers, confidence warning rule |
| `test_disease_monitoring.py` | Disease Monitoring | Location, trends, weather risk scoring |
| `test_price_prediction.py` | Price Prediction | Price normalization, locations, news impact |

## Report template (input / output)

| Test ID | Input | Expected output |
|---------|-------|-----------------|
| UT-N01 | `ok(data={"class":"Nitrogen"})` | HTTP 200, JSON with `data.class` |
| UT-M05 | `compute_trend(0.2, 0.5)` | `"IMPROVING"` |
| UT-P01 | `normalize_prices([100,150,200])` | `[0.0, 0.5, 1.0]` |

Copy terminal output from `pytest -v` into your testing report as **Actual output**.
