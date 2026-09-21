"""Dependency inventory and optional OSV-Scanner integration.

The inventory path is always local. OSV-Scanner is only invoked when the
operator explicitly allows network-backed dependency intelligence or supplies
an offline OSV database through the scanner itself.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
import re
import tomllib

from backend.core.security.findings_parser import FindingSchema, mask_secrets


MANIFESTS = {
    "package.json": "npm",
    "package-lock.json": "npm",
    "requirements.txt": "pypi",
    "pyproject.toml": "pypi",
    "poetry.lock": "pypi",
    "pom.xml": "maven",
    "build.gradle": "maven",
    "build.gradle.kts": "maven",
}


@dataclass
class DependencyResult:
    status: str
    manifests: list[dict]
    findings: list[dict]
    scanner: str
    message: str

    def as_dict(self) -> dict:
        return asdict(self)


def discover_manifests(root: str | Path) -> list[dict]:
    base = Path(root).resolve()
    results = []
    for path in base.rglob("*"):
        if not path.is_file() or path.name not in MANIFESTS:
            continue
        if {".git", "node_modules", ".venv", "venv", "dist", "build"}.intersection(path.parts):
            continue
        results.append({"path": str(path.relative_to(base)), "ecosystem": MANIFESTS[path.name]})
    return results


def inventory_dependencies(root: str | Path, manifests: list[dict] | None = None) -> list[dict]:
    base = Path(root).resolve()
    inventory = []
    for manifest in manifests or discover_manifests(base):
        path = base / manifest["path"]
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        names: list[str] = []
        if path.name in {"package.json", "package-lock.json"}:
            try:
                payload = json.loads(text)
                for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
                    names.extend(str(name) for name in (payload.get(section) or {}))
                if path.name == "package-lock.json":
                    names.extend(str(name) for name in (payload.get("packages") or {}) if name.startswith("node_modules/"))
            except json.JSONDecodeError:
                pass
        elif path.name == "pyproject.toml":
            try:
                payload = tomllib.loads(text)
                project = payload.get("project") or {}
                names.extend(str(item).split("[", 1)[0].split(">", 1)[0].split("=", 1)[0].strip() for item in project.get("dependencies", []))
                for values in (project.get("optional-dependencies") or {}).values():
                    names.extend(str(item).split("[", 1)[0].split(">", 1)[0].split("=", 1)[0].strip() for item in values)
            except tomllib.TOMLDecodeError:
                pass
        elif path.name in {"requirements.txt", "poetry.lock"}:
            names.extend(match.group(1) for match in re.finditer(r"^\s*([A-Za-z0-9_.-]+)\s*(?:[<>=!~].*)?$", text, re.MULTILINE))
        else:
            names.extend(match.group(1) for match in re.finditer(r"(?m)^\s*([A-Za-z0-9_.-]+)\s*=", text))
        inventory.append({**manifest, "packages": sorted(set(names))})
    return inventory


def scan_dependencies(root: str | Path, allow_network: bool = False, timeout: int = 45) -> DependencyResult:
    manifests = discover_manifests(root)
    if not manifests:
        return DependencyResult("no_manifests", [], [], "none", "No supported dependency manifests were found.")
    command = os.getenv("DRISHTI_OSV_SCANNER", "osv-scanner")
    if not allow_network and os.getenv("DRISHTI_ALLOW_OSV_NETWORK", "false").lower() not in {"1", "true", "yes"}:
        return DependencyResult("inventory_only", inventory_dependencies(root, manifests), [], "local-manifest-inventory", "Dependency inventory collected locally; OSV network access is disabled in local-only mode.")
    try:
        completed = subprocess.run([command, "scan", "source", "--format", "json", str(Path(root).resolve())], capture_output=True, text=True, timeout=timeout, check=False)
        payload = json.loads(completed.stdout or "{}")
        findings = normalize_osv(payload, root)
        return DependencyResult("complete" if completed.returncode == 0 else "vulnerabilities_found", inventory_dependencies(root, manifests), findings, "osv-scanner", "OSV-Scanner completed." if completed.returncode == 0 else "OSV-Scanner reported dependency vulnerabilities.")
    except FileNotFoundError:
        return DependencyResult("scanner_unavailable", inventory_dependencies(root, manifests), [], "osv-scanner", "OSV-Scanner is not installed. Install it explicitly to enable vulnerability intelligence.")
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as exc:
        return DependencyResult("scanner_error", inventory_dependencies(root, manifests), [], "osv-scanner", f"OSV-Scanner could not complete safely: {type(exc).__name__}.")


def normalize_osv(payload: dict, root: str | Path) -> list[dict]:
    findings: list[dict] = []
    for result in payload.get("results", []):
        source = result.get("source", {})
        path = source.get("path", "")
        for package in result.get("packages", []):
            pkg = package.get("package", {})
            for vulnerability in package.get("vulnerabilities", []):
                vuln_id = vulnerability.get("id", "OSV-UNKNOWN")
                summary = mask_secrets(vulnerability.get("summary", "Dependency vulnerability"))
                findings.append(FindingSchema(issue_id=vuln_id, severity="high", confidence=0.9, issue_text=summary, line_number=1, file_path=path, vuln_type="Dependency vulnerability", code_snippet=f"{pkg.get('name', 'unknown')} {pkg.get('version', '')}".strip(), cwe_id=None, test_id=vuln_id, source="osv-scanner", language=pkg.get("ecosystem", "dependency"), detector="OSV-Scanner", recommendation="Upgrade or replace the affected dependency according to the advisory.", evidence={"aliases": vulnerability.get("aliases", []), "manifest": path}, patch_status="RULE_DETECTED"))
    return findings
