"""Hadoop Streaming mapper for assurance decision logs.

Input: one JSON object per line
  {"decision": "blocked", "categories": ["privacy"], "score": 60}

Output: tab-separated
  decision <decision> 1
  category <category> 1
  score_sum <score> 1
"""
import json
import sys


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        decision = str(row.get("decision") or "unknown")
        print(f"decision\t{decision}\t1")
        for category in row.get("categories") or []:
            print(f"category\t{category}\t1")
        if row.get("score") is not None:
            print(f"score_sum\t{int(row['score'])}\t1")


if __name__ == "__main__":
    main()
