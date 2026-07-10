#!/usr/bin/env python3
"""Compare an original COBRA model with an annotated model and write HTML."""

import argparse
import re
from collections import Counter
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Dict, List, Tuple

import cobra


SECTIONS = {
    "reactions": lambda model: model.reactions,
    "metabolites": lambda model: model.metabolites,
    "genes": lambda model: model.genes,
}


def read_model(path: Path) -> cobra.Model:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return cobra.io.load_json_model(str(path))
    if suffix in {".xml", ".sbml"}:
        return cobra.io.read_sbml_model(str(path))
    raise ValueError(f"Unsupported model format: {path.suffix}")


def annotation_values(value) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, list):
        return tuple(str(item) for item in value if item not in (None, ""))
    return (str(value),) if value != "" else ()


def annotation_value_count(annotation: Dict) -> int:
    return sum(len(annotation_values(value)) for value in annotation.values())


def compare_annotations(before: Dict, after: Dict) -> Dict:
    before_keys = set(before)
    after_keys = set(after)
    added_keys = sorted(after_keys - before_keys)
    removed_keys = sorted(before_keys - after_keys)
    changed_keys = []
    values_added = {}
    values_removed = {}

    for key in sorted(before_keys & after_keys):
        before_values = set(annotation_values(before.get(key)))
        after_values = set(annotation_values(after.get(key)))
        added = sorted(after_values - before_values)
        removed = sorted(before_values - after_values)
        if added or removed:
            changed_keys.append(key)
            if added:
                values_added[key] = added
            if removed:
                values_removed[key] = removed

    return {
        "added_keys": added_keys,
        "removed_keys": removed_keys,
        "changed_keys": changed_keys,
        "values_added": values_added,
        "values_removed": values_removed,
    }


def analyze_section(main_model: cobra.Model, annotated_model: cobra.Model, section: str) -> Dict:
    main_entities = SECTIONS[section](main_model)
    annotated_entities = SECTIONS[section](annotated_model)
    main_by_id = {entity.id: entity for entity in main_entities}
    annotated_by_id = {entity.id: entity for entity in annotated_entities}

    key_main = Counter()
    key_annotated = Counter()
    value_main = Counter()
    value_annotated = Counter()
    key_added_entities = Counter()
    key_removed_entities = Counter()
    key_changed_entities = Counter()
    values_added_total = Counter()
    values_removed_total = Counter()

    changed_examples = []
    changed_entities = 0
    unchanged_entities = 0
    entities_with_more_annotations = 0
    entities_with_fewer_annotations = 0

    all_ids = sorted(set(main_by_id) | set(annotated_by_id))
    for entity_id in all_ids:
        main_entity = main_by_id.get(entity_id)
        annotated_entity = annotated_by_id.get(entity_id)
        before = dict(getattr(main_entity, "annotation", {}) or {})
        after = dict(getattr(annotated_entity, "annotation", {}) or {})

        for key, value in before.items():
            key_main[key] += 1
            value_main[key] += len(annotation_values(value))
        for key, value in after.items():
            key_annotated[key] += 1
            value_annotated[key] += len(annotation_values(value))

        diff = compare_annotations(before, after)
        entity_changed = bool(
            diff["added_keys"]
            or diff["removed_keys"]
            or diff["changed_keys"]
            or main_entity is None
            or annotated_entity is None
        )
        if entity_changed:
            changed_entities += 1
        else:
            unchanged_entities += 1

        before_count = annotation_value_count(before)
        after_count = annotation_value_count(after)
        if after_count > before_count:
            entities_with_more_annotations += 1
        elif after_count < before_count:
            entities_with_fewer_annotations += 1

        for key in diff["added_keys"]:
            key_added_entities[key] += 1
            values_added_total[key] += len(annotation_values(after.get(key)))
        for key in diff["removed_keys"]:
            key_removed_entities[key] += 1
            values_removed_total[key] += len(annotation_values(before.get(key)))
        for key in diff["changed_keys"]:
            key_changed_entities[key] += 1
        for key, added_values in diff["values_added"].items():
            values_added_total[key] += len(added_values)
        for key, removed_values in diff["values_removed"].items():
            values_removed_total[key] += len(removed_values)

        if entity_changed and len(changed_examples) < 60:
            changed_examples.append(
                {
                    "id": entity_id,
                    "name": getattr(annotated_entity or main_entity, "name", ""),
                    "before_count": before_count,
                    "after_count": after_count,
                    "added_keys": diff["added_keys"],
                    "changed_keys": diff["changed_keys"],
                    "removed_keys": diff["removed_keys"],
                }
            )

    key_rows = []
    for key in sorted(set(key_main) | set(key_annotated)):
        key_rows.append(
            {
                "key": key,
                "main_entities": key_main[key],
                "annotated_entities": key_annotated[key],
                "entity_delta": key_annotated[key] - key_main[key],
                "main_values": value_main[key],
                "annotated_values": value_annotated[key],
                "value_delta": value_annotated[key] - value_main[key],
                "new_key_entities": key_added_entities[key],
                "changed_value_entities": key_changed_entities[key],
                "removed_key_entities": key_removed_entities[key],
                "values_added": values_added_total[key],
                "values_removed": values_removed_total[key],
            }
        )

    key_rows.sort(
        key=lambda row: (
            abs(row["value_delta"]) + row["values_added"] + row["values_removed"],
            abs(row["entity_delta"]),
        ),
        reverse=True,
    )

    return {
        "section": section,
        "main_total": len(main_entities),
        "annotated_total": len(annotated_entities),
        "entities_added": sorted(set(annotated_by_id) - set(main_by_id)),
        "entities_removed": sorted(set(main_by_id) - set(annotated_by_id)),
        "changed_entities": changed_entities,
        "unchanged_entities": unchanged_entities,
        "entities_with_more_annotations": entities_with_more_annotations,
        "entities_with_fewer_annotations": entities_with_fewer_annotations,
        "keys_main": len(key_main),
        "keys_annotated": len(key_annotated),
        "values_main": sum(value_main.values()),
        "values_annotated": sum(value_annotated.values()),
        "key_rows": key_rows,
        "changed_examples": changed_examples,
    }


def format_quality_checks(path: Path) -> Dict[str, int]:
    if path.suffix.lower() != ".json":
        return {}
    text = path.read_text(encoding="utf-8")
    checks = {
        'ec-code values with "EC:"': r'"ec-code"\s*:\s*(?:"EC:|\[[^\]]*"EC:)',
        'sbo values with "SBO:"': r'"sbo"\s*:\s*(?:"SBO:|\[[^\]]*"SBO:)',
        'inchi values with "InChI="': r'"inchi"\s*:\s*(?:"InChI=|\[[^\]]*"InChI=)',
        'legacy "inchi_key" keys': r'"inchi_key"\s*:',
        'uppercase "SBO" keys': r'"SBO"\s*:',
        'uppercase "EC" keys': r'"EC"\s*:',
    }
    return {label: len(re.findall(pattern, text, flags=re.IGNORECASE)) for label, pattern in checks.items()}


def pct(part: int, total: int) -> str:
    return f"{part / total * 100:.1f}%" if total else "0.0%"


def td(value) -> str:
    return f"<td>{escape(str(value))}</td>"


def render_summary_cards(sections: List[Dict]) -> str:
    cards = []
    for data in sections:
        cards.append(
            f"""
            <section class="card">
                <h3>{escape(data["section"].title())}</h3>
                <div class="metric"><span>Entities</span><strong>{data["main_total"]} to {data["annotated_total"]}</strong></div>
                <div class="metric"><span>Changed entities</span><strong>{data["changed_entities"]} ({pct(data["changed_entities"], data["annotated_total"])})</strong></div>
                <div class="metric"><span>Annotation keys</span><strong>{data["keys_main"]} to {data["keys_annotated"]}</strong></div>
                <div class="metric"><span>Annotation values</span><strong>{data["values_main"]} to {data["values_annotated"]}</strong></div>
            </section>
            """
        )
    return "\n".join(cards)


def render_key_rows(data: Dict) -> str:
    rows = []
    for row in data["key_rows"]:
        rows.append(
            "<tr>"
            + td(row["key"])
            + td(row["main_entities"])
            + td(row["annotated_entities"])
            + td(f"{row['entity_delta']:+d}")
            + td(row["main_values"])
            + td(row["annotated_values"])
            + td(f"{row['value_delta']:+d}")
            + td(row["new_key_entities"])
            + td(row["changed_value_entities"])
            + td(row["removed_key_entities"])
            + "</tr>"
        )
    if not rows:
        rows.append('<tr><td colspan="10">No annotation keys found.</td></tr>')
    return "\n".join(rows)


def render_examples(data: Dict) -> str:
    rows = []
    for example in data["changed_examples"]:
        rows.append(
            "<tr>"
            + td(example["id"])
            + td(example["name"])
            + td(f"{example['before_count']} to {example['after_count']}")
            + td(", ".join(example["added_keys"]) or "-")
            + td(", ".join(example["changed_keys"]) or "-")
            + td(", ".join(example["removed_keys"]) or "-")
            + "</tr>"
        )
    if not rows:
        rows.append('<tr><td colspan="6">No changed examples.</td></tr>')
    return "\n".join(rows)


def render_quality_rows(checks: Dict[str, int]) -> str:
    rows = []
    for label, count in checks.items():
        status = "OK" if count == 0 else "Needs cleanup"
        rows.append("<tr>" + td(label) + td(count) + td(status) + "</tr>")
    return "\n".join(rows)


def generate_html_report(main_model_path: Path, annotated_model_path: Path, output_path: Path) -> None:
    main_model = read_model(main_model_path)
    annotated_model = read_model(annotated_model_path)
    sections = [
        analyze_section(main_model, annotated_model, section)
        for section in ("reactions", "metabolites", "genes")
    ]
    quality_checks = format_quality_checks(annotated_model_path)

    section_html = []
    for data in sections:
        section_html.append(
            f"""
            <section class="panel">
                <h2>{escape(data["section"].title())}</h2>
                <div class="summary-grid compact">
                    <div><span>Changed</span><strong>{data["changed_entities"]}</strong></div>
                    <div><span>Unchanged</span><strong>{data["unchanged_entities"]}</strong></div>
                    <div><span>More annotations</span><strong>{data["entities_with_more_annotations"]}</strong></div>
                    <div><span>Fewer annotations</span><strong>{data["entities_with_fewer_annotations"]}</strong></div>
                    <div><span>Entities added</span><strong>{len(data["entities_added"])}</strong></div>
                    <div><span>Entities removed</span><strong>{len(data["entities_removed"])}</strong></div>
                </div>

                <h3>Annotation Parameters</h3>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Parameter</th>
                                <th>Main entities</th>
                                <th>Annotated entities</th>
                                <th>Entity delta</th>
                                <th>Main values</th>
                                <th>Annotated values</th>
                                <th>Value delta</th>
                                <th>New key on entities</th>
                                <th>Value changed on entities</th>
                                <th>Key removed on entities</th>
                            </tr>
                        </thead>
                        <tbody>{render_key_rows(data)}</tbody>
                    </table>
                </div>

                <h3>Changed Entity Examples</h3>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Name</th>
                                <th>Value count</th>
                                <th>New parameters</th>
                                <th>Changed parameters</th>
                                <th>Removed parameters</th>
                            </tr>
                        </thead>
                        <tbody>{render_examples(data)}</tbody>
                    </table>
                </div>
            </section>
            """
        )

    quality_html = ""
    if quality_checks:
        quality_html = f"""
        <section class="panel">
            <h2>Format Quality Checks</h2>
            <div class="table-wrap">
                <table>
                    <thead><tr><th>Check</th><th>Matches</th><th>Status</th></tr></thead>
                    <tbody>{render_quality_rows(quality_checks)}</tbody>
                </table>
            </div>
        </section>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Model Annotation Comparison Report</title>
    <style>
        :root {{
            --bg: #f6f7f9;
            --panel: #ffffff;
            --text: #17202a;
            --muted: #5c6b7a;
            --line: #d9e0e7;
            --header: #263746;
            --accent: #1f7a8c;
            --accent-soft: #e8f4f6;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            font-family: Arial, Helvetica, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.45;
        }}
        header {{
            background: var(--header);
            color: white;
            padding: 28px 36px;
        }}
        header h1 {{ margin: 0 0 8px; font-size: 28px; }}
        header p {{ margin: 4px 0; color: #d8e0e8; }}
        main {{ padding: 24px 36px 40px; }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 22px;
        }}
        .summary-grid.compact {{
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        }}
        .card, .panel {{
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 18px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }}
        .panel {{ margin: 0 0 22px; }}
        h2 {{ margin: 0 0 14px; font-size: 22px; }}
        h3 {{ margin: 18px 0 10px; font-size: 17px; }}
        .metric, .summary-grid.compact div {{
            display: flex;
            justify-content: space-between;
            gap: 12px;
            padding: 10px 0;
            border-top: 1px solid var(--line);
        }}
        .metric:first-of-type {{ border-top: 0; }}
        .metric span, .summary-grid.compact span {{ color: var(--muted); }}
        .metric strong, .summary-grid.compact strong {{ color: var(--header); }}
        .table-wrap {{ overflow-x: auto; border: 1px solid var(--line); border-radius: 6px; }}
        table {{ width: 100%; border-collapse: collapse; background: white; }}
        th {{
            position: sticky;
            top: 0;
            background: var(--header);
            color: white;
            text-align: left;
            padding: 9px 10px;
            white-space: nowrap;
            font-size: 13px;
        }}
        td {{
            padding: 8px 10px;
            border-top: 1px solid var(--line);
            vertical-align: top;
            font-size: 13px;
        }}
        tr:nth-child(even) td {{ background: #fafbfc; }}
        .note {{
            background: var(--accent-soft);
            border-left: 4px solid var(--accent);
            padding: 12px 14px;
            margin: 0 0 22px;
        }}
    </style>
</head>
<body>
    <header>
        <h1>Model Annotation Comparison Report</h1>
        <p>Generated: {escape(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))}</p>
        <p>Main model: {escape(str(main_model_path))}</p>
        <p>Annotated model: {escape(str(annotated_model_path))}</p>
    </header>
    <main>
        <div class="note">
            This report compares the original model with the annotated model. It counts annotation keys and individual annotation values, including list values.
        </div>
        <section class="summary-grid">
            {render_summary_cards(sections)}
        </section>
        {quality_html}
        {"".join(section_html)}
    </main>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare a main model with an annotated model and generate an HTML report."
    )
    parser.add_argument("--main-model", required=True, help="Original model path, JSON or SBML/XML")
    parser.add_argument("--annotated-model", required=True, help="Annotated model path, JSON or SBML/XML")
    parser.add_argument("--output", required=True, help="Output HTML report path")
    args = parser.parse_args()

    generate_html_report(
        Path(args.main_model),
        Path(args.annotated_model),
        Path(args.output),
    )
    print(args.output)


if __name__ == "__main__":
    main()
