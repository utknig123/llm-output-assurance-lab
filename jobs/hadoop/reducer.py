"""Hadoop Streaming reducer. Sums the third column for each key pair."""
import sys


def main() -> None:
    current = None
    total = 0
    for line in sys.stdin:
        parts = line.rstrip("\n").split("\t")
        if len(parts) != 3:
            continue
        kind, name, count = parts
        key = (kind, name)
        count_i = int(count)
        if current is None:
            current = key
        if key != current:
            print(f"{current[0]}\t{current[1]}\t{total}")
            current = key
            total = 0
        total += count_i
    if current is not None:
        print(f"{current[0]}\t{current[1]}\t{total}")


if __name__ == "__main__":
    main()
