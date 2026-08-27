# Image Consistency

Visual embeddings (EfficientNet feature vectors) are compared using cosine similarity on L2-normalized vectors.

Default thresholds:

- MATCH: `>= 0.85`
- POSSIBLE MATCH: `>= 0.65 and < 0.85`
- MISMATCH: `< 0.65`

First observation: `BASELINE`

`confirm_same_case=true` allows manual override for low similarity.

This is **visual consistency evidence**, not guaranteed plant identity.

`confirm_same_case=true` is required to accept POSSIBLE_MATCH or MISMATCH into history.
