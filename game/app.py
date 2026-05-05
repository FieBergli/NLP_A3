"""
Word Association Bias Game
Run with: streamlit run app.py
"""

import streamlit as st
import random
from word_pairs import WORD_PAIRS, N_ASSOCIATIONS
from llm import load_model, get_associations
from scorer import load_embedder, score_guess, score_label
from evaluator import consistency_score, bias_score

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Word Association Bias Game", page_icon="🧠", layout="centered")

st.markdown("""
<style>
    .big-word { font-size: 2.5rem; font-weight: 800; letter-spacing: -1px; }
    .assoc-pill {
        display: inline-block; background: #1e293b; color: #e2e8f0;
        border-radius: 999px; padding: 4px 14px; margin: 4px;
        font-size: 0.9rem;
    }
    .bias-box {
        background: #0f172a; border-left: 4px solid #f43f5e;
        padding: 1rem 1.5rem; border-radius: 8px; margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Load models (cached — only runs once) ──────────────────────────────────────
@st.cache_resource
def get_models():
    return load_model(), load_embedder()

with st.spinner("Loading models (first run downloads ~350MB)..."):
    pipe, embedder = get_models()

# ── Session state init ─────────────────────────────────────────────────────────
def init_state():
    if "pair" not in st.session_state:
        st.session_state.pair = random.choice(WORD_PAIRS)
    if "associations" not in st.session_state:
        st.session_state.associations = {}   # {"doctor": [...], "nurse": [...]}
    if "guesses" not in st.session_state:
        st.session_state.guesses = {}        # {word: [(guess, score, match), ...]}
    if "revealed" not in st.session_state:
        st.session_state.revealed = False
    if "scores_this_round" not in st.session_state:
        st.session_state.scores_this_round = []

init_state()

# ── Helper: generate associations for current pair ─────────────────────────────
def generate_associations():
    pair = st.session_state.pair
    for role, word in [("male", pair["male"]), ("female", pair["female"])]:
        if word not in st.session_state.associations:
            with st.spinner(f"LLM generating associations for '{word}'..."):
                st.session_state.associations[word] = get_associations(pipe, word, N_ASSOCIATIONS)

# ── Helper: new round ──────────────────────────────────────────────────────────
def new_round():
    st.session_state.pair = random.choice(WORD_PAIRS)
    st.session_state.associations = {}
    st.session_state.guesses = {}
    st.session_state.revealed = False
    st.session_state.scores_this_round = []

# ══════════════════════════════════════════════════════════════════════════════
# MAIN UI
# ══════════════════════════════════════════════════════════════════════════════

st.title("🧠 Word Association Bias Game")
st.caption("Guess what words an LLM associates with gendered word pairs — then see the bias revealed.")

st.divider()

pair = st.session_state.pair
generate_associations()

# ── Side-by-side word columns ──────────────────────────────────────────────────
col1, col2 = st.columns(2)

for col, word in zip([col1, col2], [pair["male"], pair["female"]]):
    with col:
        st.markdown(f'<div class="big-word">{word.upper()}</div>', unsafe_allow_html=True)
        st.caption(f"The LLM generated {N_ASSOCIATIONS} associations. Can you guess them?")

        # Guess input
        guess_key = f"guess_input_{word}"
        guess = st.text_input(f"Your guess for '{word}'", key=guess_key, placeholder="Type a word…")

        if st.button(f"Submit guess", key=f"btn_{word}"):
            if guess.strip():
                targets = st.session_state.associations[word]
                st.write(type(targets), targets)
                sim, match = score_guess(embedder, guess.strip(), targets)
                label = score_label(sim)
                entry = (guess.strip(), sim, match, label)
                st.session_state.guesses.setdefault(word, []).append(entry)
                st.session_state.scores_this_round.append(sim)

        # Show submitted guesses
        if word in st.session_state.guesses:
            for g, sim, match, label in st.session_state.guesses[word]:
                st.markdown(f"**{g}** → {label} `{sim}`")

st.divider()

# ── Reveal button ──────────────────────────────────────────────────────────────
if st.button("🔍 Reveal LLM associations & bias analysis", type="primary"):
    st.session_state.revealed = True

if st.session_state.revealed:
    st.subheader("What the LLM actually said")

    rcol1, rcol2 = st.columns(2)
    for col, word in zip([rcol1, rcol2], [pair["male"], pair["female"]]):
        with col:
            st.markdown(f"**{word}**")
            words = st.session_state.associations[word]
            pills = " ".join(f'<span class="assoc-pill">{w}</span>' for w in words)
            st.markdown(pills, unsafe_allow_html=True)

    # Bias analysis
    st.subheader("🔬 Bias Analysis")
    male_words = st.session_state.associations[pair["male"]]
    female_words = st.session_state.associations[pair["female"]]
    result = bias_score(embedder, male_words, female_words)

    st.markdown(f"""
<div class="bias-box">
<strong>Cross-similarity score:</strong> {result['avg_cross_similarity']} / 1.0<br>
<strong>Interpretation:</strong> {result['bias_label']}<br><br>
A <em>low score</em> means the LLM uses semantically different language for
<strong>{pair['male']}</strong> vs <strong>{pair['female']}</strong> — a sign of gender bias in its associations.
</div>
""", unsafe_allow_html=True)

    # Player score summary
    if st.session_state.scores_this_round:
        avg = sum(st.session_state.scores_this_round) / len(st.session_state.scores_this_round)
        st.metric("Your average guess similarity", f"{avg:.2f}")

st.divider()

# ── Controls ───────────────────────────────────────────────────────────────────
bcol1, bcol2 = st.columns(2)
with bcol1:
    if st.button("🔄 New word pair"):
        new_round()
        st.rerun()

with bcol2:
    with st.expander("🧪 Run consistency test (slow)"):
        test_word = st.selectbox("Test word", [pair["male"], pair["female"]])
        if st.button("Run 3 trials"):
            with st.spinner("Running consistency test..."):
                result = consistency_score(pipe, embedder, test_word, runs=3, n=N_ASSOCIATIONS)
            st.write(f"**Consistency score:** {result['consistency_score']} / 1.0")
            for i, run in enumerate(result["runs"]):
                st.write(f"Run {i+1}: {', '.join(run)}")
