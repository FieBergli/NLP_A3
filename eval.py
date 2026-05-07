import os
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

from model_utils import (
    load_model,
    analyze_text,
    get_prompt_a,
    get_prompt_b,
    get_prompt_c,
    get_prompt_d
)

DATA_PATH = "data/gold_main_category_dataset.csv"

os.makedirs("results", exist_ok=True)


def normalize_category(category):
    if not isinstance(category, str):
        return "Invalid"

    category = category.strip().lower()

    if "non-neutral" in category or "non neutral" in category:
        return "Non-neutral"

    if category == "neutral":
        return "Neutral"

    return "Invalid"


def evaluate_prompt(prompt_name, prompt, df, tokenizer, model):

    print(f"\n===== Running Prompt {prompt_name} =====\n")

    rows = []

    for i, (_, row) in enumerate(df.iterrows(), start=1):

        print(f"[{i}/{len(df)}] Running...", flush=True)

        result = analyze_text(
            row["text"],
            tokenizer,
            model,
            system_prompt=prompt
        )

        pred_category = normalize_category(
            result.get("category", "")
        )

        gold_category = row["gold_category"]

        rows.append({
            "id": row["id"],
            "text": row["text"],
            "source_label": row["source_label"],
            "gold_category": gold_category,
            "pred_category": pred_category,
            "pred_subcategory": result.get("subcategory", ""),
            "confidence": result.get("confidence", ""),
            "reason": result.get("reason", ""),
            "neutral_rewrite": result.get("neutral_rewrite", ""),
            "raw_output": result.get("raw_output", "")
        })

    results = pd.DataFrame(rows)

    results_path = f"results/evaluation_results_{prompt_name}.csv"

    results.to_csv(results_path, index=False)

    accuracy = (
        results["gold_category"]
        == results["pred_category"]
    ).mean()

    print("\nAccuracy:", accuracy)

    print("\nPrediction counts:")
    print(results["pred_category"].value_counts())

    print("\nClassification report:")
    print(classification_report(
        results["gold_category"],
        results["pred_category"],
        zero_division=0
    ))

    print("\nConfusion matrix:")
    print(confusion_matrix(
        results["gold_category"],
        results["pred_category"],
        labels=["Neutral", "Non-neutral"]
    ))

    print(f"\nSaved results to {results_path}")


def main():

    print("Loading model...", flush=True)

    tokenizer, model = load_model()

    print("Model loaded.", flush=True)

    df = pd.read_csv(DATA_PATH)

    print(f"Loaded dataset with {len(df)} rows.", flush=True)

    prompts = {
        "A": get_prompt_a(),
        "B": get_prompt_b(),
        "C": get_prompt_c(),
        "D": get_prompt_d()
    }

    for prompt_name, prompt in prompts.items():

        evaluate_prompt(
            prompt_name,
            prompt,
            df,
            tokenizer,
            model
        )


if __name__ == "__main__":
    main()