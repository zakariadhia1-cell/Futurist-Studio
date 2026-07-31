"""Splits raw text into overlapping word-based chunks for embedding.

Word count (not a real tokenizer) is a deliberate simplification for now - it keeps this
provider-agnostic (no dependency on any one vendor's tokenizer) and is close enough for
chunk-sizing purposes. Revisit if a specific provider's token limits become a problem.
"""


def chunk_text(text: str, chunk_size: int = 200, overlap: int = 40) -> list[str]:
    words = text.split()
    if not words:
        return []
    if len(words) <= chunk_size:
        return [text.strip()]

    step = chunk_size - overlap
    chunks = []
    for start in range(0, len(words), step):
        chunk_words = words[start : start + chunk_size]
        if not chunk_words:
            break
        chunks.append(" ".join(chunk_words))
        if start + chunk_size >= len(words):
            break
    return chunks
