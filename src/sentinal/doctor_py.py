"""Doctor — environment and index health checks for SENTINAL."""

from __future__ import annotations

import importlib
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from sentinal.config import SentinalConfig
from sentinal.logging_utils import get_logger

log = get_logger("doctor")


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    remediation: Optional[str] = None


@dataclass
class DoctorReport:
    checks: List[CheckResult] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return all(c.passed for c in self.checks)

    def summary(self) -> str:
        lines = ["SENTINAL Doctor Report", "=" * 40]
        for c in self.checks:
            icon = "✓" if c.passed else "✗"
            lines.append(f"  {icon} {c.name}: {c.message}")
            if not c.passed and c.remediation:
                lines.append(f"      → {c.remediation}")
        lines.append("=" * 40)
        lines.append("Status: " + ("HEALTHY" if self.healthy else "ISSUES FOUND"))
        return "\n".join(lines)


def run_doctor(config: SentinalConfig) -> DoctorReport:
    """Run all health checks and return a DoctorReport.

    Args:
        config: Validated SentinalConfig.

    Returns:
        DoctorReport with individual check results.
    """
    report = DoctorReport()

    # 1. Python version
    py = sys.version_info
    report.checks.append(CheckResult(
        name="Python version",
        passed=py >= (3, 9),
        message=f"{py.major}.{py.minor}.{py.micro}",
        remediation="Upgrade to Python 3.9+ for full SENTINAL support.",
    ))

    # 2. Data directory
    data_ok = config.data_dir.exists() and config.data_dir.is_dir()
    report.checks.append(CheckResult(
        name="Data directory",
        passed=data_ok,
        message=str(config.data_dir) + (" (exists)" if data_ok else " (missing)"),
        remediation=f"Run `sentinal init` to create '{config.data_dir}'.",
    ))

    # 3. Disk space (warn if < 100 MB free on data dir parent)
    free_mb: Optional[float] = None
    try:
        usage = shutil.disk_usage(config.data_dir.parent)
        free_mb = usage.free / (1024 ** 2)
    except OSError:
        pass

    if free_mb is not None:
        report.checks.append(CheckResult(
            name="Disk space",
            passed=free_mb >= 100,
            message=f"{free_mb:.0f} MB free",
            remediation="Free up disk space before ingesting large document sets.",
        ))

    # 4. SQLite DB
    db_ok = config.db_path.exists()
    report.checks.append(CheckResult(
        name="Metadata DB",
        passed=db_ok,
        message=str(config.db_path) + (" (exists)" if db_ok else " (not yet created)"),
        remediation="Run `sentinal init` or ingest a document to create the DB.",
    ))

    # 5. Index directory
    idx_ok = config.index_path.exists()
    report.checks.append(CheckResult(
        name="Index directory",
        passed=idx_ok,
        message=str(config.index_path) + (" (exists)" if idx_ok else " (not yet created)"),
        remediation="Run `sentinal ingest` to build the index.",
    ))

    # 6. Optional deps
    for pkg, friendly, install_hint in [
        ("pypdf", "PDF support", "pip install pypdf"),
        ("numpy", "Fast vector index", "pip install numpy"),
        ("tomli", "TOML config (Python < 3.11)", "pip install tomli"),
    ]:
        spec = importlib.util.find_spec(pkg)  # type: ignore[attr-defined]
        available = spec is not None
        report.checks.append(CheckResult(
            name=f"Optional dep: {pkg}",
            passed=available,
            message="installed" if available else "not installed",
            remediation=None if available else f"{install_hint}  ({friendly})",
        ))

    # 7. Index integrity (if index exists)
    if idx_ok:
        from sentinal.index import VectorIndex
        try:
            vi = VectorIndex(index_dir=config.index_path)
            issues = vi.integrity_check()
            report.checks.append(CheckResult(
                name="Index integrity",
                passed=len(issues) == 0,
                message="OK" if not issues else "; ".join(issues),
                remediation="Run `sentinal ingest --force` to rebuild affected documents.",
            ))
        except Exception as exc:
            report.checks.append(CheckResult(
                name="Index integrity",
                passed=False,
                message=f"Failed to load index: {exc}",
                remediation="Delete the index directory and re-ingest all documents.",
            ))

    return report
