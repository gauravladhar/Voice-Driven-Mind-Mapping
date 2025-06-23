# import os
# from openai import OpenAI

# def get_openai_client():
#     api_key = os.getenv("OPENAI_API_KEY")
#     if not api_key:
#         raise RuntimeError("OPENAI_API_KEY is not set. Set it in your environment or .env file.")
#     return OpenAI(api_key=api_key)

# def get_embedding(text: str) -> list[float]:
#     client = get_openai_client()
#     response = client.embeddings.create(
#         input=[text],
#         model="text-embedding-3-small"
#     )
#     return response.data[0].embedding

# def summarize_text(text: str) -> str:
#     client = get_openai_client()
#     response = client.chat.completions.create(
#         model="gpt-4",
#         messages=[
#             {"role": "system", "content": "Summarize the following thought."},
#             {"role": "user", "content": text}
#         ]
#     )
#     return response.choices[0].message.content.strip()


# openai_utils.py
import os, json
from typing import List, Dict
from openai import OpenAI

# ───────────────────────────────────────────
#  OpenAI client helper
# ───────────────────────────────────────────
def get_openai_client() -> OpenAI:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=key)

# ───────────────────────────────────────────
#  Embedding helper
# ───────────────────────────────────────────
def get_embedding(text: str) -> List[float]:
    client = get_openai_client()
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return resp.data[0].embedding

# ───────────────────────────────────────────
#  Batch semantic chunk + meta   (ONE call)
#  Returns List[ Dict{ title,tags,text } ]
# ───────────────────────────────────────────
_SEGMENT_FN = {
    "name": "return_segments",
    "description": (
        "Provide a list of segments for a long transcript. "
        "Each segment must have: title (string ≤10 words), "
        "tags (0-5 single-word strings), text (original words)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "segments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "tags":  {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "text":  {"type": "string"}
                    },
                    "required": ["title", "text"]
                }
            }
        },
        "required": ["segments"]
    }
}

def gpt_batch_segments(raw_text: str, target_max=80) -> List[Dict]:
    """
    Returns a list of {title,tags,text} dicts.
    Falls back to naive word-chunk if GPT fails.
    """
    client = get_openai_client()

    # *Very* big transcripts? clip to first 12k words to stay < 16k tokens
    words = raw_text.split()
    if len(words) > 12000:
        raw_text = " ".join(words[:12000])

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Split the transcript into 50-80 coherent chunks, "
                        "each ≤150 words. Call the function."
                    )
                },
                {"role": "user", "content": raw_text}
            ],
            functions=[_SEGMENT_FN],
            function_call={"name": "return_segments"},
            temperature=0.2,
            max_tokens=8192
        )
        segments_json = resp.choices[0].message.function_call.arguments
        segments = json.loads(segments_json)["segments"]
        return segments[:target_max]          # strong safety cap
    except Exception as e:
        print("GPT segmenter failed, fallback to word windows:", e)
        return _fallback_word_segments(raw_text)

# ───────────────────────────────────────────
#  Fallback deterministic chunker
# ───────────────────────────────────────────
def _fallback_word_segments(text: str, words_per=120) -> List[Dict]:
    words = text.split()
    slices = [
        " ".join(words[i : i + words_per])
        for i in range(0, len(words), words_per)
    ]
    return [
        {"title": s[:40] + "...", "tags": [], "text": s}
        for s in slices
    ]
