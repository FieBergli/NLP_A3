# Word Association Bias Game

Exposes gender bias in LLM language through interactive gameplay.

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run app.py
```

First run will download two models (~350MB total):
- `google/flan-t5-base` — generates word associations
- `sentence-transformers/all-MiniLM-L6-v2` — scores guesses by semantic similarity

Both are cached after first download.

## Project structure

```
app.py          ← Streamlit game UI
llm.py          ← HuggingFace model, association generation
scorer.py       ← Cosine similarity scoring of guesses
evaluator.py    ← Consistency tests + bias analysis
word_pairs.py   ← Gendered word pairs + prompt template
requirements.txt
```

## Switching to a larger model

In `llm.py`, change:
```python
MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"
```
And update the pipeline type to `"text-generation"` with `return_full_text=False`.
Requires a GPU and a HuggingFace account (`huggingface-cli login`).
