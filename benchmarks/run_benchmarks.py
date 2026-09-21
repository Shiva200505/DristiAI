import argparse
import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.core.scanner import scan_code
from backend.utils.hardware import detect_hardware


def percentile(values: list[float], p: float) -> float:
    values = sorted(values)
    return values[min(len(values) - 1, round((len(values) - 1) * p))]


def run(iterations: int = 10) -> dict:
    source = (ROOT / "demo-repo/python/sql_injection.py").read_text(encoding="utf-8")
    samples = []
    for _ in range(iterations):
        started = time.perf_counter()
        scan_code(source, "sql_injection.py", "python", use_external_tools=False)
        samples.append((time.perf_counter() - started) * 1000)
    device = detect_hardware()
    return {"device": device.__dict__, "timestamp": datetime.now(timezone.utc).isoformat(), "component": "scanner", "iterations": iterations, "mean_ms": statistics.mean(samples), "p50_ms": percentile(samples, .50), "p95_ms": percentile(samples, .95), "p99_ms": percentile(samples, .99), "std_dev_ms": statistics.pstdev(samples), "backend_used": "CPU_FALLBACK", "notes": "Development machine measurement; not Snapdragon hardware"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--component", default="scanner", choices=["scanner", "all"])
    parser.add_argument("--iterations", type=int, default=10)
    args = parser.parse_args()
    result = run(args.iterations)
    output = ROOT / "benchmarks" / "results"
    output.mkdir(parents=True, exist_ok=True)
    target = output / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{result['device']['device_label']}.json"
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"Saved actual measurement to {target.relative_to(ROOT)}")
