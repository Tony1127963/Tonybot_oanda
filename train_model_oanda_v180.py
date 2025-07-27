import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib

# === Načtení dat ===
data = pd.read_csv("training_data.csv")

X = data.drop(columns=["time", "symbol", "signal"])
y = data["signal"]

# === Doplnění NaN hodnot mediánem
X = X.fillna(X.median(numeric_only=True))

# === Rozdělení dat ===
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# === Trénování modelů ===
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)

xgb = XGBClassifier(n_estimators=100, use_label_encoder=False, eval_metric="mlogloss", objective="multi:softmax", num_class=3)
xgb.fit(X_train, y_train)

# === Uložení modelů ===
joblib.dump(rf, "model_rf_oanda_v180.pkl")
joblib.dump(xgb, "model_xgb_oanda_v180.pkl")
print("✅ Modely úspěšně uloženy jako model_rf_oanda_v180.pkl a model_xgb_oanda_v180.pkl")

# === Ensemble predikce ===
rf_preds = rf.predict(X_test)
xgb_preds = xgb.predict(X_test)
final_preds = []

for r, x in zip(rf_preds, xgb_preds):
    if r == x:
        final_preds.append(r)
    else:
        final_preds.append(0)  # HOLD, když se neshodnou

# === Výpis výsledků ===
report = classification_report(y_test, final_preds)
accuracy = accuracy_score(y_test, final_preds)

print("\n=== Ensemble Výsledky ===")
print(report)
print(f"Celková přesnost: {accuracy:.4f}")

# === Uložení do souboru ===
with open("vysledky_modelu.txt", "w") as f:
    f.write("=== Ensemble Výsledky ===\n")
    f.write(report)
    f.write(f"\nCelková přesnost: {accuracy:.4f}")
