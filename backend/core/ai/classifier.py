from backend.core.scanner import scan_code


class SemanticClassifier:
    def classify(self, code: str, filename: str, language: str = "Python") -> list[dict]:
        return [finding.as_dict() for finding in scan_code(code, filename, language, use_external_tools=False)]
