#!/usr/bin/env python3
"""
Universal VMH annotator with UniProt fallback for missing gene UniProt IDs.

Version 4 keeps the VMH annotation behavior from vmh_annotator3.py and adds a
single extra resource: UniProt REST search. UniProt is used only for genes and
only when the ``uniprot`` annotation is still missing after the VMH lookup.
"""

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import cobra
import requests

from report_generator import generate_html_report, report_only_stats
from model_io import read_model, write_model
from vmh_annotator3 import VMHAnnotator3


logger = logging.getLogger(__name__)


class VMHAnnotator4(VMHAnnotator3):
    """Annotate models using VMH plus UniProt for missing gene UniProt IDs."""

    UNIPROT_SEARCH_URL = "https://rest.uniprot.org/uniprotkb/search"

    def __init__(
        self,
        cache_responses: bool = True,
        max_workers: int = 10,
        query_mode: str = "auto",
        uniprot_organism_id: str = "9606",
        uniprot_reviewed_only: bool = True,
    ):
        super().__init__(
            cache_responses=cache_responses,
            max_workers=max_workers,
            query_mode=query_mode,
        )
        self.uniprot_organism_id = str(uniprot_organism_id or "").strip()
        self.uniprot_reviewed_only = uniprot_reviewed_only
        self.stats["uniprot_fallback"] = {
            "queries": 0,
            "matches": 0,
            "no_matches": 0,
            "errors": 0,
            "skipped_existing": 0,
            "skipped_no_query_id": 0,
        }

    def _record_uniprot_event(self, event: str, amount: int = 1) -> None:
        with self.stats_lock:
            self.stats["uniprot_fallback"][event] += amount

    @staticmethod
    def _has_uniprot(annotation: Dict) -> bool:
        return bool(VMHAnnotator4._annotation_values(annotation.get("uniprot")))

    @staticmethod
    def _is_probable_gene_symbol(value: str) -> bool:
        value = str(value or "").strip()
        if not value:
            return False
        if value.startswith(("ENSG", "HGNC:")):
            return False
        if re.match(r"^\d+(_AT\d+)?$", value):
            return False
        return bool(re.match(r"^[A-Za-z][A-Za-z0-9.-]{1,30}$", value))

    def _uniprot_query_candidates(self, gene: cobra.Gene) -> List[str]:
        """Build focused UniProt search queries from available gene identifiers."""
        queries: List[str] = []

        def add(query: str) -> None:
            query = query.strip()
            if query and query not in queries:
                queries.append(query)

        ensembl_values = [
            *self._annotation_values(gene.annotation.get("ensembl")),
            gene.id,
            gene.name,
        ]
        for value in ensembl_values:
            cleaned = self._clean_gene_text(str(value or "").strip())
            if cleaned.startswith("ENSG"):
                add(f"xref:Ensembl-{cleaned}")

        for value in self._annotation_values(gene.annotation.get("ncbi.geneid")):
            cleaned = str(value).strip()
            if cleaned.isdigit():
                add(f"xref:GeneID-{cleaned}")

        for value in (gene.name, *self._annotation_values(gene.annotation.get("refseq_name")), gene.id):
            cleaned = self._clean_gene_text(str(value or "").strip())
            if self._is_probable_gene_symbol(cleaned):
                add(f"gene_exact:{cleaned}")

        return queries

    def _decorate_uniprot_query(self, query: str) -> str:
        filters = [f"({query})"]
        if self.uniprot_organism_id:
            filters.append(f"(organism_id:{self.uniprot_organism_id})")
        if self.uniprot_reviewed_only:
            filters.append("(reviewed:true)")
        return " AND ".join(filters)

    def _get_from_uniprot(self, query: str) -> Dict:
        decorated_query = self._decorate_uniprot_query(query)
        params = {
            "query": decorated_query,
            "format": "json",
            "fields": "accession,gene_primary,organism_id,reviewed",
            "size": 5,
        }
        cache_key = f"uniprot:{decorated_query}"

        if self.cache_responses:
            with self.cache_lock:
                if cache_key in self.response_cache:
                    return self.response_cache[cache_key]

        try:
            response = requests.get(self.UNIPROT_SEARCH_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            logger.warning("UniProt API error for %s: %s", decorated_query, exc)
            self._record_uniprot_event("errors")
            with self.stats_lock:
                self.stats["api_errors"] += 1
            return {}

        self._record_uniprot_event("queries")
        with self.stats_lock:
            self.stats["api_calls"] += 1

        if self.cache_responses:
            with self.cache_lock:
                self.response_cache[cache_key] = data

        return data

    @staticmethod
    def _uniprot_accessions(data: Dict) -> List[str]:
        accessions: List[str] = []
        for result in data.get("results", []):
            accession = result.get("primaryAccession")
            if accession and accession not in accessions:
                accessions.append(accession)
        return accessions

    def _add_missing_uniprot_from_uniprot_org(self, gene: cobra.Gene) -> bool:
        if self._has_uniprot(gene.annotation):
            self._record_uniprot_event("skipped_existing")
            return False

        queries = self._uniprot_query_candidates(gene)
        if not queries:
            self._record_uniprot_event("skipped_no_query_id")
            return False

        for query in queries:
            data = self._get_from_uniprot(query)
            accessions = self._uniprot_accessions(data)
            if not accessions:
                continue

            change_type = self._merge_annotation_value(
                gene.annotation,
                "uniprot",
                accessions,
            )
            if change_type:
                self._record_uniprot_event("matches")
                self._record_field_change("genes", "uniprot", change_type)
                return True

        self._record_uniprot_event("no_matches")
        return False

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

        annotated = False
        if not queried:
            self._record_entity_event("genes", "no_query_id")
        elif not result:
            self._record_entity_event("genes", "vmh_no_matches")
        else:
            self._record_entity_event("genes", "vmh_matches")
            annotated = self._add_mapping_fields(
                gene.annotation,
                result,
                self.GENE_FIELD_MAPPING,
                "genes",
            )

        annotated = self._add_missing_uniprot_from_uniprot_org(gene) or annotated

        if annotated:
            with self.stats_lock:
                self.stats["genes_annotated"] += 1
        return annotated

    def print_stats(self) -> None:
        super().print_stats()
        stats = self.get_stats().get("uniprot_fallback", {})
        print("UNIPROT FALLBACK")
        print("=" * 60)
        print(f"Queries made:           {stats.get('queries', 0)}")
        print(f"Matches added:          {stats.get('matches', 0)}")
        print(f"No matches:             {stats.get('no_matches', 0)}")
        print(f"Skipped existing:       {stats.get('skipped_existing', 0)}")
        print(f"Skipped no query ID:    {stats.get('skipped_no_query_id', 0)}")
        print(f"Errors:                 {stats.get('errors', 0)}")
        print("=" * 60 + "\n")


def default_output_path(model_path: Path) -> Path:
    return model_path.with_name(f"{model_path.stem}_annotated4{model_path.suffix}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Annotate Recon3D-like and ENGRO2-like models using VMH plus UniProt",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python vmh_annotator4.py Recon3D.json -o recon3D_annotated4.json
  python vmh_annotator4.py ENGRO2.json -o ENGRO2_annotated4.json --query-mode auto
  python vmh_annotator4.py ENGRO2.json -o ENGRO2_annotated4.json --query-mode fallback
  python vmh_annotator4.py model.json --uniprot-organism-id 9606
  python vmh_annotator4.py annotated.json --report report.html --report-only
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
    parser.add_argument("--workers", type=int, default=10, help="Number of parallel API workers")
    parser.add_argument("--no-cache", action="store_true", help="Disable API response caching")
    parser.add_argument(
        "--uniprot-organism-id",
        default="9606",
        help="NCBI taxonomy ID filter for UniProt fallback searches; default is human, 9606",
    )
    parser.add_argument(
        "--include-unreviewed-uniprot",
        action="store_true",
        help="Allow UniProt fallback to return unreviewed TrEMBL entries",
    )
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

        annotator = VMHAnnotator4(
            cache_responses=not args.no_cache,
            max_workers=args.workers,
            query_mode=args.query_mode,
            uniprot_organism_id=args.uniprot_organism_id,
            uniprot_reviewed_only=not args.include_unreviewed_uniprot,
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
