import os
import time
from datetime import datetime
import pandas as pd
from model_utils import analyze_text, get_prompt_a, get_prompt_b, get_prompt_c, load_model


os.makedirs("results", exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
RESULTS_PATH = f"results/consistency_eval_{timestamp}.txt"


def write_line(file, text=""):
    file.write(text + "\n")
    file.flush()


start = time.time()
print("Loading model...", flush=True)
tokenizer, model = load_model()
print(f"Model loaded in {time.time() - start:.1f}s", flush=True)
print(f"Model device: {model.device}", flush=True)
print(f"Writing results to {RESULTS_PATH}", flush=True)

gender_anti = pd.read_csv("data/gender dataset - antistereo.csv")
gender_stereo = pd.read_csv("data/gender dataset - stereo.csv")
combined = pd.concat([gender_anti, gender_stereo], ignore_index=True)
TEST_SET = combined["Text"].dropna().tolist()[:5]

prompts = {
    "A": get_prompt_a(),
    "B": get_prompt_b(),
    "C": get_prompt_c(),
}

with open(RESULTS_PATH, "w", encoding="utf-8") as results_file:
    write_line(results_file, "Consistency evaluation")
    write_line(results_file, f"Model device: {model.device}")
    write_line(results_file, f"Number of test sentences: {len(TEST_SET)}")
    write_line(results_file)

    for i, sentence in enumerate(TEST_SET, start=1):
        sentence_start = time.time()
        write_line(results_file, f"[{i}/{len(TEST_SET)}] {sentence}")

        for prompt_name, prompt in prompts.items():
            prompt_start = time.time()
            result = analyze_text(sentence, tokenizer, model, prompt)
            write_line(
                results_file,
                f"  {prompt_name}: {result['category']} ({result['confidence']}) "
                f"in {time.time() - prompt_start:.1f}s"
            )

        write_line(results_file, f"  Time: {time.time() - sentence_start:.1f}s")
        write_line(results_file)