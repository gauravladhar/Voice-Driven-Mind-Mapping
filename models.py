# from pydantic import BaseModel, Field
# from typing import List, Optional
# from datetime import datetime
# import uuid


# class Thought(BaseModel):
#     id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier (UUID or short id)")
#     title: str  # GPT-generated or user-modified title
#     content: str  # Detailed description of the thought
#     embedding_source: str  # e.g., "openai", "cohere"
#     embedding_used: str  # e.g., "text-embedding-3-small"
#     created_at: datetime = Field(default_factory=datetime.utcnow, description="Time the thought was created")
#     updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
#     history_titles: List[str] = Field(default_factory=list, description="Chronological history of previous titles")
#     tags: List[str] = Field(default_factory=list, description="Optional tags for classification")
#     origin_input: Optional[str] = Field(default=None, description="Raw input that generated this node")
#     user_id: str  # ID of the user who created the thought
#     related_ids: List[str] = Field(default_factory=list, description="IDs of related thought nodes (via RELATED_TO)")


from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

class Thought(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()),
                    description="Unique identifier (UUID)")
    title: str                              # GPT or user title
    content: str                            # Full chunk text
    embedding_source: str                   # "openai", "cohere", …
    embedding_used: str                     # "text-embedding-3-small"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    history_titles: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    origin_input: Optional[str] = None
    user_id: str
    related_ids: List[str] = Field(default_factory=list)


