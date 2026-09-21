import hashlib


class LocalEmbedder:
    """Small deterministic fallback so retrieval remains local without a model download."""
    dimensions = 32

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            vectors.append([round(byte / 255, 4) for byte in digest[: self.dimensions]])
        return vectors
