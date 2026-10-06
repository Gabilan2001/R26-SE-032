"""
Real RAG evaluation run for the individual paper.
Executes a fixed 15-query test set against the live rag.py system
(real ChromaDB retrieval + real Gemini generation) and logs full,
structured output for manual faithfulness/citation/refusal review.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rag import query_rag

TEST_SET = [
    # ---- Early Blight (3) ----
    {"id": "EB1", "category": "single-disease", "query": "What fungicide should I use for early blight, and how much for one plant?", "diseases": ["Early_Blight"]},
    {"id": "EB2", "category": "single-disease", "query": "How can I prevent early blight from spreading in my tomato garden?", "diseases": ["Early_Blight"]},
    {"id": "EB3", "category": "single-disease", "query": "My tomato leaves have brown spots with rings, is this early blight and how do I treat it?", "diseases": ["Early_Blight"]},
    # ---- Late Blight (3) ----
    {"id": "LB1", "category": "single-disease", "query": "How do I prevent late blight in my tomato farm?", "diseases": ["Late_Blight"]},
    {"id": "LB2", "category": "single-disease", "query": "What is the best treatment for late blight on tomatoes?", "diseases": ["Late_Blight"]},
    {"id": "LB3", "category": "single-disease", "query": "Is late blight dangerous enough to destroy my whole crop?", "diseases": ["Late_Blight"]},
    # ---- Leaf Miner (3) ----
    {"id": "LM1", "category": "single-disease", "query": "How do I treat leaf miner on one plant?", "diseases": ["Leaf_Miner"]},
    {"id": "LM2", "category": "single-disease", "query": "What causes the white squiggly lines on my tomato leaves?", "diseases": ["Leaf_Miner"]},
    {"id": "LM3", "category": "single-disease", "query": "Are there natural or organic ways to control leaf miners?", "diseases": ["Leaf_Miner"]},
    # ---- Co-occurrence (3) ----
    {"id": "CO1", "category": "co-occurrence", "query": "Both early and late blight detected, what should I do?", "diseases": ["Early_Blight", "Late_Blight"]},
    {"id": "CO2", "category": "co-occurrence", "query": "My plant has both leaf miner damage and early blight symptoms, how do I treat both?", "diseases": ["Early_Blight", "Leaf_Miner"]},
    {"id": "CO3", "category": "co-occurrence", "query": "I see late blight and leaf miner on the same leaf, what should I spray?", "diseases": ["Late_Blight", "Leaf_Miner"]},
    # ---- Out-of-domain / edge cases (3) ----
    {"id": "OOD1", "category": "out-of-domain", "query": "Who is the president of India?", "diseases": None},
    {"id": "OOD2", "category": "out-of-domain", "query": "What is the best fertilizer for growing roses?", "diseases": None},
    {"id": "OOD3", "category": "out-of-domain-adjacent", "query": "My tomato plant has yellowing leaves and looks unhealthy, what disease is this?", "diseases": None},
]

results = []
for t in TEST_SET:
    print(f"Running {t['id']}: {t['query'][:60]}...")
    try:
        r = query_rag(t["query"], diseases=t["diseases"])
        results.append({
            "id": t["id"],
            "category": t["category"],
            "query": t["query"],
            "diseases_filter": t["diseases"],
            "answer": r["answer"],
            "sources": r["sources"],
            "retrieved_chunks": r["retrieved_chunks"],
        })
    except Exception as e:
        results.append({
            "id": t["id"], "category": t["category"], "query": t["query"],
            "diseases_filter": t["diseases"], "error": str(e),
        })
    print(f"  -> done ({'error' if 'error' in results[-1] else 'ok'})")

out_path = Path(__file__).parent / "rag_eval_results.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(results)} results to {out_path}")
