"""
ingest.py
=========
Chunks the knowledge base and stores embeddings in ChromaDB.
Run this ONCE before using rag.py.

Save to:
  C:\\...\\stage4_inference\\ingest.py

Run:
  python ingest.py
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv

import chromadb
from sentence_transformers import SentenceTransformer

# ── Config ────────────────────────────────────────────────────────────────────
BASE        = Path(__file__).parent
KB_PATH     = BASE / "knowledge_base.json"
CHROMA_PATH = BASE / "chroma_db"

load_dotenv(BASE / ".env")


# ── Load knowledge base ───────────────────────────────────────────────────────
def load_kb():
    with open(KB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Chunk knowledge base into passages ───────────────────────────────────────
def create_chunks(kb):
    chunks = []

    for disease_key, disease in kb["diseases"].items():
        name = disease["name"]
        sci  = disease["scientific_name"]
        # Each disease declares its own narrative source; falls back to a
        # generic label only if a disease entry doesn't specify one.
        src  = disease.get("source", "DOA Sri Lanka / Peer-reviewed Research")

        # Chunk 1 — Overview
        chunks.append({
            "id"      : f"{disease_key}_overview",
            "text"    : f"{name} ({sci}): {disease['description']} Severity: {disease['severity']}. Type: {disease['type']}.",
            "disease" : disease_key,
            "category": "overview",
            "source"  : src,
        })

        # Chunk 2 — Symptoms
        symptoms_text = f"{name} symptoms: " + " ".join(disease["symptoms"])
        chunks.append({
            "id"      : f"{disease_key}_symptoms",
            "text"    : symptoms_text,
            "disease" : disease_key,
            "category": "symptoms",
            "source"  : src,
        })

        # Chunk 3 — Favorable conditions
        conditions_text = f"Conditions that favor {name}: " + " ".join(disease["favorable_conditions"])
        chunks.append({
            "id"      : f"{disease_key}_conditions",
            "text"    : conditions_text,
            "disease" : disease_key,
            "category": "conditions",
            "source"  : src,
        })

        # Chunk 4 — Chemical treatment (one chunk per fungicide)
        for i, chem in enumerate(disease["treatment"]["chemical"]):
            phi_text = f" Pre-harvest interval: {chem['pre_harvest_interval']}." if chem.get("pre_harvest_interval") else ""
            chunks.append({
                "id"      : f"{disease_key}_chemical_{i}",
                "text"    : (
                    f"Chemical treatment for {name}: Use {chem['fungicide']} "
                    f"at {chem['dosage']} every {chem['interval']}."
                    f"{phi_text} "
                    f"Type: {chem['type']}. {chem['notes']}"
                ),
                "disease" : disease_key,
                "category": "chemical_treatment",
                "source"  : chem["source"],
            })

        # Chunk 5 — Biological treatment
        for i, bio in enumerate(disease["treatment"]["biological"]):
            chunks.append({
                "id"      : f"{disease_key}_biological_{i}",
                "text"    : (
                    f"Biological treatment for {name}: {bio['agent']}. {bio['notes']}"
                ),
                "disease" : disease_key,
                "category": "biological_treatment",
                "source"  : bio["source"],
            })

        # Chunk 6 — Application tips
        tips_text = f"Application tips for {name} fungicides: " + " ".join(disease["treatment"]["application_tips"])
        chunks.append({
            "id"      : f"{disease_key}_tips",
            "text"    : tips_text,
            "disease" : disease_key,
            "category": "application_tips",
            "source"  : src,
        })

        # Chunk 6b — Per-plant application volume (how much to use for ONE plant)
        vol = disease["treatment"].get("application_volume")
        if vol:
            vol_text = (
                f"How much {name} treatment to use for ONE plant: {vol['ml_per_mature_plant']}. "
                f"{vol['note']} {vol['minimum_practical_batch']}"
            )
            chunks.append({
                "id"      : f"{disease_key}_application_volume",
                "text"    : vol_text,
                "disease" : disease_key,
                "category": "application_volume",
                "source"  : vol.get("source", src),
            })

        # Chunk 7 — Prevention (one chunk per category)
        for cat in disease["prevention"]:
            chunks.append({
                "id"      : f"{disease_key}_prevention_{cat['category'].replace(' ','_')}",
                "text"    : (
                    f"Prevention of {name} - {cat['category']}: "
                    + " ".join(cat["practices"])
                ),
                "disease" : disease_key,
                "category": "prevention",
                "source"  : src,
            })

    # Co-occurrence guidance chunks (tagged "general" so they're always
    # retrievable regardless of which disease(s) are being filtered on)
    if "co_occurrence_guidance" in kb:
        for note in kb["co_occurrence_guidance"]["notes"]:
            chunks.append({
                "id"      : f"co_occurrence_{note['topic'][:30].replace(' ','_').replace('/','_').replace('(','').replace(')','').replace('+','and')}",
                "text"    : f"When multiple diseases/pests are detected together — {note['topic']}: {note['text']}",
                "disease" : "general",
                "category": "co_occurrence",
                "source"  : note["source"],
            })

    # General IPM chunk
    ipm = kb["general_ipm"]
    chunks.append({
        "id"      : "general_ipm",
        "text"    : (
            "General Integrated Pest Management for tomato diseases in Sri Lanka: "
            + " ".join(ipm["principles"])
            + f" Contact: {ipm['contact']['institution']}, "
            f"{ipm['contact']['phone']}, {ipm['contact']['website']}"
        ),
        "disease" : "general",
        "category": "ipm",
        "source"  : "DOA_SL_2020",
    })

    return chunks


# ── Store in ChromaDB ─────────────────────────────────────────────────────────
def ingest():
    print("=" * 55)
    print("RAG Knowledge Base Ingestion")
    print("=" * 55)

    kb     = load_kb()
    chunks = create_chunks(kb)
    print(f"  Created {len(chunks)} chunks from knowledge base")

    # Load embedding model
    print("  Loading embedding model (all-MiniLM-L6-v2)...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    print("  Embedding model loaded ✅")

    # Create ChromaDB
    print(f"  Setting up ChromaDB at {CHROMA_PATH}...")
    client     = chromadb.PersistentClient(path=str(CHROMA_PATH))

    # Delete existing collection if exists
    try:
        client.delete_collection("tomato_disease_kb")
        print("  Cleared existing collection")
    except:
        pass

    collection = client.create_collection(
        name     = "tomato_disease_kb",
        metadata = {"hnsw:space": "cosine"}
    )

    # Generate embeddings and store
    print("  Generating embeddings and storing...")
    texts     = [c["text"]     for c in chunks]
    ids       = [c["id"]       for c in chunks]
    metadatas = [{
        "disease" : c["disease"],
        "category": c["category"],
        "source"  : c["source"],
    } for c in chunks]

    embeddings = embedder.encode(texts, show_progress_bar=True).tolist()

    collection.add(
        ids        = ids,
        documents  = texts,
        embeddings = embeddings,
        metadatas  = metadatas,
    )

    print(f"\n  Stored {len(chunks)} chunks in ChromaDB ✅")
    print(f"  Location: {CHROMA_PATH}")
    print("\n  Ingestion complete — now run rag.py")
    print("=" * 55)


if __name__ == "__main__":
    ingest()
