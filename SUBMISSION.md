# PayDrishti — Devpost submission

**Author:** kx_builds · **Entry:** solo · **Hackathon:** PayPal AI Hackathon 2026 — "Build What's Next with PayPal and AI"

> Copy each section below into the matching field on the Devpost submission form.
> Swap the links in **Submission details** once your repo, video, and sandbox demo are live.

---

## Project name
PayDrishti

## Elevator pitch (tagline — keep it short)
An AI safety layer for PayPal that warns people *before* they pay a scam — catching fraud at the one place criminals can't hide: the money.

---

## Inspiration
Most payment fraud and trafficking money doesn't move through dramatic hacks — it moves through ordinary payments made by ordinary people who were tricked. Victims are rushed into paying a "job fee," a "deposit," or a "fine" to an account they've never used. By the time anyone notices, the money is gone.

The key realisation: criminals can throw away the *front* of an operation cheaply — fake ads, burner accounts, spoofed numbers — but they **cannot** cheaply replace the thin layer of real cash-out accounts the money funnels into. That reused infrastructure is the one thing that stays constant. PayDrishti targets exactly that, at the exact moment it matters: the instant someone clicks "pay."

## What it does
PayDrishti sits inside a PayPal checkout. When you're about to send money, it scores the payment with AI in real time. If the recipient shows the fingerprints of a scam or money-laundering operation, PayDrishti pauses the payment with a clear, plain-language warning — *before* the money is captured — and lets you decide whether to continue. It never blocks you; it informs you.

- **Safe payee** → payment goes straight through, no friction.
- **Risky payee** → an interstitial explains why, shows a risk score, and points to help — and you choose "Cancel" or "Pay anyway."

## How we built it
A chokepoint inserted into PayPal's own payment flow:

**create order → PayPal approval → PayDrishti risk check → (warn if risky) → capture**

- **Risk model** — a gradient-boosted classifier (scikit-learn) scoring each payment from the payee's behavioural profile. Trained on a synthetic transaction world that models the real adversarial pattern: a churning shell of disposable front accounts hiding a thin, persistent core of reused cash-out accounts. The model reaches ~0.97 ROC-AUC, and its single strongest predictor is `reused_endpoint` — confirming the thesis that the *reused infrastructure*, not the disposable identity, is what gives an operation away.
- **Explainer** — a second AI surface turns the model's risk flags into a short, calm warning the payer actually reads. Runs on a **local LLM (Llama 3 via Ollama)** so it's free and no payment data leaves the machine; hosted models are also supported.
- **PayPal integration** — the backend (FastAPI) uses the PayPal **Orders API v2** on the sandbox to create and capture orders, with the AI risk check gating the capture step. The frontend uses the PayPal JS SDK buttons and PayPal sandbox test accounts.

## How it uses PayPal *and* AI (the core requirement)
- **PayPal:** the payment is created and captured through PayPal's sandbox Orders API; PayPal is the chokepoint the whole product is built around. The risk check lives *between* order approval and capture — a natural control point PayPal's flow provides.
- **AI (two surfaces):** (1) the ML model that decides *how risky* a payment is, and (2) the LLM that decides *what to say* to the user. Neither is cosmetic — the product does not exist without both.

## Challenges we ran into
- **The data problem.** Real fraud data is private and sensitive, and criminals deliberately churn identities. The fix was to stop chasing identity and build a synthetic world that models *infrastructure reuse*, then prove the model recovers the hidden core — rather than assuming clean, honest data.
- **Not crying wolf.** A fraud flag that freezes innocent people is worse than useless. PayDrishti weights signals by how hard they are to fake, treats "no history" as low risk (not high), and always leaves the decision to the human.
- **Making AI output safe.** The warning had to be firm without being alarmist or accusing, and it must never invent helpline numbers — so those are appended from a verified list, never generated.

## Accomplishments that I'm proud of
- A working end-to-end demo: real PayPal sandbox payments gated by a live AI risk check.
- A model whose most important feature independently validates the design thesis.
- A privacy-first explainer that runs entirely on-device.
- A design that protects the *payer* — prevention — rather than only reporting fraud after the fact.

## What I learned
That the leverage against payment-enabled crime isn't identity detection or offensive tooling — it's the money trail and the chokepoint, surfaced to a human who can act. And that a safety tool's hardest problems are ethical (false positives, victim safety, data privacy), not just technical.

## What's next for PayDrishti
- A graph/fusion layer that links accounts, devices, and cash-out endpoints to surface whole rings, not single payments.
- Partnership path: the real cash-out and device signals live inside banks, exchanges, and PSPs — the deployable version is built *with* a payment provider.
- A recruitment-scam detector feeding the same risk graph (the fake-overseas-job pipeline).

## Built with
`python` · `fastapi` · `scikit-learn` · `pandas` · `javascript` · `html` · `css` · `paypal-orders-api` · `paypal-js-sdk` · `ollama` · `llama3` · `uvicorn`

---

## Submission details (fill in before you submit)
- **Try it (repo):** `https://github.com/<your-username>/paydrishti`
- **Demo video (≤ 3 min, public — YouTube/Vimeo):** `<link>`
- **What to test:** pay "Ria's Craft Store" (goes through) vs "GlobalPay Settlements" / "QuickHire Jobs" (warning fires).

---

## Submission checklist
- [ ] Register + verify your Devpost account (real info; `kx_builds` as display name)
- [ ] Confirm eligibility: legal age of majority in India (18+)
- [ ] Push code to a **public** repo (make sure `.env` is NOT committed — `.gitignore` already excludes it)
- [ ] Get PayPal sandbox Client ID → run in live mode for the recording
- [ ] Record the demo video (see VIDEO_SCRIPT.md), upload as **public**, paste the link
- [ ] Fill every Devpost field above
- [ ] Add "Built with" tags
- [ ] Skim the official rules' eligibility + IP sections
- [ ] Submit before **Nov 13, 2026, 1:30 AM IST** (don't wait for the last hour)
