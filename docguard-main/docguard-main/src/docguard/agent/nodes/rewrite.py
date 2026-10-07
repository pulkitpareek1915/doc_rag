import logging

from langfuse import get_client

from docguard.agent.state import AgentState, Document
from docguard.clients import anthropic_client
from docguard.config import settings

logger = logging.getLogger(__name__)

REWRITER_PROMPT = """
You are a search query rewriting specialist for a document retrieval system.

Rewrite the user's search query to improve retrieval against a document
knowledge base.

The rewritten query should:

- preserve the user's original intent
- add useful specificity when appropriate
- remove unnecessary conversational wording
- emphasize important technical concepts
- remain concise
- NOT answer the question
- NOT invent facts
- NOT introduce unrelated topics

Return ONLY the rewritten search query.
Do not return JSON.
Do not add explanations.
Do not use quotation marks.

Original query:
{query}

Retrieved documents that were judged insufficient:
{documents}
"""


def _format_documents(docs: list[Document]) -> str:
    formatted = []
    for i, doc in enumerate(docs):
        content = doc.get("content", "")
        # limit each document to ~1200 characters
        if len(content) > 1200:
            content = content[:1200] + "..."
        formatted.append(f"[{i}] {content}")
    return "\n".join(formatted)


def _call_claude_rewriter(query: str, documents: list[Document]) -> str:
    if not settings.anthropic_api_key:
        logger.warning("ANTHROPIC_API_KEY missing. Deterministic fallback used.")
        return query

    try:
        formatted_docs = _format_documents(documents)
        prompt = REWRITER_PROMPT.format(query=query, documents=formatted_docs)

        response = anthropic_client().messages.create(
            model=settings.llm_model,
            max_tokens=200,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )

        # Update Langfuse token usage if traced
        try:
            if response.usage:
                langfuse = get_client()
                langfuse.update_current_generation(
                    usage_details={
                        "input": response.usage.input_tokens,
                        "output": response.usage.output_tokens
                    }
                )
        except Exception:
            pass

        # type ignore is needed because Anthropic SDK typing isn't perfect for content blocks
        rewritten = response.content[0].text.strip()  # type: ignore

        if not rewritten:
            logger.warning("Empty rewrite from Claude. Using fallback.")
            return query

        if rewritten == query:
            return query

        if len(rewritten) > settings.max_query_length:
            rewritten = rewritten[: settings.max_query_length]

        return rewritten

    except Exception as e:
        logger.error(f"Claude API failed during rewrite: {e}")
        return query


from langfuse import observe


@observe(as_type="generation", name="rewrite", capture_input=False, capture_output=False)
def rewrite_node(state: AgentState) -> dict:
    count = state.get("rewrite_count", 0) + 1

    current_query = state.get("active_query") or state.get("query", "")

    # We only send documents that were judged insufficient (irrelevant).
    irrelevant_docs = [
        doc
        for doc in state.get("documents", [])
        if doc.get("grade") != "relevant"
    ]

    rewritten_query = _call_claude_rewriter(current_query, irrelevant_docs)

    return {
        "active_query": rewritten_query,
        "rewrite_count": count,
    }
