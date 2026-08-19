import json
import os
import sys
from typing import Iterable, List

# Normalize FORCE_COLOR before importing `colored`.
# The `colored` library expects FORCE_COLOR to be an int ("0".."3");
# common shells export it as "true"/"false", which crashes int() parsing.
# Only translate non-numeric truthy/falsy words; leave unset values alone
# so normal TTY detection still works.
_fc = os.environ.get("FORCE_COLOR", "")
if _fc:
    _fc_low = _fc.strip().lower()
    if _fc_low in ("true", "yes", "on"):
        os.environ["FORCE_COLOR"] = "1"
    elif _fc_low in ("false", "no", "off"):
        os.environ["FORCE_COLOR"] = "0"
    # else: leave numeric values ("0".."3") untouched

from colored import fg, attr, bg
from .models import ModelResult


# Global config for output
class OutputConfig:
    no_json = False
    output_file = None


def print_separator() -> None:
    print(f"{fg(240)}--------------------------------------------------------------------------------{attr('reset')}", file=sys.stderr, flush=True)


def print_start(run_label: str, model_display: str) -> None:
    print(f"{fg('blue')}[START]  {attr('reset')} {run_label} {fg('cyan')}{model_display}{attr('reset')}", file=sys.stderr, flush=True)


def print_request(run_label: str, model_display: str, url: str) -> None:
    print(f"{fg('blue')}[REQUEST]{attr('reset')} {run_label} {fg('cyan')}{model_display}{attr('reset')} {fg('magenta')} POST {attr('reset')} {url}", file=sys.stderr, flush=True)


def print_end(run_label: str, model_display: str, ok: bool, latency_ms: int = None, reason: str = "") -> None:
    status_color = f"{bg('green')}{fg('white')}" if ok else f"{bg('red')}{fg('white')}"
    status_text = " PASS " if ok else " FAIL "
    end_color = fg('green' if ok else 'red')
    latency_suffix = f" latency={latency_ms}ms" if latency_ms is not None else ""
    reason_suffix = f" reason={reason}" if reason else ""

    print(f"{end_color}[END]    {attr('reset')} {run_label} {fg('cyan')}{model_display}{attr('reset')} {status_color}{status_text}{attr('reset')}{latency_suffix}{reason_suffix}", file=sys.stderr, flush=True)


def print_verbose_response(status_code: int, response: dict) -> None:
    print(f"  status_code={status_code} response_json={json.dumps(response, separators=(',', ':'))}", file=sys.stderr, flush=True)


def print_models_header(models: List[str]) -> None:
    print("", file=sys.stderr, flush=True)
    print(f"{fg('magenta')}========== MODELS =========={attr('reset')}", file=sys.stderr, flush=True)
    print(f"count={len(models)}", file=sys.stderr, flush=True)

    for i, m in enumerate(models, 1):
        print(f"{i:02d}. {fg('cyan')}{m}{attr('reset')}", file=sys.stderr, flush=True)

    print(f"{fg('magenta')}============================{attr('reset')}", file=sys.stderr, flush=True)
    print("", file=sys.stderr, flush=True)


def print_summary(results: List[ModelResult], total_ms: int) -> None:
    passed = sum(1 for r in results if r.ok)
    failed = len(results) - passed
    latencies = [r.latency_ms for r in results if r.latency_ms is not None]
    avg_latency = int(sum(latencies) / len(latencies)) if latencies else 0

    print("", file=sys.stderr, flush=True)
    print(f"{fg('magenta')}======== COMPLETED ========={attr('reset')}", file=sys.stderr, flush=True)
    print(f"total={len(results)} passed={fg('green')}{passed}{attr('reset')} failed={fg('red')}{failed}{attr('reset')}", file=sys.stderr, flush=True)
    print(f"total_time_ms={total_ms} avg_latency_ms={avg_latency}", file=sys.stderr, flush=True)
    print(f"{fg('magenta')}============================{attr('reset')}", file=sys.stderr, flush=True)


def render_results(results: Iterable[ModelResult]) -> str:
    rows = []

    for result in results:
        status = "PASS" if result.ok else "FAIL"
        latency = f"{result.latency_ms}ms" if result.latency_ms is not None else "-"
        error = result.error or "-"
        rows.append(
            {
                "model": result.model,
                "status": status,
                "latency": latency,
                "error": error,
                "status_code": result.status_code,
                "response_json": result.response_json,
                "response_text": result.response_text,
            }
        )

    return json.dumps({"results": rows}, indent=2)


def output_results(json_str: str) -> None:
    """Output results to stdout or file."""
    if OutputConfig.no_json and not OutputConfig.output_file:
        return
    
    if OutputConfig.output_file:
        with open(OutputConfig.output_file, "w") as f:
            f.write(json_str)
        print(f"\n{fg('green')}✓ JSON saved to: {OutputConfig.output_file}{attr('reset')}", file=sys.stderr, flush=True)
    else:
        print(json_str)
