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


# ------------------------------------------------------------------ slides 5 and 6: one row per app
def _fill_app_table(builder, spec, apps, target, kpi, colors):
    """Shared by slides 5 and 6. A column with "field": null is written empty (filled later)."""
    rows, fills = [], {}
    for r, app in enumerate(apps):
        row = []
        for c, col in enumerate(spec["columns"]):
            if col["field"] is None:
                row.append("")
                continue
            value = app[col["field"]]
            row.append(value if col["format"] == "text" else format_value(value, col["format"]))
            if col.get("status_fill"):
                fills[(r, c)] = colors[kpi_status(value, target)]
        rows.append(row)

    shape = builder.find_shape(spec["shape"])
    builder.fill_repeating_table(shape, spec["template_row"], rows, fills)
    if spec.get("fit"):
        builder.fit_table(shape, spec["template_row"], spec["fit"]["max_bottom_in"], spec["fit"]["min_font_pt"])
    below = [a["nar_id"] for a in apps if kpi_status(a["pct"], target) == "red"]
    if below:
        log.info("%s: apps below %s target: %s", spec["shape"], kpi, ", ".join(below))


def fill_portfolio_release(builder, mapping, config, apps, nc_releases):
    """Slide 5: Release Compliance, one row per application, in Excel order.

    nc_releases: {nar_id: [release numbers]} from Raw Data-RMC (core_extractor.read_grouped_values)
    """
    checked = []
    for app in apps:
        # Non compliant = total - compliant (column P is usually blank in the report)
        calc = app["total"] - app["compliant"]
        if app["non_compliant"] and app["non_compliant"] != calc:
            log.warning("%s: # Release Non Compliant is %s in Excel but total - compliant = %s",
                        app["nar_id"], app["non_compliant"], calc)
        releases = sorted(nc_releases.get(app["nar_id"], []))
        if len(releases) != calc:
            log.warning("%s: %s non-compliant release(s) in Applications View but %d found in Raw Data-RMC",
                        app["nar_id"], calc, len(releases))
        checked.append({**app, "non_compliant": calc, "non_compliant_releases": ", ".join(releases)})

    orphans = sorted(set(nc_releases) - {a["nar_id"] for a in apps})
    if orphans:
        log.warning("Raw Data-RMC has non-compliant releases for NAR IDs not in Applications View: %s",
                    ", ".join(orphans))
    _fill_app_table(builder, mapping["portfolio_release"]["table"], checked,
                    config["targets"]["release"], "release", mapping["status_fill_colors"])


def fill_portfolio_automation(builder, mapping, config, apps, manual_controls, manual_releases):
    """Slide 6: Automation Compliance, one row per application, in Excel order.

    manual_controls / manual_releases: {nar_id: [names]} from Raw Data-RMC, where
    RMC Control? = Yes and Control Closure Pattern KPI2 = Closed Manually.
    """
    rows = [{**app,
             "manual_controls": ", ".join(sorted(manual_controls.get(app["nar_id"], []))),
             "manual_releases": ", ".join(sorted(manual_releases.get(app["nar_id"], [])))}
            for app in apps]
    for app in rows:
        if app["automatic"] < app["total"] and not app["manual_releases"]:
            log.warning("%s: %d control(s) not closed automatically, but no 'Closed Manually' rows in Raw Data-RMC",
                        app["nar_id"], app["total"] - app["automatic"])

    orphans = sorted((set(manual_controls) | set(manual_releases)) - {a["nar_id"] for a in apps})
    if orphans:
        log.warning("Raw Data-RMC has manually closed controls for NAR IDs not in Applications View: %s",
                    ", ".join(orphans))
    _fill_app_table(builder, mapping["portfolio_automation"]["table"], rows,
                    config["targets"]["automation"], "automation", mapping["status_fill_colors"])
