#!/usr/bin/env python3
# compute_initial_weights_and_graphs.py
# ───────────────────────── Imports ─────────────────────────
import json, textwrap
from pathlib import Path




from pyvis.network import Network                # interactive graphs
import matplotlib.cm as cm                        # colour map "Blues"
import matplotlib.colors as mcolors               # RGB → #RRGGBB

# ───────────────────────── Paths ──────────────────────────
BASE_DIR  = Path(__file__).resolve().parent
SRC_DIR   = BASE_DIR / "Kialo_debates"
DST_DIR   = BASE_DIR / "kialo_debates_initial_weights_added"
GRAPH_DIR = BASE_DIR / "graphs_initial_weights_added"

DST_DIR.mkdir(exist_ok=True)
GRAPH_DIR.mkdir(exist_ok=True)

# ─────────────────── Helper functions ─────────────────────
def aggregate_votes(votes: dict, neutral: float = 0.5) -> float:
    """
    Compute the initial weight s_i(a, w) described by Yang et al. [2]  
    and reused by Young et al.

    Parameters
    ----------
    votes : dict
        Anonymized votes stored as {"0": count, "1": count, ..., "4": count}
        – keys are strings "0"‥"4"; values are integers (vote counts).
    neutral : float
        Value to return when no one has voted yet (paper sets this to 0.5).

    Returns
    -------
    float
        A score in [0, 1].

    Formula
    -------
                 ⎧ 0.5                       if no votes
        s_i(a) = ⎨
                 ⎩  (v · w) / Σ v_k          otherwise

        • v      = [#votes_0, #votes_1, #votes_2, #votes_3, #votes_4] ∈ ℕ⁵
        • w      = [0.00, 0.25, 0.50, 0.75, 1.00] ∈ ℝ⁵
        • “·”    = dot product
        • Σ v_k  = total number of votes (normalisation)
    """

    # ── 1) fixed weights w for scores 0 .. 4
    weights = [0.00, 0.25, 0.50, 0.75, 1.00]

    # ── 2) build the vote-count vector v from anonymized counts
    # votes.get(str(i), 0) returns the count for key "i" (or 0 if missing)
    counts = [votes.get(str(i), 0) for i in range(5)]

    # total number of people who voted on this argument
    total = sum(counts)

    # ── 3) if nobody voted, return the neutral default (0.5)
    if total == 0:
        return neutral

    # ── 4) compute the weighted average  (v · w) / total
    weighted_sum = sum(c * w for c, w in zip(counts, weights))
    return weighted_sum / total



def blues(weight: float) -> str:
    """Return a darker blue (#RRGGBB) as the weight increases."""
    rgb = cm.get_cmap("Blues")(0.3 + 0.7 * weight)[:3]  # modern Matplotlib call
    return mcolors.to_hex(rgb)


def enrich_and_save(src: Path, dst: Path) -> dict:
    """
    Read JSON file `src`, add 'initial_weight' to every node,
    write the enriched file to `dst`, and return the JSON dict.
    """
    data = json.loads(src.read_text(encoding="utf-8"))

    for node in data["nodes"].values():
        node["initial_weight"] = aggregate_votes(node.get("votes", {}))

    dst.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data

# ─────────────── Build an interactive tree graph ────────────────
def build_tree_graph(data: dict, html_path: Path):
    """
    Create a pyvis Network where each node is:

      • a plain white circle with black border
      • label split into two parts:
            line 1 → argument ID  (inside the circle)
            line 2 → w=<initial_weight>  (just below / next to circle)

    Edge orientation = Kialo JSON direction (source ▶ successor).
    Saved as HTML without opening a browser.
    """
    net = Network(height="750px",
                  width="100%",
                  directed=True,
                  bgcolor="#ffffff")

    # 1) Nodes --------------------------------------------------------------
    for nid, nd in data["nodes"].items():
        w = nd["initial_weight"]

        # multi-line label: ID on first line, weight on second
        label = f"{nid}\nw={w:.2f}"

        # colour object → white fill, black border, same on hover
        color_obj = {
            "border": "#000000",
            "background": "#ffffff",
            "highlight": {"border": "#000000", "background": "#ffffff"},
            "hover":     {"border": "#000000", "background": "#ffffff"}
        }

        net.add_node(
            nid,
            label=label,
            title=f"Node: {nid} | Weight: {w:.3f} | Votes: {nd.get('votes', {})}",  # tooltip with node info
            color=color_obj,
            size=10 + 30 * w,             # node size ∝ weight
            shape="circle",
            font={"multi": "html"}        # allow newline in label
        )

    # 2) Edges --------------------------------------------------------------
    for src_id, edge in data["edges"].items():
        dst_id = edge["successor_id"]
        rel    = edge.get("relation", 0.0)
        if rel == 0.0:
            continue

        net.add_edge(
            src_id, dst_id,
            color="#d62728" if rel < 0 else "#2ca02c",
            arrows="to",
            width=2
        )

    # 3) Layout -------------------------------------------------------------
    net.set_options("""
    var options = {
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "DU",      
          "sortMethod": "directed"
        }
      },
      "physics": { "enabled": false },
      "edges": { "smooth": false },
      "interaction": { "navigationButtons": true }
    }
    """)
    

    # 4) Save HTML ----------------------------------------------------------
    net.write_html(str(html_path), open_browser=False)


# ───────────────────────── Pipeline ─────────────────────────
for src_json in SRC_DIR.glob("*.json"):
    # 1) enrich JSON and save
    enriched_path = DST_DIR / src_json.name
    debate        = enrich_and_save(src_json, enriched_path)

    # 2) build HTML graph
    html_file = GRAPH_DIR / f"{src_json.stem}.html"
    build_tree_graph(debate, html_file)

    print(f"✔ {src_json.name:<15} →  {html_file.name}")

print("\n🎉 All done!  Open any .html file inside the 'graphs_initial_weights_added' folder to explore the debates.")

