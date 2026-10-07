import json
import logging
from typing import Any

from langfuse import get_client, observe

from docguard.agent.prompts import GENERATION_SYSTEM_PROMPT, GENERATION_USER_PROMPT
from docguard.agent.state import AgentState, Document
from docguard.clients import anthropic_client
from docguard.config import settings

logger = logging.getLogger(__name__)


def _format_context(docs: list[Document]) -> str:
    formatted = []
    for doc in docs:
        content = doc.get("content", "")
        doc_id = doc.get("id", "unknown")
        formatted.append(f"[{doc_id}]\n{content}")
    return "\n\n".join(formatted)


def _parse_generation_response(raw: str, valid_ids: set[str]) -> dict[str, Any]:
    try:
        start_idx = raw.find("{")
        end_idx = raw.rfind("}")
        if start_idx == -1 or end_idx == -1:
            raise ValueError("No JSON object found in response")

        json_str = raw[start_idx : end_idx + 1]
        data = json.loads(json_str)

        if not isinstance(data, dict):
            raise ValueError("Parsed JSON is not a dictionary")

        answer = data.get("answer")
        citations = data.get("citations", [])
        refusal_reason = data.get("refusal_reason")

        if not isinstance(citations, list):
            citations = []

        # Filter citations to only allow those strictly passed in valid_ids
        valid_citations = [str(c) for c in citations if str(c) in valid_ids]

        return {
            "answer": str(answer) if answer is not None else None,
            "citations": valid_citations,
            "refusal_reason": str(refusal_reason) if refusal_reason else None,
        }

    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse Claude generation response: {e}")
        return {
            "answer": None,
            "citations": [],
            "refusal_reason": "generation_unavailable",
        }


def _call_claude_generator(query: str, docs: list[Document]) -> dict[str, Any]:
    if not settings.anthropic_api_key:
        logger.warning("ANTHROPIC_API_KEY is not set. Generation requires Claude.")
        return {
            "answer": None,
            "citations": [],
            "refusal_reason": "generation_unavailable",
        }

    try:
        formatted_docs = _format_context(docs)
        prompt = GENERATION_USER_PROMPT.format(
            query=query, documents=formatted_docs
        )

        response = anthropic_client().messages.create(
            model=settings.llm_model,
            system=GENERATION_SYSTEM_PROMPT,
            max_tokens=1024,
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

        raw_text = response.content[0].text  # type: ignore

        valid_ids = {str(d.get("id")) for d in docs}
        return _parse_generation_response(raw_text, valid_ids)

    except Exception as e:
        logger.error(f"Claude API call failed during generation: {e}")
        return {
            "answer": None,
            "citations": [],
            "refusal_reason": "generation_unavailable",
        }


@observe(as_type="generation", name="generate", capture_input=False, capture_output=False)
def generate_node(state: AgentState) -> dict:
    documents = state.get("relevant_docs", [])

    if not documents:
        return {
            "answer": None,
            "citations": [],
            "refusal_reason": "insufficient_context",
        }

    top_documents = documents[: settings.generation_max_context_docs]
    query = state.get("query", "")

    result = _call_claude_generator(query, top_documents)

    return result
