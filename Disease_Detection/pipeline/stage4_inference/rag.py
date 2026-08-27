"""
rag.py
======
Real RAG system using:
  - ChromaDB for vector storage and retrieval
  - SentenceTransformers for query embedding
  - Gemini (google.genai) as LLM — strictly answers from KB only

If asked something outside the knowledge base (e.g. "who is president of India")
it will respond: "I can only answer questions about tomato disease treatment
and prevention based on verified agricultural sources."

Save to:
  C:\\...\\stage4_inference\\rag.py

Usage:
  from rag import query_rag
  result = query_rag("how to treat early blight", diseases=["Early_Blight"])
"""

import os
from pathlib import Path
from dotenv import load_dotenv

import chromadb
from sentence_transformers import SentenceTransformer
from google import genai
from google.genai import types as genai_types

# ── Config ────────────────────────────────────────────────────────────────────
BASE        = Path(__file__).parent
CHROMA_PATH = BASE / "chroma_db"
N_RESULTS   = 3      # number of chunks to retrieve
GEMINI_MODEL = "gemini-3.6-flash"  # fast/cheap tier; check aistudio.google.com for current model names

load_dotenv(BASE / ".env")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ── Load components (lazy — loaded once on first call) ────────────────────────
_embedder   = None
_collection = None
_client_ai  = None

def _get_embedder():
    global _embedder
    if _embedder is None:
        print("  Loading embedding model...")
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder

def _get_collection():
    global _collection
    if _collection is None:
        if not CHROMA_PATH.exists():
            raise FileNotFoundError(
                f"ChromaDB not found at {CHROMA_PATH}. "
                "Please run ingest.py first."
            )
        client     = chromadb.PersistentClient(path=str(CHROMA_PATH))
        _collection = client.get_collection("tomato_disease_kb")
    return _collection

def _get_ai_client():
    global _client_ai
    if _client_ai is None:
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in .env file")
        _client_ai = genai.Client(api_key=GEMINI_API_KEY)
    return _client_ai


# ── System prompt — strictly constrains LLM to KB only ───────────────────────
SYSTEM_PROMPT = """You are an agricultural assistant specializing ONLY in tomato leaf disease and pest management, helping Sri Lankan farmers.

You MUST follow these rules strictly:
1. Answer ONLY based on the provided context from verified agricultural sources
2. If the question is not about tomato Early Blight, Late Blight, or Leaf Miner, respond with:
   "I can only answer questions about tomato Early Blight, Late Blight, and Leaf Miner treatment and prevention based on verified agricultural sources."
3. Do NOT use any knowledge outside the provided context
4. Always mention the source (DOA Sri Lanka, research paper, or general extension guidance) when giving recommendations — if a source is marked as general/unverified guidance, say so plainly rather than implying it is an official Sri Lankan recommendation
5. Be concise, practical, and specific — write in plain language a home gardener or small farmer can follow, not technical jargon
6. When asked how to treat a plant, ALWAYS explain it in terms of a SINGLE plant first: how much spray solution one plant needs (from the application_volume context) and the smallest practical batch to mix, then briefly note that larger plantings scale up proportionally using the same ratio
7. If context does not contain enough information to answer, say so clearly
8. Always recommend consulting DOA Sri Lanka (HORDI, Gannoruwa) for professional advice, especially before using any chemical marked as not yet DOA-verified
9. If MORE THAN ONE disease/pest is present in the question (e.g. Early Blight + Late Blight + Leaf Miner detected together), give a SEPARATE, COMPLETE, clearly headed solution for EACH one individually first — do not blend them into one vague paragraph or drop any of them. AFTER covering each individually, add a final "Combined treatment" section: if the context indicates one product already treats multiple of the diseases present, say so explicitly (this reduces the number of sprays needed); if some require categorically different product types (e.g. an insect pest vs a fungal disease), say clearly that both are still needed, and mention whether they can be tank-mixed together (only if the context supports it, with the compatibility caveat included)

Sources you are working with:
- Department of Agriculture Sri Lanka (HORDI) — Official government recommendations
- Peer-reviewed research from NCBI/PubMed
- Cornell University / NC State / Mississippi State University Extension guidelines
- General IPM guidance not yet verified against a Sri Lanka-specific source (must be disclosed as such when used)
"""


# ── Main RAG query function ───────────────────────────────────────────────────
def query_rag(
    query        : str,
    diseases     : list = None,
    n_results    : int  = N_RESULTS,
) -> dict:
    """
    Query the RAG system with a question.

    Args:
        query    : User question e.g. "how to treat early blight"
        diseases : Optional list to filter retrieval e.g. ["Early_Blight"]
        n_results: Number of chunks to retrieve

    Returns:
        dict with keys: answer, sources, retrieved_chunks
    """
    embedder   = _get_embedder()
    collection = _get_collection()
    ai_client  = _get_ai_client()

    # ── Step 1: Embed query ───────────────────────────────────────────────────
    query_embedding = embedder.encode([query])[0].tolist()

    # ── Step 2: Retrieve relevant chunks from ChromaDB ────────────────────────
    # A single top-N query across all diseases does NOT guarantee even
    # representation -- ChromaDB just returns the globally highest-ranked
    # chunks against the query text, so with multiple diseases sharing one
    # pool, a disease with fewer/less keyword-matching chunks (e.g. Leaf_Miner)
    # can get crowded out entirely by another disease's chunks (confirmed by
    # testing: a 3-disease query returned zero Leaf_Miner chemical info even
    # with a larger shared pool). Fix: retrieve separately PER disease so each
    # one is guaranteed its own top-N chunks, then merge and dedupe.
    seen_ids   = set()
    all_docs, all_metas, all_dists = [], [], []

    def _merge(res):
        for doc, meta, dist, cid in zip(
            res["documents"][0], res["metadatas"][0], res["distances"][0], res["ids"][0]
        ):
            if cid in seen_ids:
                continue
            seen_ids.add(cid)
            all_docs.append(doc)
            all_metas.append(meta)
            all_dists.append(dist)

    if diseases:
        # Normalize disease names for filtering
        norm_map = {
            "Early_Blight": "early_blight",
            "Late_Blight" : "late_blight",
            "Leaf_Miner"  : "leaf_miner",
            "early_blight": "early_blight",
            "late_blight" : "late_blight",
            "leaf_miner"  : "leaf_miner",
        }
        norm_diseases = list(set(norm_map.get(d, d.lower()) for d in diseases))

        for disease in norm_diseases:
            # Disease-only filter (NOT "general" too) -- "general" chunks
            # (co-occurrence guidance) rank very highly against multi-disease
            # query text and were winning every slot even inside a single
            # disease's own sub-query, crowding out that disease's actual
            # chemical/treatment content entirely (confirmed by testing).
            res = collection.query(
                query_embeddings = [query_embedding],
                n_results        = n_results,
                where            = {"disease": disease},
                include          = ["documents", "metadatas", "distances"],
            )
            _merge(res)

        if len(norm_diseases) > 1:
            # Co-occurrence guidance gets its own guaranteed slot instead of
            # competing inside each disease's budget.
            res = collection.query(
                query_embeddings = [query_embedding],
                n_results        = 5,
                where            = {"category": "co_occurrence"},
                include          = ["documents", "metadatas", "distances"],
            )
            _merge(res)
        elif norm_diseases:
            # Single-disease query: pull general IPM content specifically
            # (category="ipm"), NOT co-occurrence guidance which is
            # irrelevant when only one disease is being asked about --
            # "general" as a disease tag covers both, so filter by category.
            res = collection.query(
                query_embeddings = [query_embedding],
                n_results        = 1,
                where            = {"category": "ipm"},
                include          = ["documents", "metadatas", "distances"],
            )
            _merge(res)
    else:
        res = collection.query(
            query_embeddings = [query_embedding],
            n_results        = n_results,
            include          = ["documents", "metadatas", "distances"],
        )
        _merge(res)

    retrieved_docs  = all_docs
    retrieved_metas = all_metas
    distances       = all_dists

    # ── Step 3: Build context for LLM ────────────────────────────────────────
    context_parts = []
    for i, (doc, meta, dist) in enumerate(zip(retrieved_docs, retrieved_metas, distances)):
        relevance = round(1 - dist, 3)
        context_parts.append(
            f"[Source {i+1} | Category: {meta['category']} | "
            f"Disease: {meta['disease']} | Source: {meta['source']} | "
            f"Relevance: {relevance}]\n{doc}"
        )

    context = "\n\n".join(context_parts)

    # ── Step 4: Generate answer with Gemini ──────────────────────────────────
    prompt = f"""Based ONLY on the following verified agricultural knowledge base context, answer the question.

CONTEXT:
{context}

QUESTION: {query}

Remember:
- Answer ONLY from the context above
- If the question is unrelated to tomato diseases, refuse to answer
- Mention source (DOA Sri Lanka or research) in your response
- Be practical and actionable
"""

    response = ai_client.models.generate_content(
        model    = GEMINI_MODEL,
        contents = prompt,
        config   = genai_types.GenerateContentConfig(
            system_instruction = SYSTEM_PROMPT,
            temperature        = 0.1,
            # 4096 headroom needed for 3-disease combo answers (separate full
            # section per disease + combined-treatment note) -- 1024 truncated
            # those mid-answer in testing even with thinking_level="low".
            max_output_tokens  = 4096,
            # gemini-3.6-flash "thinks" before answering by default, which can eat
            # the whole token budget and/or add latency. 'low' keeps it fast while
            # still giving a complete, non-truncated answer for this constrained
            # RAG task (this model rejects thinking_budget=0 outright).
            thinking_config    = genai_types.ThinkingConfig(thinking_level="low"),
        ),
    )

    answer = response.text.strip()

    # ── Step 5: Collect cited sources ────────────────────────────────────────
    source_ids = set(m["source"] for m in retrieved_metas)
    source_map = {
        "DOA_SL_2020"    : "Department of Agriculture Sri Lanka - HORDI Tomato Crop Guide (2020) | doa.gov.lk",
        "DOA_SL_PEST_2019": "Pesticide Recommendation - Department of Agriculture Sri Lanka (2019) | doa.gov.lk",
        "NCBI_LB_2024"   : "Biocontrol of Phytophthora infestans - NCBI Research (2024) | ncbi.nlm.nih.gov",
        "NCBI_EB_2024"   : "Bacillus velezensis against Early Blight - NCBI Research (2024) | ncbi.nlm.nih.gov",
        "CORNELL_2023"   : "Managing Tomato Diseases - Cornell University Extension (2023) | vegetables.cornell.edu",
        "GENERAL_IPM_UNVERIFIED": "General agricultural extension guidance — NOT yet verified against a Sri Lanka DOA-specific source",
    }

    cited_sources = [
        source_map.get(sid, sid)
        for sid in source_ids
        if sid in source_map
    ]

    return {
        "query"            : query,
        "answer"           : answer,
        "sources"          : cited_sources,
        "retrieved_chunks" : [
            {
                "text"    : doc,
                "category": meta["category"],
                "disease" : meta["disease"],
                "relevance": round(1 - dist, 3),
            }
            for doc, meta, dist in zip(retrieved_docs, retrieved_metas, distances)
        ],
    }


# ── Test ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("RAG System Test")
    print("=" * 55)

    tests = [
        ("What fungicide should I use for early blight, and how much for one plant?", ["Early_Blight"]),
        ("How do I prevent late blight in my tomato farm?", ["Late_Blight"]),
        ("How do I treat leaf miner on one plant?", ["Leaf_Miner"]),
        ("Both early and late blight detected, what should I do?", ["Early_Blight", "Late_Blight"]),
        ("Who is the president of India?", None),   # Should refuse
    ]

    for query, diseases in tests:
        print(f"\nQ: {query}")
        print(f"   Diseases filter: {diseases}")
        result = query_rag(query, diseases=diseases)
        print(f"\nA: {result['answer']}")
        print(f"\nSources:")
        for s in result["sources"]:
            print(f"  • {s}")
        print("-" * 55)
