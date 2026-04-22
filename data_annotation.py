#!/usr/bin/env python3
"""
Data annotation utilities for Recon3D model annotation.

This module provides helper functions and utilities for annotating
metabolic models using cross-reference data and API integrations.
"""

import cobra
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class CrossReferenceMapper:
    """Load and manage cross-reference mappings from TSV files."""
    
    def __init__(self):
        """Initialize the mapper."""
        self.reactions_mapping = defaultdict(dict)
        self.metabolites_mapping = defaultdict(dict)
        self.genes_mapping = defaultdict(dict)
    
    def load_from_tsv(self, file_path: str, entity_type: str = 'reaction') -> int:
        """
        Load cross-reference data from TSV file.
        
        Expected format: reference_id<TAB>entity_id<TAB>additional_data...
        
        Args:
            file_path: Path to TSV file
            entity_type: Type of entity ('reaction', 'metabolite', or 'gene')
            
        Returns:
            Number of records loaded
        """
        count = 0
        target_mapping = {
            'reaction': self.reactions_mapping,
            'metabolite': self.metabolites_mapping,
            'gene': self.genes_mapping
        }.get(entity_type, self.reactions_mapping)
        
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    # Skip comments and empty lines
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) < 2:
                        continue
                    
                    ref = parts[0]
                    entity_id = parts[1]
                    
                    # Parse the reference
                    if ':' in ref:
                        db_name, db_id = ref.split(':', 1)
                        target_mapping[entity_id][db_name] = db_id
                        count += 1
            
            logger.info(f"Loaded {count} {entity_type} cross-references from {file_path}")
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
        
        return count
    
    def get_reaction_refs(self, reaction_id: str) -> Dict:
        """Get cross-references for a reaction."""
        return self.reactions_mapping.get(reaction_id, {})
    
    def get_metabolite_refs(self, metabolite_id: str) -> Dict:
        """Get cross-references for a metabolite."""
        return self.metabolites_mapping.get(metabolite_id, {})
    
    def get_gene_refs(self, gene_id: str) -> Dict:
        """Get cross-references for a gene."""
        return self.genes_mapping.get(gene_id, {})


def enrich_model_from_mappings(model: cobra.Model, mapper: CrossReferenceMapper):
    """
    Enrich model annotations using cross-reference mappings.
    
    Args:
        model: COBRApy model
        mapper: CrossReferenceMapper instance with loaded data
    """
    reactions_enriched = 0
    metabolites_enriched = 0
    genes_enriched = 0
    
    # Enrich reactions
    for reaction in model.reactions:
        refs = mapper.get_reaction_refs(reaction.id)
        if refs:
            if reaction.annotation is None:
                reaction.annotation = {}
            for db_name, db_id in refs.items():
                reaction.annotation[f"{db_name}.reaction"] = db_id
            reactions_enriched += 1
    
    # Enrich metabolites
    for metabolite in model.metabolites:
        refs = mapper.get_metabolite_refs(metabolite.id)
        if refs:
            if metabolite.annotation is None:
                metabolite.annotation = {}
            for db_name, db_id in refs.items():
                metabolite.annotation[f"{db_name}.metabolite"] = db_id
            metabolites_enriched += 1
    
    # Enrich genes
    for gene in model.genes:
        refs = mapper.get_gene_refs(gene.id)
        if refs:
            if gene.annotation is None:
                gene.annotation = {}
            for db_name, db_id in refs.items():
                gene.annotation[db_name] = db_id
            genes_enriched += 1
    
    logger.info(f"Enriched {reactions_enriched} reactions, "
                f"{metabolites_enriched} metabolites, "
                f"{genes_enriched} genes")


def classify_reaction_by_name(reaction: cobra.Reaction) -> Optional[str]:
    """
    Classify a reaction based on its name and return SBO term.
    
    Args:
        reaction: COBRApy reaction
        
    Returns:
        SBO term string or None
    """
    name = reaction.name.lower()
    
    # Enzyme classification based on EC-like patterns
    if 'transport' in name or 'antiport' in name or 'symport' in name:
        return 'SBO:0000655'  # Transport reaction
    elif 'dehydrogenase' in name or 'oxidase' in name:
        return 'SBO:0000657'  # Oxidoreductase
    elif 'kinase' in name or 'phosphorylation' in name:
        return 'SBO:0000661'  # Phosphorylation
    elif 'phosphatase' in name or 'dephosphorylation' in name:
        return 'SBO:0000330'  # Dephosphorylation
    elif 'isomerase' in name:
        return 'SBO:0000659'  # Isomerization
    elif 'ligase' in name:
        return 'SBO:0000662'  # Ligase
    elif 'transferase' in name:
        return 'SBO:0000660'  # Transferase
    elif 'hydrolase' in name:
        return 'SBO:0000658'  # Hydrolysis
    else:
        return 'SBO:0000167'  # Generic biochemical reaction
    

def extract_ec_code_from_name(name: str) -> Optional[str]:
    """
    Extract EC code from reaction name if present.
    
    Args:
        name: Reaction name
        
    Returns:
        EC code string or None
    """
    import re
    ec_pattern = r'\b(\d+\.\d+\.\d+\.(?:\d+|-|n))\b'
    match = re.search(ec_pattern, name)
    return match.group(1) if match else None


def print_model_summary(model: cobra.Model):
    """Print a summary of the model."""
    print(f"\n{'='*60}")
    print(f"Model: {model.id}")
    print(f"{'='*60}")
    print(f"Reactions: {len(model.reactions):>10}")
    print(f"Metabolites: {len(model.metabolites):>8}")
    print(f"Genes: {len(model.genes):>15}")
    print(f"{'='*60}\n")
    
    # Print annotation coverage
    reactions_annotated = sum(1 for r in model.reactions if r.annotation)
    metabolites_annotated = sum(1 for m in model.metabolites if m.annotation)
    genes_annotated = sum(1 for g in model.genes if g.annotation)
    
    print("Annotation Coverage:")
    print(f"  Reactions: {reactions_annotated}/{len(model.reactions)} ({reactions_annotated/len(model.reactions)*100:.1f}%)")
    print(f"  Metabolites: {metabolites_annotated}/{len(model.metabolites)} ({metabolites_annotated/len(model.metabolites)*100:.1f}%)")
    print(f"  Genes: {genes_annotated}/{len(model.genes)} ({genes_annotated/len(model.genes)*100:.1f}%)")
    print()


def save_annotation_report(model: cobra.Model, output_path: str):
    """Save annotation report as JSON."""
    report = {
        'model_id': model.id,
        'total_reactions': len(model.reactions),
        'total_metabolites': len(model.metabolites),
        'total_genes': len(model.genes),
        'reactions_annotated': sum(1 for r in model.reactions if r.annotation),
        'metabolites_annotated': sum(1 for m in model.metabolites if m.annotation),
        'genes_annotated': sum(1 for g in model.genes if g.annotation),
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Report saved to {output_path}")


if __name__ == '__main__':
    # Example usage
    print("Data annotation utilities loaded successfully!")

        if mnx in mapping:
            ann.update(mapping[mnx])   # 🔥 REAL DATA HERE
            ann['confidence'] = 'high'
        else:
            ann.setdefault('kegg.reaction', 'unknown')
            ann.setdefault('ec-code', 'unknown')
            ann.setdefault('rhea.reaction', 'unknown')
            ann['confidence'] = 'low'



# rxn = model.reactions[0]

# print("BEFORE:")
# print(rxn.annotation)

# annotate_reaction(rxn)

# print("AFTER:")
# print(rxn.annotation)


# for rxn in model.reactions:
#     annotate_reaction(rxn)


for rxn in model.reactions:
    if "dehydrogenase" in rxn.name.lower():
        print(rxn.id, rxn.annotation)
        break

print(mapping.get(rxn.annotation['metanetx.reaction']))