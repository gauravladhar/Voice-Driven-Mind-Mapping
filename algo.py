from dotenv import load_dotenv
load_dotenv()


# algo.py — Improved semantic pipeline with detailed logging
import json, uuid, textwrap
from datetime import datetime, timezone
from typing import List, Dict, Tuple

import openai
from neo4j import GraphDatabase, basic_auth

# ──────────────────────────  HELPERS  ──────────────────────────────────
def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def log(section: str, msg: str) -> None:
    print(f"[{_ts()}] [{section.upper():7}] {msg}")

def truncate(s: str, n: int = 120) -> str:
    return (s[: n - 3] + "...") if len(s) > n else s

# ───────────────────────────  CONFIG  ──────────────────────────────────


import os

openai.api_key = os.getenv("OPENAI_API_KEY")


NEO4J = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=basic_auth(
        os.getenv("NEO4J_USER"),
        os.getenv("NEO4J_PASSWORD")
    )
)

EMBED_MODEL = "text-embedding-3-large"
CHUNK_MODEL = "gpt-4o"

AUTO_LINK_T = 0.65
FUZZY_MIN_T = 0.40
FUZZY_MAX_T = 0.65


log("INIT", f"chunk={CHUNK_MODEL}, embed={EMBED_MODEL}")

# ────────────────────────  CHROMA HELPERS  ─────────────────────────────
from db.chroma import add_to_chroma, query_chroma

# ─────────────────────────  GPT SCHEMA  ────────────────────────────────
gpt_schema = {
    "name": "CreateThoughtNodes",
    "description": "Return thought-node objects from raw text.",
    "parameters": {
        "type": "object",
        "properties": {
            "nodes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["title", "content", "tags"],
                    "properties": {
                        "title":   {"type": "string"},
                        "content": {"type": "string"},
                        "tags":    {"type": "array", "items": {"type": "string"}},
                    },
                },
            }
        },
        "required": ["nodes"],
    },
}

# ───────────────────── 1. CHUNK WITH GPT-4o ────────────────────────────
def chunk_raw_text(raw_text: str) -> List[Dict]:
    log("CHUNK", f"Sending {len(raw_text):,} characters to GPT-4o")
    resp = openai.chat.completions.create(
        model=CHUNK_MODEL,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "Break text into the fewest thought nodes possible. "
                    "Each node must capture a complete concept, have a descriptive title, "
                    "between 100–150 words of detailed content, and up to 4 tags."
                ),
            },
            {"role": "user", "content": raw_text},
        ],
        functions=[gpt_schema],
        function_call={"name": "CreateThoughtNodes"},
    )
    nodes = json.loads(resp.choices[0].message.function_call.arguments)["nodes"]
    log("CHUNK", f"GPT returned {len(nodes)} nodes")
    for i, n in enumerate(nodes, 1):
        log("CHUNK", f"  {i:02}. {truncate(n['title'])} ({len(n['content'].split()):3} words)")
    return nodes

# ────────────────────── 2. EMBED ALL NODES ─────────────────────────────
def batch_embed(nodes: List[Dict]) -> List[List[float]]:
    texts = [
    f"User Thought Log\nTopic: {n['title']}\nSummary: {n['content']}\nTagged With: {', '.join(n['tags'])}"
    for n in nodes
]


    log("EMBED", f"Requesting {len(texts)} embeddings from {EMBED_MODEL}")
    resp = openai.embeddings.create(model=EMBED_MODEL, input=texts)
    dim = len(resp.data[0].embedding)
    log("EMBED", f"Received {len(resp.data)} vectors (dim={dim})")
    return [v.embedding for v in resp.data]

# ──────────────── 3. SIMILARITY SEARCH / LINKING ───────────────────────
def decide_links(vec: List[float], user_id: str, k: int = 10) -> Tuple[List[str], List[str]]:
    q = query_chroma(vec, user_id=user_id, top_k=k)
    ids, dists = q["ids"][0], q["distances"][0]
    sims = [(i, 1 - d) for i, d in zip(ids, dists)]
    direct = [nid for nid, s in sims if s >= AUTO_LINK_T]
    fuzzy = [nid for nid, s in sims if FUZZY_MIN_T <= s < FUZZY_MAX_T]
    log("LINK", f"top-{k}: " + ", ".join(f"{truncate(i,8)}={s:.3f}" for i, s in sims))
    log("LINK", f"direct={len(direct)}, fuzzy={len(fuzzy)}")
    return direct, fuzzy

# ────────────────────── 4. STORE IN NEO4J ──────────────────────────────
def store_in_neo4j(node: Dict):
    with NEO4J.session() as s:
        s.run("MERGE (t:Thought {id:$id}) SET t += $props", id=node["id"], props=node)
        for rid in node["related_ids"]:
            s.run("MATCH (a:Thought {id:$a}), (b:Thought {id:$b}) MERGE (a)-[:RELATED_TO]->(b)", a=node["id"], b=rid)
    log("NEO4J", f"Stored {node['id']} (+{len(node['related_ids'])} edges)")

# ───────────────────────── 5. PIPELINE ─────────────────────────────────
def ingest_entry(raw_text: str, user_id: str) -> List[str]:
    log("PIPE", f"Start ingest for user={user_id}")
    nodes = chunk_raw_text(raw_text)
    nowiso = datetime.now(timezone.utc).isoformat()

    for n in nodes:
        n.update({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "origin_input": truncate(raw_text, 2000),
            "created_at": nowiso,
            "updated_at": nowiso,
            "embedding_source": "openai",
            "embedding_used": EMBED_MODEL,
            "related_ids": [],
        })

    vectors = batch_embed(nodes)

    for node, vec in zip(nodes, vectors):
        direct, fuzzy = decide_links(vec, user_id)
        node["related_ids"] = direct + fuzzy
        meta = {"title": node["title"], "content": node["content"], "tags": ", ".join(node["tags"]),
                "origin_input": node["origin_input"], "created_at": node["created_at"],
                "updated_at": node["updated_at"], "embedding_source": node["embedding_source"],
                "embedding_used": node["embedding_used"], "related_ids": json.dumps(node["related_ids"])}
        add_to_chroma(user_id, node["id"], vec, meta)
        log("CHROMA", f"Added {node['id']} (total rels={len(node['related_ids'])})")
        store_in_neo4j(node)

    log("PIPE", f"Done – {len(nodes)} nodes ingested")
    return nodes  # full node dicts, already enriched

    # return [n["id"] for n in nodes]

# ─────────────────────────  CLI TEST  ──────────────────────────────────
if __name__ == "__main__":
    sample = textwrap.dedent(
        """\
ChatGPT, developed by OpenAI, represents one of the most advanced AI language models ever built. Its rapid rise in popularity has sparked a mix of excitement and concern over its influence on work, communication, and knowledge. "ChatGPT taking over the world" is a provocative phrase often used to describe the growing reliance on AI in daily life — not literal global domination, but the way this technology is reshaping industries, habits, and even identities.

ChatGPT is already disrupting traditional workflows in fields like customer service, education, programming, writing, design, and research. Businesses use it to automate conversations, draft emails, write code, and summarize documents — cutting costs and boosting productivity. Students and professionals rely on it for instant explanations, brainstorming, and feedback. Creative fields are also affected, as ChatGPT can generate poems, stories, dialogue, and marketing content in seconds.

The influence goes beyond productivity. AI is altering how people think, learn, and solve problems. Some fear that over-reliance on tools like ChatGPT could erode critical thinking, creativity, or even job security. Others worry about ethical risks, such as misinformation, deepfakes, AI bias, and surveillance.

Despite these concerns, ChatGPT doesn't have desires or intent — it's a tool, not a sentient entity. Its “takeover” depends on how humans choose to integrate it. The future likely holds tighter regulation, stronger safeguards, and new norms around how AI should be used responsibly.

In essence, ChatGPT is not taking over the world in a dystopian sense — but it is becoming an invisible force behind how the world works. Whether that leads to empowerment or dependence depends on the choices individuals, companies, and governments make today. The key challenge now is ensuring that AI remains aligned with human values, creativity, and control.
        """
    )
    ids = ingest_entry(sample, user_id="user_001")
    print("Created nodes:", ids)
