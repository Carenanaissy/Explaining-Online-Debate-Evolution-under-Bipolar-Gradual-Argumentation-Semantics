import os
import json
from collections import defaultdict

INPUT_FOLDER = 'kialo_debates_final_weights_added'
OUTPUT_FOLDER = 'sub-debates'

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def get_targets(debate_id, edges):
    root_id = f"{debate_id}.0"
    neutral_predecessors = [src for src, edge in edges.items()
                            if edge.get('successor_id') == root_id and edge.get('relation') == 0.0]
    if not neutral_predecessors:
        return [root_id]
    return neutral_predecessors

def get_connected_arguments(target_id, edges):
    """
    Find all arguments connected to the target by any path (regardless of length).
    Uses BFS to traverse the graph backwards from the target.
    """
    connected = set([target_id])
    queue = [target_id]  # Queue for BFS
    visited = set([target_id])
    
    while queue:
        current = queue.pop(0)  # BFS: take from front
        
        # Find all arguments that point to the current argument
        for src, edge in edges.items():
            successor_id = edge.get('successor_id')
            relation = edge.get('relation', 0.0)
            
            # If this edge points to current and has a non-zero relation
            if successor_id == current and relation != 0.0:
                if src not in visited:
                    visited.add(src)
                    connected.add(src)
                    queue.append(src)  # Continue searching from this argument
    
    return connected

def main():
    for fname in os.listdir(INPUT_FOLDER):
        if not fname.endswith('.json'):
            continue
        debate_id = fname.rsplit('.', 1)[0]
        fpath = os.path.join(INPUT_FOLDER, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading {fpath}: {e}")
            continue
        nodes = data.get('nodes', {})
        edges = data.get('edges', {})
        targets = get_targets(debate_id, edges)
        n_targets = len(targets)
        for idx, target_id in enumerate(targets, 1):
            connected = get_connected_arguments(target_id, edges)
            sub_nodes = {nid: nodes[nid] for nid in connected if nid in nodes}
            sub_edges = {src: edge for src, edge in edges.items()
                         if src in connected and edge.get('successor_id') in connected}
            outname = f"{debate_id}_T{idx}of{n_targets}_{target_id}.json"
            outpath = os.path.join(OUTPUT_FOLDER, outname)
            with open(outpath, 'w', encoding='utf-8') as outf:
                json.dump({'nodes': sub_nodes, 'edges': sub_edges}, outf, indent=2, ensure_ascii=False)
            print(f"Wrote {outpath}")

if __name__ == '__main__':
    main()
