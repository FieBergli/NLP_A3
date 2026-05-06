import os
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
from model_utils import load_model, analyze_text

DATA_PATH = "data/gold_main_category_dataset.csv"
RESULTS_PATH = "results/evaluation_results.csv"

os.makedirs("results", exist_ok=True)


def normalize_category(category):
    if not isinstance(category, str):
        return "Invalid"

    category = category.strip().lower()

    if "non-neutral" in category or "non neutral" in category:
        return "Non-neutral"
    if "borderline" in category or "context" in category:
        return "Borderline"
    if category == "neutral":
        return "Neutral"

    return "Invalid"


def strict_score(gold, pred):
    return int(gold == pred)


def lenient_score(gold, pred):
    if gold == pred:
        return 1.0
    if pred == "Borderline":
        return 0.5
    return 0.0


def main():
    tokenizer, model = load_model()
    df = pd.read_csv(DATA_PATH)

    rows = []

    for _, row in df.iterrows():
        result = analyze_text(row["text"], tokenizer, model)

        pred_category = normalize_category(result.get("category", ""))
        gold_category = row["gold_category"]

        rows.append({
            "id": row["id"],
            "text": row["text"],
            "source_label": row["source_label"],
            "gold_category": gold_category,
            "pred_category": pred_category,
            "pred_subcategory": result.get("subcategory", ""),
            "strict_correct": strict_score(gold_category, pred_category),
            "lenient_score": lenient_score(gold_category, pred_category),
            "confidence": result.get("confidence", ""),
            "reason": result.get("reason", ""),
            "neutral_rewrite": result.get("neutral_rewrite", ""),
            "raw_output": result.get("raw_output", "")
        })

    results = pd.DataFrame(rows)
    results.to_csv(RESULTS_PATH, index=False)

    print("Strict accuracy:", results["strict_correct"].mean())
    print("Lenient accuracy:", results["lenient_score"].mean())

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
        labels=["Neutral", "Non-neutral", "Borderline"]
    ))

    print(f"\nSaved results to {RESULTS_PATH}")


if __name__ == "__main__":
    main()