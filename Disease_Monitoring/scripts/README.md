# Observation Monitoring — utility scripts
#
# LEAF demo sequences (crop/framing only):
#   python scripts/build_observation_demo_kit.py --cases-per-class 20 --clean
#   Output: demo_data/observation_sequences/
#
# FRUIT demo sequences (crop/framing only; FRUIT-gate filtered):
#   python scripts/build_fruit_observation_demo_kit.py --cases-per-class 25 --clean
#   Output: demo_data/observation_sequences_fruit/
#
# Seed DEMO observations into existing SQLite schema:
#   python scripts/seed_leaf_demo_observations.py --replace-demo
#   python scripts/seed_fruit_demo_observations.py --replace-demo
#
# Verify same-plant MATCH / unrelated MISMATCH on demo crops:
#   python scripts/verify_demo_match_mismatch.py
#
# See each kit folder README for honesty statements and upload order.
