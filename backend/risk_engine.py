"""
PayDrishti risk engine.

Scores a single payment at the moment of checkout and decides whether the
payer should see an interstitial warning BEFORE the money is captured.

Design (straight from the architecture we sketched):
  - ML model gives a base probability from the payee's behavioural profile.
  - Typology RULES add interpretable, permanence-weighted flags (reused
    cash-out endpoint, fan-in funnel, brand-new payee, high cash-out ratio).
  - The two combine into a 0-100 score + a band + plain-language reasons.
  - Output is advice, never an automated block: the human always decides.

The payee profile is looked up from data/payees.json (built by synth.py).
Unknown payees default to low risk -- absence of a bad signal is not a bad
signal.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Optional

import joblib
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")

BAND_LOW = 35
BAND_HIGH = 65  # >= HIGH -> interstitial fires


@dataclass
class RiskResult:
    score: int                       # 0-100
    band: str                        # "low" | "medium" | "high"
    show_interstitial: bool
    reasons: list = field(default_factory=list)   # structured flags
    model_probability: float = 0.0
    payee_known: bool = False

    def to_dict(self):
        return {
            "score": self.score,
            "band": self.band,
            "show_interstitial": self.show_interstitial,
            "reasons": self.reasons,
            "model_probability": round(self.model_probability, 3),
            "payee_known": self.payee_known,
        }


class RiskEngine:
    def __init__(self):
        with open(os.path.join(DATA, "payees.json")) as f:
            self.payees = json.load(f)
        bundle = joblib.load(os.path.join(DATA, "model.pkl"))
        self.model = bundle["model"]
        self.features = bundle["features"]

    def _profile(self, payee_id: str) -> Optional[dict]:
        return self.payees.get(payee_id)

    def _feature_row(self, amount: float, p: Optional[dict]) -> pd.DataFrame:
        if p is None:
            row = dict(amount=amount, payee_age_days=365, payee_fan_in=1,
                       payee_velocity=1, cashout_ratio=0.2, first_time_pair=1,
                       proxy_flag=0, reused_endpoint=0)
        else:
            row = dict(
                amount=amount,
                payee_age_days=p["age_days"],
                payee_fan_in=p["fan_in"],
                payee_velocity=p["tx_count"],
                cashout_ratio=p["cashout_ratio"],
                first_time_pair=1,
                proxy_flag=p["proxy_flag"],
                reused_endpoint=p["reused_endpoint"],
            )
        return pd.DataFrame([row])[self.features]

    def _typology_flags(self, amount: float, p: Optional[dict]) -> list:
        """Interpretable rules. Weight = how hard the signal is to fake."""
        flags = []
        if p is None:
            return flags
        # heavy signals (expensive for criminals to discard)
        if p.get("reused_endpoint"):
            flags.append({"code": "REUSED_CASHOUT", "weight": 30,
                          "text": "pays into a cash-out endpoint reused by many "
                                  "other flagged accounts"})
        if p.get("fan_in", 0) >= 25:
            flags.append({"code": "FAN_IN_FUNNEL", "weight": 25,
                          "text": f"receives money from {p['fan_in']} different "
                                  "senders (funnel pattern)"})
        if p.get("cashout_ratio", 0) >= 0.85:
            flags.append({"code": "HIGH_CASHOUT", "weight": 20,
                          "text": "pushes almost all money straight back out "
                                  "(pass-through account)"})
        # light signals (cheap to change -- supporting evidence only)
        if p.get("age_days", 999) <= 14:
            flags.append({"code": "NEW_PAYEE", "weight": 12,
                          "text": f"account is only {p['age_days']} days old"})
        if p.get("proxy_flag"):
            flags.append({"code": "PROXY", "weight": 6,
                          "text": "traffic routed through a proxy / VPN pool"})
        if amount >= 300:
            flags.append({"code": "LARGE_AMOUNT", "weight": 5,
                          "text": "unusually large one-off payment"})
        return flags

    def score(self, payer_id: str, payee_id: str, amount: float) -> RiskResult:
        p = self._profile(payee_id)
        X = self._feature_row(amount, p)
        model_prob = float(self.model.predict_proba(X)[:, 1][0])

        flags = self._typology_flags(amount, p)
        rule_score = min(sum(f["weight"] for f in flags), 70)

        # blend: model carries general pattern, rules carry permanence + reasons
        combined = 0.55 * (model_prob * 100) + 0.45 * rule_score
        score = int(round(min(combined, 100)))

        band = "low" if score < BAND_LOW else "medium" if score < BAND_HIGH else "high"
        return RiskResult(
            score=score,
            band=band,
            show_interstitial=(band == "high"),
            reasons=flags,
            model_probability=model_prob,
            payee_known=p is not None,
        )


if __name__ == "__main__":
    eng = RiskEngine()
    # quick smoke test against a known core and a known legit payee
    core = next(k for k, v in eng.payees.items() if v["kind"] == "core")
    legit = next(k for k, v in eng.payees.items() if v["kind"] == "legit")
    for label, pid in [("CORE (should be high)", core),
                       ("LEGIT (should be low)", legit),
                       ("UNKNOWN payee", "pay_99999")]:
        r = eng.score("user_00001", pid, 250.0)
        print(f"{label:28s} score={r.score:3d} band={r.band:6s} "
              f"interstitial={r.show_interstitial}")
