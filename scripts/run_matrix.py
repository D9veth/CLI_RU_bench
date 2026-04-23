#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


def _discover_configs(path: Path) -> List[Path]:
    if path.is_file():
        if path.suffix.lower() in {".yaml", ".yml"}:
            return [path]
        return []
    if not path.is_dir():
        return []

    configs: List[Path] = []
    for p in sorted(path.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in {".yaml", ".yml"}:
            continue
        if p.name.startswith("_"):
            # Keeps placeholders/templates out of matrix runs by default.
            continue
        if "smoke" in p.stem.lower():
            # Smoke helpers are not part of the practical D0-D3 matrix.
            continue
        configs.append(p)
    return configs


def _snapshot_run_dirs(out_dir: Path) -> set[Path]:
    if not out_dir.exists() or not out_dir.is_dir():
        return set()
    return {p.resolve() for p in out_dir.iterdir() if p.is_dir()}


def _parse_run_dir_from_output(text: str) -> Optional[Path]:
    # bench run prints: "Done. run_id=...  artifacts=<run_dir>"
    m = re.search(r"artifacts=(.+)$", text.strip(), flags=re.MULTILINE)
    if not m:
        return None
    return Path(m.group(1).strip())


def _detect_new_run_dir(out_dir: Path, before: set[Path], output_text: str) -> Optional[Path]:
    after = _snapshot_run_dirs(out_dir)
    new_dirs = sorted(after - before, key=lambda p: p.name)
    if new_dirs:
        return new_dirs[-1]

    parsed = _parse_run_dir_from_output(output_text)
    if parsed and parsed.exists() and parsed.is_dir():
        return parsed.resolve()
    return None


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _format_float(x: Any, ndigits: int = 4) -> str:
    if x is None:
        return "-"
    try:
        return f"{float(x):.{ndigits}f}"
    except Exception:
        return "-"


def _pick_top_status(status_counts: Dict[str, Any]) -> str:
    if not isinstance(status_counts, dict):
        return "-"
    items: List[tuple[str, int]] = []
    for k, v in status_counts.items():
        try:
            n = int(v)
        except Exception:
            continue
        if k == "ok":
            continue
        items.append((str(k), n))
    if not items:
        return "-"
    items.sort(key=lambda kv: (-kv[1], kv[0]))
    k, v = items[0]
    return f"{k}:{v}"


def _short_error(stderr: str, stdout: str, limit: int = 120) -> str:
    text = (stderr or "").strip() or (stdout or "").strip()
    if not text:
        return "-"
    line = text.splitlines()[-1].strip()
    if len(line) <= limit:
        return line
    return line[: limit - 3] + "..."


def _render_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def fmt_row(vals: Sequence[str]) -> str:
        return " | ".join(vals[i].ljust(widths[i]) for i in range(len(vals)))

    sep = "-+-".join("-" * w for w in widths)
    out = [fmt_row(headers), sep]
    for row in rows:
        out.append(fmt_row(row))
    return "\n".join(out)


def _build_cmd(
    config_path: Path,
    *,
    dataset: Path,
    split: str,
    dataset_version: Optional[str],
    repeats: Optional[int],
    out_dir: Path,
    skip_preflight: bool,
    base_url: Optional[str],
    endpoint_url: Optional[str],
    model: Optional[str],
    api_key_env: Optional[str],
) -> List[str]:
    cmd = [
        sys.executable,
        "-m",
        "bench.cli",
        "run",
        "--config",
        str(config_path),
        "--dataset",
        str(dataset),
        "--split",
        split,
        "--out",
        str(out_dir),
    ]
    if dataset_version:
        cmd.extend(["--dataset-version", dataset_version])
    if repeats is not None:
        cmd.extend(["--repeats", str(repeats)])
    if skip_preflight:
        cmd.append("--skip-preflight")
    if base_url:
        cmd.extend(["--base-url", base_url])
    if endpoint_url:
        cmd.extend(["--endpoint-url", endpoint_url])
    if model:
        cmd.extend(["--model", model])
    if api_key_env:
        cmd.extend(["--api-key-env", api_key_env])
    return cmd


def main() -> int:
    ap = argparse.ArgumentParser(description="Run a matrix of configs with bench run and print success/error table.")
    ap.add_argument("--configs-dir", required=True, help="Directory (or file) with YAML configs.")
    ap.add_argument("--dataset", required=True, help="Dataset path.")
    ap.add_argument("--split", default="dev", choices=["dev", "test"], help="Dataset split to record in artifacts.")
    ap.add_argument("--dataset-version", default=None, help="Dataset version/tag to record in artifacts.")
    ap.add_argument("--repeats", type=int, default=None, help="Override repeats for all runs.")
    ap.add_argument("--out", required=True, help="Output directory for run artifacts.")

    # Optional overrides / ops knobs.
    ap.add_argument("--skip-preflight", action="store_true", help="Pass --skip-preflight to each bench run.")
    ap.add_argument("--base-url", default=None, help="Override target.base_url for all runs.")
    ap.add_argument("--endpoint-url", default=None, help="Override target.endpoint_url for all runs.")
    ap.add_argument("--model", default=None, help="Override target.model for all runs.")
    ap.add_argument("--api-key-env", default=None, help="Override target.api_key_env for all runs.")
    ap.add_argument(
        "--report-json",
        default=None,
        help="Optional path to write detailed JSON report (defaults to <out>/run_matrix_report.json).",
    )
    args = ap.parse_args()

    configs_root = Path(args.configs_dir)
    dataset = Path(args.dataset)
    out_dir = Path(args.out)
    if args.repeats is not None and args.repeats < 1:
        print("--repeats must be >= 1", file=sys.stderr)
        return 2
    if not dataset.exists():
        print(f"Dataset not found: {dataset}", file=sys.stderr)
        return 2

    configs = _discover_configs(configs_root)
    if not configs:
        print(f"No YAML configs found in: {configs_root}", file=sys.stderr)
        return 2

    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Configs discovered: {len(configs)}")
    print(f"Dataset: {dataset}")
    print(f"Out: {out_dir}")
    print()

    rows: List[Dict[str, Any]] = []
    for i, cfg in enumerate(configs, start=1):
        print(f"[{i}/{len(configs)}] {cfg}")
        before = _snapshot_run_dirs(out_dir)
        cmd = _build_cmd(
            cfg,
            dataset=dataset,
            split=args.split,
            dataset_version=args.dataset_version,
            repeats=args.repeats,
            out_dir=out_dir,
            skip_preflight=bool(args.skip_preflight),
            base_url=args.base_url,
            endpoint_url=args.endpoint_url,
            model=args.model,
            api_key_env=args.api_key_env,
        )
        t0 = time.perf_counter()
        proc = subprocess.run(cmd, capture_output=True, text=True, env=os.environ.copy())
        elapsed_s = float(time.perf_counter() - t0)
        output_text = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
        run_dir = _detect_new_run_dir(out_dir, before, output_text)

        summary: Dict[str, Any] = {}
        if run_dir is not None:
            summary_p = run_dir / "summary.json"
            if summary_p.exists():
                try:
                    summary = _load_json(summary_p)
                except Exception:
                    summary = {}

        status_counts = summary.get("status_counts") if isinstance(summary.get("status_counts"), dict) else {}
        row = {
            "config": str(cfg),
            "cli_rc": int(proc.returncode),
            "elapsed_s": elapsed_s,
            "run_dir": str(run_dir) if run_dir else "",
            "run_id": run_dir.name if run_dir else "",
            "n_attempts": summary.get("n_attempts"),
            "n_ok_attempts": summary.get("n_ok_attempts"),
            "n_failed_attempts": summary.get("n_failed_attempts"),
            "failure_rate": summary.get("failure_rate"),
            "parse_error_rate": summary.get("parse_error_rate"),
            "status_counts": status_counts,
            "top_status": _pick_top_status(status_counts),
            "error": _short_error(proc.stderr or "", proc.stdout or "") if proc.returncode != 0 else "",
        }
        rows.append(row)

    headers = [
        "config",
        "cli_rc",
        "run_id",
        "n_attempts",
        "n_failed",
        "failure_rate",
        "parse_error_rate",
        "top_status",
        "error",
    ]
    printable_rows: List[List[str]] = []
    for r in rows:
        printable_rows.append(
            [
                Path(r["config"]).name,
                str(r["cli_rc"]),
                str(r["run_id"] or "-"),
                str(r["n_attempts"] if r["n_attempts"] is not None else "-"),
                str(r["n_failed_attempts"] if r["n_failed_attempts"] is not None else "-"),
                _format_float(r["failure_rate"]),
                _format_float(r["parse_error_rate"]),
                str(r["top_status"] or "-"),
                str(r["error"] or "-"),
            ]
        )

    print()
    print(_render_table(headers, printable_rows))
    print()

    n_total = len(rows)
    n_cli_ok = sum(1 for r in rows if r["cli_rc"] == 0)
    n_cli_fail = n_total - n_cli_ok
    n_with_summary = sum(1 for r in rows if r["n_attempts"] is not None)
    print(f"Totals: configs={n_total}, cli_ok={n_cli_ok}, cli_failed={n_cli_fail}, with_summary={n_with_summary}")

    report_path = Path(args.report_json) if args.report_json else (out_dir / "run_matrix_report.json")
    report = {
        "configs_dir": str(configs_root),
        "dataset": str(dataset),
        "split": args.split,
        "dataset_version": args.dataset_version,
        "repeats": args.repeats,
        "out": str(out_dir),
        "rows": rows,
        "totals": {
            "configs": n_total,
            "cli_ok": n_cli_ok,
            "cli_failed": n_cli_fail,
            "with_summary": n_with_summary,
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Report JSON: {report_path}")
    return 0 if n_cli_fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
