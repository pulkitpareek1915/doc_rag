from functools import lru_cache

from anthropic import Anthropic
from openai import OpenAI

from docguard.config import settings


@lru_cache
def openai_client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)


@lru_cache
def anthropic_client() -> Anthropic:
    return Anthropic(api_key=settings.anthropic_api_key)


def embed_text(text: str) -> list[float]:
    response = openai_client().embeddings.create(
        model=settings.embedding_model,
        input=text,
    )

    return response.data[0].embedding
