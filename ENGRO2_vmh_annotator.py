#!/usr/bin/env python3
"""
VMH annotator for ENGRO2-style models.

ENGRO2 does not always contain the BiGG annotation keys used by
vmh_annotator2.py. This wrapper keeps the same merge and normalization logic,
but adds fallback searches based on model IDs and converted gene identifiers.
"""

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import cobra

from report_generator import generate_html_report, report_only_stats
from vmh_annotator2 import VMHAnnotator, read_model, write_model


logger = logging.getLogger(__name__)


class ENGRO2VMHAnnotator(VMHAnnotator):
    """Annotate ENGRO2 by trying VMH-compatible fallback identifiers."""

    @staticmethod
    def _dedupe(values: Iterable[str]) -> List[str]:
        seen = []
        for value in values:
            if value and value not in seen:
                seen.append(value)
        return seen

    @staticmethod
    def _without_compartment(entity_id: str) -> str:
        """Return accoa from accoa_c, but keep IDs without a clear suffix."""
        match = re.match(r"^(.+)_([a-z][a-z0-9]*)$", entity_id)
        if not match:
            return entity_id
        return match.group(1)

    @staticmethod
    def _clean_gene_text(value: str) -> str:
        return re.sub(r"^G_", "", value or "")

    def _reaction_query_ids(self, reaction: cobra.Reaction) -> List[str]:
        annotation_ids = self._annotation_values(
            reaction.annotation.get("bigg.reaction")
        )
        return self._dedupe([*annotation_ids, reaction.id])

    def _metabolite_query_ids(self, metabolite: cobra.Metabolite) -> List[str]:
        annotation_ids = self._annotation_values(
            metabolite.annotation.get("bigg.metabolite")
        )
        fallback_ids = [metabolite.id, self._without_compartment(metabolite.id)]
        return self._dedupe([*annotation_ids, *fallback_ids])

    def _gene_query_params(self, gene: cobra.Gene) -> List[Tuple[str, str]]:
        """Build VMH /genes/ query parameters from ENGRO2 gene identifiers."""
        candidates: List[Tuple[str, str]] = []

        def add(param: str, value: str) -> None:
            value = str(value or "").strip()
            if value and (param, value) not in candidates:
                candidates.append((param, value))

        for symbol in self._annotation_values(gene.annotation.get("refseq_name")):
            add("symbol", symbol)

        if gene.name:
            cleaned_name = self._clean_gene_text(gene.name)
            if cleaned_name.startswith("ENSG"):
                add("search", cleaned_name)
            else:
                add("symbol", gene.name)

        if gene.id.startswith("HGNC:"):
            hgnc_number = gene.id.split(":", 1)[1]
            add("gene_number", hgnc_number)
            add("search", gene.id)
            add("search", hgnc_number)
        else:
            cleaned_id = self._clean_gene_text(gene.id)
            if cleaned_id.startswith("ENSG"):
                add("search", cleaned_id)
            else:
                add("symbol", cleaned_id)

        return candidates

    def _first_vmh_result(self, endpoint: str, query_params: Iterable[Dict]) -> Tuple[Dict, bool]:
        queried = False
        for params in query_params:
            queried = True
            vmh_data = self._get_from_vmh(endpoint, params=params)
            if vmh_data and vmh_data.get("results"):
                return vmh_data["results"][0], queried
        return {}, queried

    def annotate_reaction(self, reaction: cobra.Reaction) -> bool:
        if reaction.annotation is None:
            reaction.annotation = {}
        self._normalize_sbo_annotation(reaction.annotation)
        self._normalize_annotation_aliases(reaction.annotation)
        self._normalize_prefixed_identifiers(reaction.annotation)

        params = [
            {"abbreviation": query_id}
            for query_id in self._reaction_query_ids(reaction)
        ]
        result, queried = self._first_vmh_result("/reactions/", params)

        if not queried:
            self._record_entity_event("reactions", "no_query_id")
            return False
        if not result:
            self._record_entity_event("reactions", "vmh_no_matches")
            return False

        self._record_entity_event("reactions", "vmh_matches")
        annotated = self._add_mapping_fields(
            reaction.annotation,
            result,
            self.REACTION_FIELD_MAPPING,
            "reactions",
        )
        if annotated:
            with self.stats_lock:
                self.stats["reactions_annotated"] += 1
        return annotated

    def annotate_metabolite(self, metabolite: cobra.Metabolite) -> bool:
        if metabolite.annotation is None:
            metabolite.annotation = {}
        self._normalize_sbo_annotation(metabolite.annotation)
        self._normalize_annotation_aliases(metabolite.annotation)
        self._normalize_prefixed_identifiers(metabolite.annotation)

        params = [
            {"abbreviation": query_id}
            for query_id in self._metabolite_query_ids(metabolite)
        ]
        result, queried = self._first_vmh_result("/metabolites/", params)

        if not queried:
            self._record_entity_event("metabolites", "no_query_id")
            return False
        if not result:
            self._record_entity_event("metabolites", "vmh_no_matches")
            return False

        self._record_entity_event("metabolites", "vmh_matches")
        annotated = self._add_mapping_fields(
            metabolite.annotation,
            result,
            self.METABOLITE_FIELD_MAPPING,
            "metabolites",
        )

        if result.get("formula") and "formula" not in metabolite.annotation:
            metabolite.annotation["formula"] = str(result["formula"])
            self._record_field_change("metabolites", "formula", "added")
            annotated = True

        if result.get("charge") is not None and "charge" not in metabolite.annotation:
            metabolite.annotation["charge"] = str(result["charge"])
            self._record_field_change("metabolites", "charge", "added")
            annotated = True

        if annotated:
            with self.stats_lock:
                self.stats["metabolites_annotated"] += 1
        return annotated

    def annotate_gene(self, gene: cobra.Gene) -> bool:
        if gene.annotation is None:
            gene.annotation = {}
        self._normalize_sbo_annotation(gene.annotation)
        self._normalize_annotation_aliases(gene.annotation)
        self._normalize_prefixed_identifiers(gene.annotation)

        params = [
            {param: value}
            for param, value in self._gene_query_params(gene)
        ]
        result, queried = self._first_vmh_result("/genes/", params)

        if not queried:
            self._record_entity_event("genes", "no_query_id")
            return False
        if not result:
            self._record_entity_event("genes", "vmh_no_matches")
            return False

        self._record_entity_event("genes", "vmh_matches")
        annotated = self._add_mapping_fields(
            gene.annotation,
            result,
            self.GENE_FIELD_MAPPING,
            "genes",
        )
        if annotated:
            with self.stats_lock:
                self.stats["genes_annotated"] += 1
        return annotated


def default_output_path(model_path: Path) -> Path:
    return model_path.with_name(f"{model_path.stem}_ENGRO2_annotated{model_path.suffix}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Annotate ENGRO2 models using VMH with ID conversion fallbacks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python ENGRO2_vmh_annotator.py ENGRO2.json -o ENGRO2_annotated.json
  python ENGRO2_vmh_annotator.py ENGRO2.json -o ENGRO2_annotated.json --report ENGRO2_report.html
  python ENGRO2_vmh_annotator.py ENGRO2_annotated.json --report ENGRO2_report.html --report-only
""",
    )
    parser.add_argument("model", help="Path to an ENGRO2 COBRA JSON or SBML/XML model")
    parser.add_argument("-o", "--output", help="Output path for annotated model")
    parser.add_argument("--report", help="Generate an HTML report at this path")
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Generate an HTML report without calling VMH or saving a model",
    )
    parser.add_argument("--workers", type=int, default=6, help="Number of parallel VMH workers")
    parser.add_argument("--no-cache", action="store_true", help="Disable API response caching")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    model_path = Path(args.model)
    if not model_path.exists():
        logger.error("Model file not found: %s", model_path)
        sys.exit(1)

    output_path = Path(args.output) if args.output else default_output_path(model_path)

    try:
        logger.info("Loading model from: %s", model_path)
        model = read_model(model_path)
        logger.info("Model loaded: %s", model.id)

        if args.report_only:
            if not args.report:
                logger.error("--report-only requires --report")
                sys.exit(1)
            stats = report_only_stats(model)
            generate_html_report(model, stats, Path(args.report))
            return

        annotator = ENGRO2VMHAnnotator(
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
        logger.error("Error during ENGRO2 annotation: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
