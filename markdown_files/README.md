# Recon3D Model Annotation Tool

A comprehensive Python tool for annotating genome-scale metabolic models (GEMs), such as Recon3D, using the VMH (Virtual Metabolic Human) API.

## Problem Statement

Genome-scale metabolic models (GEMs), such as Recon3D, are widely used to study cellular metabolism. These models describe biochemical reactions, metabolites, and genes in a structured way. However, many models lack detailed or standardized annotations (e.g., identifiers linking reactions or metabolites to external databases), making it difficult to connect the model to biological knowledge available in databases.

Annotation is especially important for enzyme-constrained models (ecModels), which require additional information such as enzyme turnover numbers (kcat). Without proper annotations (e.g., enzyme IDs, reaction IDs), retrieval of this information from external databases becomes incomplete or inaccurate.

## Solution

This project provides a **command-line tool (CLI)** and **Python library** for automatic annotation of metabolic models using the VMH API and cross-reference data.

## Features

✅ **Automatic Annotation**: Uses VMH API to retrieve annotations for reactions, metabolites, and genes  
✅ **Cross-Reference Integration**: Supports loading and using cross-reference data from TSV files  
✅ **Reaction Classification**: Automatically classifies reactions using SBO terms  
✅ **EC Code Extraction**: Extracts EC codes from reaction names  
✅ **HTML Reports**: Generates beautiful HTML reports with annotation statistics  
✅ **Caching**: Optional caching of API responses to minimize API calls  
✅ **Flexible Output**: Supports multiple output formats (SBML XML, JSON reports)  

## Quick Start

### 1. Install Dependencies

Using the setup script:
```bash
python setup_env.py
```

Or manually:
```bash
pip install -r requirements.txt
```

### 2. Annotate a Model

**Basic usage:**
```bash
python vmh_annotator.py Recon3D.xml
```

**With custom output name:**
```bash
python vmh_annotator.py Recon3D.xml -o Recon3D_annotated.xml
```

**Generate HTML report:**
```bash
python vmh_annotator.py Recon3D.xml --report annotation_report.html
```

**Verbose mode (for debugging):**
```bash
python vmh_annotator.py Recon3D.xml -v
```

**Disable caching (use fresh API calls):**
```bash
python vmh_annotator.py Recon3D.xml --no-cache
```

## Project Structure

```
recon3D-annotations/
├── vmh_annotator.py          # Main CLI tool for model annotation
├── data_annotation.py        # Utilities for cross-reference handling
├── example_usage.py          # Example scripts showing how to use the library
├── setup_env.py              # Virtual environment setup script
├── requirements.txt          # Python package dependencies
├── Recon3D.xml              # Input model file
├── reac_xref.tsv            # Cross-reference data
└── README.md                # This file
```

## Annotation Format

The tool adds annotations following the standard BiGG/VMH format:

### Reactions
```python
reaction.annotation = {
    'rhea.reaction': 'RHEA:12345',
    'kegg.reaction': 'R12345',
    'ec-code': '1.1.1.1',
    'SBO': 'SBO:0000655',
    'bigg.reaction': 'PFK',
    # ... other references
}
```

### Metabolites
```python
metabolite.annotation = {
    'chebi.metabolite': 'CHEBI:12345',
    'kegg.compound': 'C00001',
    'inchi': 'InChI=1S/...',
    'formula': 'C6H12O6',
    'charge': '0',
    'SBO': 'SBO:0000247',
    # ... other references
}
```

### Genes
```python
gene.annotation = {
    'ncbi.geneid': '1234567',
    'uniprot': 'P12345',
    'SBO': 'SBO:0000243',
    # ... other references
}
```

## Usage Examples

### Example 1: Basic Command-Line Usage

```bash
# Annotate model with default settings
python vmh_annotator.py Recon3D.xml

# The tool will:
# 1. Load the model
# 2. Query VMH API for annotations
# 3. Add annotations to reactions, metabolites, and genes
# 4. Save annotated model as Recon3D_annotated.xml
```

### Example 2: Using as a Python Library

```python
from vmh_annotator import VMHAnnotator
import cobra

# Load model
model = cobra.io.read_sbml_model("Recon3D.xml")

# Create annotator
annotator = VMHAnnotator(cache_responses=True)

# Annotate all entities
stats = annotator.annotate_model(model)

# Save
cobra.io.write_sbml_model(model, "annotated_model.xml")

# Print statistics
annotator.print_stats()
```

### Example 3: Cross-Reference Enrichment

```python
from data_annotation import CrossReferenceMapper, enrich_model_from_mappings
import cobra

# Load model
model = cobra.io.read_sbml_model("Recon3D.xml")

# Load cross-reference data
mapper = CrossReferenceMapper()
mapper.load_from_tsv("reac_xref.tsv", entity_type='reaction')

# Enrich annotations
enrich_model_from_mappings(model, mapper)

# Save
cobra.io.write_sbml_model(model, "enriched_model.xml")
```

### Example 4: With HTML Report

```python
from vmh_annotator import VMHAnnotator, generate_html_report
from pathlib import Path
import cobra

# Load and annotate
model = cobra.io.read_sbml_model("Recon3D.xml")
annotator = VMHAnnotator()
stats = annotator.annotate_model(model)

# Generate HTML report
generate_html_report(model, stats, Path("report.html"))
```

## Output Files

The tool generates:

1. **Annotated Model** (SBML XML)
   - Original model with added annotations
   - Includes all cross-references and SBO terms

2. **HTML Report** (optional)
   - Visual summary of annotations
   - Coverage statistics
   - Breakdown by entity type

3. **JSON Report** (optional)
   - Machine-readable annotation statistics
   - Useful for integration with other tools

## API Documentation

### VMHAnnotator Class

Main class for annotating models.

**Methods:**
- `annotate_model(model)` - Annotate all entities in model
- `annotate_reaction(reaction)` - Annotate single reaction
- `annotate_metabolite(metabolite)` - Annotate single metabolite
- `annotate_gene(gene)` - Annotate single gene
- `get_stats()` - Get annotation statistics
- `print_stats()` - Print formatted statistics

### CrossReferenceMapper Class

Utility for loading and managing cross-reference data.

**Methods:**
- `load_from_tsv(file_path, entity_type)` - Load cross-references
- `get_reaction_refs(reaction_id)` - Get reaction references
- `get_metabolite_refs(metabolite_id)` - Get metabolite references
- `get_gene_refs(gene_id)` - Get gene references

## Data Sources

The tool integrates with:

- **VMH API**: https://delta.vmh.life/apiDocs
- **BiGG Database**: http://bigg.ucsd.edu/models/Recon3D
- **Cross-reference Data**: Various database identifiers

## Requirements

- Python 3.8+
- COBRApy (for metabolic model handling)
- Requests (for VMH API calls)
- tqdm (for progress bars)
- Rich (for terminal output)

See `requirements.txt` for exact versions.

## Installation

### Option 1: Using setup script (Recommended)
```bash
python setup_env.py
```

### Option 2: Manual installation
```bash
pip install -r requirements.txt
```

## Performance

- **API Caching**: Responses are cached by default to avoid redundant API calls
- **Progress Bars**: Visual feedback during processing
- **Batch Processing**: Efficient handling of large models

## Troubleshooting

### Issue: "Model file not found"
```bash
# Make sure Recon3D.xml is in the current directory
ls Recon3D.xml
```

### Issue: API errors
```bash
# Check VMH API availability
# Disable caching to get fresh responses
python vmh_annotator.py Recon3D.xml --no-cache
```

### Issue: ImportError (Missing packages)
```bash
# Install requirements
pip install -r requirements.txt
```

## Future Enhancements

Possible features:
- ✅ HTML report generation (implemented)
- ⏳ Web interface for interactive annotation
- ⏳ Integration with COBRAMod
- ⏳ Collaboration with Recon4 project
- ⏳ Advanced EC code mapping
- ⏳ Custom database support

## Citation

If you use this tool in your research, please cite:

> [Citation information to be added]

## License

[Add appropriate license]

## Support

For issues, questions, or contributions, please [add contact information].

## References

- **Recon3D**: Swainston et al., 2016
- **VMH Database**: https://www.vmh.life/
- **COBRApy**: Ebrahim et al., 2013
- **Systems Biology Ontology (SBO)**: https://www.ebi.ac.uk/sbo/

---

**Last Updated**: 2026-04-23  
**Version**: 1.0.0 

