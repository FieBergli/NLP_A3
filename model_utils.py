from propmts import PROMPT_A, PROMPT_B, PROMPT_C
import torch
import json
import re
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"


def get_best_device():
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load_model():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    device = get_best_device()

    if device == "cuda":
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float16,
            device_map="auto"
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float16 if device == "mps" else torch.float32
        )
        model.to(device)

    model.eval()

    return tokenizer, model

def get_prompt_a():
    return PROMPT_A

def get_prompt_b():
    return PROMPT_B

def get_prompt_c():
    return PROMPT_C


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


def analyze_text(text, tokenizer, model, system_prompt=PROMPT_A, max_new_tokens=160):

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
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )

    generated_tokens = outputs[0][inputs["input_ids"].shape[-1]:]
    response = tokenizer.decode(generated_tokens, skip_special_tokens=True)

    result = extract_json(response.strip())
    result["raw_output"] = response.strip()

    return result
