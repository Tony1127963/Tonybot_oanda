import os
import pandas as pd
from voting_signal import get_voting_signal

folder = "indikatory"
out_file = "training_data.csv"
dfs = []

for filename in os.listdir(folder):
    if filename.endswith(".csv"):
        path = os.path.join(folder, filename)
        df = pd.read_csv(path)
        df["symbol"] = filename.replace(".csv", "")
        df["signal"] = df.apply(get_voting_signal, axis=1)
        dfs.append(df)

combined = pd.concat(dfs, ignore_index=True)
combined.to_csv(out_file, index=False)
print(f"✅ Uloženo do {out_file}")
