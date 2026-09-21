from dataclasses import asdict, dataclass
from backend.core.ai.model_registry import ModelRegistry
from backend.core.security.findings_parser import FindingSchema


@dataclass
class ExplanationResult:
    what_happened: str
    where: str
    why_dangerous: str
    attack_scenario: str
    secure_recommendation: str
    proposed_patch: str
    confidence: float
    source: str

    def as_dict(self):
        return asdict(self)


class ExplainerService:
    def __init__(self, registry: ModelRegistry | None = None):
        self.registry = registry or ModelRegistry()
        self.llm = self.registry.get_llm()

    def explain_finding(self, finding: FindingSchema, code_context: str = "", rag_context: str = "") -> ExplanationResult:
        if self.llm:
            prompt = f"Explain this security finding for a developer. Never claim certainty. Finding: {finding.issue_text}. File: {finding.file_path}:{finding.line_number}. Code: {code_context}. Project context: {rag_context}"
            generated = "".join(self.llm.generate(prompt, max_tokens=220)).strip()
            if generated:
                return ExplanationResult(what_happened=generated, where=f"{finding.file_path}:{finding.line_number}", why_dangerous=f"{finding.vuln_type} can let untrusted input cross a security boundary.", attack_scenario="Review the proposed scenario against your application trust boundaries.", secure_recommendation=finding.explanation or "Validate input at the boundary and use a safe API.", proposed_patch="Review the generated patch before applying it.", confidence=finding.confidence, source="ai_explanation")
        # This fallback is intentionally useful and honest. A local GGUF provider replaces it without changing the API.
        return ExplanationResult(what_happened=finding.issue_text, where=f"{finding.file_path}:{finding.line_number}", why_dangerous=f"{finding.vuln_type} can let untrusted input cross a security boundary.", attack_scenario=f"An attacker supplies crafted input that reaches the vulnerable operation at line {finding.line_number}.", secure_recommendation=finding.explanation or "Validate input at the boundary and use a safe API.", proposed_patch="Generate a reviewed patch using the secure coding recommendation.", confidence=finding.confidence, source="ai_explanation" if self.registry.llm_available else "deterministic_fallback")
