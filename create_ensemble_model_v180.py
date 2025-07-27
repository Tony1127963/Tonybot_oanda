import joblib
from ensemble_model import EnsembleModel
import time

# Načti jednotlivé modely
rf = joblib.load("model_rf_oanda_v180.pkl")
xgb = joblib.load("model_xgb_oanda_v180.pkl")

# Vytvoř ensemble model
ensemble = EnsembleModel(rf, xgb)

# Uložení modelu do jednoho .pkl
joblib.dump(ensemble, "model_v180_ensemble.pkl")

print("✅ Ensemble model úspěšně vytvořen a uložen jako model_v180_ensemble.pkl")
time.sleep(5)  # Pauza na zobrazení výpisu
