"""
Run logging + diagnostics for the Wiz Health Assessment.

Why this exists
---------------
Small tenants "just work", but large accounts run into slow queries, timeouts,
rate limits, and the 10k graphSearch cap. When that happens the deck can quietly
come out with 0s in a few cells and the operator has no idea which query failed
(stdout has already scrolled away). This module gives every run:

* A timestamped **log file** under `output/logs/` that tees everything printed to
  the console, so a customer can send one file back for diagnosis.
* A structured **per-query record** (duration, attempts, HTTP codes seen, final
  outcome, row count) collected as the run proceeds.
* A **RUN DIAGNOSTICS** summary at the end that flags exactly which queries came
  back empty / hit a permission wall / hit the 10k cap / ran slow, plus a JSON
  sidecar next to the log for programmatic triage.

Dependency-free (stdlib only) and safe: logging must never be the thing that
crashes a run, so every method swallows its own I/O errors.
"""

import json
import os
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

# Outcome vocabulary shared with run_gql. Kept small and stable so the JSON
# sidecar is easy to grep/aggregate across many customer runs.
OK = "ok"                 # data returned, looks populated
EMPTY = "empty"           # top-level data null / {} after retries (suspect metric)
PERMISSION = "permission" # service account lacks scope (often benign, e.g. audit logs)
FAILED = "failed"         # exhausted retries on HTTP/network error
CAP = "cap"               # totalCount hit the 10k graphSearch ceiling (undercount)

# Queries slower than this (seconds) are highlighted in the summary as the likely
# scaling bottleneck on a large tenant.
SLOW_THRESHOLD_S = 30.0

_LEVELS = {"DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40}


class RunLogger:
    def __init__(self, log_path=None, console=True, min_level="INFO"):
        self.console = console
        self.min_level = _LEVELS.get(min_level, 20)
        self.events = []      # structured per-query records
        self.warnings = []    # human-readable warning strings
        self.errors = []      # human-readable error strings
        self.started = time.time()
        self.log_path = None
        self._fh = None
        if log_path:
            try:
                p = Path(log_path)
                p.parent.mkdir(parents=True, exist_ok=True)
                self._fh = open(p, "a", encoding="utf-8", errors="replace")
                self.log_path = str(p.resolve())
            except Exception:
                # Never let log-file setup abort a run; degrade to console only.
                self._fh = None
                self.log_path = None

    # -- core -----------------------------------------------------------------
    def log(self, message, level="INFO"):
        lvl = _LEVELS.get(level, 20)
        if lvl >= _LEVELS["WARN"]:
            (self.errors if lvl >= _LEVELS["ERROR"] else self.warnings).append(message)
        if self.console and lvl >= self.min_level:
            print(message)
        if self._fh is not None:
            try:
                ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                self._fh.write(f"{ts} {level:<5} {message}\n")
                self._fh.flush()
            except Exception:
                pass

    def info(self, m):
        self.log(m, "INFO")

    def warn(self, m):
        self.log(m, "WARN")

    def error(self, m):
        self.log(m, "ERROR")

    def exception(self, prefix, exc):
        """Record an exception with its traceback to the log file for triage."""
        self.error(f"{prefix}: {type(exc).__name__}: {exc}")
        if self._fh is not None:
            try:
                self._fh.write(traceback.format_exc() + "\n")
                self._fh.flush()
            except Exception:
                pass

    # -- per-query bookkeeping ------------------------------------------------
    def record_query(self, name, status, elapsed, attempts=1, http_codes=None,
                     total=None, note=None):
        """Record the outcome of one GraphQL query for the diagnostics summary."""
        rec = {
            "name": name,
            "status": status,
            "elapsed_s": round(elapsed, 1),
            "attempts": attempts,
            "http_codes": http_codes or [],
            "total": total,
            "note": note,
        }
        self.events.append(rec)
        # Surface anything that isn't a clean OK as a warning line in the log so
        # it's visible in-stream, not just in the end summary.
        if status == FAILED:
            self.error(f"    [query FAILED] {name}: {note or 'exhausted retries'} "
                       f"({elapsed:.0f}s, {attempts} attempts)")
        elif status == EMPTY:
            self.warn(f"    [query EMPTY] {name}: returned no data "
                      f"({elapsed:.0f}s, {attempts} attempts) — dependent metrics may show 0")
        elif status == PERMISSION:
            self.warn(f"    [query PERMISSION] {name}: {note or 'access denied'} — skipped")
        elif elapsed >= SLOW_THRESHOLD_S:
            self.warn(f"    [query SLOW] {name}: {elapsed:.0f}s "
                      f"(raise WIZ_QUERY_TIMEOUT if this times out on retries)")

    def cap_hit(self, detail):
        """Record a 10k graphSearch cap (totalCount is a floor / undercount)."""
        self.warnings.append(f"CAP: {detail}")
        self.events.append({"name": detail, "status": CAP, "elapsed_s": None,
                            "attempts": None, "http_codes": [], "total": None,
                            "note": "totalCount hit 10,000 ceiling"})

    # -- summary --------------------------------------------------------------
    def summary(self):
        """Return the human-readable RUN DIAGNOSTICS block as a string."""
        elapsed = time.time() - self.started
        failed = [e for e in self.events if e["status"] == FAILED]
        empty = [e for e in self.events if e["status"] == EMPTY]
        perm = [e for e in self.events if e["status"] == PERMISSION]
        capped = [e for e in self.events if e["status"] == CAP]
        slow = [e for e in self.events
                if e.get("elapsed_s") and e["elapsed_s"] >= SLOW_THRESHOLD_S]
        ok = [e for e in self.events if e["status"] == OK]

        lines = []
        lines.append("=======================================================")
        lines.append("                  RUN DIAGNOSTICS                      ")
        lines.append("=======================================================")
        lines.append(f" Queries: {len(self.events)} recorded  "
                     f"(OK {len(ok)}, empty {len(empty)}, failed {len(failed)}, "
                     f"permission {len(perm)}, capped {len(capped)})")
        lines.append(f" Elapsed: {elapsed:.0f}s")

        if failed:
            lines.append("")
            lines.append(" [!] FAILED queries (metrics below will be blank/0):")
            for e in failed:
                lines.append(f"     - {e['name']}  ({e['elapsed_s']}s, "
                             f"{e['attempts']} attempts, HTTP {e['http_codes'] or 'n/a'})")
            lines.append("     -> Re-run; if it persists on a large tenant, raise the")
            lines.append("        per-query timeout:  export WIZ_QUERY_TIMEOUT=300")
        if empty:
            lines.append("")
            lines.append(" [!] EMPTY queries (returned no data — verify these cells):")
            for e in empty:
                lines.append(f"     - {e['name']}  ({e['elapsed_s']}s)")
        if capped:
            lines.append("")
            lines.append(" [!] 10k CAP hit (counts are a FLOOR / undercount):")
            for e in capped:
                lines.append(f"     - {e['name']}")
            lines.append("     -> Sub-partition that type (by provider/subscription) for an exact count.")
        if perm:
            lines.append("")
            lines.append(" [i] Permission-restricted (skipped; often expected):")
            for e in perm:
                lines.append(f"     - {e['name']}")
        if slow:
            lines.append("")
            lines.append(f" [i] Slow queries (>= {int(SLOW_THRESHOLD_S)}s) — scaling bottlenecks:")
            for e in sorted(slow, key=lambda x: -x["elapsed_s"]):
                lines.append(f"     - {e['name']}: {e['elapsed_s']}s")

        if not (failed or empty or capped):
            lines.append("")
            lines.append(" [OK] All queries returned data. No blanks expected from API failures.")

        if self.log_path:
            lines.append("")
            lines.append(f" Full log:   {self.log_path}")
            json_path = self._json_path()
            if json_path:
                lines.append(f" Diagnostics JSON: {json_path}")
            lines.append(" Share the log file above with your Wiz TAM if numbers look off.")
        lines.append("=======================================================")
        return "\n".join(lines)

    def _json_path(self):
        if not self.log_path:
            return None
        return str(Path(self.log_path).with_suffix(".diagnostics.json"))

    def write_summary(self):
        """Print the diagnostics summary and write the JSON sidecar."""
        block = self.summary()
        # Print directly (bypass level filtering) so the summary always shows.
        print("\n" + block + "\n")
        if self._fh is not None:
            try:
                self._fh.write("\n" + block + "\n")
                self._fh.flush()
            except Exception:
                pass
        json_path = self._json_path()
        if json_path:
            try:
                payload = {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "elapsed_s": round(time.time() - self.started, 1),
                    "queries": self.events,
                    "warnings": self.warnings,
                    "errors": self.errors,
                }
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2)
            except Exception:
                pass

    def close(self):
        if self._fh is not None:
            try:
                self._fh.close()
            except Exception:
                pass
            self._fh = None


# -- module-level singleton --------------------------------------------------
# run_gql is a free function called ~19 times; a singleton keeps wiring minimal.
_LOGGER = None


def init_logger(log_path=None, console=True, min_level="INFO"):
    global _LOGGER
    _LOGGER = RunLogger(log_path=log_path, console=console, min_level=min_level)
    return _LOGGER


def get_logger():
    """Return the active logger, creating a console-only one if none was set up."""
    global _LOGGER
    if _LOGGER is None:
        _LOGGER = RunLogger(log_path=None, console=True)
    return _LOGGER


def default_log_path(output_dir=None):
    """output/logs/wiz_health_run_<UTC timestamp>.log"""
    base = Path(output_dir) if output_dir else (Path.cwd() / "output")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return str(base / "logs" / f"wiz_health_run_{ts}.log")
