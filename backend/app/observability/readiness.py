"""
app/observability/readiness.py — Phase 11 Readiness Checker

Strictly separated from health.py (per approved spec):
  /live   → process alive? (no I/O, always fast)
  /ready  → can the process serve requests? (minimal fast checks)
  /health → full diagnostic (may be slow)

ReadinessChecker performs only fast, critical checks:
  1. Configuration validity
  2. Required filesystem directories

It does NOT check database connectivity (that belongs to /health).
This keeps /ready ultra-fast for Kubernetes readiness probes.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict

from app.core.config import Config


class ReadinessStatus(str, Enum):
    READY     = "ready"
    NOT_READY = "not_ready"


@dataclass
class ReadinessReport:
    status:  ReadinessStatus
    checks:  Dict[str, bool] = field(default_factory=dict)
    details: Dict[str, str]  = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "status":      self.status.value,
            "service":     Config.APP_NAME,
            "version":     Config.VERSION,
            "environment": Config.ENV,
            "checks":      self.checks,
            "details":     self.details,
        }


class ReadinessChecker:
    """
    Lightweight readiness probe. All checks must be fast (< 100ms total).

    Checks performed:
      - config       : Config.validate() returns True
      - upload_dir   : directory exists and is writable
      - results_dir  : directory exists and is writable
      - storage_root : storage root exists and is writable
    """

    def check(self) -> ReadinessReport:
        checks:  Dict[str, bool] = {}
        details: Dict[str, str]  = {}

        # 1. Config
        try:
            Config.validate()
            checks["config"]  = True
            details["config"] = "OK"
        except Exception as exc:
            checks["config"]  = False
            details["config"] = str(exc)

        # 2. Filesystem directories
        dirs = {
            "upload_dir":   Config.UPLOAD_DIR,
            "results_dir":  Config.RESULTS_DIR,
            "storage_root": Config.STORAGE_ROOT,
        }
        for name, directory in dirs.items():
            try:
                os.makedirs(directory, exist_ok=True)
                probe = os.path.join(directory, ".readiness_probe")
                with open(probe, "w") as f:
                    f.write("ready")
                os.remove(probe)
                checks[name]  = True
                details[name] = f"Writable: {directory}"
            except Exception as exc:
                checks[name]  = False
                details[name] = f"Error accessing {directory}: {exc}"

        all_ready = all(checks.values())
        return ReadinessReport(
            status  = ReadinessStatus.READY if all_ready else ReadinessStatus.NOT_READY,
            checks  = checks,
            details = details,
        )


def liveness_response() -> dict:
    """
    /live response — no I/O, just confirms the process is running.
    Must complete in < 1ms.
    """
    return {
        "status":      "alive",
        "service":     Config.APP_NAME,
        "version":     Config.VERSION,
        "environment": Config.ENV,
        "timestamp":   time.time(),
    }
