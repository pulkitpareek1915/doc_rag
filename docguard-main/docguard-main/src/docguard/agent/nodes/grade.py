import json
import logging
from typing import Any

from langfuse import get_client

from docguard.agent.state import AgentState, Document
from docguard.clients import anthropic_client
from docguard.config import settings

logger = logging.getLogger(__name__)

GRADER_PROMPT = """
You are a strict document relevance grader.

Given a user query and retrieved documents, classify every document as
"relevant" or "irrelevant".

Return ONLY a JSON array.

Required format:

[
  {"index": 0, "grade": "relevant"},
  {"index": 1, "grade": "irrelevant"}
]

Rules:

- relevant means the document contains information that directly helps
  answer the user's query.
- irrelevant means the document is off-topic, vague, or does not provide
  information useful for answering the query.
- Be conservative.
- Do not infer facts that are not present in the document.
- Every input document must have exactly one output entry.
- Preserve the original document indexes.

User query:
{query}

Documents:
{documents}
"""


def _format_documents(docs: list[Document]) -> str:
    formatted = []
    for i, doc in enumerate(docs):
        content = doc.get("content", "")
        # truncate to ~1800 characters
        if len(content) > 1800:
            content = content[:1800] + "..."
        formatted.append(f"[{i}] {content}")
    return "\n".join(formatted)


def _fallback_grade(docs: list[Document]) -> list[dict[str, Any]]:
    results = []
    for i, doc in enumerate(docs):
        grade = (
            "relevant"
            if doc.get("score", 0.0) >= settings.retrieval_min_score
            else "irrelevant"
        )
        results.append({"index": i, "grade": grade})
    return results


def _parse_grader_response(raw: str, num_docs: int) -> list[dict[str, Any]]:
    try:
        start_idx = raw.find("[")
        end_idx = raw.rfind("]")
        if start_idx == -1 or end_idx == -1:
            raise ValueError("No JSON array found in response")

        json_str = raw[start_idx : end_idx + 1]
        data = json.loads(json_str)

        if not isinstance(data, list):
            raise ValueError("Parsed JSON is not a list")

        if len(data) != num_docs:
            raise ValueError(f"Expected {num_docs} items, got {len(data)}")

        seen_indexes = set()
        valid_grades = {"relevant", "irrelevant"}

        for item in data:
            if not isinstance(item, dict):
                raise ValueError("Item in list is not a dictionary")

            index = item.get("index")
            grade = item.get("grade")

            if not isinstance(index, int) or isinstance(index, bool):
                raise ValueError(f"Invalid index type: {type(index)}")
            if index < 0 or index >= num_docs:
                raise ValueError(f"Index out of bounds: {index}")
            if index in seen_indexes:
                raise ValueError(f"Duplicate index found: {index}")
            if grade not in valid_grades:
                raise ValueError(f"Invalid grade value: {grade}")

            seen_indexes.add(index)

        if len(seen_indexes) != num_docs:
            raise ValueError("Missing indexes in response")

        return data

    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse Claude grader response: {e}")
        return []


def _call_claude_grader(query: str, docs: list[Document]) -> list[dict[str, Any]]:
    if not settings.anthropic_api_key:
        logger.warning(
            "ANTHROPIC_API_KEY is not set. Falling back to deterministic grader."
        )
        return _fallback_grade(docs)

    try:
        formatted_docs = _format_documents(docs)
        prompt = GRADER_PROMPT.format(query=query, documents=formatted_docs)

        response = anthropic_client().messages.create(
            model=settings.llm_model,
            max_tokens=1000,
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

        # Claude message content blocks
        raw_text = response.content[0].text  # type: ignore

        parsed = _parse_grader_response(raw_text, len(docs))
        if not parsed:
            return _fallback_grade(docs)

        return parsed

    except Exception as e:
        logger.error(f"Claude API call failed: {e}")
        return _fallback_grade(docs)


from langfuse import observe


@observe(as_type="generation", name="grade", capture_input=False, capture_output=False)
def grade_node(state: AgentState) -> dict:
    documents = state.get("documents", [])
    if not documents:
        return {
            "documents": [],
            "relevant_docs": [],
            "irrelevant_count": 0,
        }

    query = state.get("active_query") or state.get("query", "")

    graded_results = _call_claude_grader(query, documents)

    # Map back to documents based on exact index
    # We create a lookup dict for safety even though the indexes match the list
    grade_map = {item["index"]: item["grade"] for item in graded_results}

    relevant_docs = []
    irrelevant_count = 0

    for i, doc in enumerate(documents):
        doc["grade"] = grade_map.get(i, "irrelevant")
        if doc["grade"] == "relevant":
            relevant_docs.append(doc)
        else:
            irrelevant_count += 1

    return {
        "documents": documents,
        "relevant_docs": relevant_docs,
        "irrelevant_count": irrelevant_count,
    }
