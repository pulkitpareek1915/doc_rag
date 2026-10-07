from docguard.agent.graph import graph
from docguard.config import settings


def main() -> None:
    print(f"ANTHROPIC_API_KEY IS SET: {bool(settings.anthropic_api_key)}")
    result = graph.invoke({"query": "How does DocGuard handle security?"})
    print(f"REFUSAL: {result.get('refusal_reason')}")
    print(f"RELEVANT: {len(result.get('relevant_docs', []))}")
    print(f"IRRELEVANT: {result.get('irrelevant_count')}")


if __name__ == "__main__":
    main()
