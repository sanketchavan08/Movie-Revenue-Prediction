"""Turns raw Excel values into everything the slides need: rounded numbers, statuses, text."""
import logging
import re
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from utils_config import MONTH_ABBR

log = logging.getLogger(__name__)


# ---------------------------------------------------------------- number helpers
def round_half_up(value, decimals):
    """Excel-style rounding (0.125 -> 0.13). Python's round() would give 0.12."""
    q = Decimal(1).scaleb(-decimals)          # decimals=2 -> Decimal('0.01')
    return float(Decimal(str(value)).quantize(q, rounding=ROUND_HALF_UP))


def format_value(value, fmt):
    """fmt: 'int' -> '86'  |  '0.0' -> '100.0'  |  '0.00' -> '95.60'"""
    if value is None:
        return "-"
    if fmt == "int":
        return str(int(round_half_up(value, 0)))
    decimals = len(fmt.split(".")[1]) if "." in fmt else 0
    return f"{round_half_up(value, decimals):.{decimals}f}"


def format_pct_auto(percent):
    """95.6 -> '95.60%',  100 -> '100%'  (input is on the 0-100 scale)"""
    if percent is None:
        return "-"
    r = round_half_up(percent, 2)
    return f"{int(r)}%" if r == int(r) else f"{r:.2f}%"


def kpi_status(percent, target):
    """'green' if the KPI meets its target, else 'red'. Compared at 2 decimals, like the slide."""
    return "green" if round_half_up(percent, 2) >= target else "red"


# ---------------------------------------------------------------- dates
def parse_reporting_period(text):
    """'Reporting Period: 2026-SEP to 2026-SEP' -> date(2026, 9, 1)"""
    found = re.findall(r"(\d{4})\s*-\s*([A-Za-z]{3})", text or "")
    if not found:
        raise ValueError(f"Could not read a month from Reporting Period text: '{text}'")
    months = {date(int(y), MONTH_ABBR.index(m.title()) + 1, 1) for y, m in found}
    if len(months) > 1:
        raise ValueError(f"Reporting Period covers more than one month: '{text}'")
    return months.pop()


def month_window(end_month, count):
    """month_window(date(2026,9,1), 4) -> [Jun 2026, Jul 2026, Aug 2026, Sep 2026]"""
    months = []
    y, m = end_month.year, end_month.month
    for _ in range(count):
        months.append(date(y, m, 1))
        y, m = (y, m - 1) if m > 1 else (y - 1, 12)
    return list(reversed(months))


# ---------------------------------------------------------------- main transform
def build_metrics(summary, settings, mapping):
    targets = settings.config["targets"]

    # 1. The Excel must be for the month we were asked to build.
    excel_month = parse_reporting_period(summary["reporting_period"])
    if excel_month != settings.report_month:
        raise ValueError(
            f"config.json says {settings.report_month:%Y-%m} but the Excel's Reporting Period is "
            f"{excel_month:%Y-%m}. Wrong file in the month folder, or wrong report_month?")

    # 2. Cross-checks (warnings only: the Excel stays the source of truth).
    s = summary
    if s["total_releases"] - s["releases_compliant"] != s["releases_non_compliant"]:
        log.warning("Total releases (%s) - compliant (%s) != non compliant (%s)",
                    s["total_releases"], s["releases_compliant"], s["releases_non_compliant"])
    if s["total_releases"]:
        calc = s["releases_compliant"] / s["total_releases"] * 100
        if abs(calc - s["release_pct"]) > 0.01:
            log.warning("% Release Compliant is %s but compliant/total gives %.2f", s["release_pct"], calc)
    if s["controls_total"]:
        calc = s["controls_automatic"] / s["controls_total"] * 100
        if abs(calc - s["automation_pct"]) > 0.01:
            log.warning("% Automation is %s but automatic/total gives %.2f", s["automation_pct"], calc)

    # 3. Statuses and the slide 4 status sentence.
    release_status = kpi_status(s["release_pct"], targets["release"])
    automation_status = kpi_status(s["automation_pct"], targets["automation"])
    status_line = mapping["status_lines"][f"{release_status}_{automation_status}"]

    metrics = dict(summary)
    metrics.update({
        "mon": MONTH_ABBR[settings.report_month.month - 1],      # Sep
        "year": str(settings.report_month.year),                 # 2026
        "release_status": release_status,
        "automation_status": automation_status,
        "status_line": status_line,
        # history file stores fractions (1.0 = 100%), rounded to 2 decimals of a percent
        "release_frac": round_half_up(s["release_pct"] / 100, 4),
        "automation_frac": round_half_up(s["automation_pct"] / 100, 4),
    })
    log.info("Release %s (%s), Automation %s (%s)", s["release_pct"], release_status,
             s["automation_pct"], automation_status)
    return metrics
