#!/usr/bin/env python3
"""
Quick Model Analysis Script

Fast analysis and visualization of model properties.
Run this for a quick overview of your model.
"""

import cobra
from pathlib import Path
from collections import Counter
import json


def quick_analysis(model_path="Recon3D.xml"):
    """Run quick analysis."""
    if not Path(model_path).exists():
        print(f"Error: {model_path} not found")
        return
    
    print(f"Loading {model_path}...", end=" ")
    model = cobra.io.read_sbml_model(model_path)
    print("✓\n")
    
    print("╔" + "═"*78 + "╗")
    print("║" + " "*20 + "RECON3D MODEL QUICK ANALYSIS" + " "*30 + "║")
    print("╚" + "═"*78 + "╝\n")
    
    # ===== BASIC INFO =====
    print("📊 BASIC INFORMATION")
    print("─" * 80)
    print(f"  Model ID:              {model.id}")
    print(f"  Reactions:             {len(model.reactions):>15,}")
    print(f"  Metabolites:           {len(model.metabolites):>15,}")
    print(f"  Genes:                 {len(model.genes):>15,}")
    print(f"  Compartments:          {len(model.compartments):>15,}")
    print()
    
    # ===== REACTION TYPES =====
    print("⚗️ REACTION BREAKDOWN")
    print("─" * 80)
    reversible = sum(1 for r in model.reactions if r.reversibility)
    boundary = sum(1 for r in model.reactions if r.boundary)
    exchange = sum(1 for r in model.reactions if r.id.startswith('EX_'))
    transport = sum(1 for r in model.reactions if 'transport' in r.name.lower())
    
    print(f"  Total:                 {len(model.reactions):>15,}")
    print(f"  Reversible:            {reversible:>15,} ({reversible/len(model.reactions)*100:>5.1f}%)")
    print(f"  Boundary:              {boundary:>15,} ({boundary/len(model.reactions)*100:>5.1f}%)")
    print(f"  Exchange:              {exchange:>15,} ({exchange/len(model.reactions)*100:>5.1f}%)")
    print(f"  Transport:             {transport:>15,} ({transport/len(model.reactions)*100:>5.1f}%)")
    print()
    
    # ===== METABOLITE INFO =====
    print("⚛️ METABOLITE INFORMATION")
    print("─" * 80)
    charged = sum(1 for m in model.metabolites if m.charge != 0)
    with_formula = sum(1 for m in model.metabolites if m.formula)
    
    print(f"  Total:                 {len(model.metabolites):>15,}")
    print(f"  With Formula:          {with_formula:>15,} ({with_formula/len(model.metabolites)*100:>5.1f}%)")
    print(f"  Charged:               {charged:>15,} ({charged/len(model.metabolites)*100:>5.1f}%)")
    print(f"  Uncharged:             {len(model.metabolites)-charged:>15,}")
    print()
    
    # ===== GENE INFO =====
    print("🧬 GENE INFORMATION")
    print("─" * 80)
    genes_in_rxn = set()
    for rxn in model.reactions:
        genes_in_rxn.update(rxn.genes)
    
    rxn_with_genes = sum(1 for r in model.reactions if r.genes)
    
    print(f"  Total Genes:           {len(model.genes):>15,}")
    print(f"  Genes in Reactions:    {len(genes_in_rxn):>15,} ({len(genes_in_rxn)/len(model.genes)*100:>5.1f}%)")
    print(f"  Reactions with GPR:    {rxn_with_genes:>15,} ({rxn_with_genes/len(model.reactions)*100:>5.1f}%)")
    print()
    
    # ===== ANNOTATIONS =====
    print("🏷️  ANNOTATION COVERAGE")
    print("─" * 80)
    rxn_annot = sum(1 for r in model.reactions if r.annotation)
    met_annot = sum(1 for m in model.metabolites if m.annotation)
    gene_annot = sum(1 for g in model.genes if g.annotation)
    
    print(f"  Reactions Annotated:   {rxn_annot:>15,} ({rxn_annot/len(model.reactions)*100:>5.1f}%)")
    print(f"  Metabolites Annotated: {met_annot:>15,} ({met_annot/len(model.metabolites)*100:>5.1f}%)")
    print(f"  Genes Annotated:       {gene_annot:>15,} ({gene_annot/len(model.genes)*100:>5.1f}%)")
    print()
    
    # ===== COMPARTMENTS =====
    print("🏢 COMPARTMENTS")
    print("─" * 80)
    for comp_id in sorted(model.compartments.keys()):
        comp_name = model.compartments[comp_id]
        count = sum(1 for m in model.metabolites if m.compartment == comp_id)
        print(f"  {comp_id:4s} - {comp_name:30s}: {count:>8,} metabolites")
    print()
    
    # ===== TOP SUBSYSTEMS =====
    subsystems = Counter()
    for rxn in model.reactions:
        if rxn.subsystem:
            subsystems[rxn.subsystem] += 1
    
    print("📂 TOP 10 SUBSYSTEMS")
    print("─" * 80)
    for subsys, count in subsystems.most_common(10):
        print(f"  {subsys:50s}: {count:>6,} reactions")
    print()
    
    # ===== ANNOTATION TYPES =====
    reaction_annot_types = Counter()
    for rxn in model.reactions:
        if rxn.annotation:
            for key in rxn.annotation.keys():
                reaction_annot_types[key] += 1
    
    if reaction_annot_types:
        print("📋 TOP REACTION ANNOTATION TYPES")
        print("─" * 80)
        for annot_type, count in reaction_annot_types.most_common(10):
            pct = count / rxn_annot * 100 if rxn_annot > 0 else 0
            print(f"  {annot_type:30s}: {count:>8,} ({pct:>5.1f}%)")
        print()
    
    # ===== METABOLITES PER REACTION =====
    met_per_rxn = [len(r.metabolites) for r in model.reactions]
    print("📊 METABOLITES PER REACTION STATISTICS")
    print("─" * 80)
    print(f"  Min:                   {min(met_per_rxn):>15,}")
    print(f"  Max:                   {max(met_per_rxn):>15,}")
    print(f"  Average:               {sum(met_per_rxn)/len(met_per_rxn):>15.2f}")
    print()
    
    # ===== GENES PER REACTION =====
    genes_per_rxn = [len(r.genes) for r in model.reactions if r.genes]
    if genes_per_rxn:
        print("🧬 GENES PER REACTION (with genes) STATISTICS")
        print("─" * 80)
        print(f"  Min:                   {min(genes_per_rxn):>15,}")
        print(f"  Max:                   {max(genes_per_rxn):>15,}")
        print(f"  Average:               {sum(genes_per_rxn)/len(genes_per_rxn):>15.2f}")
        print()
    
    # ===== SUMMARY TABLE =====
    print("📈 SUMMARY TABLE")
    print("─" * 80)
    print(f"{'Property':<30} {'Count':>20} {'%':>20}")
    print("─" * 80)
    
    data = [
        ("Reactions", len(model.reactions), 100),
        ("  Reversible", reversible, reversible/len(model.reactions)*100),
        ("  Boundary", boundary, boundary/len(model.reactions)*100),
        ("  With Genes", rxn_with_genes, rxn_with_genes/len(model.reactions)*100),
        ("  Annotated", rxn_annot, rxn_annot/len(model.reactions)*100),
        ("Metabolites", len(model.metabolites), 100),
        ("  With Formula", with_formula, with_formula/len(model.metabolites)*100),
        ("  Charged", charged, charged/len(model.metabolites)*100),
        ("  Annotated", met_annot, met_annot/len(model.metabolites)*100),
        ("Genes", len(model.genes), 100),
        ("  In Reactions", len(genes_in_rxn), len(genes_in_rxn)/len(model.genes)*100),
        ("  Annotated", gene_annot, gene_annot/len(model.genes)*100),
    ]
    
    for prop, count, pct in data:
        print(f"{prop:<30} {count:>20,} {pct:>19.1f}%")
    
    print("─" * 80)
    print()
    
    # ===== EXPORT STATS =====
    stats = {
        'model_id': model.id,
        'num_reactions': len(model.reactions),
        'num_metabolites': len(model.metabolites),
        'num_genes': len(model.genes),
        'num_compartments': len(model.compartments),
        'reversible': reversible,
        'boundary': boundary,
        'exchange': exchange,
        'transport': transport,
        'reactions_with_genes': rxn_with_genes,
        'genes_in_reactions': len(genes_in_rxn),
        'annotated_reactions': rxn_annot,
        'annotated_metabolites': met_annot,
        'annotated_genes': gene_annot,
        'subsystems': dict(subsystems.most_common()),
    }
    
    with open('model_summary.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    print("✓ Summary saved to: model_summary.json\n")


if __name__ == '__main__':
    quick_analysis()
