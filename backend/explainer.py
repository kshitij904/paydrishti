"""
PayDrishti explainer — the second AI surface.

Turns the risk engine's structured flags into a short, calm, plain-language
warning the payer actually reads at checkout. This is separate from the ML
model: the model decides *how risky*, the explainer decides *what to say*.

Providers (set LLM_PROVIDER in .env):
  none      -> deterministic template (always works, no setup)
  ollama    -> FREE local model on your Mac (no API key, data stays on device)
  anthropic -> Claude API (needs LLM_API_KEY)
  openai    -> OpenAI API (needs LLM_API_KEY)

Whatever the provider, the explainer:
  - is given ONLY abstract risk flags, never raw personal/payment data
  - never invents helpline numbers (we append verified ones ourselves)
  - falls back to the template on any error, so checkout never breaks
"""

import os
import requests

HELPLINES = [
    "National Cyber Crime helpline (India): 1930",
    "Report at cybercrime.gov.in",
    "Anti-Human-Trafficking helpline: 1800-11-3090",
]


def active_provider() -> str:
    p = os.getenv("LLM_PROVIDER", "none").lower()
    if p in ("anthropic", "openai") and not os.getenv("LLM_API_KEY", "").strip():
        return "none"  # key missing -> template
    return p


def _helpline_line() -> str:
    return f"Need help? {HELPLINES[0]} | {HELPLINES[1]}"


def _template(band: str, amount: float) -> str:
    headline = ("This payment shows strong signs of a scam."
                if band == "high" else
                "This payment has a few warning signs.")
    return (
        f"{headline} Scammers often rush you to pay a 'fee', 'deposit' or "
        f"'fine' to a new account. If you were contacted about a job, prize, or "
        f"urgent problem, stop and verify through an official channel before "
        f"sending ${amount:.0f}.\n\n{_helpline_line()}"
    )


def _prompt(score: int, reasons: list, amount: float, payee_label: str) -> str:
    flags = "; ".join(r["text"] for r in reasons[:5]) or "no specific flags"
    return (
        "You write short scam warnings shown to someone at the moment they are "
        "about to send money. Our fraud model flagged this payment as high risk.\n\n"
        "Write 2-3 short sentences that:\n"
        "- say plainly that this payment looks like a likely scam and they could "
        "lose this money (state it directly in the first sentence)\n"
        "- tell them to stop and verify the recipient through an official source "
        "before paying\n"
        "- stay calm and plain-spoken; do NOT blame the user\n\n"
        "Rules: everyday words, no jargon (avoid phrases like 'cash-out purpose' "
        "or 'taking precautions'), no corporate filler, no markdown, no invented "
        "facts or phone numbers.\n\n"
        "Good example tone: \"This payment looks like a likely scam, and if you "
        "send it you may not get the money back. The account has the hallmarks of "
        "ones used to collect scam payments. Please stop and confirm who you're "
        "really paying through an official source first.\"\n\n"
        f"Details: risk {score}/100, amount ${amount:.0f}, paying '{payee_label}'. "
        f"Reasons: {flags}."
    )


def _ollama(prompt: str) -> str:
    model = os.getenv("LLM_MODEL", "llama3.2")
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    resp = requests.post(
        f"{host}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False,
              "options": {"temperature": 0.4, "num_predict": 160}},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["response"].strip()


def _anthropic(prompt: str) -> str:
    key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "claude-3-5-haiku-20241022")
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": model, "max_tokens": 200,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"].strip()


def _openai(prompt: str) -> str:
    key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "content-type": "application/json"},
        json={"model": model, "max_tokens": 200,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def explain(score: int, band: str, reasons: list, amount: float,
            payee_label: str = "this payee") -> str:
    """Return payer-facing warning text. Falls back to template on any issue."""
    provider = active_provider()
    if provider == "none":
        return _template(band, amount)

    try:
        prompt = _prompt(score, reasons, amount, payee_label)
        text = {"ollama": _ollama, "anthropic": _anthropic,
                "openai": _openai}[provider](prompt)
        if text:
            return f"{text}\n\n{_helpline_line()}"
    except Exception:
        pass
    return _template(band, amount)
