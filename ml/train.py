"""
Treina XGBoost nos sinais ICT rotulados.
TimeSeriesSplit para evitar look-ahead. Salva modelo em ml/models/.

Uso: python ml/train.py
     python ml/train.py --dataset ml/data/all_signals_log.json
"""
import sys
import json
import argparse
import os
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ml.feature_extractor import FEATURE_NAMES


def train(dataset_path: str = "ml/data/all_signals_log.json"):
    print(f"[train] Carregando dataset: {dataset_path}")
    with open(dataset_path, encoding="utf-8") as f:
        signals = json.load(f)

    # Filtrar sinais com label válido (0 ou 1)
    signals = [s for s in signals if s.get("label") in (0, 1)]
    print(f"[train] {len(signals)} sinais válidos (WIN/LOSS apenas)")

    if len(signals) < 30:
        print("[AVISO] Menos de 30 sinais. Resultado estatisticamente inválido.")
        if len(signals) == 0:
            return None, None

    # Montar X e y
    rows = []
    for s in signals:
        feat = s["features"]
        row = [feat.get(k, 0.0) for k in FEATURE_NAMES]
        rows.append(row)

    X = np.array(rows, dtype=np.float32)
    y = np.array([s["label"] for s in signals], dtype=int)
    timestamps = [s["timestamp"] for s in signals]

    print(f"[train] Features: {X.shape} | WIN: {y.sum()} | LOSS: {(y==0).sum()}")

    try:
        import xgboost as xgb
        from sklearn.model_selection import TimeSeriesSplit
        from sklearn.metrics import roc_auc_score
    except ImportError as e:
        print(f"[ERRO] Dependência não instalada: {e}")
        print("Execute: pip install xgboost scikit-learn")
        return None, None

    # Cross-validation temporal
    n_splits = min(5, len(signals) // 10)
    if n_splits < 2:
        n_splits = 2

    tscv = TimeSeriesSplit(n_splits=n_splits)
    auc_scores = []

    for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        if len(np.unique(y_val)) < 2:
            continue

        pos_weight = len(y_train[y_train == 0]) / max(1, len(y_train[y_train == 1]))
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=pos_weight,
            random_state=42,
            eval_metric="logloss",
            verbosity=0,
        )
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

        proba = model.predict_proba(X_val)[:, 1]
        auc = roc_auc_score(y_val, proba)
        auc_scores.append(auc)
        print(f"  Fold {fold+1}: AUC={auc:.3f} | n_val={len(val_idx)}")

    if auc_scores:
        print(f"\n[train] AUC médio: {np.mean(auc_scores):.3f} ± {np.std(auc_scores):.3f}")

    # Treinar modelo final em todo o dataset
    pos_weight = len(y[y == 0]) / max(1, len(y[y == 1]))
    final_model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=pos_weight,
        random_state=42,
        verbosity=0,
    )
    final_model.fit(X, y)

    # Feature importance
    importance = dict(zip(FEATURE_NAMES, final_model.feature_importances_))
    top5 = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]
    print("\n[train] Top 5 features:")
    for name, imp in top5:
        print(f"  {name}: {imp:.4f}")

    # Threshold ótimo (maximiza F1)
    probas = final_model.predict_proba(X)[:, 1]
    best_t, best_f1 = 0.5, 0.0
    for t in np.arange(0.35, 0.75, 0.02):
        preds = (probas >= t).astype(int)
        tp = int(((preds == 1) & (y == 1)).sum())
        fp = int(((preds == 1) & (y == 0)).sum())
        fn = int(((preds == 0) & (y == 1)).sum())
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec  = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1   = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        if f1 > best_f1:
            best_f1, best_t = f1, t

    # Salvar
    os.makedirs("ml/models", exist_ok=True)
    final_model.save_model("ml/models/xgb_ict_gate.json")
    with open("ml/models/threshold.json", "w") as f:
        json.dump({"threshold": round(best_t, 2), "f1": round(best_f1, 4),
                   "auc_mean": round(float(np.mean(auc_scores)), 4) if auc_scores else 0,
                   "n_signals": len(signals)}, f, indent=2)

    print(f"\n[train] Modelo salvo. Threshold={best_t:.2f} F1={best_f1:.3f}")
    print(f"[train] Trades que passariam pelo gate: {int((probas >= best_t).sum())} de {len(signals)}")
    return final_model, best_t


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="ml/data/all_signals_log.json")
    args = parser.parse_args()
    train(args.dataset)
