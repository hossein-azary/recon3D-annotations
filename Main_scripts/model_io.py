#!/usr/bin/env python3
"""Read and write COBRA models for the VMH annotation scripts."""

from pathlib import Path

import cobra

from vmh_base import VMHAnnotator


def read_model(path: Path) -> cobra.Model:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return cobra.io.load_json_model(str(path))
    if suffix in {".xml", ".sbml"}:
        return cobra.io.read_sbml_model(str(path))
    raise ValueError(f"Unsupported model format: {path.suffix}")


def write_model(model: cobra.Model, path: Path) -> None:
    VMHAnnotator.normalize_model_annotations(model)
    suffix = path.suffix.lower()
    if suffix == ".json":
        cobra.io.save_json_model(model, str(path), pretty=True)
    elif suffix in {".xml", ".sbml"}:
        cobra.io.write_sbml_model(model, str(path))
    else:
        raise ValueError(f"Unsupported output format: {path.suffix}")
