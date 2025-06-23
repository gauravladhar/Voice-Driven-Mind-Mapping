# import uuid
# from db.neo4j import create_thought_node
# from db.chroma import add_to_chroma, query_chroma
# from openai_utils import get_embedding, summarize_text

# def process_text_into_graph(user_id: str, raw_text: str):
#     # 1. Summarize with GPT
#     summary = summarize_text(raw_text)

#     # 2. Generate OpenAI embedding
#     embedding = get_embedding(summary)

#     # 3. Query Chroma for similar thoughts
#     search_results = query_chroma(embedding)

#     # 4. Create a new unique node ID
#     node_id = str(uuid.uuid4())

#     # 5. Store in Chroma
#     add_to_chroma(
#         user_id=user_id,
#         node_id=node_id,
#         embedding=embedding,
#         metadata={
#             "user_id": user_id,
#             "content": raw_text,
#             "summary": summary
#         }
#     )

#     # 6. Store in Neo4j
#     create_thought_node(
#         user_id=user_id,
#         title=summary,
#         content=raw_text
#     )

#     # 7. Return result (for frontend or logs)
#     return {
#         "summary": summary,
#         "node_id": node_id,
#         "related_results": search_results
#     }


# logic.py
import uuid
from datetime import datetime
from typing import List, Dict

from openai_utils import (
    gpt_batch_segments,
    get_embedding
)
from db.chroma import add_to_chroma, query_chroma
from db.neo4j  import create_thought_node

# ───────────────────────────────────────────
def _persist_segment(seg: Dict, user_id: str) -> Dict:
    """
    seg = {title, tags, text}
    Builds full Thought node dict, stores to Chroma & Neo4j, returns node.
    """
    embedding = get_embedding(seg["text"])

    # similarity search
    sim = query_chroma(embedding, user_id=user_id, top_k=5)
    related_ids = [
        rid for rid, dist in zip(sim["ids"][0], sim["distances"][0])
        if dist < 0.40
    ]

    now     = datetime.utcnow().isoformat()
    node_id = str(uuid.uuid4())

    node = {
        "id": node_id,
        "title": seg["title"],
        "content": seg["text"],
        "embedding_source": "openai",
        "embedding_used": "text-embedding-3-small",
        "created_at": now,
        "updated_at": now,
        "history_titles": [],
        "tags": seg.get("tags", []),
        "origin_input": seg["text"],
        "user_id": user_id,
        "related_ids": related_ids
    }

    add_to_chroma(user_id, node_id, embedding, node)
    create_thought_node(**node)
    return node

# ───────────────────────────────────────────
# logic.py
from algo import ingest_entry  # your actual pipeline

def process_text_into_graph(user_id: str, raw_text: str):
    # created_nodes = ingest_entry(raw_text, user_id)
    # return created_nodes
    return ingest_entry(raw_text, user_id)