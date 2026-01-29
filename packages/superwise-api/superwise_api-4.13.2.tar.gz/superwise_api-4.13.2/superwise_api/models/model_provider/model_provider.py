from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal, Union
from pydantic import UUID4, BaseModel, ConfigDict, Field, RootModel

from superwise_api.models import SuperwiseEntity


class ServiceAccount(RootModel[dict[str, Any]]):
    pass


class Providers(str, Enum):
    OPENAI = "OpenAI"
    OPENAI_COMPATIBLE = "OpenAICompatible"
    GOOGLE = "GoogleAI"
    ANTHROPIC = "Anthropic"
    VERTEX_AI_MODEL_GARDEN = "VertexAIModelGarden"
    SUPERWISE = "Superwise"


class BaseProviderConfig(BaseModel):
    model_config = ConfigDict(extra="allow")


class OpenAIProviderConfig(BaseProviderConfig):
    provider: Literal[Providers.OPENAI.value] = Field(default=Providers.OPENAI.value)
    api_key: str = Field(..., min_length=1, description="OpenAI API key")


class OpenAICompatibleProviderConfig(BaseProviderConfig):
    provider: Literal[Providers.OPENAI_COMPATIBLE.value] = Field(default=Providers.OPENAI_COMPATIBLE.value)
    api_key: str = Field(..., min_length=1, description="OpenAI compatible API key")
    base_url: str = Field(..., description="Base URL for the compatible OpenAI endpoint")


class GoogleAIProviderConfig(BaseProviderConfig):
    provider: Literal[Providers.GOOGLE.value] = Field(default=Providers.GOOGLE.value)
    api_key: str = Field(..., min_length=1, description="Google AI API key")


class AnthropicProviderConfig(BaseProviderConfig):
    provider: Literal[Providers.ANTHROPIC.value] = Field(default=Providers.ANTHROPIC.value)
    api_key: str = Field(..., min_length=1, description="Anthropic API key")


class VertexAIProviderConfig(BaseProviderConfig):
    provider: Literal[Providers.VERTEX_AI_MODEL_GARDEN.value] = Field(default=Providers.VERTEX_AI_MODEL_GARDEN.value)
    project_id: str = Field(..., min_length=1)
    endpoint_id: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)
    service_account: ServiceAccount = Field(..., description="Service account JSON")


class SuperwiseProviderConfig(BaseProviderConfig):
    provider: Literal[Providers.SUPERWISE.value] = Field(default=Providers.SUPERWISE.value)


ProviderConfig = Annotated[
    Union[
        OpenAIProviderConfig,
        OpenAICompatibleProviderConfig,
        GoogleAIProviderConfig,
        AnthropicProviderConfig,
        VertexAIProviderConfig,
        SuperwiseProviderConfig,
    ],
    Field(discriminator="provider"),
]

ProviderCreateConfig = Annotated[
    Union[
        OpenAIProviderConfig,
        OpenAICompatibleProviderConfig,
        GoogleAIProviderConfig,
        AnthropicProviderConfig,
        VertexAIProviderConfig,
    ],
    Field(discriminator="provider"),
]


class PrebuiltProviderStatus(BaseModel):
    total_budget: float
    budget_spent: float
    budget_reset_at: datetime

    @classmethod
    def from_dict(cls, obj: dict):
        if obj is None:
            return None

        return PrebuiltProviderStatus.model_validate(obj)


class ModelProvider(SuperwiseEntity):
    id: UUID4
    name: str = Field(..., min_length=1, max_length=100)
    config: ProviderConfig
    created_by: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    @classmethod
    def from_dict(cls, obj: dict):
        if obj is None:
            return None

        return ModelProvider.model_validate(obj)
