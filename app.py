import streamlit as st
from model_utils import get_prompt_a, load_model, analyze_text

st.set_page_config(page_title="Gender Bias Analyzer")

st.title("Gender Bias Analyzer")

st.write(
    "Enter a piece of text. The app classifies it as Neutral or Non-neutral "
    "and adds an explanatory subcategory, and suggests a neutral rewrite if needed."
)


@st.cache_resource
def cached_model():
    return load_model()


user_text = st.text_area(
    "Text to analyze:",
    height=150,
    placeholder="Example: Women are naturally better at caring jobs.",
)

if st.button("Analyze"):
    if user_text.strip() == "":
        st.warning("Please enter some text first.")
    else:
        with st.spinner("Loading model and analyzing text..."):
            tokenizer, model = cached_model()
            result = analyze_text(user_text, tokenizer, model, get_prompt_a())

        st.subheader("Result")

        st.markdown(f"**Category:** {result.get('category', '')}")
        st.markdown(f"**Subcategory:** {result.get('subcategory', '')}")
        st.markdown(f"**Problematic phrase:** {result.get('problematic_phrase', '')}")
        st.markdown(f"**Reason:** {result.get('reason', '')}")
        st.markdown(f"**Neutral rewrite:** {result.get('neutral_rewrite', '')}")
        st.markdown(f"**Confidence:** {result.get('confidence', '')}")

        with st.expander("Show raw model output"):
            st.code(result.get("raw_output", ""))
