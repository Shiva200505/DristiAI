from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.core.scanner import scan_code


def main() -> int:
    expected = {"DRISHTI-SQL-001", "DRISHTI-SHELL-006", "DRISHTI-PATH-008", "DRISHTI-SECRET-014", "DRISHTI-CRYPTO-018", "DRISHTI-DESER-019", "DRISHTI-XSS-021", "DRISHTI-SSRF-025"}
    detected = set()
    files = list((ROOT / "demo-repo").rglob("*.py")) + list((ROOT / "demo-repo").rglob("*.js"))
    for path in files:
        findings = scan_code(path.read_text(encoding="utf-8"), str(path.relative_to(ROOT)), "javascript" if path.suffix == ".js" else "python", use_external_tools=False)
        detected.update(item.issue_id for item in findings)
        print(f"  {path.relative_to(ROOT)}: {len(findings)} local findings")
    missing = expected - detected
    if missing:
        print(f"[FAIL] Demo preparation failed; missing: {', '.join(sorted(missing))}")
        return 1
    print(f"[OK] Drishti demo environment ready ({len(detected)} vulnerability classes loaded)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
