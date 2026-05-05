"""
LLM wrapper for generating word associations.

Model choice: google/flan-t5-base
- Instruction-tuned so it follows the "list N words" format reliably
- Small (~250MB), CPU-friendly, no login required
- Fast enough for an interactive game

To switch to a larger model (better quality but needs GPU + HF login):
  MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"
  Change pipeline to: pipeline("text-generation", model=MODEL_NAME, ...)
"""

from transformers import pipeline
from word_pairs import ASSOCIATIONS_PROMPT
import re

MODEL_NAME = "google/flan-t5-base"
N_ASSOCIATIONS = 3  # number of associations to generate per word


def load_model():
    """Load the model once and cache it (Streamlit will cache this via @st.cache_resource)."""
    return pipeline(
        "text-generation",
        model=MODEL_NAME,
        max_new_tokens=60,
        return_full_text=False,
        do_sample=False,
    )


def get_associations(pipe, word: str, n: int = N_ASSOCIATIONS) -> list[str]:
    """
    Generate n word associations for a given word.
    Returns a list of cleaned, lowercase strings.
    """
    prompt = ASSOCIATIONS_PROMPT.format(n=n, word=word)
    output = pipe(prompt)[0]["generated_text"]

    # Parse comma-separated words, strip noise
    raw_words = re.split(r"[,\n]", output)
    words = []
    for w in raw_words:
        w = w.strip().lower()
        w = re.sub(r"[^a-z\-]", "", w)  # keep only letters and hyphens
        if w and w != word.lower():
            words.append(w)

    return words[:n]  # cap at n in case model over-generates
