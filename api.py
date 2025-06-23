# # # from fastapi import APIRouter, HTTPException
# # # from models import User
# # # from uuid import UUID

# # # router = APIRouter()
# # # db = []  # In-memory fake DB

# # # @router.get("/users")
# # # async def get_user(user: User):
# # #     db.append(user)
# # #     return {"id": user.id}

# # # @router.delete("/users/{user_id}")
# # # async def delete_user(user_id: UUID):
# # #     for user in db:
# # #         if user.id == user_id:
# # #             db.remove(user)
# # #             return
# # #     raise HTTPException(status_code=404, detail=f"User with id: {user_id} does not exist")

# # #Route Definition for /process-text

# # from typing import List
# # from fastapi import APIRouter, HTTPException
# # from pydantic import BaseModel
# # from db.neo4j import get_all_thought_nodes, ping_neo4j
# # from logic import process_text_into_graph
# # from models import Thought

# # router = APIRouter()

# # # Temporary inline schema (you can move this to models.py later)
# # class UserTextInput(BaseModel):
# #     user_id: str
# #     raw_text: str


# # @router.get("/health")
# # def health_check():
# #     if ping_neo4j():
# #         return {"neo4j": "connected"}
# #     else:
# #         return {"neo4j": "disconnected"}

# # @router.post("/process-text")
# # async def process_text(input_data: UserTextInput):
# #     try:
# #         result = process_text_into_graph(input_data.user_id, input_data.raw_text)
# #         return {"status": "success", "result": result}
# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=str(e))

# # @router.get("/thoughts", response_model=List[Thought])
# # async def get_thoughts():
# #     return get_all_thought_nodes()


# # api.py
# from typing import List
# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel

# from logic import process_text_into_graph
# from db.neo4j import ping_neo4j, get_all_thought_nodes
# #from model.models import Thought           # your TS interface has no runtime effect, but fine.

# router = APIRouter()

# class UserTextInput(BaseModel):
#     user_id: str
#     raw_text: str

# # ─── health ────────────────────────────────────────────────────
# @router.get("/health")
# def health():
#     return {"neo4j": "connected" if ping_neo4j() else "disconnected"}

# # ─── main ingest ───────────────────────────────────────────────
# @router.post("/process-text")
# def process_text(input: UserTextInput):
#     try:
#         return process_text_into_graph(input.user_id, input.raw_text)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# # ─── fetch all nodes ───────────────────────────────────────────
# @router.get("/thoughts", response_model=List[Thought])  # typing hint for docs
# def thoughts():
#     return get_all_thought_nodes()


# api.py  (root level)
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from logic import process_text_into_graph
from db.neo4j import ping_neo4j, get_all_thought_nodes
from models import Thought          # ← use your existing model

# speech-to-text integration
from fastapi import UploadFile, File
import whisper
import shutil
import os

router = APIRouter()

class UserTextInput(BaseModel):
    user_id: str
    raw_text: str

@router.get("/health")
def health_check():
    return {"neo4j": "connected" if ping_neo4j() else "disconnected"}

@router.post("/process-text")
def process_text(payload: UserTextInput):
    try:
        process_text_into_graph(
            user_id=payload.user_id,
            raw_text=payload.raw_text
        )
        # ⬇️ Instead of just returning node IDs, return all thoughts
        return get_all_thought_nodes()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/thoughts", response_model=List[Thought])
def fetch_thoughts():
    return get_all_thought_nodes()

# Load Whisper once at the top-level
whisper_model = whisper.load_model("tiny")

@router.post("/transcribe-audio")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = whisper_model.transcribe(temp_path)
        os.remove(temp_path)

        transcribed_text = result["text"]

        # 👇 Call your node creation logic directly
        process_text_into_graph(
            user_id="default_user",  # You can adjust this if you want user tracking
            raw_text=transcribed_text
        )

        # 👇 Return the thought nodes after processing
        return {
            "transcription": transcribed_text,
            "nodes": get_all_thought_nodes()
        }

    except Exception as e:
        return {"error": str(e)}


# @router.post("/transcribe-audio")
# async def transcribe_audio(file: UploadFile = File(...)):
#     try:
#         # Save uploaded file
#         temp_path = f"temp_{file.filename}"
#         with open(temp_path, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)

#         # Transcribe
#         result = whisper_model.transcribe(temp_path)

#         # Optional: Delete file after
#         os.remove(temp_path)

#         return {"transcription": result["text"]}

#     except Exception as e:
#         return {"error": str(e)}
