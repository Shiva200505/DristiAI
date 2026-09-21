from __future__ import annotations

import hashlib
import os


class EmbeddingUnavailable(RuntimeError):
    pass


class LocalEmbedder:
    """Real local embeddings when explicitly installed, with a test-only fallback.

    The fallback is deliberately exposed as ``EMERGENCY_HASH_FALLBACK``. It is
    useful for an offline smoke test but is never presented as semantic AI.
    """

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or os.getenv("DRISHTI_EMBEDDING_MODEL")
        self._model = None
        self.use_hash_fallback = os.getenv("DRISHTI_EMERGENCY_HASH_EMBEDDINGS", "false").lower() in {"1", "true", "yes"}
        self.backend = "EMERGENCY_HASH_FALLBACK" if self.use_hash_fallback else "NO_EMBEDDING_MODEL"
        self.dimensions = 32 if self.use_hash_fallback else 0
        if self.model_name:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name, local_files_only=os.getenv("DRISHTI_ALLOW_MODEL_DOWNLOAD", "false").lower() not in {"1", "true", "yes"})
                self.dimensions = int(self._model.get_sentence_embedding_dimension())
                self.backend = "SENTENCE_TRANSFORMERS_CPU"
            except Exception:
                self._model = None

    @property
    def is_real_model(self) -> bool:
        return self._model is not None

    def metadata(self) -> dict:
        return {"model": self.model_name or "none", "backend": self.backend, "dimensions": self.dimensions, "semantic": self.is_real_model}

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self._model is not None:
            return [[round(float(value), 8) for value in vector] for vector in self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)]
        if not self.use_hash_fallback:
            return [[] for _ in texts]
        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            vectors.append([round(byte / 255, 4) for byte in digest[: self.dimensions]])
        return vectors
