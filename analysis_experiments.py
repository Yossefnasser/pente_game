import time
from typing import List, Dict, Any
import json
import csv
import os

from game_logic import PenteGame, WHITE, BLACK
from ai_engine import PenteAI


def make_position_center() -> PenteGame:
    g = PenteGame()
    g.make_move(9, 9, WHITE)
    g.make_move(9, 10, BLACK)
    g.make_move(10, 9, WHITE)
    g.make_move(8, 9, BLACK)
    return g


def make_position_open_three() -> PenteGame:
    g = PenteGame()
    g.make_move(5, 5, WHITE)
    g.make_move(9, 9, BLACK)
    g.make_move(5, 6, WHITE)
    g.make_move(6, 6, BLACK)
    g.make_move(5, 7, WHITE)
    return g


POSITIONS = {
    "center": make_position_center,
    "open_three": make_position_open_three,
}

# Simpler, focused comparison set
# Focused quick comparison set (keeps runtime low)
MODES = [
    ("minimax_h1", 2),
    ("alphabeta_h1", 2),
    ("minimax_h2", 2),
    ("alphabeta_h2", 2),
]


def run_one(ai_mode: str, depth: int, game: PenteGame, player_color: int) -> Dict[str, Any]:
    ai = PenteAI(mode=ai_mode, player_color=player_color, depth=depth)
    start = time.time()
    move = ai.get_best_move(game)
    elapsed = time.time() - start
    return {
        "mode": ai_mode,
        "depth": depth,
        "player": "BLACK" if player_color == BLACK else "WHITE",
        "nodes": ai.nodes_explored,
        "pruned": ai.pruned_branches,
        "time_s": round(elapsed, 4),
        "move": move,
    }


def save_results(results: List[Dict[str, Any]], tag: str):
    ts = time.strftime("%Y%m%d-%H%M%S")
    os.makedirs("results", exist_ok=True)
    json_path = os.path.join("results", f"{tag}-{ts}.json")
    csv_path = os.path.join("results", f"{tag}-{ts}.csv")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    if results:
        keys = [
            "position",
            "player",
            "mode",
            "depth",
            "nodes",
            "pruned",
            "time_s",
            "move",
        ]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for r in results:
                row = {k: r.get(k) for k in keys}
                w.writerow(row)
    print(f"Saved results to {json_path} and {csv_path}")


def summarize_simple(results: List[Dict[str, Any]]):
    print("\n=== Summary ===")
    for r in results:
        print(
            f"pos={r['position']:<12} ply={r['player']:<5} {r['mode']:<12} d={r['depth']} | nodes={r['nodes']:<7} pruned={r['pruned']:<5} time={r['time_s']:<6}s move={r['move']}"
        )

    # Compact alpha-beta vs minimax delta
    print("\n--- Compact Comparisons (same heuristic/depth) ---")
    index = {}
    for r in results:
        key = (r['position'], r['player'], r['depth'], r['mode'].split('_')[-1])
        index.setdefault(key, []).append(r)
    for key, arr in index.items():
        ab = next((x for x in arr if x['mode'].startswith('alphabeta')), None)
        mm = next((x for x in arr if x['mode'].startswith('minimax')), None)
        if ab and mm:
            pos, ply, d, h = key
            dn = mm['nodes'] - ab['nodes']
            dt = round(mm['time_s'] - ab['time_s'], 4)
            print(
                f"{pos}/{ply}/d{d}/{h}: nodes Δ={dn}, time Δ={dt}s | mm={mm['nodes']}nodes {mm['time_s']}s vs ab={ab['nodes']}nodes {ab['time_s']}s"
            )


def run_experiments(tag: str = "default") -> List[Dict[str, Any]]:
    all_results: List[Dict[str, Any]] = []
    for pos_name, pos_fn in POSITIONS.items():
        base_game = pos_fn()
        for player in (BLACK, WHITE):
            for mode, depth in MODES:
                # Fresh copy
                g = PenteGame()
                for r in range(len(base_game.grid)):
                    for c in range(len(base_game.grid[r])):
                        cell = base_game.grid[r][c]
                        if cell != 0:
                            g.make_move(r, c, cell)
                res = run_one(mode, depth, g, player)
                res["position"] = pos_name
                all_results.append(res)
    save_results(all_results, tag)
    summarize_simple(all_results)
    return all_results


def aggregate(results: List[Dict[str, Any]]):
    """Aggregate by (position, player, heuristic) comparing minimax vs alphabeta sums."""
    # buckets: {(pos, player, h): {mm_sum_time, mm_sum_nodes, ab_sum_time, ab_sum_nodes}}
    buckets: Dict[tuple, Dict[str, float]] = {}
    for r in results:
        h = r['mode'].split('_')[-1]
        key = (r['position'], r['player'], h)
        b = buckets.setdefault(key, {
            'mm_time': 0.0, 'mm_nodes': 0,
            'ab_time': 0.0, 'ab_nodes': 0,
            'count_mm': 0, 'count_ab': 0
        })
        if r['mode'].startswith('minimax'):
            b['mm_time'] += r['time_s']
            b['mm_nodes'] += r['nodes']
            b['count_mm'] += 1
        else:
            b['ab_time'] += r['time_s']
            b['ab_nodes'] += r['nodes']
            b['count_ab'] += 1
    # Produce list rows
    rows = []
    for (pos, ply, h), b in buckets.items():
        rows.append({
            'position': pos,
            'player': ply,
            'heuristic': h,
            'mm_time_sum': round(b['mm_time'], 4),
            'ab_time_sum': round(b['ab_time'], 4),
            'mm_nodes_sum': b['mm_nodes'],
            'ab_nodes_sum': b['ab_nodes'],
            'time_delta': round(b['mm_time'] - b['ab_time'], 4),
            'nodes_delta': b['mm_nodes'] - b['ab_nodes'],
        })
    return rows


def run_aggregated(tag: str = "default") -> List[Dict[str, Any]]:
    res = run_experiments(tag)
    rows = aggregate(res)
    # Save a compact aggregated CSV for GUI comparison
    ts = time.strftime("%Y%m%d-%H%M%S")
    os.makedirs("results", exist_ok=True)
    agg_csv = os.path.join("results", f"{tag}-aggregated-{ts}.csv")
    keys = ['position', 'player', 'heuristic', 'mm_time_sum', 'ab_time_sum', 'mm_nodes_sum', 'ab_nodes_sum', 'time_delta', 'nodes_delta']
    with open(agg_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for row in rows:
            w.writerow(row)
    print(f"Saved aggregated comparison to {agg_csv}")
    return rows


def main():
    run_experiments("simple")


if __name__ == "__main__":
    main()
