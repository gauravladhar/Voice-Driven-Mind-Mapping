from chromadb import Client

# Assuming you created it earlier in the same process:
client = Client()                     # ← same process = same in-mem DB
# or reuse the instance you already have: client = CHROMA

# 1. List collections
for col in client.list_collections():
    print(f"📚 {col.name}  →  {col.count()} items")

# 2. Open your “thoughts” collection
col = client.get_collection("thoughts")

# 3. Quick peek (first 10 docs)
print(col.peek(n_results=10))         # shows ids + docs

# 4. Full dump (ids, documents, metadata, embeddings)
dump = col.get(include=["documents", "metadatas", "embeddings"])
print(dump["ids"][:3])                # first three ids
print(dump["metadatas"][0])           # metadata of first vector