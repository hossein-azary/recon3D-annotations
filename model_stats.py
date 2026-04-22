#!/usr/bin/env python3
"""
Model Statistics and Exploration Script

This script loads the Recon3D model and displays comprehensive statistics
and information about reactions, metabolites, genes, and compartments.
"""

import cobra
from pathlib import Path
from collections import Counter, defaultdict
import json


def load_model(model_path="Recon3D.xml"):
    """Load the metabolic model."""
    if not Path(model_path).exists():
        print(f"Error: {model_path} not found")
        return None
    
    print(f"Loading model from: {model_path}")
    model = cobra.io.read_sbml_model(model_path)
    print(f"✓ Model loaded: {model.id}\n")
    return model


def print_basic_stats(model):
    """Print basic model statistics."""
    print("="*70)
    print("BASIC MODEL STATISTICS")
    print("="*70)
    print(f"Model ID:           {model.id}")
    print(f"Model Description:  {model.description if model.description else 'N/A'}")
    print(f"Total Reactions:    {len(model.reactions):>10}")
    print(f"Total Metabolites:  {len(model.metabolites):>10}")
    print(f"Total Genes:        {len(model.genes):>10}")
    print(f"Total Compartments: {len(model.compartments):>10}")
    print("="*70 + "\n")


def print_compartments(model):
    """Print compartment information."""
    print("="*70)
    print("COMPARTMENTS")
    print("="*70)
    for comp_id, comp_name in sorted(model.compartments.items()):
        metabolites_in_comp = sum(1 for m in model.metabolites if m.compartment == comp_id)
        print(f"  {comp_id:4s} - {comp_name:40s} ({metabolites_in_comp:>5} metabolites)")
    print("="*70 + "\n")


def print_reaction_stats(model):
    """Print reaction statistics."""
    print("="*70)
    print("REACTION STATISTICS")
    print("="*70)
    
    # Basic counts
    print(f"Total Reactions: {len(model.reactions)}")
    
    # Reaction types
    reversible = sum(1 for r in model.reactions if r.reversibility)
    irreversible = len(model.reactions) - reversible
    print(f"  Reversible:     {reversible}")
    print(f"  Irreversible:   {irreversible}")
    
    # Boundary reactions
    boundary = sum(1 for r in model.reactions if r.boundary)
    print(f"  Boundary:       {boundary}")
    
    # Exchange reactions
    exchange = sum(1 for r in model.reactions if r.id.startswith('EX_'))
    print(f"  Exchange:       {exchange}")
    
    # Transport reactions
    transport = sum(1 for r in model.reactions if 'transport' in r.name.lower())
    print(f"  Transport:      {transport}")
    
    # Reactions by number of metabolites
    metabolites_per_reaction = [len(r.metabolites) for r in model.reactions]
    print(f"\nMetabolites per reaction:")
    print(f"  Min:  {min(metabolites_per_reaction)}")
    print(f"  Max:  {max(metabolites_per_reaction)}")
    print(f"  Avg:  {sum(metabolites_per_reaction)/len(metabolites_per_reaction):.2f}")
    
    # Reactions with genes
    rxn_with_genes = sum(1 for r in model.reactions if r.gene_reaction_rule)
    print(f"\nReactions with gene associations: {rxn_with_genes}/{len(model.reactions)}")
    
    # Annotation coverage
    annotated = sum(1 for r in model.reactions if r.annotation)
    print(f"Annotated reactions: {annotated}/{len(model.reactions)} ({annotated/len(model.reactions)*100:.1f}%)")
    
    print("="*70 + "\n")


def print_metabolite_stats(model):
    """Print metabolite statistics."""
    print("="*70)
    print("METABOLITE STATISTICS")
    print("="*70)
    
    print(f"Total Metabolites: {len(model.metabolites)}")
    
    # Metabolites by compartment
    print("\nMetabolites per compartment:")
    comp_counts = Counter(m.compartment for m in model.metabolites)
    for comp_id in sorted(model.compartments.keys()):
        count = comp_counts.get(comp_id, 0)
        comp_name = model.compartments[comp_id]
        print(f"  {comp_id}: {count:>5} ({comp_name})")
    
    # Charged metabolites
    charged = sum(1 for m in model.metabolites if m.charge != 0)
    print(f"\nCharged metabolites: {charged}/{len(model.metabolites)}")
    
    # Metabolites with formula
    with_formula = sum(1 for m in model.metabolites if m.formula)
    print(f"Metabolites with formula: {with_formula}/{len(model.metabolites)}")
    
    # Annotation coverage
    annotated = sum(1 for m in model.metabolites if m.annotation)
    print(f"Annotated metabolites: {annotated}/{len(model.metabolites)} ({annotated/len(model.metabolites)*100:.1f}%)")
    
    # Metabolites used in reactions
    used_metabolites = set()
    for reaction in model.reactions:
        for metabolite in reaction.metabolites:
            used_metabolites.add(metabolite.id)
    
    unused = len(model.metabolites) - len(used_metabolites)
    print(f"Unused metabolites: {unused}/{len(model.metabolites)}")
    
    print("="*70 + "\n")


def print_gene_stats(model):
    """Print gene statistics."""
    print("="*70)
    print("GENE STATISTICS")
    print("="*70)
    
    print(f"Total Genes: {len(model.genes)}")
    
    # Genes used in reactions
    genes_in_reactions = set()
    for reaction in model.reactions:
        genes_in_reactions.update(reaction.genes)
    
    used = len(genes_in_reactions)
    unused = len(model.genes) - used
    print(f"  Used in reactions:   {used}")
    print(f"  Not used:            {unused}")
    
    # Annotation coverage
    annotated = sum(1 for g in model.genes if g.annotation)
    print(f"\nAnnotated genes: {annotated}/{len(model.genes)} ({annotated/len(model.genes)*100:.1f}%)")
    
    # Genes per reaction
    genes_per_rxn = []
    for rxn in model.reactions:
        if rxn.genes:
            genes_per_rxn.append(len(rxn.genes))
    
    if genes_per_rxn:
        print(f"\nGenes per reaction (for reactions with genes):")
        print(f"  Min:  {min(genes_per_rxn)}")
        print(f"  Max:  {max(genes_per_rxn)}")
        print(f"  Avg:  {sum(genes_per_rxn)/len(genes_per_rxn):.2f}")
    
    print("="*70 + "\n")


def print_example_reactions(model, num_examples=5):
    """Print example reactions."""
    print("="*70)
    print(f"EXAMPLE REACTIONS (first {num_examples})")
    print("="*70)
    
    for i, rxn in enumerate(model.reactions[:num_examples], 1):
        print(f"\n{i}. {rxn.id}")
        print(f"   Name:      {rxn.name}")
        print(f"   Reversible: {rxn.reversibility}")
        print(f"   Equation:  {rxn.reaction}")
        print(f"   GPR:       {rxn.gene_reaction_rule if rxn.gene_reaction_rule else 'None'}")
        print(f"   Bounds:    [{rxn.lower_bound}, {rxn.upper_bound}]")
        if rxn.annotation:
            print(f"   Annotations: {list(rxn.annotation.keys())}")
    
    print("\n" + "="*70 + "\n")


def print_example_metabolites(model, num_examples=5):
    """Print example metabolites."""
    print("="*70)
    print(f"EXAMPLE METABOLITES (first {num_examples})")
    print("="*70)
    
    for i, met in enumerate(model.metabolites[:num_examples], 1):
        print(f"\n{i}. {met.id}")
        print(f"   Name:       {met.name}")
        print(f"   Compartment: {met.compartment} ({model.compartments.get(met.compartment, 'Unknown')})")
        print(f"   Formula:    {met.formula if met.formula else 'N/A'}")
        print(f"   Charge:     {met.charge}")
        print(f"   In {len(met.reactions)} reactions")
        if met.annotation:
            print(f"   Annotations: {list(met.annotation.keys())}")
    
    print("\n" + "="*70 + "\n")


def print_example_genes(model, num_examples=5):
    """Print example genes."""
    print("="*70)
    print(f"EXAMPLE GENES (first {num_examples})")
    print("="*70)
    
    for i, gene in enumerate(model.genes[:num_examples], 1):
        print(f"\n{i}. {gene.id}")
        print(f"   Name:     {gene.name if gene.name else 'N/A'}")
        print(f"   In {len(gene.reactions)} reactions")
        if gene.annotation:
            print(f"   Annotations: {list(gene.annotation.keys())}")
    
    print("\n" + "="*70 + "\n")


def print_annotation_summary(model):
    """Print summary of annotations."""
    print("="*70)
    print("ANNOTATION SUMMARY")
    print("="*70)
    
    # Reaction annotations
    reaction_annot_types = Counter()
    for rxn in model.reactions:
        if rxn.annotation:
            for key in rxn.annotation.keys():
                reaction_annot_types[key] += 1
    
    print("\nReaction Annotations:")
    if reaction_annot_types:
        for annot_type, count in sorted(reaction_annot_types.items(), key=lambda x: -x[1])[:10]:
            print(f"  {annot_type:30s}: {count:>5}")
    else:
        print("  None")
    
    # Metabolite annotations
    metabolite_annot_types = Counter()
    for met in model.metabolites:
        if met.annotation:
            for key in met.annotation.keys():
                metabolite_annot_types[key] += 1
    
    print("\nMetabolite Annotations:")
    if metabolite_annot_types:
        for annot_type, count in sorted(metabolite_annot_types.items(), key=lambda x: -x[1])[:10]:
            print(f"  {annot_type:30s}: {count:>5}")
    else:
        print("  None")
    
    # Gene annotations
    gene_annot_types = Counter()
    for gene in model.genes:
        if gene.annotation:
            for key in gene.annotation.keys():
                gene_annot_types[key] += 1
    
    print("\nGene Annotations:")
    if gene_annot_types:
        for annot_type, count in sorted(gene_annot_types.items(), key=lambda x: -x[1])[:10]:
            print(f"  {annot_type:30s}: {count:>5}")
    else:
        print("  None")
    
    print("="*70 + "\n")


def print_mass_balance_info(model):
    """Print information about mass balance."""
    print("="*70)
    print("MASS BALANCE INFORMATION")
    print("="*70)
    
    # Reactions with mass imbalance
    unbalanced = 0
    for rxn in model.reactions:
        try:
            imbalance = cobra.core.reaction.Reaction.check_mass_balance(rxn)
            if imbalance:
                unbalanced += 1
        except:
            pass
    
    print(f"Reactions potentially unbalanced: {unbalanced}/{len(model.reactions)}")
    
    # Metabolites with no formula
    no_formula = sum(1 for m in model.metabolites if not m.formula)
    print(f"Metabolites without formula: {no_formula}/{len(model.metabolites)}")
    
    print("="*70 + "\n")


def export_stats_to_json(model, output_file="model_stats.json"):
    """Export model statistics to JSON file."""
    stats = {
        'model_id': model.id,
        'num_reactions': len(model.reactions),
        'num_metabolites': len(model.metabolites),
        'num_genes': len(model.genes),
        'num_compartments': len(model.compartments),
        'reversible_reactions': sum(1 for r in model.reactions if r.reversibility),
        'boundary_reactions': sum(1 for r in model.reactions if r.boundary),
        'reactions_with_genes': sum(1 for r in model.reactions if r.gene_reaction_rule),
        'annotated_reactions': sum(1 for r in model.reactions if r.annotation),
        'annotated_metabolites': sum(1 for m in model.metabolites if m.annotation),
        'annotated_genes': sum(1 for g in model.genes if g.annotation),
    }
    
    with open(output_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"✓ Statistics exported to: {output_file}\n")


def main():
    """Main function."""
    print("\n" + "="*70)
    print("RECON3D MODEL STATISTICS & EXPLORATION")
    print("="*70 + "\n")
    
    # Load model
    model = load_model("Recon3D.xml")
    if model is None:
        return
    
    # Print statistics
    print_basic_stats(model)
    print_compartments(model)
    print_reaction_stats(model)
    print_metabolite_stats(model)
    print_gene_stats(model)
    print_example_reactions(model, num_examples=3)
    print_example_metabolites(model, num_examples=3)
    print_example_genes(model, num_examples=3)
    print_annotation_summary(model)
    print_mass_balance_info(model)
    
    # Export to JSON
    export_stats_to_json(model)
    
    print("="*70)
    print("✓ Analysis Complete!")
    print("="*70)


if __name__ == '__main__':
    main()
