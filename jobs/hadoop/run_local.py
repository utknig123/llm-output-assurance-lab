"""Run the Streaming mapper and reducer locally, the same contract Hadoop uses.

On a cluster:
  hadoop jar hadoop-streaming.jar -input logs -output out \\
    -mapper "python mapper.py" -reducer "python reducer.py"
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SAMPLE = ROOT / "sample_logs.jsonl"


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else SAMPLE
    mapper = subprocess.Popen(
        [sys.executable, str(ROOT / "mapper.py")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    mapped, _ = mapper.communicate(src.read_text(encoding="utf-8"))
    if mapper.returncode != 0:
        raise SystemExit(mapper.returncode)
    ordered = "".join(sorted(mapped.splitlines(keepends=True)))
    reducer = subprocess.Popen(
        [sys.executable, str(ROOT / "reducer.py")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    reduced, _ = reducer.communicate(ordered)
    if reducer.returncode != 0:
        raise SystemExit(reducer.returncode)
    out = ROOT / "tally.tsv"
    out.write_text(reduced, encoding="utf-8")
    sys.stdout.write(reduced)


if __name__ == "__main__":
    main()
