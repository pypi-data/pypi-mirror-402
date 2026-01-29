"""HTML Report Generator.

This module is responsible for rendering the visual representation of the coverage.
It combines data from the [`AgentRegistry`][agent_cover.registry.AgentRegistry]
with the Business Logic rules from the config.

The report is divided into:
1.  **Summary Cards**: High-level percentages for Prompts and Decisions.
2.  **File Breakdown**: Detailed view of every prompt/tool with line numbers and hit status.
3.  **Business Logic Table**: Visual progress bars showing how many expected values were observed.
"""

import html
import os
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from agent_cover.utils import format_iso_time

# Unchanged CSS styles
CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 20px; background: #fdfdfd; color: #333; }
h1 { font-size: 1.5em; margin-bottom: 20px; }
h2 { font-size: 1.3em; margin-top: 40px; margin-bottom: 10px; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 5px; }
h3 { font-size: 1.1em; margin-top: 25px; margin-bottom: 10px; color: #555; }
.meta { color: #666; font-size: 0.9em; margin-bottom: 30px; }
table { width: 100%; border-collapse: collapse; background: white; border: 1px solid #ddd; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 20px;}
th, td { text-align: left; padding: 10px 15px; border-bottom: 1px solid #eee; }
th { background: #f8f9fa; font-weight: 600; color: #444; }
tr:hover { background: #fbfbfb; }
.num { text-align: right; font-family: monospace; }
.bar-container { width: 100px; background: #eee; height: 18px; border-radius: 3px; overflow: hidden; display: inline-block; vertical-align: middle; margin-right: 10px; }
.bar { height: 100%; }
.green { background: #4caf50; }
.red { background: #ef5350; }
.orange { background: #ff9800; }
.badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-weight: bold; color: white; min-width: 40px; text-align: center; }
.tag { display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 0.85em; margin-right: 4px; border: 1px solid #ddd; background: #fafafa; color: #555; margin-bottom: 2px;}
.tag.hit { background: #e8f5e9; border-color: #c8e6c9; color: #2e7d32; }
.tag.miss { background: #ffebee; border-color: #ffcdd2; color: #c62828; text-decoration: line-through; opacity: 0.8; }
.preview { color: #888; font-style: italic; font-size: 0.9em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 400px; display:inline-block; vertical-align:middle;}
.summary-card { padding: 15px; background: white; border: 1px solid #ddd; margin-bottom: 20px; border-radius: 4px; }
.card-prompt { border-left: 5px solid #9c27b0; }
.card-decision { border-left: 5px solid #2196F3; }
"""


def _default_file_writer(path: str, content: str) -> None:
    """Writes content to a file on the local disk.

    Args:
        path: The file system path where the content should be written.
        content: The string content to write to the file.
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def generate_html_report(
    definitions: Dict[str, Any],
    executions: Set[str],
    output_dir: str = "prompt_html",
    decision_config: Optional[Any] = None,
    decision_hits: Optional[Dict[str, Set[str]]] = None,
    writer_func: Optional[Callable[[str, str], None]] = None,
    timestamp: Optional[float] = None,
) -> str:
    """Generates a static HTML website for coverage results.

    It creates an `index.html` file with embedded CSS, making the report portable
    (single folder, no external dependencies).

    Args:
        definitions: A dictionary containing the static definitions of prompts
            and tools found in the codebase.
        executions: A set of identifiers representing the code paths that were
            executed during the run.
        output_dir: The directory where the HTML report should be saved.
            Defaults to "prompt_html".
        decision_config: Configuration object containing business logic decisions
            (YAML based) to be tracked.
        decision_hits: A dictionary mapping decision IDs to sets of observed values,
            used to calculate coverage of expected values.
        writer_func: An optional callable to handle file writing. If None,
            defaults to writing to the local disk.
        timestamp: An optional timestamp (float) to use for the report generation time.
            If None, the current time is used.

    Returns:
        The absolute path to the output directory where the report was generated.
    """
    if writer_func is None:
        writer_func = _default_file_writer

    # Create actual directory only if using the default writer
    if writer_func == _default_file_writer:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    # Use injected or current timestamp
    time_str = format_iso_time(timestamp)

    # --- 1. PROMPT DATA PREP ---
    prompts = {k: v for k, v in definitions.items() if v.get("type") == "PROMPT"}

    # --- 2. TOOLS DATA PREP ---
    tools = {k: v for k, v in definitions.items() if v.get("type") == "TOOL"}

    # --- HTML GENERATION ---

    # A. PROMPT SECTION
    prompts_html, prompts_summary = _render_file_table(prompts, executions, "Prompts")

    # B. DECISION SECTION
    yaml_html = ""
    yaml_stats = {"total": 0, "covered": 0}
    if decision_config and decision_config.decisions:
        rows = ""
        for dec in decision_config.decisions:
            hits = decision_hits.get(dec.id, set()) if decision_hits else set()

            val_html = ""
            covered_count = 0
            for val in dec.expected_values:
                is_hit = str(val) in hits
                css = "hit" if is_hit else "miss"
                val_html += f'<span class="tag {css}">{val}</span>'
                if is_hit:
                    covered_count += 1

            yaml_stats["total"] += len(dec.expected_values)
            yaml_stats["covered"] += covered_count

            row_pct = (
                (covered_count / len(dec.expected_values) * 100)
                if dec.expected_values
                else 0
            )
            color = "green" if row_pct == 100 else "orange" if row_pct > 50 else "red"

            rows += f"""
            <tr>
                <td><strong>{dec.id}</strong><br><small style="color:#999">{dec.description}</small></td>
                <td><code>{dec.target_field}</code></td>
                <td>
                    <div class="bar-container"><div class="bar {color}" style="width: {row_pct}%"></div></div>
                    <span class="num">{int(row_pct)}%</span>
                </td>
                <td>{val_html}</td>
            </tr>
            """

        yaml_html = f"""
        <h3>🧠 Business Logic (Configured)</h3>
        <table>
            <thead>
                <tr>
                    <th width="30%">Decision ID</th>
                    <th width="15%">Field</th>
                    <th width="20%">Coverage</th>
                    <th>Expected Values</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        """

    # B2. Tools Code Table
    tools_html, tools_summary = _render_file_table(tools, executions, "Internal Tools")

    # B3. Unified Decision Summary
    tot_dec = yaml_stats["total"] + tools_summary["total"]
    cov_dec = yaml_stats["covered"] + tools_summary["executed"]
    dec_pct = (cov_dec / tot_dec * 100) if tot_dec > 0 else 0

    decision_summary_card = f"""
    <div class="summary-card card-decision">
        <strong>🧭 Decision Coverage:</strong>
        <span class="badge {"green" if dec_pct > 80 else "red"}">{dec_pct:.1f}%</span>
        <span style="margin-left: 20px; color:#666;">
            (Business Logic: {yaml_stats["covered"]}/{yaml_stats["total"]} items) +
            (Internal Tools: {tools_summary["executed"]}/{tools_summary["total"]} calls)
        </span>
    </div>
    """

    prompt_pct = (
        (prompts_summary["executed"] / prompts_summary["total"] * 100)
        if prompts_summary["total"] > 0
        else 0
    )
    prompt_summary_card = f"""
    <div class="summary-card card-prompt">
        <strong>📝 Prompt Coverage:</strong>
        <span class="badge {"green" if prompt_pct > 80 else "red"}">{prompt_pct:.1f}%</span>
        <span style="margin-left: 20px; color:#666;">
            {prompts_summary["executed"]} / {prompts_summary["total"]} items covered
        </span>
    </div>
    """

    # --- FINAL ASSEMBLY ---
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Agent Coverage Report</title>
        <style>{CSS}</style>
    </head>
    <body>
        <h1>🛡️ Agent Coverage Report</h1>
        <div class="meta">Generated on {time_str}</div>

        {prompt_summary_card}
        {decision_summary_card}

        <h2>📝 Prompt Details</h2>
        {prompts_html if prompts_summary["total"] > 0 else "<p>No prompts detected.</p>"}

        <h2>🧭 Decision Details</h2>
        {yaml_html}
        {tools_html if tools_summary["total"] > 0 else ""}

        {"<p>No decisions or tools detected.</p>" if (not yaml_html and tools_summary["total"] == 0) else ""}

    </body>
    </html>
    """

    out_path = os.path.join(output_dir, "index.html")
    writer_func(out_path, html_content)

    return os.path.abspath(output_dir)


def _render_file_table(
    items_dict: Dict[str, Any], executions: Set[str], title_prefix: str
) -> Tuple[str, Dict[str, int]]:
    """Renders a specific section of the report as an HTML table grouped by file.

    Args:
        items_dict: A dictionary of items (prompts or tools) where keys are IDs
            (usually "filepath:lineno") and values are metadata dictionaries.
        executions: A set of executed item IDs.
        title_prefix: The prefix for the section title (e.g., "Prompts").

    Returns:
        A tuple containing:
            1. The generated HTML string for the table.
            2. A dictionary with execution statistics {"total": int, "executed": int}.
    """
    # Group items by file path
    files_data: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {}
    for key, meta in items_dict.items():
        # --- ID Parsing Logic ---
        if key.startswith("RAW:"):
            fpath = key[4:].split("::")[0]
        elif key.startswith("FILE:"):
            fpath = key[5:]
        else:
            fpath = key.split(":")[0]

        if fpath not in files_data:
            files_data[fpath] = []
        files_data[fpath].append((key, meta))

    rows_html = ""
    sorted_files = sorted(files_data.keys())

    total_items = len(items_dict)
    total_exec = 0

    for fpath in sorted_files:
        items = files_data[fpath]
        try:
            rel_path = os.path.relpath(fpath, os.getcwd())
        except ValueError:
            # Handles cases where paths are on different drives on Windows
            rel_path = fpath

        n_total = len(items)
        n_missed = sum(1 for k, _ in items if k not in executions)
        n_exec = n_total - n_missed
        total_exec += n_exec

        pct = (n_exec / n_total * 100) if n_total > 0 else 0
        color_class = "green" if n_missed == 0 else "red"

        previews_list = []
        for k, meta in items:
            try:
                line_no = k.split(":")[1].split("#")[0]
            except IndexError:
                line_no = ""

            preview_txt = html.escape((meta.get("preview") or "")[:80])
            status = "✅" if k in executions else "❌"
            previews_list.append(
                f"<div><small>{line_no}:</small> {status} <span class='preview'>{preview_txt}</span></div>"
            )

        previews_html = "".join(previews_list)

        rows_html += f"""
        <tr>
            <td valign="top"><strong>{html.escape(rel_path)}</strong></td>
            <td class="num" valign="top">{n_total}</td>
            <td class="num" valign="top">{n_missed}</td>
            <td valign="top">
                <div class="bar-container"><div class="bar {color_class}" style="width: {pct}%"></div></div>
                <span class="num">{int(pct)}%</span>
            </td>
            <td valign="top">{previews_html}</td>
        </tr>
        """

    table_html = f"""
    <h3>{title_prefix} (File Breakdown)</h3>
    <table>
        <thead>
            <tr>
                <th>File</th>
                <th class="num">Items</th>
                <th class="num">Missed</th>
                <th>Coverage</th>
                <th>Details</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
    """

    return table_html, {"total": total_items, "executed": total_exec}
