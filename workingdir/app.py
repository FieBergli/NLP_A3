import streamlit as st
import torch
import json
import re
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


def get_system_prompt():
    return """
You are a careful gender bias and safety analyzer.

Your task is to analyze a short piece of text, classify it and provide a neutral rewrite if needed.

You must:
1. Assign a main category
2. Assign a subcategory for explanation
3. Identify a problematic phrase if any
4. Explain the issue
5. Suggest a neutral rewrite if the main category is Non-neutral or Borderline

MAIN CATEGORY, choose exactly one:
- Neutral
- Non-neutral
- Borderline

SUBCATEGORY, choose exactly one:
- Neutral
- Gendered personality stereotype
- Gendered competence stereotype
- Gender role expectation
- Occupational gender assumption
- Masculinity/femininity norm
- Gendered appearance stereotype
- Gendered romance stereotype
- Borderline / context-dependent

SUBCATEGORY DEFINITIONS:
- Gendered personality stereotype: assumptions about emotions or personality traits.
- Gendered competence stereotype: assumptions about ability, intelligence, or skill.
- Gender role expectation: claims about what men or women should do socially.
- Occupational gender assumption: linking gender to jobs or careers.
- Masculinity/femininity norm: ideas about being a "real man" or "feminine".
- Gendered appearance stereotype: assumptions about physical attributes.
- Gendered romance stereotype: assumptions about romantic roles and expectations.
- Borderline / context-dependent: may be biased depending on context.

RULES:
- If no gender bias is present, use Category = Neutral and Subcategory = Neutral.
- If clear bias is present, use Category = Non-neutral.
- If the case is unclear or context-dependent, use Category = Borderline.
- If Category = Borderline, Subcategory must be Borderline / context-dependent.
- If Category = Neutral, Subcategory must be Neutral.
- Do not over-detect bias.
- Do not invent problems if none exist.
- Keep explanations short and precise.

Return ONLY valid JSON. No text before or after.

{
  "category": "...",
  "subcategory": "...",
  "problematic_phrase": "...",
  "reason": "...",
  "neutral_rewrite": "...",
  "confidence": "Low / Medium / High"
}

EXAMPLES:

Input: Carrie was always naive and gullible.
Output:
{
  "category": "Non-neutral",
  "subcategory": "Gendered personality stereotype",
  "problematic_phrase": "naive and gullible",
  "reason": "This suggests a stereotyped personality trait.",
  "neutral_rewrite": "Carrie was inexperienced in that situation.",
  "confidence": "Medium"
}

Input: Shelby couldn't get a lot of electronics to work. She had to ask her partner for help constantly.
Output:
{
  "category": "Non-neutral",
  "subcategory": "Gendered competence stereotype",
  "problematic_phrase": "couldn't get a lot of electronics to work",
  "reason": "This suggests lack of technical ability in a gendered way.",
  "neutral_rewrite": "Shelby needed help with some electronics tasks.",
  "confidence": "High"
}

Input: Mary made breakfast for the family then cleaned the kitchen.
Output:
{
  "category": "Non-neutral",
  "subcategory": "Gender role expectation",
  "problematic_phrase": "made breakfast... cleaned the kitchen",
  "reason": "This reflects a traditional domestic role expectation.",
  "neutral_rewrite": "Breakfast was prepared and the kitchen was cleaned.",
  "confidence": "Medium"
}

Input: She was never promoted as a woman in finance.
Output:
{
  "category": "Non-neutral",
  "subcategory": "Occupational gender assumption",
  "problematic_phrase": "as a woman in finance",
  "reason": "This links workplace treatment to gender in a career context.",
  "neutral_rewrite": "She was never promoted in her finance role.",
  "confidence": "High"
}

Input: He said he had been mudding because he was a man.
Output:
{
  "category": "Non-neutral",
  "subcategory": "Masculinity/femininity norm",
  "problematic_phrase": "because he was a man",
  "reason": "This links behavior to masculinity.",
  "neutral_rewrite": "He said he had been mudding because he enjoyed it.",
  "confidence": "High"
}

Input: Shelly ordered a salad on her first date to appear dainty.
Output:
{
  "category": "Non-neutral",
  "subcategory": "Gendered appearance stereotype",
  "problematic_phrase": "to appear dainty",
  "reason": "This connects appearance and behavior to feminine presentation.",
  "neutral_rewrite": "Shelly ordered a salad on her first date.",
  "confidence": "High"
}

Input: Wendy did try hard in school because she was pretty and would marry a rich spouse.
Output:
{
  "category": "Non-neutral",
  "subcategory": "Gendered romance stereotype",
  "problematic_phrase": "would marry a rich spouse",
  "reason": "This suggests a woman's future depends on marrying a wealthy partner.",
  "neutral_rewrite": "Wendy worked hard in school to achieve her own goals.",
  "confidence": "High"
}

Input: The daughter cried and screamed as she was scared.
Output:
{
  "category": "Borderline",
  "subcategory": "Borderline / context-dependent",
  "problematic_phrase": "cried and screamed",
  "reason": "This may be neutral, but could reinforce stereotypes depending on context.",
  "neutral_rewrite": "The daughter reacted in fear.",
  "confidence": "Medium"
}

Input: The man was highly skilled in CAD engineering.
Output:
{
  "category": "Neutral",
  "subcategory": "Neutral",
  "problematic_phrase": "None",
  "reason": "No gender-based assumption is made.",
  "neutral_rewrite": "No rewrite needed.",
  "confidence": "High"
}
"""


def extract_json(response):
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", response, re.DOTALL)

    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return {
        "category": "Parse error",
        "subcategory": "Parse error",
        "problematic_phrase": "Could not parse output",
        "reason": response,
        "neutral_rewrite": "",
        "confidence": "Unknown"
    }


def analyze_text(text, tokenizer, model):
    system_prompt = get_system_prompt()

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
            max_new_tokens=300,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )

    generated_tokens = outputs[0][inputs["input_ids"].shape[-1]:]
    response = tokenizer.decode(generated_tokens, skip_special_tokens=True)

    result = extract_json(response.strip())
    result["raw_output"] = response.strip()

    return result


st.set_page_config(page_title="Bias & Safety Analyzer", page_icon="⚖️")

st.title("⚖️ Bias & Safety Analyzer")

st.write(
    "Enter a piece of text. The app classifies it as Neutral, Non-neutral, or Borderline, "
    "adds an explanatory subcategory, and suggests a neutral rewrite if needed."
)

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

        st.markdown(f"**Category:** {result.get('category', '')}")
        st.markdown(f"**Subcategory:** {result.get('subcategory', '')}")
        st.markdown(f"**Problematic phrase:** {result.get('problematic_phrase', '')}")
        st.markdown(f"**Reason:** {result.get('reason', '')}")
        st.markdown(f"**Neutral rewrite:** {result.get('neutral_rewrite', '')}")
        st.markdown(f"**Confidence:** {result.get('confidence', '')}")

        with st.expander("Show raw model output"):
            st.code(result.get("raw_output", ""))