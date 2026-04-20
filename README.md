# Project 1 - Recon3D Model Annotation 

Genome-scale metabolic models (GEMs), such as Recon3D, are widely used to study cellular metabolism. These models describe biochemical reactions, metabolites, and genes in a structured way.
However, many models lack detailed or standardized annotations (e.g., identifiers linking reactions or metabolites to external databases). This makes it difficult to connect the model to biological knowledge available in databases.
Annotation is especially important for enzyme-constrained models (ecModels). These models require additional information, such as enzyme turnover numbers (kcat), which are typically retrieved from external databases. Without proper annotations (e.g., enzyme IDs, reaction IDs), this retrieval becomes incomplete or inaccurate.

---

## Objective 
Annotate a Recon3D-like metabolic model using the VMH API.

---

## Data
* Recon3D: http://bigg.ucsd.edu/models/Recon3D
* VMH API: https://delta.vmh.life/apiDocs 
* COBRAMod: https://github.com/Toepfer-Lab/cobramod/

---

## Expected output: 

Create a script or command-line tool (CLI) that:
* Takes a Recon3D-like model as input
* Uses the VMH API to retrieve annotations
* Adds these annotations to the model
* Outputs an annotated version of the model

Annotation format: 
* Store annotations in the `annotation` field of the model
* Follow a structure similar to existing annotated models: 

| *Metabolic reactions* | *Metabolites* | *Genes* |
|-----------|-----------|-----------|
| rhea.reaction | chebi.metabolite | NCBI accession | 
| kegg.reaction | kegg.compound | UniProt |
| metacyc.reaction |inchi | SBO
| reactome.reaction |inchikey | 
| seed.reaction | smiles | 
| bigg.reaction | formula | 
| ec-code | charge |
| SBO |SBO |

Possible Features: 
* Standalone Python package or collaboration with COBRAMod
* HTML report with statistics about the annotation process
* Web interface
* Collaboration with Recon4 project (Ronan Fleming Lab)

---

# Usefull packages: 

* cobrapy
* requests 
* tqdm / rich 

