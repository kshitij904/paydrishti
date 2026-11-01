# PayDrishti — demo video script (~3 minutes)

A shot-by-shot script. Left = what's on screen. Right = what you say (narration).
Aim for 2:45–3:00. Record screen with QuickTime (Mac: Cmd+Shift+5) and talk over it,
or record narration separately. Speak calmly; let the product do the work.

**Before recording:**
- Ideally run in **live mode** (sandbox Client ID in `.env`) so real PayPal buttons show. If PayPal isn't set up yet, mock mode is fine — just say "PayPal sandbox" and the flow is identical.
- Have the app open at http://localhost:8000 and a terminal ready.
- Set amount to 250–300 for the risky demo.

---

### Scene 1 — The hook (0:00–0:20)
**Screen:** Title card or the checkout page, still.
**Say:** "Most scam and trafficking money doesn't move through hacking — it moves through normal payments, made by people who were tricked into paying a fake fee or deposit. By the time anyone notices, the money's gone. PayDrishti stops it at the one place criminals can't hide: the payment itself."

### Scene 2 — What it is (0:20–0:40)
**Screen:** The PayDrishti checkout, pointing at the badge and payee dropdown.
**Say:** "PayDrishti is an AI safety layer that lives inside a PayPal checkout. The moment you're about to send money, it scores the payment — and if the recipient looks like a scam operation, it warns you before the money leaves your account. It never blocks you. You decide."

### Scene 3 — A safe payment (0:40–1:05)
**Screen:** Select "Ria's Craft Store", amount 85, click Pay / PayPal button, complete.
**Say:** "Here's a normal payment to a real merchant. PayDrishti scores it, sees nothing suspicious, and gets out of the way — the payment goes straight through PayPal. No friction for honest transactions. That matters: a safety tool that nags on every payment is useless."

### Scene 4 — A risky payment (1:05–1:55) — THE HERO MOMENT
**Screen:** Select "GlobalPay Settlements" (or "QuickHire Jobs"), amount 300, click Pay. The interstitial appears.
**Say:** "Now the same checkout, but paying an account with the fingerprints of a scam cash-out. Watch — PayDrishti pauses the payment *before* it's captured."
**Screen:** Point to the risk meter, the reason bullets, the AI warning text.
**Say:** "It shows why: this account is reused by many other flagged accounts, it passes money straight through, it's brand new. And the warning in plain language — written by an on-device AI model — tells me to stop and verify before paying. I can cancel, or pay anyway. I'll cancel."
**Screen:** Click "Cancel payment" → the "good call" message.

### Scene 5 — The network view (1:55–2:25) — SHOWS THE DEPTH
**Screen:** Click "See the fraud network view" → the graph loads. Let it settle, then hover a red hub.
**Say:** "Here's why it works. This is the fraud network PayDrishti sees. Each red hub is a cash-out account — and all these amber front accounts funnel into it. Criminals throw away the fronts cheaply, but they can't cheaply replace the hub the money collects in. The legit merchants, in green, sit in separate shallow clusters. PayDrishti scores the *shape* of these funnels, not identities — so it still works when the fronts are burners."

### Scene 5b — The proof (2:25–2:40)
**Screen:** Terminal showing `python backend/model.py` output (the feature-importance list).
**Say:** "And the model independently confirms it: its single strongest signal is 'reused endpoint' — exactly the infrastructure criminals can't discard. The whole risk check sits inside PayPal's Orders API flow, between approval and capture."

### Scene 6 — Close (2:40–3:00)
**Screen:** Back to the interstitial, or a closing card with the helpline line visible.
**Say:** "PayDrishti protects the person *before* they're caught — not after the money's gone. It uses PayPal as the chokepoint and AI as the judgment, and it runs privately, on-device. That's what's next for payment safety. Thanks for watching."

---

### Tips
- Keep each scene tight — if you run long, trim Scene 1 and 5 first.
- Do one practice run, then a clean take. You don't need it perfect.
- Make sure the risk meter and warning text are readable on screen (zoom the browser to 110–125% before recording).
- Upload as **Public** (not Unlisted-only if the rules require public) and paste the link into Devpost.
