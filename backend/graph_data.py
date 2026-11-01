"""
Builds the network graph that visualises PayDrishti's core thesis:
a churning SHELL of disposable front accounts funnelling into a thin,
PERSISTENT CORE of reused cash-out accounts.

We don't dump all 734 payees (unreadable). We select a few rings plus some
legit payees for contrast, and emit nodes + edges for the frontend to draw.

Node kinds:
  victim  -> a person who paid (gray)
  front   -> disposable front account (amber)
  core    -> persistent cash-out account (red, large)
  legit   -> ordinary merchant + its normal payers (teal)

Edge = money flow (payer -> payee).
"""

import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")


def build_graph(n_rings: int = 3, fronts_per_ring: int = 8,
                victims_per_front: int = 2, n_legit: int = 4, seed: int = 7) -> dict:
    rng = random.Random(seed)
    with open(os.path.join(DATA, "payees.json")) as f:
        payees = json.load(f)

    # group fronts and cores by ring
    cores = {v["ring_id"]: pid for pid, v in payees.items() if v["kind"] == "core"}
    fronts_by_ring = {}
    for pid, v in payees.items():
        if v["kind"] == "front":
            fronts_by_ring.setdefault(v["ring_id"], []).append(pid)

    chosen_rings = sorted(cores.keys())[:n_rings]
    nodes, edges = [], []
    seen = set()

    def add_node(nid, label, kind, score=None, size=16):
        if nid in seen:
            return
        seen.add(nid)
        nodes.append({"id": nid, "label": label, "kind": kind,
                      "score": score, "size": size})

    victim_counter = 0
    for r in chosen_rings:
        core_id = cores[r]
        c = payees[core_id]
        add_node(core_id, f"cash-out #{r}", "core",
                 score=85, size=34)

        fronts = fronts_by_ring.get(r, [])[:fronts_per_ring]
        for fid in fronts:
            add_node(fid, "front", "front", score=72, size=16)
            # front funnels into the shared core (the permanence edge)
            if payees[fid].get("reused_endpoint"):
                edges.append({"from": fid, "to": core_id, "kind": "funnel"})
            # victims pay the front
            for _ in range(victims_per_front):
                victim_counter += 1
                vid = f"victim_{victim_counter}"
                add_node(vid, "payer", "victim", size=9)
                edges.append({"from": vid, "to": fid, "kind": "pay"})

    # legit contrast: ordinary merchants with scattered, unconnected payers
    legit_ids = [pid for pid, v in payees.items() if v["kind"] == "legit"][:n_legit]
    for i, lid in enumerate(legit_ids):
        add_node(lid, f"merchant {i+1}", "legit", score=3, size=22)
        for _ in range(rng.randint(2, 4)):
            victim_counter += 1
            vid = f"cust_{victim_counter}"
            add_node(vid, "customer", "legit_payer", size=9)
            edges.append({"from": vid, "to": lid, "kind": "pay"})

    return {
        "nodes": nodes,
        "edges": edges,
        "legend": {
            "core": "persistent cash-out account (reused)",
            "front": "disposable front account",
            "victim": "person who paid a front",
            "legit": "ordinary merchant (for contrast)",
        },
        "stats": {
            "rings": len(chosen_rings),
            "fronts": sum(1 for n in nodes if n["kind"] == "front"),
            "cores": sum(1 for n in nodes if n["kind"] == "core"),
        },
    }


if __name__ == "__main__":
    g = build_graph()
    print(f"nodes={len(g['nodes'])} edges={len(g['edges'])} stats={g['stats']}")
