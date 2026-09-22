from backend.core.ai.explainer import ExplainerService
from backend.core.ai.model_registry import ModelRegistry
from backend.core.scanner import scan_code


class SemanticClassifier:
    def __init__(self, registry: ModelRegistry | None = None):
        self.registry = registry or ModelRegistry()
        self.explainer = ExplainerService(self.registry)

    def classify(self, code: str, filename: str, language: str = "Python") -> list[dict]:
        findings = scan_code(code, filename, language, use_external_tools=False)
        results = []
        for finding in findings:
            explanation = self.explainer.explain_finding(finding, code_context=finding.surrounding_context)
            payload = finding.as_dict()
            payload.update({
                "semantic_status": explanation.source,
                "semantic_confidence": explanation.confidence,
                "semantic_explanation": explanation.what_happened,
                "semantic_attack_scenario": explanation.attack_scenario,
                "semantic_recommendation": explanation.secure_recommendation,
                "semantic_patch": explanation.proposed_patch,
                "semantic_model": explanation.model,
                "semantic_runtime": explanation.runtime,
                "semantic_provenance": explanation.provenance,
                "requires_review": explanation.requires_review,
            })
            results.append(payload)
        return results
