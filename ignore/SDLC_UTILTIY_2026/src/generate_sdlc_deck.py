"""Builds the monthly SDLC Governance deck.

Run from PyCharm (uses report_month in config.json), or from a terminal:
    python generate_sdlc_deck.py                   # month from config.json
    python generate_sdlc_deck.py --month 2026-10   # override the month
    python generate_sdlc_deck.py --no-history      # don't write to SDLC_PROGRESS_GRAPHS.xlsx

Nothing is saved unless every step succeeds.
"""
import argparse
import logging
import sys

from core_extractor import read_grouped_values, read_summary, read_table
from core_history import HistoryBook
from core_ppt_builder import PPTBuilder
from core_transformer import build_metrics, month_window, portfolio_status_line
from slide_builders import (fill_kpi_targets, fill_portfolio_automation, fill_portfolio_release,
                            fill_summary_tables, update_kpi_chart)
from utils_config import load_mapping, load_settings

log = logging.getLogger("sdlc_deck")


def run(month=None, update_history=None):
    settings = load_settings(month)
    mapping = load_mapping()
    config = settings.config
    if update_history is None:
        update_history = config.get("update_history", True)
    log.info("=== Building deck for %s ===", f"{settings.report_month:%b %Y}")

    # 1. Extract: raw monthly Excel -> dict
    summary = read_summary(settings.input_path, mapping["summary_sheet"])
    release_apps = read_table(settings.input_path, mapping["portfolio_release"])
    automation_apps = read_table(settings.input_path, mapping["portfolio_automation"])
    release_nc = read_grouped_values(settings.input_path, mapping["release_non_compliant_releases"])
    manual_releases = read_grouped_values(settings.input_path, mapping["automation_manual_releases"])
    manual_controls = read_grouped_values(settings.input_path, mapping["automation_manual_controls"])

    # 2. Transform: validate, round, decide green/red, pick the status sentence
    metrics = build_metrics(summary, settings, mapping)
    lines, targets = mapping["portfolio_status_lines"], config["targets"]
    metrics["release_portfolio_line"] = portfolio_status_line(
        "release", metrics["release_status"], release_apps, targets["release"], lines)
    metrics["automation_portfolio_line"] = portfolio_status_line(
        "automation", metrics["automation_status"], automation_apps, targets["automation"], lines)

    # 3. History: put this month into the history (in memory), then read the windows
    history = HistoryBook(settings.history_path, mapping["history"])
    history.upsert(settings.report_month, metrics["release_frac"], metrics["automation_frac"])
    grid_window = history.window(month_window(settings.report_month, config["slide2_months"]))
    chart_window = history.window(month_window(settings.report_month, config["chart_months"]))

    # 4. Build the deck in memory
    builder = PPTBuilder(settings.template_path)
    builder.replace_tokens({token: metrics[field] for token, field in mapping["tokens"].items()})
    fill_kpi_targets(builder, mapping, config, grid_window)       # slide 2
    fill_summary_tables(builder, mapping, metrics)                # slide 4 tables
    update_kpi_chart(builder, mapping, chart_window)              # slide 4 chart
    fill_portfolio_release(builder, mapping, config, release_apps, release_nc)      # slide 5
    fill_portfolio_automation(builder, mapping, config, automation_apps,
                              manual_controls, manual_releases)                    # slide 6

    leftovers = builder.leftover_tokens()
    if leftovers:
        raise ValueError("Tokens still in the deck (missing from mapping.json 'tokens'?): "
                         + ", ".join(f"slide {s}: {t}" for s, t in leftovers))

    # 5. Save - only reached when everything above worked
    if update_history:
        history.save(settings.backup_dir)
    else:
        log.info("History file NOT updated (update_history is off)")
    builder.save(settings.output_path)
    return settings.output_path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate the SDLC Governance compliance deck")
    parser.add_argument("--month", help="Report month as YYYY-MM (overrides config.json)")
    parser.add_argument("--no-history", action="store_true", help="Do not update the history Excel")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(message)s")
    try:
        run(args.month, False if args.no_history else None)
    except Exception as exc:
        log.error("FAILED: %s", exc)
        log.debug("Details", exc_info=True)
        return 1
    log.info("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
