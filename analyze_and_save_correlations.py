#!/usr/bin/env python3
# analyze_and_save_correlations.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr, spearmanr
from pathlib import Path

# 1) Répertoires
COV_DIR    = Path("size_explanation")
WEIGHT_DIR = Path("debates_with_target_weight_change")

OUT_DIR    = Path("correlation_analysis_output")
PLOTS_DIR  = OUT_DIR / "plots"
OUT_FILE   = OUT_DIR / "correlations_by_type_heuristic.csv"

OUT_DIR.mkdir(exist_ok=True)
PLOTS_DIR.mkdir(exist_ok=True)

# 2) Chargement et fusion
records = []

for cov_path in COV_DIR.glob("*_size_analysis.csv"):
    try:
        parts = cov_path.stem.split("_")
        if len(parts) < 7:
            raise ValueError(f"Filename parsing failed for {cov_path.name}")
        did = parts[0]
        tid = parts[2]
        #breakpoint()  # Breakpoint 1
        try:
            df_cov = pd.read_csv(cov_path, engine="python")
        except Exception as e:
            raise RuntimeError(f"CSV read failed for {cov_path.name}: {e}")
        #breakpoint()  # Breakpoint 2
        df_cov = df_cov.rename(columns={"ranking": "heuristic"})
        df_cov = df_cov[[
            "debate_id",
            "t_id",
            "explanation_type",
            "heuristic",
            "pct_args_of_graph"
        ]]
        json_files = list(WEIGHT_DIR.glob(f"{did}_*_{tid}.json"))
        if not json_files:
            raise FileNotFoundError(f"No JSON file for debate_id={did}, t_id={tid}")
        import json
        try:
            with open(json_files[0], 'r', encoding='utf-8') as f:
                debate_data = json.load(f)
        except Exception as e:
            raise RuntimeError(f"JSON load failed for {json_files[0].name}: {e}")
        target_node = debate_data.get('nodes', {}).get(tid, {})
        initial_weight_t = target_node.get('initial_weight', 0.0)
        final_weight_t = target_node.get('final_weight', 0.0)
        #breakpoint()  # Breakpoint 3
        df_w = pd.DataFrame({
            "debate_id": [int(did)],
            "t_id": [float(tid)],
            "initial_weight_t": [initial_weight_t],
            "final_weight_t": [final_weight_t]
        })
        #breakpoint()  # Breakpoint 4
        try:
            df = pd.merge(df_cov, df_w, on=["debate_id","t_id"])
        except Exception as e:
            raise RuntimeError(f"Merge failed for debate_id={did}, t_id={tid}: {e}")
        #breakpoint()  # Breakpoint 5
        df["weight_diff"] = (df.final_weight_t - df.initial_weight_t).abs()
        #breakpoint()  # Breakpoint 6
        records.append(df)
    except Exception as error:
        print(f"❌ ERROR: {error}")
        raise


if not records:
    raise RuntimeError("Aucune donnée fusionnée – vérifiez les chemins et patterns.")

full_df = pd.concat(records, ignore_index=True)

# 3) Calcul des corrélations pour chaque (type, heuristic)
results = []
groups = full_df.groupby(["explanation_type","heuristic"])
for (etype, heur), grp in groups:
    if len(grp) < 3:
        continue
    #breakpoint()  # Breakpoint 7: At start of correlation calculation loop
    x = grp.weight_diff
    y = grp.pct_args_of_graph
    r_p, p_p = pearsonr(x, y)
    r_s, p_s = spearmanr(x, y)
    results.append({
        "explanation_type": etype,
        "heuristic":        heur,
        "n_samples":        len(grp),
        "pearson_r":        r_p,
        "pearson_p":        p_p,
        "spearman_rho":     r_s,
        "spearman_p":       p_s
    })

pd.DataFrame(results).to_csv(OUT_FILE, index=False)
print(f"✅ Corrélations enregistrées dans {OUT_FILE}")

# 4) Tracés par combinaison
sns.set(style="whitegrid", font_scale=1.1)
for (etype, heur), grp in groups:
    if len(grp) < 3:
        continue

    plt.figure(figsize=(6,4))
    ax = sns.regplot(
        data=grp,
        x="weight_diff",
        y="pct_args_of_graph",
        scatter_kws={"alpha":0.5, "s":40},
        line_kws={"color":"C1"}
    )
    title = f"{etype.capitalize()} – {heur.replace('_',' ').capitalize()}"
    ax.set_title(title)
    ax.set_xlabel("Absolute value of weight difference")
    ax.set_ylabel("Argument coverage")

    out_png = PLOTS_DIR / f"scatter_{etype}_{heur}.png"
    plt.tight_layout()
    plt.savefig(out_png)
    plt.close()
    print(f"✅ Figure enregistrée dans {out_png}")
