# Deploying PayDrishti live (free, safe, sandbox-only)

This puts a public "try it" link in front of judges. It runs the **PayPal
sandbox only** — no real money can move. Your PayPal secret is entered
privately in the host dashboard and never stored in git.

We use **Render.com** (free tier, no card required).

## What the cloud version does differently (and why that's fine)
- **AI warnings:** the cloud has no Ollama, so the live site uses the clean
  built-in **template** warnings (set by `LLM_PROVIDER=none`). Your *video* can
  still use the nicer local-LLM warnings — the live link is just "proof it runs".
- **Everything else is identical:** real PayPal sandbox Orders API, the risk
  check, the interstitial, the network graph.

## Steps

### 1. Push render.yaml to GitHub (it holds NO secrets)
In VS Code terminal (project root):
```
git add render.yaml DEPLOY.md
git commit -m "Add Render deployment config"
git push origin main
```

### 2. Create the Render service
1. Go to **https://render.com** → sign up (you can use "Sign in with GitHub").
2. Click **New +** → **Blueprint**.
3. Connect your GitHub and pick the **paydrishti** repo.
4. Render reads `render.yaml` and shows the service. Click **Apply**.

### 3. Enter your sandbox credentials privately
Render will prompt for the two `sync:false` secrets (or add them under the
service's **Environment** tab):
- `PAYPAL_CLIENT_ID` = your **US sandbox app** Client ID
- `PAYPAL_CLIENT_SECRET` = your **US sandbox app** Secret

These live only in Render, never in git.

### 4. Deploy
Render builds (installs deps, generates data, trains the model) and starts the
app. First build takes ~3–5 minutes. When it's live you get a URL like
`https://paydrishti.onrender.com`.

### 5. Test the live URL
Open it → badge says **sandbox** → pick GlobalPay Settlements → PayPal → log in
with your **US sandbox buyer** → Complete Purchase → the AI warning fires.

> Free tier note: the service **sleeps after ~15 min idle**, so the first visit
> after a nap takes ~30–50s to wake. Fine for judging — just open your link a
> minute before you need to show it. Put the link in your Devpost "Try it" field.

## Safety checklist
- [x] Secret only in Render dashboard, never in git (`.env` + render.yaml both clean)
- [x] `PAYPAL_ENV=sandbox` — no real money
- [x] Public page clearly shows the **sandbox** badge
