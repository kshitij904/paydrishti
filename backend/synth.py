"""
Synthetic transaction generator for PayDrishti.

This models the adversarial world we discussed: a churning SHELL of disposable
front accounts hiding a thin, PERSISTENT CORE of reused cash-out accounts.
The detector should not care who an account "is" -- it should surface the core
by the things criminals cannot cheaply throw away (reused payout endpoints,
fan-in funnels, synchronized bursts).

Outputs:
  data/transactions.csv   -> labeled rows for training the model
  data/payees.json        -> per-payee profile the live risk engine looks up
  data/flagged_core.json  -> the persistent-core payees (demo "known bad" list)

Run:  python backend/synth.py
"""

import json
import os
import random
from dataclasses import dataclass, field, asdict

import numpy as np
import pandas as pd

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
os.makedirs(DATA, exist_ok=True)

# ---- world size knobs -------------------------------------------------------
N_LEGIT_PAYEES = 400        # ordinary merchants / people
N_RINGS = 12                # trafficking / scam operations
FRONTS_PER_RING = (15, 40)  # disposable front accounts per ring (min, max)
N_VICTIMS = 600             # people who get scammed into paying
LEGIT_TX = 6000             # ordinary transactions
CORE_ROTATION = 0.15        # how often the core swaps infrastructure (difficulty knob)
# Higher CORE_ROTATION = core hides better = harder detection. Try 0.05 vs 0.4.


@dataclass
class Payee:
    payee_id: str
    kind: str                 # "legit", "front", "core"
    age_days: int             # account age; fronts are young and respawn
    fan_in: int = 0           # distinct payers seen (computed later)
    tx_count: int = 0         # transactions received
    total_in: float = 0.0
    total_out: float = 0.0
    proxy_flag: int = 0       # light signal: traffic via datacenter/VPN pool
    ring_id: int = -1         # which operation it belongs to (-1 = none)
    reused_endpoint: int = 0  # shares a cash-out wallet/device with the core
    aggregator: int = 0       # legit high-throughput payee (bill-pay, wallet)

    @property
    def cashout_ratio(self) -> float:
        # fraction of received money that is pushed straight back out
        if self.total_in <= 0:
            return 0.0
        return round(min(self.total_out / self.total_in, 1.5), 3)


def _new_id(prefix: str, n: int) -> str:
    return f"{prefix}_{n:05d}"


def build_payees():
    payees = {}

    # ordinary payees: mostly mature + clean, but with realistic exceptions so
    # no single feature cleanly separates good from bad:
    #  - ~15% are NEW legit merchants (young age, like a front)
    #  - ~10% are AGGREGATORS (bill-pay/wallets) with high cash-out + high fan-in
    for i in range(N_LEGIT_PAYEES):
        pid = _new_id("pay", i)
        is_new = np.random.random() < 0.15
        is_agg = np.random.random() < 0.10
        payees[pid] = Payee(
            payee_id=pid,
            kind="legit",
            age_days=(int(np.random.uniform(1, 20)) if is_new
                      else int(np.random.gamma(6, 120)) + 30),
            proxy_flag=int(np.random.random() < 0.08),   # some legit VPN users
            aggregator=int(is_agg),
        )

    # rings: one persistent core + many disposable fronts
    core_ids = []
    ring_fronts = {}
    for r in range(N_RINGS):
        core_id = _new_id("core", r)
        payees[core_id] = Payee(
            payee_id=core_id,
            kind="core",
            age_days=int(np.random.uniform(40, 300)),  # core persists across churn
            proxy_flag=1,
            ring_id=r,
            reused_endpoint=1,
        )
        core_ids.append(core_id)

        n_fronts = random.randint(*FRONTS_PER_RING)
        fronts = []
        for f in range(n_fronts):
            fid = _new_id(f"front{r}", f)
            payees[fid] = Payee(
                payee_id=fid,
                kind="front",
                age_days=int(np.random.uniform(0, 14)),  # burners: days old
                proxy_flag=int(np.random.random() < 0.8),
                ring_id=r,
                # most fronts quietly reuse the ring's cash-out endpoint;
                # CORE_ROTATION fraction rotate to new infra and look cleaner
                reused_endpoint=int(np.random.random() > CORE_ROTATION),
            )
            fronts.append(fid)
        ring_fronts[r] = fronts

    return payees, core_ids, ring_fronts


def generate_transactions(payees, core_ids, ring_fronts):
    rows = []
    legit_ids = [p for p, v in payees.items() if v.kind == "legit"]
    victim_ids = [_new_id("victim", i) for i in range(N_VICTIMS)]
    payer_pool = [_new_id("user", i) for i in range(2000)]

    # ---- legitimate traffic: normal people paying normal payees ----
    for _ in range(LEGIT_TX):
        payer = random.choice(payer_pool)
        payee = random.choice(legit_ids)
        amount = round(float(np.random.lognormal(mean=3.2, sigma=0.9)), 2)
        rows.append((payer, payee, amount, 0))
        p = payees[payee]
        p.tx_count += 1
        p.total_in += amount
        # aggregators pass most money onward too -> high cash-out ratio overlaps
        # with fronts, so cash-out alone can't separate the classes
        if p.aggregator:
            p.total_out += amount * np.random.uniform(0.7, 0.95)
        else:
            p.total_out += amount * np.random.uniform(0.0, 0.45)

    # ---- fraudulent traffic: victims pay fronts, fronts funnel to core ----
    for r in range(N_RINGS):
        fronts = ring_fronts[r]
        core = core_ids[r]
        # each ring processes a burst of victims
        n_hits = random.randint(40, 140)
        for _ in range(n_hits):
            victim = random.choice(victim_ids)
            front = random.choice(fronts)
            amount = round(float(np.random.lognormal(mean=4.0, sigma=0.7)), 2)
            rows.append((victim, front, amount, 1))
            f = payees[front]
            f.tx_count += 1
            f.total_in += amount
            # most fronts push money straight on, but rotated fronts hold some
            # back to look cleaner -> wider, overlapping cash-out range
            if f.reused_endpoint:
                f.total_out += amount * np.random.uniform(0.8, 1.0)
            else:
                f.total_out += amount * np.random.uniform(0.4, 0.75)

            # the funnel: front -> core (reused endpoint)
            if payees[front].reused_endpoint:
                rows.append((front, core, round(amount * 0.95, 2), 1))
                c = payees[core]
                c.tx_count += 1
                c.total_in += amount * 0.95
                c.total_out += amount * np.random.uniform(0.9, 1.0)

    # ---- compute fan-in (distinct payers per payee) ----
    df = pd.DataFrame(rows, columns=["payer_id", "payee_id", "amount", "label"])
    fan = df.groupby("payee_id")["payer_id"].nunique()
    for pid, n in fan.items():
        if pid in payees:
            payees[pid].fan_in = int(n)

    return df, payees, victim_ids


def featurize(df, payees):
    """Attach the model features to every transaction row."""
    seen_pairs = set()
    feats = []
    for row in df.itertuples(index=False):
        p = payees.get(row.payee_id)
        if p is None:
            # payer paying someone not in our profile store (unknown payee)
            feats.append(dict(
                amount=row.amount, payee_age_days=365, payee_fan_in=1,
                payee_velocity=1, cashout_ratio=0.2, first_time_pair=1,
                proxy_flag=0, reused_endpoint=0, label=row.label))
            continue
        pair = (row.payer_id, row.payee_id)
        first_time = int(pair not in seen_pairs)
        seen_pairs.add(pair)
        feats.append(dict(
            amount=row.amount,
            payee_age_days=p.age_days,
            payee_fan_in=p.fan_in,
            payee_velocity=p.tx_count,
            cashout_ratio=p.cashout_ratio,
            first_time_pair=first_time,
            proxy_flag=p.proxy_flag,
            reused_endpoint=p.reused_endpoint,
            label=row.label,
        ))
    return pd.DataFrame(feats)


def main():
    payees, core_ids, ring_fronts = build_payees()
    df, payees, victim_ids = generate_transactions(payees, core_ids, ring_fronts)
    feat_df = featurize(df, payees)

    # realistic label noise: ~2.5% of records are mislabeled (ambiguous cases,
    # reporting lag). Keeps the model honest -- no synthetic 100% accuracy.
    flip = feat_df.sample(frac=0.025, random_state=SEED).index
    feat_df.loc[flip, "label"] = 1 - feat_df.loc[flip, "label"]

    feat_df.to_csv(os.path.join(DATA, "transactions.csv"), index=False)

    payee_store = {pid: asdict(p) | {"cashout_ratio": p.cashout_ratio}
                   for pid, p in payees.items()}
    with open(os.path.join(DATA, "payees.json"), "w") as f:
        json.dump(payee_store, f, indent=2)

    flagged = {pid: asdict(p) | {"cashout_ratio": p.cashout_ratio}
               for pid, p in payees.items() if p.kind == "core"}
    with open(os.path.join(DATA, "flagged_core.json"), "w") as f:
        json.dump(flagged, f, indent=2)

    n_fraud = int(feat_df["label"].sum())
    print(f"transactions: {len(feat_df)}  fraud: {n_fraud}  "
          f"legit: {len(feat_df) - n_fraud}")
    print(f"payees: {len(payee_store)}  persistent cores: {len(flagged)}")
    print(f"core rotation (difficulty): {CORE_ROTATION}")
    print("wrote data/transactions.csv, data/payees.json, data/flagged_core.json")


if __name__ == "__main__":
    main()
