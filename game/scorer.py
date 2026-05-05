"""
Scoring system using sentence-transformers for semantic similarity.

Why sentence-transformers over exact match:
- "surgeon" should score well for "doctor" — exact match would give 0
- "caregiver" should score well for "nurse" — same reason
- This makes the game fair and more interesting

Model: all-MiniLM-L6-v2
- 80MB, fast on CPU, high quality embeddings
"""

from sentence_transformers import SentenceTransformer, util

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def load_embedder():
    """Load embedding model (cached by Streamlit)."""
    return SentenceTransformer(EMBEDDING_MODEL)


def score_guess(embedder, guess: str, target_words: list[str]) -> tuple[float, str]:
    """
    Score a player's guess against a list of LLM-generated target words.

    Returns:
        (best_score, best_match) where score is 0.0–1.0
        and best_match is the target word the guess was closest to.
    """
    if not guess.strip():
        return 0.0, ""

    guess_emb = embedder.encode(guess, convert_to_tensor=True)
    target_embs = embedder.encode(target_words, convert_to_tensor=True)

    cosine_scores = util.cos_sim(guess_emb, target_embs)[0]
    best_idx = cosine_scores.argmax().item()
    best_score = cosine_scores[best_idx].item()

    return round(best_score, 3), target_words[best_idx]


def score_label(score: float) -> str:
    """Convert numeric score to a human-readable label."""
    if score >= 0.75:
        return "🎯 Exact match!"
    elif score >= 0.55:
        return "🔥 Very close!"
    elif score >= 0.40:
        return "👍 Decent guess"
    elif score >= 0.25:
        return "🤔 Loosely related"
    else:
        return "❌ Far off"
