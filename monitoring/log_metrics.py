import json
import re
import sys

def p95(values):
    """Calcule le 95ème centile d'une liste de valeurs."""
    values = sorted(v for v in values if isinstance(v, (int, float)))
    if not values:
        return 0
    idx = int(0.95 * (len(values) - 1))
    return values[idx]

def main(path_in, path_out):
    logs = []

    try:
        with open(path_in, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                # On nettoie les codes couleurs ANSI (au cas où)
                line = re.sub(r'\x1b\[[0-9;]*m', '', line)
                
                # On ignore strictment tout ce qui ne commence pas par '{'
                if not line.startswith("{"):
                    continue
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"Erreur: Le fichier {path_in} n'existe pas.")
        sys.exit(1)

    valid_logs = [x for x in logs if isinstance(x, dict)]
    
    status_codes = [x.get("status") for x in valid_logs]
    latencies = [x.get("latency_ms") for x in valid_logs]
    queries = [x.get("query", "") for x in valid_logs]

    count_5xx = sum(1 for s in status_codes if isinstance(s, int) and s >= 500)
    p95_lat = p95(latencies)

    traversal_hits = sum(1 for q in queries if q and re.search(r"\.\./", q))
    cmd_hits = sum(1 for q in queries if q and "cmd=" in q)

    report = {
        "n_logs": len(valid_logs),
        "count_5xx": count_5xx,
        "p95_latency_ms": p95_lat,
        "patterns": {
            "path_traversal_hits": traversal_hits,
            "cmd_param_hits": cmd_hits
        }
    }

    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python monitoring/log_metrics.py <in.jsonl> <out.json>")
        sys.exit(2)
    
    main(sys.argv[1], sys.argv[2])