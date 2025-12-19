

# ── stdlib
import json
from pathlib import Path

# ── 3rd-party
import networkx as nx
import pandas as pd
from pyvis.network import Network


# ═══════════════════ QEM helper functions ════════════════════
def calculate_energy(n, sup, att, final_acc):
    """ Σ(final supporters) − Σ(final attackers) """
    return sum(final_acc.get(s, 0) for s in sup.get(n, [])) - \
           sum(final_acc.get(a, 0) for a in att.get(n, []))


def h(x):                            
    return (max(x, 0) ** 2) / (1 + max(x, 0) ** 2)


def qem_accept(n, sup, att, final_acc, w_init):
    """QEM-Semantics"""
    # sup est un dictionnaire où les clés sont les arguments et les valeurs sont des listes qui contiennt les supporteurs de chaque argument, si n n'appartient pas à sup ça veut dire l'argument n n'apas de supporteurs
    if n not in sup and n not in att:      # no parents → base weight
        return w_init[n]
    e  = calculate_energy(n, sup, att, final_acc)
    w0 = w_init[n]
    return w0 + (1 - w0) * h(e) if e > 0 else w0 - w0 * h(-e)


# ═════════════ process 1 debate JSON (adds final_weight) ════════════════
def enrich_with_final(src: Path, dst: Path) -> dict:
    """
    Read src JSON, compute final_weight for every node, save to dst.
    Return the loaded & enriched dict (for graph drawing).
    """
    data   = json.loads(src.read_text(encoding="utf-8"))
    nodes, edges = data["nodes"], data["edges"]

    # 1) initial weights as Series , prend les identifiants des arguments et leur poids intitial
    w_init = pd.Series({nid: nd["initial_weight"] for nid, nd in nodes.items()})

    # 2) supporters / attackers + graph
    sup, att, G = {}, {}, nx.DiGraph()
    # prend chaque argument a et son dictionnaire correspondant
    for src_id, e in edges.items():
        # prend l'argument b relié à a, et sa relation soit a attaque soit soutien soit rien 
        dst_id, rel = e["successor_id"], e.get("relation", 0.0)
        G.add_edge(src_id, dst_id)
        #pour chaque argument qui est dst_id ça veut dire destination ajoute tous ses supporteurs dans une liste, donc sup c'est un dictionnaire où les clés sont les arguments et chaque valeur est une liste qui contient les supporteurs de chaque argument. Pareil pour les attaques
        if rel > 0:  sup.setdefault(dst_id, []).append(src_id)
        elif rel<0:  att.setdefault(dst_id, []).append(src_id)

    topo = list(nx.topological_sort(G))  # raises if cycle
    # 3) iterative QEM
    final_acc = {}
    for n in topo:
        # qem_accept prend l'argument poulequel on veut calculer son degré d'acceptabilité, tous les supporteurs et attaquants de tous les arguments, la liste de poids finaux déjà calculés (ici pour le 1er argument la liste est vide mais au fur et à mesure ça se rempli), et finalement les poids initiaux de tous les arguments
        final_acc[n] = qem_accept(n, sup, att, final_acc, w_init)
        nodes[n]["final_weight"] = final_acc[n]

    # 4) save enriched JSON
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    return data


# ═════════════ draw graph (initial & final shown) ═══════════════════════
def build_tree_graph(data: dict, html_path: Path):
    """
    White circle, black border.
    Label (multi-line):
        id
        w0=<initial_weight>
        w1=<final_weight>
    """
    net = Network(height="750px", width="100%", directed=True, bgcolor="#ffffff")

    # ---- nodes ----
    for nid, nd in data["nodes"].items():
        w,  𝜎 = nd["initial_weight"], nd["final_weight"]
        label  = f"{nid}\nw={w:.2f}\n𝜎={𝜎:.2f}"
        tip    = f"Node: {nid} | Initial: {w:.3f} | Final: {𝜎:.3f} | Votes: {nd.get('votes', {})}"
        net.add_node(
            nid, label=label, title=tip,
            color={"border":"#000","background":"#fff"},
            shape="circle", size=10 + 30 * w,
            font={"multi":"html"}
        )

    # ---- edges ----
    for src, e in data["edges"].items():
        dst, rel = e["successor_id"], e.get("relation",0.0)
        if rel == 0:   # neutral / unknown
            continue
        net.add_edge(
            src, dst,
            color="#d62728" if rel < 0 else "#2ca02c",
            arrows="to", width=2
        )

    # ---- layout (compact tree) ----
    net.set_options("""
    {"layout":{"hierarchical":{"enabled":true,"direction":"DU",
                               "sortMethod":"directed",
                               "levelSeparation":80,"nodeSpacing":80}},
     "physics":{"enabled":false},
     "edges":{"smooth":false},
     "interaction":{"navigationButtons":true}}
    """)

    net.write_html(str(html_path), open_browser=False)


# ═════════════════════ batch runner ═════════════════════════
if __name__ == "__main__":
    BASE = Path(__file__).resolve().parent
    SRC_DIR = BASE / "kialo_debates_initial_weights_added"
    JSON_DST_DIR   = BASE / "kialo_debates_final_weights_added"
    GRAPH_DST_DIR  = BASE / "graphs_final_weights_added"
    GRAPH_DST_DIR.mkdir(parents=True, exist_ok=True)

    processed = skipped = 0
    for src_json in SRC_DIR.glob("*.json"):
        dst_json   = JSON_DST_DIR  / src_json.name
        graph_html = GRAPH_DST_DIR / f"{src_json.stem}.html"
        try:
            debate_dict = enrich_with_final(src_json, dst_json)
            build_tree_graph(debate_dict, graph_html)
            processed += 1
            print(f"✔ {src_json.name}")
        except nx.NetworkXUnfeasible:
            skipped += 1
            print(f"✗ {src_json.name} (cycle detected, skipped)")

    print(f"\n🎉 Done.  {processed} debates processed, {skipped} skipped.")
    print(f"JSON with final weights → {JSON_DST_DIR}")
    print(f"Graphs                → {GRAPH_DST_DIR}")
