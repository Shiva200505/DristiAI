from pathlib import Path
import os
import ast
import hashlib
from backend.core.retrieval.vector_store import Document, LocalVectorStore
from backend.core.security.findings_parser import mask_secrets


def index_path(path: str | Path, store: LocalVectorStore | None = None) -> int:
    root = Path(path).resolve()
    store = store or LocalVectorStore(root.name)
    documents = []
    excluded = {".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__", ".drishti", ".pytest_cache"}
    allowed_suffixes = {".md", ".txt", ".py", ".js", ".jsx", ".ts", ".tsx", ".yaml", ".yml", ".json", ".toml", ".xml"}
    max_bytes = int(os.getenv("DRISHTI_INDEX_MAX_FILE_BYTES", str(512 * 1024)))
    for file in root.rglob("*") if root.is_dir() else [root]:
        sensitive_name = file.name.lower() in {".env", ".env.local", "id_rsa", "id_ed25519"} or file.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}
        if file.is_file() and not sensitive_name and file.suffix.lower() in allowed_suffixes and not excluded.intersection({part.lower() for part in file.parts}) and file.stat().st_size <= max_bytes:
            try:
                text = file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            relative = str(file.relative_to(root)) if root.is_dir() else str(file)
            symbols = _symbols(text, file.suffix.lower())
            lines = text.splitlines()
            for index in range(0, len(lines), 80):
                chunk_lines = lines[index:index + 80]
                chunk = "\n".join(chunk_lines)
                if not chunk.strip():
                    continue
                masked_chunk = mask_secrets(chunk)
                chunk_hash = hashlib.sha256(masked_chunk.encode("utf-8")).hexdigest()
                symbol = next((name for start, end, name in symbols if start <= index + 1 <= end), None)
                documents.append(Document(text=masked_chunk, source="local-file", file=relative, section=f"chunk-{index // 80 + 1}", metadata={"bytes": file.stat().st_size, "content_hash": chunk_hash, "line_start": index + 1, "line_end": index + len(chunk_lines), "language": file.suffix.lower().lstrip("."), "symbol": symbol, "secret_masked": True}))
    store.add_documents(documents)
    return len(documents)


def _symbols(text: str, suffix: str) -> list[tuple[int, int, str]]:
    if suffix != ".py":
        return []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    symbols = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            end = getattr(node, "end_lineno", node.lineno)
            symbols.append((node.lineno, end, node.name))
    return symbols
