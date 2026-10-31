"""
Trains the PayDrishti fraud model on the synthetic transactions.

Gradient-boosted trees on the engineered features. We also report which
features drive the score, because an unexplainable fraud flag is useless to
an analyst -- and dangerous to the person whose payment we interrupt.

Run:  python backend/model.py   (run synth.py first)
"""

import os
import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")

FEATURES = [
    "amount", "payee_age_days", "payee_fan_in", "payee_velocity",
    "cashout_ratio", "first_time_pair", "proxy_flag", "reused_endpoint",
]


def main():
    df = pd.read_csv(os.path.join(DATA, "transactions.csv"))
    X, y = df[FEATURES], df["label"]
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y)

    clf = GradientBoostingClassifier(random_state=42)
    clf.fit(Xtr, ytr)

    proba = clf.predict_proba(Xte)[:, 1]
    print(classification_report(yte, clf.predict(Xte), digits=3))
    print(f"ROC-AUC: {roc_auc_score(yte, proba):.3f}\n")

    print("feature importance (what drives the risk score):")
    for name, imp in sorted(zip(FEATURES, clf.feature_importances_),
                            key=lambda t: -t[1]):
        print(f"  {name:18s} {imp:.3f}")

    joblib.dump({"model": clf, "features": FEATURES},
                os.path.join(DATA, "model.pkl"))
    print("\nwrote data/model.pkl")


if __name__ == "__main__":
    main()
