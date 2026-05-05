import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"


@st.cache_resource
def load_model():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto"
    )

    return tokenizer, model


def analyze_text(text, tokenizer, model):
    system_prompt = """
You are a bias and safety analyzer.

Your task:
1. Decide whether the input text is Neutral or Non-neutral.
2. Non-neutral means it contains gender bias, stereotypes, victim-blaming, unsafe advice, or problematic language.
3. If the text is Neutral, say no rewrite is needed.
4. If the text is Non-neutral, provide a more neutral and safer rewrite.

Use exactly this format:

Category: Neutral or Non-neutral
Reason: short explanation
Neutral rewrite: rewrite here, or "No rewrite needed."
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Analyze this text:\n{text}"}
    ]

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=200,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )

    generated_tokens = outputs[0][inputs["input_ids"].shape[-1]:]
    response = tokenizer.decode(generated_tokens, skip_special_tokens=True)

    return response.strip()


st.set_page_config(page_title="Bias & Safety Analyzer", page_icon="⚖️")

st.title("⚖️ Bias & Safety Analyzer")
st.write("Enter a piece of text. The app will classify it as neutral or non-neutral and suggest a neutral rewrite if needed.")

user_text = st.text_area(
    "Text to analyze:",
    height=150,
    placeholder="Example: Women are naturally better at caring jobs."
)

if st.button("Analyze"):
    if user_text.strip() == "":
        st.warning("Please enter some text first.")
    else:
        with st.spinner("Loading model and analyzing text..."):
            tokenizer, model = load_model()
            result = analyze_text(user_text, tokenizer, model)

        st.subheader("Result")
        st.write(result)