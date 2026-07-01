# Recon3D VMH Annotation Pipeline

A command-line workflow for annotating Recon3D-like genome-scale metabolic models with identifiers from the Virtual Metabolic Human (VMH) API, exporting normalized COBRA JSON/SBML files, and generating HTML reports that summarize annotation coverage and before/after changes.

The project is centered on **vmh_annotator2.py**, a COBRApy-based annotator that preserves existing model annotations, enriches reactions, metabolites, and genes when VMH matches are available, and normalizes annotation keys so downstream tools can read the model consistently.

## Overview

Genome-scale metabolic models (GEMs), such as Recon3D, describe reactions, metabolites, genes, compartments, and gene-protein-reaction rules. These models are useful for flux analysis, multi-omics integration, enzyme-constrained modeling, and biological interpretation, but their usefulness depends strongly on annotation quality.

This project helps standardize and enrich model annotations by:

- reading COBRA JSON, SBML, or XML models;
- querying VMH for reaction, metabolite, and gene identifiers;
- adding missing external database identifiers without overwriting existing ones;
- saving readable, pretty-printed COBRA JSON;
- comparing original and annotated models in a separate before/after report.

## Key Features

- VMH API annotation for Recon3D-like models.
- Support for COBRA JSON, SBML, and XML input/output.
- Preservation of existing annotations.
- Normalization of common annotation issues:
  - `SBO` and `sbo` are merged into `sbo`.
  - `SBO:` prefixes are stripped from `sbo` values.
  - `inchi_key` is merged into `inchikey`.
  - `EC:` prefixes are stripped from `ec-code` values.
  - `InChI=` prefixes are stripped from `inchi` values.
- Pretty JSON output for easier inspection in VS Code.
- Report-only mode for already annotated models.
- XML/SBML-to-JSON conversion with the same normalization logic.
- Before/after comparison reports for original vs annotated models.

## Project Structure

```text
recon3D-annotations/
  vmh_annotator2.py          Main VMH annotation CLI
  convert_to_json.py         Normalized XML/SBML-to-JSON converter
  comparison_file.py         Original vs annotated HTML comparison report
  detailed_annotation_report.py
                             Detailed before/after annotation analysis
  Recon3D.xml                Original Recon3D model, if present locally
  Recon3D_annotated.xml      Annotated SBML/XML model, if present locally
  recon3D_annotated2.json    Normalized JSON output example
  requirements.txt           Python dependencies
```



### Install dependencies

Main packages used by the workflow:

- **cobra**
- **requests**
- **tqdm**

### Annotate a model with VMH

The script will:

1. load the input model;
2. query VMH using available identifiers;
3. merge new identifiers into each entity annotation;
4. normalize annotation keys and prefixes;
5. save the annotated model.




## XML/SBML to JSON Conversion

Use **convert_to_json.py** when converting XML or SBML to JSON. This is important because it uses the same normalization writer as *vmh_annotator2.py*.


## Annotation Normalization

The project normalizes annotations before saving model outputs. This prevents duplicated or inconsistent fields such as:

```json
{
  "SBO": "SBO:0000176",
  "sbo": "0000176",
  "inchi_key": "ABC...",
  "inchikey": "ABC..."
}
```

The normalized output should instead look like:

```json
{
  "sbo": "0000176",
  "inchikey": "ABC..."
}
```


## Before/After Comparison Report

Use **comparison_file.py** to compare an original model with an annotated model:



## The comparison report shows:

- total reactions, metabolites, and genes in each model;
- changed and unchanged entities;
- annotation keys before and after;
- annotation value count changes;
- examples of changed entities;
- format-quality checks for common prefix/key issues.



## Expected Annotation Fields

The annotator can add or normalize fields such as:

|| *Metabolic reactions* | *Metabolites* | *Genes* |
|-----------|-----------|-----------|
| rhea.reaction | chebi.metabolite | NCBI accession | 
| kegg.reaction | kegg.compound | UniProt |
| metacyc.reaction |inchi | SBO
| reactome.reaction |inchikey | 
| seed.reaction | smiles | 
| bigg.reaction | formula | 
| ec-code | charge |
| SBO |SBO |

## Notes and Limitations

- VMH enrichment depends on the identifiers already present in the model.
- Reactions are mainly queried through *bigg.reaction*.
- Metabolites are mainly queried through *bigg.metabolite*.
- Gene matching works best when the model has usable gene symbols or *refseq_name* annotations.
- Models with only SBO annotations may load correctly but receive little or no VMH enrichment.
- Network access is required for VMH API annotation.


### No new annotations were added

This usually means the model does not contain the identifiers used for VMH lookup, such as `bigg.reaction`, `bigg.metabolite`, or usable gene symbols.

## Useful Resources

- **Recon3D on BiGG Models**: http://bigg.ucsd.edu/models/Recon3D
-**VMH API documentation**: https://www.vmh.life/_api
- **COBRApy documentation**: https://cobrapy.readthedocs.io/
- **COBRAMod**: https://github.com/Toepfer-Lab/cobramod


## Project Status

This project currently provides a practical local workflow for Recon3D-style annotation cleanup and reporting. The main focus is producing clean, readable, standardized model outputs that are easier to inspect, compare, and use in downstream metabolic modeling workflows.
