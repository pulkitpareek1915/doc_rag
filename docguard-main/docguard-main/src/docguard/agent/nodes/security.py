import logging

from docguard.agent.state import AgentState, SecurityEvent
from docguard.security import scan_document
from docguard.storage.vector_store import VectorStore

logger = logging.getLogger(__name__)

_store = VectorStore()


from langfuse import get_client, observe


@observe(as_type="span", name="security", capture_input=False, capture_output=False)
def security_node(state: AgentState) -> dict:
    relevant_docs = state.get("relevant_docs", [])

    clean_docs = []
    quarantined_docs = []
    security_events = []

    for document in relevant_docs:
        content = document.get("content", "")
        doc_id = document.get("id", "unknown")

        findings = scan_document(content)

        if findings:
            document["security"] = "quarantined"
            quarantined_docs.append(document)

            # Combine reasons for database
            reasons = ", ".join([f.kind for f in findings])

            try:
                _store.quarantine_document(
                    doc_id=doc_id,
                    content=content,
                    reason=reasons,
                )
            except Exception as e:
                logger.error(f"Failed to quarantine document {doc_id} in DB: {e}")

            for finding in findings:
                security_events.append(
                    SecurityEvent(
                        kind=finding.kind,
                        severity=finding.severity,
                        doc_id=doc_id,
                        detector=finding.detector,
                        detail=finding.detail,
                    )
                )

            try:
                # Log sanitized finding to Langfuse
                sanitized_findings = [
                    {"detector": f.detector, "severity": f.severity}
                    for f in findings
                ]
                langfuse = get_client()
                langfuse.update_current_span(
                    metadata={
                        "security_flagged": True,
                        "document_id": doc_id,
                        "findings": sanitized_findings
                    }
                )
            except Exception:
                pass
        else:
            document["security"] = "clean"
            clean_docs.append(document)

    return {
        "relevant_docs": clean_docs,
        "quarantined_docs": quarantined_docs,
        "security_events": security_events,
    }
