"""
Carrega modelo XGBoost e prediz se sinal ICT deve ser executado.
Usado pelo live daemon e backtester.
"""
import json
import os
import numpy as np
from ml.feature_extractor import FEATURE_NAMES, features_to_array


class MLGate:
    def __init__(
        self,
        model_path: str = "ml/models/xgb_ict_gate.json",
        threshold_path: str = "ml/models/threshold.json",
    ):
        try:
            import xgboost as xgb
        except ImportError:
            raise ImportError("pip install xgboost")

        self.model = xgb.XGBClassifier()
        self.model.load_model(model_path)

        with open(threshold_path) as f:
            data = json.load(f)
        self.threshold = data["threshold"]
        print(f"[MLGate] Modelo carregado. Threshold={self.threshold:.2f} "
              f"AUC={data.get('auc_mean', '?')} n={data.get('n_signals', '?')}")

    def should_trade(self, features: dict) -> tuple:
        """Retorna (deve_executar: bool, probabilidade: float)."""
        x = features_to_array(features).reshape(1, -1)
        proba = float(self.model.predict_proba(x)[0, 1])
        return proba >= self.threshold, proba
