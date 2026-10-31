"""
Compare the explainer's output in whatever mode your .env selects.
Run:  python test_explainer.py

With LLM_PROVIDER=none you get the template.
Set LLM_PROVIDER=ollama (and run `ollama serve` + `ollama pull llama3.2`)
to see AI-generated warnings -- free, local, no API key.
"""

from dotenv import load_dotenv
load_dotenv()

from explainer import explain, active_provider

sample_reasons = [
    {"code": "REUSED_CASHOUT", "weight": 30,
     "text": "pays into a cash-out endpoint reused by many other flagged accounts"},
    {"code": "HIGH_CASHOUT", "weight": 20,
     "text": "pushes almost all money straight back out (pass-through account)"},
    {"code": "NEW_PAYEE", "weight": 12, "text": "account is only 7 days old"},
]

print(f"active explainer provider: {active_provider()}\n")
print("=" * 68)
print(explain(82, "high", sample_reasons, 300, "QuickHire Jobs (deposit)"))
print("=" * 68)
