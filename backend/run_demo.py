"""
CLI demo of the PayDrishti risk engine -- runs with NO PayPal credentials.
Shows exactly what the checkout interstitial will say.

Run (after synth.py and model.py):
    python backend/run_demo.py
"""

from risk_engine import RiskEngine
from explainer import explain


def show(eng, label, payer, payee, amount):
    r = eng.score(payer, payee, amount)
    print("=" * 68)
    print(f"{label}")
    print(f"  payee={payee}  amount={amount:.0f}  ->  "
          f"score={r.score}/100  band={r.band.upper()}  "
          f"interstitial={'YES' if r.show_interstitial else 'no'}")
    if r.show_interstitial:
        print("-" * 68)
        print("Why we're warning you:")
        for reason in r.reasons[:4]:
            print(f"  - this payee {reason['text']}")
        print()
        print(explain(r.score, r.band, r.reasons, amount))
    print()


def main():
    eng = RiskEngine()
    core = next(k for k, v in eng.payees.items() if v["kind"] == "core")
    front = next(k for k, v in eng.payees.items() if v["kind"] == "front")
    legit = next(k for k, v in eng.payees.items() if v["kind"] == "legit")

    show(eng, "1) Paying a legit merchant", "user_00001", legit, 85)
    show(eng, "2) Paying a persistent-core cash-out account", "user_00001", core, 300)
    show(eng, "3) Paying a disposable front account", "victim_0001", front, 220)
    show(eng, "4) Paying an unknown payee (no history)", "user_00001", "pay_88888", 120)


if __name__ == "__main__":
    main()
