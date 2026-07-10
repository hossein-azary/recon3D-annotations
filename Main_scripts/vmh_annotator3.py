#!/usr/bin/env python3
"""
Universal VMH annotator for Recon3D-like and ENGRO2-like models.

This script combines the standard VMH annotation workflow with the fallback
identifier searches used for ENGRO2.
Standard annotation keys are tried first; model-ID fallbacks are used when
standard query identifiers are missing or when --query-mode fallback is used.
"""

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import cobra

from report_generator import generate_html_report, report_only_stats
from model_io import read_model, write_model
from vmh_base import VMHAnnotator


logger = logging.getLogger(__name__)


class VMHAnnotator3(VMHAnnotator):
    """Annotate models using standard VMH IDs plus optional fallback searches."""

    def __init__(
        self,
        cache_responses: bool = True,
        max_workers: int = 10,
        query_mode: str = "auto",
    ):
        super().__init__(cache_responses=cache_responses, max_workers=max_workers)
        if query_mode not in {"auto", "standard", "fallback"}:
            raise ValueError("query_mode must be auto, standard, or fallback")
        self.query_mode = query_mode

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

    def _use_fallback(self, standard_values: List[str]) -> bool:
        if self.query_mode == "fallback":
            return True
        if self.query_mode == "standard":
            return False
        return not standard_values

    def _first_vmh_result(self, endpoint: str, query_params: Iterable[Dict]) -> Tuple[Dict, bool]:
        queried = False
        for params in query_params:
            queried = True
            vmh_data = self._get_from_vmh(endpoint, params=params)
            if vmh_data and vmh_data.get("results"):
                return vmh_data["results"][0], queried
        return {}, queried

    def _reaction_query_ids(self, reaction: cobra.Reaction) -> List[str]:
        standard_ids = self._annotation_values(
            reaction.annotation.get("bigg.reaction")
        )
        fallback_ids = [reaction.id] if self._use_fallback(standard_ids) else []
        return self._dedupe([*standard_ids, *fallback_ids])

    def _metabolite_query_ids(self, metabolite: cobra.Metabolite) -> List[str]:
        standard_ids = self._annotation_values(
            metabolite.annotation.get("bigg.metabolite")
        )
        fallback_ids = []
        if self._use_fallback(standard_ids):
            fallback_ids = [
                metabolite.id,
                self._without_compartment(metabolite.id),
            ]
        return self._dedupe([*standard_ids, *fallback_ids])

    def _gene_query_params(self, gene: cobra.Gene) -> List[Tuple[str, str]]:
        """Build VMH /genes/ query parameters from standard and fallback IDs."""
        candidates: List[Tuple[str, str]] = []

        def add(param: str, value: str) -> None:
            value = str(value or "").strip()
            if value and (param, value) not in candidates:
                candidates.append((param, value))

        raw_values = [
            gene.name,
            *self._annotation_values(gene.annotation.get("refseq_name")),
            gene.id,
        ]
        standard_symbols = []
        fallback_values = []

        for symbol in raw_values:
            if not symbol:
                continue
            cleaned_symbol = self._clean_gene_text(symbol)
            if cleaned_symbol.startswith("ENSG") or symbol.startswith("HGNC:"):
                if symbol not in fallback_values:
                    fallback_values.append(symbol)
            elif symbol not in standard_symbols:
                standard_symbols.append(symbol)

        for symbol in standard_symbols:
            if self.query_mode != "fallback":
                add("symbol", symbol)

        use_fallback = (
            self.query_mode == "fallback"
            or (self.query_mode == "auto" and (not standard_symbols or fallback_values))
        )
        if not use_fallback:
            return candidates

        for value in (gene.name, gene.id):
            cleaned_value = self._clean_gene_text(value)
            if cleaned_value.startswith("ENSG"):
                add("search", cleaned_value)

        if gene.id.startswith("HGNC:"):
            hgnc_number = gene.id.split(":", 1)[1]
            add("gene_number", hgnc_number)
            add("search", gene.id)
            add("search", hgnc_number)

        return candidates

    def annotate_reaction(self, reaction: cobra.Reaction) -> bool:
        if reaction.annotation is None:
            reaction.annotation = {}
        self._normalize_sbo_annotation(reaction.annotation)
        self._normalize_annotation_aliases(reaction.annotation)
        self._normalize_prefixed_identifiers(reaction.annotation)

        result, queried = self._first_vmh_result(
            "/reactions/",
            (
                {"abbreviation": query_id}
                for query_id in self._reaction_query_ids(reaction)
            ),
        )

        annotated = False
        if not queried:
            self._record_entity_event("reactions", "no_query_id")
        elif not result:
            self._record_entity_event("reactions", "vmh_no_matches")
        else:
            self._record_entity_event("reactions", "vmh_matches")
            annotated = self._add_mapping_fields(
                reaction.annotation,
                result,
                self.REACTION_FIELD_MAPPING,
                "reactions",
            )

        if "ec-code" not in reaction.annotation:
            text = f"{reaction.name or ''} {reaction.notes or ''}"
            if "EC" in text:
                match = re.search(r"\b(\d+\.\d+\.\d+\.(?:\d+|-|n))\b", text)
                if match:
                    reaction.annotation["ec-code"] = match.group(1)
                    self._record_field_change("reactions", "ec-code", "added")
                    annotated = True

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

        result, queried = self._first_vmh_result(
            "/metabolites/",
            (
                {"abbreviation": query_id}
                for query_id in self._metabolite_query_ids(metabolite)
            ),
        )

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

        result, queried = self._first_vmh_result(
            "/genes/",
            (
                {param: value}
                for param, value in self._gene_query_params(gene)
            ),
        )

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
    return model_path.with_name(f"{model_path.stem}_annotated3{model_path.suffix}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Annotate Recon3D-like and ENGRO2-like models using VMH",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python vmh_annotator3.py Recon3D.json -o recon3D_annotated3.json
  python vmh_annotator3.py ENGRO2.json -o ENGRO2_annotated3.json --query-mode auto
  python vmh_annotator3.py ENGRO2.json -o ENGRO2_annotated3.json --query-mode fallback
  python vmh_annotator3.py model.json --report report.html
  python vmh_annotator3.py annotated.json --report report.html --report-only
""",
    )
    parser.add_argument("model", help="Path to a COBRA JSON or SBML/XML model")
    parser.add_argument("-o", "--output", help="Output path for annotated model")
    parser.add_argument("--report", help="Generate an HTML report at this path")
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Generate an HTML report without calling VMH or saving a model",
    )
    parser.add_argument(
        "--query-mode",
        choices=("auto", "standard", "fallback"),
        default="auto",
        help=(
            "auto uses standard IDs first and fallbacks only when needed; "
            "standard uses existing BiGG/symbol identifiers; fallback uses model-ID searches"
        ),
    )
    parser.add_argument("--workers", type=int, default=10, help="Number of parallel VMH workers")
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

        annotator = VMHAnnotator3(
            cache_responses=not args.no_cache,
            max_workers=args.workers,
            query_mode=args.query_mode,
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
