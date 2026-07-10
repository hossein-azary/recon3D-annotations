#!/usr/bin/env python3
"""
Shared VMH annotation base class.

This module contains VMHAnnotator so vmh_annotator3.py can be uploaded with a
small shared base module.
"""

from collections import defaultdict
from copy import deepcopy
import json
import logging
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
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

    ANNOTATION_KEY_ALIASES = {
        "inchi_key": "inchikey",
        "EC": "ec-code",
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
            "entities": {
                "reactions": self._empty_entity_stats(),
                "metabolites": self._empty_entity_stats(),
                "genes": self._empty_entity_stats(),
            },
            "fields": {
                "reactions": self._empty_field_stats(),
                "metabolites": self._empty_field_stats(),
                "genes": self._empty_field_stats(),
            },
        }

    @staticmethod
    def _empty_entity_stats() -> Dict:
        return {
            "total": 0,
            "changed": 0,
            "unchanged": 0,
            "failed": 0,
            "vmh_matches": 0,
            "vmh_no_matches": 0,
            "no_query_id": 0,
        }

    @staticmethod
    def _empty_field_stats() -> Dict:
        return {
            "added": defaultdict(int),
            "updated": defaultdict(int),
        }

    @classmethod
    def empty_stats(cls, report_only: bool = False) -> Dict:
        return {
            "reactions_annotated": 0,
            "metabolites_annotated": 0,
            "genes_annotated": 0,
            "api_calls": 0,
            "api_errors": 0,
            "report_only": report_only,
            "entities": {
                "reactions": cls._empty_entity_stats(),
                "metabolites": cls._empty_entity_stats(),
                "genes": cls._empty_entity_stats(),
            },
            "fields": {
                "reactions": cls._empty_field_stats(),
                "metabolites": cls._empty_field_stats(),
                "genes": cls._empty_field_stats(),
            },
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
        """Use uppercase 'SBO', strip prefix, and deduplicate."""
        sbo_values = []
        for key in ("sbo", "SBO"):
            for value in VMHAnnotator._annotation_values(annotation.get(key)):
                value = re.sub(r"^SBO:", "", value, flags=re.IGNORECASE)
                if value not in sbo_values:
                    sbo_values.append(value)

        if sbo_values:
            annotation["SBO"] = sbo_values[0] if len(sbo_values) == 1 else sbo_values
        annotation.pop("sbo", None)

    @staticmethod
    def _normalize_annotation_aliases(annotation: Dict) -> None:
        """Merge known annotation aliases into their canonical keys."""
        for alias, canonical_key in VMHAnnotator.ANNOTATION_KEY_ALIASES.items():
            if alias not in annotation:
                continue

            alias_values = VMHAnnotator._annotation_values(annotation.get(alias))
            canonical_values = VMHAnnotator._annotation_values(annotation.get(canonical_key))
            merged_values = canonical_values.copy()

            for alias_value in alias_values:
                if alias_value not in merged_values:
                    merged_values.append(alias_value)

            if merged_values:
                annotation[canonical_key] = (
                    merged_values[0] if len(merged_values) == 1 else merged_values
                )
            annotation.pop(alias, None)

    @staticmethod
    def _strip_identifier_prefix(key: str, value: str) -> str:
        if key == "ec-code":
            return re.sub(r"^EC:", "", value, flags=re.IGNORECASE)
        if key.lower() == "sbo":
            return re.sub(r"^SBO:", "", value, flags=re.IGNORECASE)
        if key == "chebi":
            return re.sub(r"^CHEBI:", "", value, flags=re.IGNORECASE)
        if key == "inchi":
            return re.sub(r"^InChI=", "", value, flags=re.IGNORECASE)
        return value

    @staticmethod
    def _normalize_prefixed_identifiers(annotation: Dict) -> None:
        """Strip provider prefixes from fields that should store bare identifiers."""
        for key in ("ec-code", "SBO", "sbo", "chebi", "inchi"):
            values = VMHAnnotator._annotation_values(annotation.get(key))
            if not values:
                continue

            normalized_values = []
            if key == "ec-code":
                values = [
                    part.strip()
                    for item in values
                    for part in re.split(r"[,;]", item)
                    if part.strip()
                ]

            for value in values:
                normalized_value = VMHAnnotator._strip_identifier_prefix(key, value)
                if normalized_value not in normalized_values:
                    normalized_values.append(normalized_value)

            annotation[key] = (
                normalized_values[0]
                if len(normalized_values) == 1
                else normalized_values
            )

    @staticmethod
    def normalize_model_annotations(model: cobra.Model) -> None:
        """Apply annotation key/value normalization to every model entity."""
        for collection in (model.reactions, model.metabolites, model.genes):
            for entity in collection:
                if entity.annotation is None:
                    entity.annotation = {}
                VMHAnnotator._normalize_sbo_annotation(entity.annotation)
                VMHAnnotator._normalize_annotation_aliases(entity.annotation)
                VMHAnnotator._normalize_prefixed_identifiers(entity.annotation)

    @staticmethod
    def _first_annotation_value(annotation: Dict, key: str) -> Optional[str]:
        key = VMHAnnotator.ANNOTATION_KEY_ALIASES.get(key, key)
        VMHAnnotator._normalize_annotation_aliases(annotation)
        values = VMHAnnotator._annotation_values(annotation.get(key))
        return values[0] if values else None

    @staticmethod
    def _merge_annotation_value(annotation: Dict, key: str, value) -> Optional[str]:
        """Add an annotation value without replacing existing identifiers."""
        key = VMHAnnotator.ANNOTATION_KEY_ALIASES.get(key, key)
        VMHAnnotator._normalize_annotation_aliases(annotation)
        VMHAnnotator._normalize_prefixed_identifiers(annotation)
        had_key = bool(VMHAnnotator._annotation_values(annotation.get(key)))

        new_values = VMHAnnotator._annotation_values(value)
        if key in VMHAnnotator.SPLIT_ANNOTATION_KEYS:
            new_values = [
                part.strip()
                for item in new_values
                for part in re.split(r"[,;]", item)
                if part.strip()
            ]
        new_values = [
            VMHAnnotator._strip_identifier_prefix(key, item)
            for item in new_values
        ]
        if not new_values:
            return None

        existing_values = VMHAnnotator._annotation_values(annotation.get(key))
        merged_values = existing_values.copy()
        for new_value in new_values:
            if new_value not in merged_values:
                merged_values.append(new_value)

        if merged_values == existing_values:
            return None

        annotation[key] = merged_values[0] if len(merged_values) == 1 else merged_values
        return "updated" if had_key else "added"

    def _record_entity_event(self, entity_type: str, event: str, amount: int = 1) -> None:
        with self.stats_lock:
            self.stats["entities"][entity_type][event] += amount

    def _record_field_change(self, entity_type: str, key: str, change_type: str) -> None:
        with self.stats_lock:
            self.stats["fields"][entity_type][change_type][key] += 1

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

    def _add_mapping_fields(
        self,
        annotation: Dict,
        source: Dict,
        mapping: Dict[str, str],
        entity_type: str,
    ) -> bool:
        added = False
        for vmh_field, annotation_key in mapping.items():
            value = source.get(vmh_field)
            change_type = self._merge_annotation_value(annotation, annotation_key, value)
            if change_type:
                self._record_field_change(entity_type, annotation_key, change_type)
                added = True
        return added

    def annotate_reaction(self, reaction: cobra.Reaction) -> bool:
        if reaction.annotation is None:
            reaction.annotation = {}
        self._normalize_sbo_annotation(reaction.annotation)
        self._normalize_annotation_aliases(reaction.annotation)
        self._normalize_prefixed_identifiers(reaction.annotation)

        annotated = False
        bigg_id = self._first_annotation_value(reaction.annotation, "bigg.reaction")

        if bigg_id:
            vmh_data = self._get_from_vmh("/reactions/", params={"abbreviation": bigg_id})
            if vmh_data and vmh_data.get("results"):
                self._record_entity_event("reactions", "vmh_matches")
                annotated = self._add_mapping_fields(
                    reaction.annotation,
                    vmh_data["results"][0],
                    self.REACTION_FIELD_MAPPING,
                    "reactions",
                ) or annotated
            else:
                self._record_entity_event("reactions", "vmh_no_matches")
        else:
            self._record_entity_event("reactions", "no_query_id")

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

        annotated = False
        bigg_id = self._first_annotation_value(metabolite.annotation, "bigg.metabolite")

        if bigg_id:
            vmh_data = self._get_from_vmh("/metabolites/", params={"abbreviation": bigg_id})
            if vmh_data and vmh_data.get("results"):
                self._record_entity_event("metabolites", "vmh_matches")
                met_data = vmh_data["results"][0]
                annotated = self._add_mapping_fields(
                    metabolite.annotation,
                    met_data,
                    self.METABOLITE_FIELD_MAPPING,
                    "metabolites",
                ) or annotated

                if met_data.get("formula") and "formula" not in metabolite.annotation:
                    metabolite.annotation["formula"] = str(met_data["formula"])
                    self._record_field_change("metabolites", "formula", "added")
                    annotated = True

                if met_data.get("charge") is not None and "charge" not in metabolite.annotation:
                    metabolite.annotation["charge"] = str(met_data["charge"])
                    self._record_field_change("metabolites", "charge", "added")
                    annotated = True
            else:
                self._record_entity_event("metabolites", "vmh_no_matches")
        else:
            self._record_entity_event("metabolites", "no_query_id")

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
        self._normalize_annotation_aliases(gene.annotation)
        self._normalize_prefixed_identifiers(gene.annotation)

        annotated = False
        queried = False
        has_match = False
        for symbol in self._gene_query_symbols(gene):
            queried = True
            vmh_data = self._get_from_vmh("/genes/", params={"symbol": symbol})
            if not vmh_data or not vmh_data.get("results"):
                continue

            has_match = True
            self._record_entity_event("genes", "vmh_matches")
            annotated = self._add_mapping_fields(
                gene.annotation,
                vmh_data["results"][0],
                self.GENE_FIELD_MAPPING,
                "genes",
            ) or annotated
            break

        if not queried:
            self._record_entity_event("genes", "no_query_id")
        elif not has_match:
            self._record_entity_event("genes", "vmh_no_matches")

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
        entity_type = desc.lower()
        self._record_entity_event(entity_type, "total", len(entities))
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(annotate_func, entity): entity for entity in entities}
            with tqdm(total=len(entities), desc=desc) as pbar:
                for future in as_completed(futures):
                    entity = futures[future]
                    try:
                        changed = future.result()
                        self._record_entity_event(
                            entity_type,
                            "changed" if changed else "unchanged",
                        )
                    except Exception as exc:
                        logger.warning("Error annotating %s: %s", entity.id, exc)
                        self._record_entity_event(entity_type, "failed")
                    pbar.update(1)

    def get_stats(self) -> Dict:
        with self.stats_lock:
            return deepcopy(self.stats)

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
        for entity_type, entity_stats in stats["entities"].items():
            print(
                f"{entity_type.title():<23}"
                f" changed={entity_stats['changed']} "
                f"unchanged={entity_stats['unchanged']} "
                f"failed={entity_stats['failed']}"
            )
        print("=" * 60 + "\n")


