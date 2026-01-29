from datetime import datetime

from pydantic import Field
from pydantic import UUID4

from superwise_api.models import SuperwiseEntity
from superwise_api.models.tool.tool import EmbeddingModel
from superwise_api.models.tool.tool import KnowledgeMetadata


class Knowledge(SuperwiseEntity):
    id: UUID4
    name: str = Field(..., min_length=1, max_length=50)
    knowledge_metadata: KnowledgeMetadata
    embedding_model: EmbeddingModel
    created_by: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    indexed_at: datetime | None = None
