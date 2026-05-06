import os
import pandas as pd

os.makedirs("data", exist_ok=True)

stereo = pd.read_csv("data/gender dataset - stereo.csv")
antistereo = pd.read_csv("data/gender dataset - antistereo.csv")

stereo = stereo[["Text", "as_s"]].copy()
antistereo = antistereo[["Text", "as_s"]].copy()

stereo.columns = ["text", "source_label"]
antistereo.columns = ["text", "source_label"]

stereo["gold_category"] = "Non-neutral"
antistereo["gold_category"] = "Neutral"

combined = pd.concat([stereo, antistereo], ignore_index=True)

combined.insert(0, "id", range(1, len(combined) + 1))

combined.to_csv("data/gold_main_category_dataset.csv", index=False)

print("Saved data/gold_main_category_dataset.csv")
print(combined.head())
print(combined["gold_category"].value_counts())