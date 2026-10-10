"""Evidence packing and sufficiency validation for agent reasoning."""
from __future__ import annotations

from typing import Any
from app.models import EvidenceItem, EvidenceStatusEnum


class EvidencePack:
    """Pack of structured evidence for an agent invocation."""

    def __init__(
        self,
        agent_name: str,
        items: list[EvidenceItem],
        status: EvidenceStatusEnum = EvidenceStatusEnum.SUFFICIENT,
        warnings: list[str] | None = None,
        conflicts: list[str] | None = None,
        constraints: list[str] | None = None,
    ):
        self.agent_name = agent_name
        self.items = items
        self.status = status
        self.warnings = warnings or []
        self.conflicts = conflicts or []
        self.constraints = constraints or []

    @property
    def evidence_ids(self) -> list[str]:
        ids = []
        for it in self.items:
            if it.id.startswith("CLM-") and it.id not in ids:
                ids.append(it.id)
        return ids

    def to_prompt_context(self) -> str:
        """Format evidence items into a concise string for LLM prompts."""
        lines = []
        for it in self.items:
            line = f"[{it.id}] ({it.legal_status or 'status:n/a'}, {it.jurisdiction}): {it.text}"
            if it.effective_from:
                line += f" [Effective: {it.effective_from}]"
            if it.conflict_ids:
                line += f" [Conflicts: {','.join(it.conflict_ids)}]"
            lines.append(line)
        return "\n".join(lines)


def build_evidence_pack(
    agent_name: str,
    retrieval_results: list[dict[str, Any]],
    jurisdiction: str = "India",
) -> EvidencePack:
    """Build compact EvidenceItems, check sufficiency, and extract conflicts/warnings."""
    items: list[EvidenceItem] = []
    all_warnings: list[str] = []
    all_conflicts: set[str] = set()
    all_constraints: set[str] = set()
    all_claim_ids: set[str] = set()

    for r in retrieval_results:
        # Collect warnings, conflicts, constraints
        for w in r.get("warnings", []):
            if w not in all_warnings:
                all_warnings.append(w)
        for c in r.get("conflicts", []):
            all_conflicts.add(c)
        for con in r.get("constraints", []):
            all_constraints.add(con)
        for eid in r.get("evidence_ids", []):
            all_claim_ids.add(eid)

        raw_numeric = r.get("numeric")
        numeric_dict = raw_numeric if isinstance(raw_numeric, dict) else {}

        item = EvidenceItem(
            id=r["id"],
            text=r["text"][:220],
            source_id="",
            locator="",
            jurisdiction=r.get("jurisdiction", ""),
            verification=r.get("legal_status", ""),
            legal_status=r.get("legal_status", ""),
            effective_from=r.get("effective_from"),
            status_flags=[],
            conflict_ids=r.get("conflicts", []),
            gap_ids=[],
            numeric=numeric_dict,
        )
        items.append(item)

    # Sufficiency assessment
    status = EvidenceStatusEnum.SUFFICIENT
    if len(items) == 0:
        status = EvidenceStatusEnum.INSUFFICIENT
        all_warnings.append(f"No relevant evidence found for agent {agent_name}.")
    elif len(items) < 2:
        status = EvidenceStatusEnum.PARTIAL
        all_warnings.append(f"Low evidence volume ({len(items)} items) for agent {agent_name}.")

    # Domain-specific sufficiency checks
    if agent_name == "policy_institutional" and jurisdiction.lower() == "india":
        # Check if GAP-006 or airport restriction warning is noted
        pass

    return EvidencePack(
        agent_name=agent_name,
        items=items,
        status=status,
        warnings=all_warnings,
        conflicts=sorted(list(all_conflicts)),
        constraints=sorted(list(all_constraints)),
    )
