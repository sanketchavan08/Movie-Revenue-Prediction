"""Loads config.json / mapping.json and resolves every path the utility needs."""
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
BASE_DIR = SRC_DIR.parent

# Fixed English month names, so results never depend on the PC's locale settings.
MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_FULL = ["January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"]


@dataclass
class RunSettings:
    report_month: date      # first day of the reporting month, e.g. date(2026, 9, 1)
    input_path: Path        # data/SEP_2026/<raw excel>
    history_path: Path      # data/SDLC_PROGRESS_GRAPHS.xlsx
    template_path: Path     # templates/<template>.pptx
    output_path: Path       # output/<name>.pptx
    backup_dir: Path        # data/history_backups
    config: dict


def _read_json(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_report_month(text):
    """'2026-09' -> date(2026, 9, 1)"""
    try:
        year, month = str(text).strip().split("-")
        return date(int(year), int(month), 1)
    except Exception:
        raise ValueError(f"report_month must look like 'YYYY-MM' (e.g. 2026-09), got '{text}'")


def load_settings(month_override=None):
    config = _read_json(SRC_DIR / "config.json")
    report_month = parse_report_month(month_override or config["report_month"])

    mon = MONTH_ABBR[report_month.month - 1].upper()        # SEP
    yyyy = str(report_month.year)                           # 2026
    month_folder = f"{mon}_{yyyy}"                          # SEP_2026

    settings = RunSettings(
        report_month=report_month,
        input_path=BASE_DIR / "data" / month_folder / config["input_excel_name"],
        history_path=BASE_DIR / "data" / config["history_excel_name"],
        template_path=BASE_DIR / "templates" / config["template_name"],
        output_path=BASE_DIR / "output" / config["output_name"].format(MON=mon, YYYY=yyyy),
        backup_dir=BASE_DIR / "data" / "history_backups",
        config=config,
    )

    for label, path in [("Raw Excel", settings.input_path),
                        ("History Excel", settings.history_path),
                        ("Template", settings.template_path)]:
        if not path.exists():
            raise FileNotFoundError(f"{label} not found: {path}")
    return settings


def load_mapping():
    return _read_json(SRC_DIR / "mapping.json")
