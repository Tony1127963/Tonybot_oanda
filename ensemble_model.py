class EnsembleModel:
    def __init__(self, rf_model, xgb_model):
        self.rf = rf_model
        self.xgb = xgb_model

    def predict(self, X):
        rf_pred = self.rf.predict(X)
        xgb_pred = self.xgb.predict(X)
        final = []
        for r, x in zip(rf_pred, xgb_pred):
            if r == x:
                final.append(r)
            else:
                final.append(0)  # HOLD při neshodě
        return np.array(final)

    def predict_proba(self, X):
        rf_proba = self.rf.predict_proba(X)
        xgb_proba = self.xgb.predict_proba(X)
        return (rf_proba + xgb_proba) / 2
