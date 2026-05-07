import time
import pandas as pd
from model_utils import analyze_text, get_prompt_a, get_prompt_b, get_prompt_c, load_model


start = time.time()
print("Loading model...", flush=True)
tokenizer, model = load_model()
print(f"Model loaded in {time.time() - start:.1f}s", flush=True)

gender_anti = pd.read_csv("data/gender dataset - antistereo.csv")
gender_stereo = pd.read_csv("data/gender dataset - stereo.csv")
combined = pd.concat([gender_anti, gender_stereo], ignore_index=True)
TEST_SET = combined["Text"].dropna().tolist()[:5]

prompts = {
    "A": get_prompt_a(),
    "B": get_prompt_b(),
    "C": get_prompt_c(),
}

for i, sentence in enumerate(TEST_SET, start=1):
    sentence_start = time.time()
    print(f"\n[{i}/{len(TEST_SET)}] {sentence}", flush=True)

    result_a = analyze_text(sentence, tokenizer, model, prompts["A"])
    result_b = analyze_text(sentence, tokenizer, model, prompts["B"])
    result_c = analyze_text(sentence, tokenizer, model, prompts["C"])
    
    print(f"  A: {result_a['category']} ({result_a['confidence']})")
    print(f"  B: {result_b['category']} ({result_b['confidence']})")
    print(f"  C: {result_c['category']} ({result_c['confidence']})")
    print(f"  Time: {time.time() - sentence_start:.1f}s", flush=True)
