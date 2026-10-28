"""One function per slide section. Each only WRITES - all numbers are prepared beforehand.

Slide 1 and the slide 4 title/status line are plain tokens ({{MON}} {{YYYY}} {{STATUS_LINE}})
and are handled by PPTBuilder.replace_tokens() in the runner. Slide 3 is never touched.
"""
import logging

from core_transformer import format_pct_auto, format_value, kpi_status
from utils_config import MONTH_ABBR, MONTH_FULL

log = logging.getLogger(__name__)


def _month_label(month, style):
    return MONTH_FULL[month.month - 1] if style == "full" else MONTH_ABBR[month.month - 1]


# ------------------------------------------------------------------ slide 2
def fill_kpi_targets(builder, mapping, config, window):
    """Slide 2: last N months of Release KPI with Target / Achieved and up/down triangles.

    window: [{'month': date, 'release': 1.0, 'automation': 0.956}, ...] oldest first
    """
    grid = mapping["kpi_grid"]
    table = builder.get_table(builder.find_shape(grid["shape"]))
    target = config["targets"]["release"]

    needed_cols = grid["first_month_col"] + len(window)
    if len(table.columns) < needed_cols:
        raise ValueError(f"'{grid['shape']}' has {len(table.columns)} columns, needs {needed_cols}")

    for i, entry in enumerate(window):
        col = grid["first_month_col"] + i
        achieved = None if entry["release"] is None else entry["release"] * 100   # -> 0-100 scale

        builder.set_cell_text(table.cell(grid["header_row"], col), _month_label(entry["month"], grid["month_label"]))
        builder.set_cell_text(table.cell(grid["target_row"], col), format_pct_auto(target))
        builder.set_cell_text(table.cell(grid["achieved_row"], col), format_pct_auto(achieved))

        indicator = builder.find_shape(f"{grid['indicator_prefix']}{i + 1}")
        if achieved is None:
            builder.set_visible(indicator, False)       # no data -> no triangle
        else:
            builder.set_indicator(indicator, kpi_status(achieved, target), grid["indicator_colors"])

    log.info("Slide 2 grid: %s", ", ".join(
        f"{e['month']:%b %Y}={format_pct_auto(None if e['release'] is None else e['release'] * 100)}"
        for e in window))


# ------------------------------------------------------------------ slide 4 tables
def fill_summary_tables(builder, mapping, metrics):
    """Slide 4: Release and Automation one-row tables. The Owner column (col 0) is left as is."""
    colors = mapping["status_fill_colors"]
    for spec in mapping["slide4_tables"]:
        table = builder.get_table(builder.find_shape(spec["shape"]))
        row = spec["data_row"]
        for col_str, col_spec in spec["columns"].items():
            cell = table.cell(row, int(col_str))
            builder.set_cell_text(cell, format_value(metrics[col_spec["field"]], col_spec["format"]))
            if col_spec.get("status_fill"):
                status = metrics[f"{col_spec['status_fill']}_status"]
                builder.set_cell_fill(cell, colors[status])
        log.info("Slide 4 table '%s' filled", spec["shape"])


# ------------------------------------------------------------------ slide 4 chart
def update_kpi_chart(builder, mapping, window):
    """Slide 4: the combined Release + Automation line chart (last 13 months)."""
    spec = mapping["kpi_chart"]
    shape = builder.find_shape(spec["shape"])
    categories = [(e["month"].year, MONTH_ABBR[e["month"].month - 1]) for e in window]
    series = [(s["name"], [e[s["field"]] for e in window]) for s in spec["series"]]
    builder.update_line_chart(shape, categories, series, spec["number_format"],
                              two_level=spec.get("category_style", "year_month") == "year_month")
    log.info("Slide 4 chart: %s %d to %s %d (%d months)",
             categories[0][1], categories[0][0], categories[-1][1], categories[-1][0], len(categories))
