#!/usr/bin/env python3
"""
Corrected VMH API annotator for Recon3D-like metabolic models.

This version preserves existing SBO annotations, avoids guessed identifiers,
queries VMH with the right gene symbols, and can read/write SBML or COBRA JSON.
"""

import argparse
import json
import logging
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import cobra
import requests
from tqdm import tqdm


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class VMHAnnotator:
    """Annotate a COBRA model using identifiers returned by the VMH API."""

    VMH_API_BASE = "https://www.vmh.life/_api"

    REACTION_FIELD_MAPPING = {
        "abbreviation": "bigg.reaction",
        "rhea": "rhea",
        "keggId": "kegg.reaction",
        "metanetx": "metanetx.reaction",
        "seed": "seed.reaction",
        "ecnumber": "ec-code",
    }

    METABOLITE_FIELD_MAPPING = {
        "cheBlId": "chebi",
        "keggId": "kegg.compound",
        "biggId": "bigg.metabolite",
        "seed": "seed.compound",
        "metanetx": "metanetx.chemical",
        "inchiString": "inchi",
        "inchiKey": "inchikey",
        "smile": "smiles",
    }

    GENE_FIELD_MAPPING = {
        "uniprot_gname": "uniprot",
        "ensembl_gene": "ensembl",
        "entrez_id": "ncbi.geneid",
    }

    SPLIT_ANNOTATION_KEYS = {
        "ec-code",
        "rhea",
        "kegg.reaction",
        "metanetx.reaction",
        "seed.reaction",
        "chebi",
        "kegg.compound",
        "seed.compound",
        "metanetx.chemical",
        "uniprot",
        "ensembl",
        "ncbi.geneid",
    }

    def __init__(self, cache_responses: bool = True, max_workers: int = 10):
        self.cache_responses = cache_responses
        self.response_cache = {}
        self.cache_lock = threading.Lock()
        self.stats_lock = threading.Lock()
        self.max_workers = max_workers
        self.stats = {
            "reactions_annotated": 0,
            "metabolites_annotated": 0,
            "genes_annotated": 0,
            "api_calls": 0,
            "api_errors": 0,
        }

    @staticmethod
    def _annotation_values(value) -> List[str]:
        """Return an annotation value as a flat list of non-empty strings."""
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value if item]
        return [str(value)] if value else []

    @staticmethod
    def _normalize_sbo_annotation(annotation: Dict) -> None:
        """Use lowercase 'sbo' and remove duplicate uppercase 'SBO'."""
        if "SBO" in annotation and "sbo" not in annotation:
            annotation["sbo"] = annotation["SBO"]
        annotation.pop("SBO", None)

    @staticmethod
    def _first_annotation_value(annotation: Dict, key: str) -> Optional[str]:
        values = VMHAnnotator._annotation_values(annotation.get(key))
        return values[0] if values else None

    @staticmethod
    def _merge_annotation_value(annotation: Dict, key: str, value) -> bool:
        """Add an annotation value without replacing existing identifiers."""
        new_values = VMHAnnotator._annotation_values(value)
        if key in VMHAnnotator.SPLIT_ANNOTATION_KEYS:
            new_values = [
                part.strip()
                for item in new_values
                for part in re.split(r"[,;]", item)
                if part.strip()
            ]
        if not new_values:
            return False

        existing_values = VMHAnnotator._annotation_values(annotation.get(key))
        merged_values = existing_values.copy()
        for new_value in new_values:
            if new_value not in merged_values:
                merged_values.append(new_value)

        if merged_values == existing_values:
            return False

        annotation[key] = merged_values[0] if len(merged_values) == 1 else merged_values
        return True

    def _get_from_vmh(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        cache_key = f"{endpoint}:{json.dumps(params or {}, sort_keys=True)}"
        if self.cache_responses:
            with self.cache_lock:
                if cache_key in self.response_cache:
                    return self.response_cache[cache_key]

        try:
            response = requests.get(
                f"{self.VMH_API_BASE}{endpoint}",
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            logger.warning("VMH API error for %s %s: %s", endpoint, params or {}, exc)
            with self.stats_lock:
                self.stats["api_errors"] += 1
            return None

        with self.stats_lock:
            self.stats["api_calls"] += 1

        if self.cache_responses:
            with self.cache_lock:
                self.response_cache[cache_key] = data

        return data

    def _add_mapping_fields(self, annotation: Dict, source: Dict, mapping: Dict[str, str]) -> bool:
        added = False
        for vmh_field, annotation_key in mapping.items():
            value = source.get(vmh_field)
            if self._merge_annotation_value(annotation, annotation_key, value):
                added = True
        return added

    def annotate_reaction(self, reaction: cobra.Reaction) -> bool:
        if reaction.annotation is None:
            reaction.annotation = {}
        self._normalize_sbo_annotation(reaction.annotation)

        annotated = False
        bigg_id = self._first_annotation_value(reaction.annotation, "bigg.reaction")

        if bigg_id:
            vmh_data = self._get_from_vmh("/reactions/", params={"abbreviation": bigg_id})
            if vmh_data and vmh_data.get("results"):
                annotated = self._add_mapping_fields(
                    reaction.annotation,
                    vmh_data["results"][0],
                    self.REACTION_FIELD_MAPPING,
                ) or annotated

        if "ec-code" not in reaction.annotation:
            text = f"{reaction.name or ''} {reaction.notes or ''}"
            if "EC" in text:
                match = re.search(r"\b(\d+\.\d+\.\d+\.(?:\d+|-|n))\b", text)
                if match:
                    reaction.annotation["ec-code"] = match.group(1)
                    annotated = True

        if annotated:
            with self.stats_lock:
                self.stats["reactions_annotated"] += 1

        return annotated

    def annotate_metabolite(self, metabolite: cobra.Metabolite) -> bool:
        if metabolite.annotation is None:
            metabolite.annotation = {}
        self._normalize_sbo_annotation(metabolite.annotation)

        annotated = False
        bigg_id = self._first_annotation_value(metabolite.annotation, "bigg.metabolite")

        if bigg_id:
            vmh_data = self._get_from_vmh("/metabolites/", params={"abbreviation": bigg_id})
            if vmh_data and vmh_data.get("results"):
                met_data = vmh_data["results"][0]
                annotated = self._add_mapping_fields(
                    metabolite.annotation,
                    met_data,
                    self.METABOLITE_FIELD_MAPPING,
                ) or annotated

                if met_data.get("formula") and "formula" not in metabolite.annotation:
                    metabolite.annotation["formula"] = str(met_data["formula"])
                    annotated = True

                if met_data.get("charge") is not None and "charge" not in metabolite.annotation:
                    metabolite.annotation["charge"] = str(met_data["charge"])
                    annotated = True

        if annotated:
            with self.stats_lock:
                self.stats["metabolites_annotated"] += 1

        return annotated

    def _gene_query_symbols(self, gene: cobra.Gene) -> List[str]:
        symbols = []
        for candidate in (
            gene.name,
            *self._annotation_values(gene.annotation.get("refseq_name")),
            gene.id,
        ):
            if candidate and candidate not in symbols:
                symbols.append(candidate)
        return symbols

    def annotate_gene(self, gene: cobra.Gene) -> bool:
        if gene.annotation is None:
            gene.annotation = {}
        self._normalize_sbo_annotation(gene.annotation)

        annotated = False
        for symbol in self._gene_query_symbols(gene):
            vmh_data = self._get_from_vmh("/genes/", params={"symbol": symbol})
            if not vmh_data or not vmh_data.get("results"):
                continue

            annotated = self._add_mapping_fields(
                gene.annotation,
                vmh_data["results"][0],
                self.GENE_FIELD_MAPPING,
            ) or annotated
            break

        if annotated:
            with self.stats_lock:
                self.stats["genes_annotated"] += 1

        return annotated

    def annotate_model(self, model: cobra.Model) -> Dict:
        logger.info("Starting annotation of model: %s", model.id)
        logger.info("  Reactions: %s", len(model.reactions))
        logger.info("  Metabolites: %s", len(model.metabolites))
        logger.info("  Genes: %s", len(model.genes))
        logger.info("  Using %s parallel workers", self.max_workers)

        self._annotate_entities_parallel(model.reactions, self.annotate_reaction, "Reactions")
        self._annotate_entities_parallel(model.metabolites, self.annotate_metabolite, "Metabolites")
        self._annotate_entities_parallel(model.genes, self.annotate_gene, "Genes")

        logger.info("Annotation complete")
        return self.get_stats()

    def _annotate_entities_parallel(self, entities, annotate_func, desc: str) -> None:
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(annotate_func, entity): entity for entity in entities}
            with tqdm(total=len(entities), desc=desc) as pbar:
                for future in as_completed(futures):
                    entity = futures[future]
                    try:
                        future.result()
                    except Exception as exc:
                        logger.warning("Error annotating %s: %s", entity.id, exc)
                    pbar.update(1)

    def get_stats(self) -> Dict:
        with self.stats_lock:
            return self.stats.copy()

    def print_stats(self) -> None:
        stats = self.get_stats()
        print("\n" + "=" * 60)
        print("ANNOTATION STATISTICS")
        print("=" * 60)
        print(f"Reactions annotated:    {stats['reactions_annotated']}")
        print(f"Metabolites annotated:  {stats['metabolites_annotated']}")
        print(f"Genes annotated:        {stats['genes_annotated']}")
        print(f"API calls made:         {stats['api_calls']}")
        print(f"API errors:             {stats['api_errors']}")
        print("=" * 60 + "\n")


def read_model(path: Path) -> cobra.Model:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return cobra.io.load_json_model(str(path))
    if suffix in {".xml", ".sbml"}:
        return cobra.io.read_sbml_model(str(path))
    raise ValueError(f"Unsupported model format: {path.suffix}")


def write_model(model: cobra.Model, path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix == ".json":
        cobra.io.save_json_model(model, str(path))
    elif suffix in {".xml", ".sbml"}:
        cobra.io.write_sbml_model(model, str(path))
    else:
        raise ValueError(f"Unsupported output format: {path.suffix}")


def generate_html_report(model: cobra.Model, stats: Dict, output_path: Path) -> None:
    reactions_with_annotations = sum(bool(r.annotation) for r in model.reactions)
    metabolites_with_annotations = sum(bool(m.annotation) for m in model.metabolites)
    genes_with_annotations = sum(bool(g.annotation) for g in model.genes)

    reaction_coverage = (
        reactions_with_annotations / len(model.reactions) * 100 if model.reactions else 0
    )
    metabolite_coverage = (
        metabolites_with_annotations / len(model.metabolites) * 100 if model.metabolites else 0
    )
    gene_coverage = genes_with_annotations / len(model.genes) * 100 if model.genes else 0

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Recon3D Model Annotation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .container {{ background-color: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-box {{ display: inline-block; margin: 10px; padding: 15px; background-color: #ecf0f1; border-left: 4px solid #3498db; border-radius: 3px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .stat-label {{ font-size: 12px; color: #7f8c8d; text-transform: uppercase; }}
        .progress-bar {{ width: 100%; height: 30px; background-color: #ecf0f1; border-radius: 3px; overflow: hidden; margin: 10px 0; }}
        .progress {{ height: 100%; background-color: #27ae60; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background-color: #34495e; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ecf0f1; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Recon3D Model Annotation Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    <div class="container">
        <h2>Model Summary</h2>
        <div class="stat-box"><div class="stat-value">{len(model.reactions)}</div><div class="stat-label">Reactions</div></div>
        <div class="stat-box"><div class="stat-value">{len(model.metabolites)}</div><div class="stat-label">Metabolites</div></div>
        <div class="stat-box"><div class="stat-value">{len(model.genes)}</div><div class="stat-label">Genes</div></div>
    </div>
    <div class="container">
        <h2>Annotation Coverage</h2>
        <h3>Reactions</h3>
        <div class="progress-bar"><div class="progress" style="width: {reaction_coverage}%">{reaction_coverage:.1f}%</div></div>
        <p>{reactions_with_annotations} / {len(model.reactions)} reactions annotated</p>
        <h3>Metabolites</h3>
        <div class="progress-bar"><div class="progress" style="width: {metabolite_coverage}%">{metabolite_coverage:.1f}%</div></div>
        <p>{metabolites_with_annotations} / {len(model.metabolites)} metabolites annotated</p>
        <h3>Genes</h3>
        <div class="progress-bar"><div class="progress" style="width: {gene_coverage}%">{gene_coverage:.1f}%</div></div>
        <p>{genes_with_annotations} / {len(model.genes)} genes annotated</p>
    </div>
    <div class="container">
        <h2>Annotation Statistics</h2>
        <table>
            <tr><th>Metric</th><th>Count</th></tr>
            <tr><td>Reactions Annotated</td><td>{stats.get('reactions_annotated', 0)}</td></tr>
            <tr><td>Metabolites Annotated</td><td>{stats.get('metabolites_annotated', 0)}</td></tr>
            <tr><td>Genes Annotated</td><td>{stats.get('genes_annotated', 0)}</td></tr>
            <tr><td>API Calls Made</td><td>{stats.get('api_calls', 0)}</td></tr>
            <tr><td>API Errors</td><td>{stats.get('api_errors', 0)}</td></tr>
        </table>
    </div>
</body>
</html>
"""
    output_path.write_text(html_content, encoding="utf-8")
    logger.info("HTML report generated: %s", output_path)


def default_output_path(model_path: Path) -> Path:
    return model_path.with_name(f"{model_path.stem}_annotated2{model_path.suffix}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Annotate Recon3D-like metabolic models using the VMH API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python vmh_annotator2.py Recon3D.xml
  python vmh_annotator2.py Recon3D.json -o Recon3D_annotated2.json
  python vmh_annotator2.py Recon3D.xml --report report.html
  python vmh_annotator2.py Recon3D.xml --workers 4 --no-cache
""",
    )
    parser.add_argument("model", help="Path to a COBRA JSON or SBML/XML model")
    parser.add_argument("-o", "--output", help="Output path for annotated model")
    parser.add_argument("--report", help="Generate an HTML report at this path")
    parser.add_argument("--workers", type=int, default=10, help="Number of parallel VMH workers")
    parser.add_argument("--no-cache", action="store_true", help="Disable API response caching")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    model_path = Path(args.model)
    if not model_path.exists():
        logger.error("Model file not found: %s", model_path)
        sys.exit(1)

    output_path = Path(args.output) if args.output else default_output_path(model_path)

    try:
        logger.info("Loading model from: %s", model_path)
        model = read_model(model_path)
        logger.info("Model loaded: %s", model.id)

        annotator = VMHAnnotator(
            cache_responses=not args.no_cache,
            max_workers=args.workers,
        )
        stats = annotator.annotate_model(model)
        annotator.print_stats()

        logger.info("Saving annotated model to: %s", output_path)
        write_model(model, output_path)
        logger.info("Model saved successfully")

        if args.report:
            generate_html_report(model, stats, Path(args.report))

    except Exception as exc:
        logger.error("Error during annotation: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
