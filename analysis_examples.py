#!/usr/bin/env python3
"""
Code Examples for Model Analysis

This script shows practical code examples for analyzing the Recon3D model.
Copy and modify these examples for your own analyses.
"""

import cobra
from pathlib import Path


def load_model(model_path="Recon3D.xml"):
    """Load model."""
    return cobra.io.read_sbml_model(model_path)


# ============================================================================
# EXAMPLE 1: Basic Model Properties
# ============================================================================
def example_basic_properties():
    """Example: Get basic model properties."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Model Properties")
    print("="*70)
    
    model = load_model()
    
    print(f"Model ID: {model.id}")
    print(f"Number of reactions: {len(model.reactions)}")
    print(f"Number of metabolites: {len(model.metabolites)}")
    print(f"Number of genes: {len(model.genes)}")
    print(f"Compartments: {list(model.compartments.keys())}")


# ============================================================================
# EXAMPLE 2: Find and Examine a Reaction
# ============================================================================
def example_find_reaction():
    """Example: Find and examine a reaction."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Find and Examine a Reaction")
    print("="*70)
    
    model = load_model()
    
    # Get a reaction by ID
    reaction_id = "R_PFK"  # Phosphofructokinase
    try:
        reaction = model.reactions.get_by_id(reaction_id)
    except KeyError:
        # Find first reaction with 'PFK' in name
        reactions = [r for r in model.reactions if 'phosphofructokinase' in r.name.lower()]
        if reactions:
            reaction = reactions[0]
            print(f"Found reaction: {reaction.id}")
        else:
            print("Reaction not found")
            return
    
    print(f"\nReaction ID: {reaction.id}")
    print(f"Name: {reaction.name}")
    print(f"Equation: {reaction.reaction}")
    print(f"Reversible: {reaction.reversibility}")
    print(f"Bounds: [{reaction.lower_bound}, {reaction.upper_bound}]")
    print(f"Subsystem: {reaction.subsystem}")
    print(f"Gene rule: {reaction.gene_reaction_rule}")
    print(f"Metabolites: {len(reaction.metabolites)}")


# ============================================================================
# EXAMPLE 3: Find Metabolites
# ============================================================================
def example_find_metabolites():
    """Example: Find and examine metabolites."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Find and Examine Metabolites")
    print("="*70)
    
    model = load_model()
    
    # Search for glucose
    glucose_metabolites = [m for m in model.metabolites if 'glucose' in m.name.lower()]
    
    print(f"Found {len(glucose_metabolites)} glucose metabolites:\n")
    
    for met in glucose_metabolites[:5]:  # Show first 5
        print(f"ID: {met.id}")
        print(f"  Name: {met.name}")
        print(f"  Compartment: {met.compartment}")
        print(f"  Formula: {met.formula}")
        print(f"  Charge: {met.charge}")
        print(f"  In {len(met.reactions)} reactions")
        print()


# ============================================================================
# EXAMPLE 4: Get All Reactions in a Pathway
# ============================================================================
def example_reactions_in_pathway():
    """Example: Get all reactions in a specific pathway."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Reactions in a Pathway")
    print("="*70)
    
    model = load_model()
    
    # Find all subsystems
    subsystems = set()
    for rxn in model.reactions:
        if rxn.subsystem:
            subsystems.add(rxn.subsystem)
    
    print(f"Available subsystems: {len(subsystems)}\n")
    
    # Get reactions in first subsystem with 'glycol' in name
    for subsys in sorted(subsystems):
        if 'glycol' in subsys.lower():
            reactions = [r for r in model.reactions if r.subsystem == subsys]
            print(f"Subsystem: {subsys}")
            print(f"Reactions: {len(reactions)}\n")
            
            for rxn in reactions[:5]:
                print(f"  {rxn.id:30s} {rxn.name}")
            
            if len(reactions) > 5:
                print(f"  ... and {len(reactions)-5} more")
            
            break


# ============================================================================
# EXAMPLE 5: Analyze Gene-Reaction Relationships
# ============================================================================
def example_gene_analysis():
    """Example: Analyze gene-reaction relationships."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Gene-Reaction Relationships")
    print("="*70)
    
    model = load_model()
    
    # Find a gene
    if model.genes:
        gene = model.genes[0]
        
        print(f"Gene ID: {gene.id}")
        print(f"Number of reactions: {len(gene.reactions)}")
        print(f"\nAssociated reactions:")
        
        for rxn in list(gene.reactions)[:10]:
            print(f"  {rxn.id:30s} {rxn.name}")
        
        if len(gene.reactions) > 10:
            print(f"  ... and {len(gene.reactions)-10} more")


# ============================================================================
# EXAMPLE 6: Count Reactions by Type
# ============================================================================
def example_count_by_type():
    """Example: Count reactions by type."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Count Reactions by Type")
    print("="*70)
    
    model = load_model()
    
    # Count reversible
    reversible = sum(1 for r in model.reactions if r.reversibility)
    print(f"Reversible reactions: {reversible}")
    
    # Count boundary
    boundary = sum(1 for r in model.reactions if r.boundary)
    print(f"Boundary reactions: {boundary}")
    
    # Count exchange (start with EX_)
    exchange = sum(1 for r in model.reactions if r.id.startswith('EX_'))
    print(f"Exchange reactions: {exchange}")
    
    # Count by subsystem
    subsys_counts = {}
    for rxn in model.reactions:
        if rxn.subsystem:
            subsys_counts[rxn.subsystem] = subsys_counts.get(rxn.subsystem, 0) + 1
    
    print(f"\nTop 5 subsystems:")
    for subsys, count in sorted(subsys_counts.items(), key=lambda x: -x[1])[:5]:
        print(f"  {subsys:40s}: {count:>4} reactions")


# ============================================================================
# EXAMPLE 7: Get Metabolites in a Specific Compartment
# ============================================================================
def example_metabolites_in_compartment():
    """Example: Get metabolites in specific compartment."""
    print("\n" + "="*70)
    print("EXAMPLE 7: Metabolites in a Compartment")
    print("="*70)
    
    model = load_model()
    
    # List all compartments
    print("Compartments:")
    for comp_id, comp_name in sorted(model.compartments.items()):
        mets = [m for m in model.metabolites if m.compartment == comp_id]
        print(f"  {comp_id}: {comp_name:30s} ({len(mets):>5} metabolites)")
    
    # Get metabolites in first major compartment
    first_comp = list(model.compartments.keys())[0]
    mets = [m for m in model.metabolites if m.compartment == first_comp]
    
    print(f"\nFirst 5 metabolites in '{first_comp}':")
    for met in mets[:5]:
        print(f"  {met.id:30s} {met.name}")


# ============================================================================
# EXAMPLE 8: Check Annotations
# ============================================================================
def example_check_annotations():
    """Example: Check annotation coverage."""
    print("\n" + "="*70)
    print("EXAMPLE 8: Check Annotations")
    print("="*70)
    
    model = load_model()
    
    # Reactions
    annotated_rxn = sum(1 for r in model.reactions if r.annotation)
    print(f"Reactions with annotations: {annotated_rxn}/{len(model.reactions)}")
    
    # Metabolites
    annotated_met = sum(1 for m in model.metabolites if m.annotation)
    print(f"Metabolites with annotations: {annotated_met}/{len(model.metabolites)}")
    
    # Genes
    annotated_genes = sum(1 for g in model.genes if g.annotation)
    print(f"Genes with annotations: {annotated_genes}/{len(model.genes)}")
    
    # Show annotation types in reactions
    annot_types = {}
    for rxn in model.reactions:
        if rxn.annotation:
            for key in rxn.annotation.keys():
                annot_types[key] = annot_types.get(key, 0) + 1
    
    if annot_types:
        print(f"\nAnnotation types in reactions:")
        for annot_type, count in sorted(annot_types.items(), key=lambda x: -x[1])[:10]:
            print(f"  {annot_type:30s}: {count:>5}")


# ============================================================================
# EXAMPLE 9: Calculate Metabolite Properties
# ============================================================================
def example_metabolite_properties():
    """Example: Calculate metabolite properties."""
    print("\n" + "="*70)
    print("EXAMPLE 9: Metabolite Properties")
    print("="*70)
    
    model = load_model()
    
    # Count charged
    charged = sum(1 for m in model.metabolites if m.charge != 0)
    print(f"Charged metabolites: {charged}/{len(model.metabolites)}")
    
    # Count with formula
    with_formula = sum(1 for m in model.metabolites if m.formula)
    print(f"Metabolites with formula: {with_formula}/{len(model.metabolites)}")
    
    # Average charge
    charges = [m.charge for m in model.metabolites if m.charge != 0]
    if charges:
        print(f"Average charge (for charged): {sum(charges)/len(charges):.2f}")
    
    # Find most used metabolite
    met_usage = {}
    for rxn in model.reactions:
        for met in rxn.metabolites:
            met_usage[met.id] = met_usage.get(met.id, 0) + 1
    
    print(f"\nMost used metabolites:")
    for met_id, count in sorted(met_usage.items(), key=lambda x: -x[1])[:5]:
        met = model.metabolites.get_by_id(met_id)
        print(f"  {met.name:40s}: {count:>5} reactions")


# ============================================================================
# EXAMPLE 10: Search for Specific Patterns
# ============================================================================
def example_pattern_search():
    """Example: Search for specific patterns."""
    print("\n" + "="*70)
    print("EXAMPLE 10: Pattern Search")
    print("="*70)
    
    model = load_model()
    
    # Find transport reactions
    transport = [r for r in model.reactions if 'transport' in r.name.lower()]
    print(f"Transport reactions: {len(transport)}")
    
    # Find dehydrogenase reactions
    dehydrogenase = [r for r in model.reactions if 'dehydrogenase' in r.name.lower()]
    print(f"Dehydrogenase reactions: {len(dehydrogenase)}")
    
    # Find ATP-consuming reactions
    atp_consuming = [r for r in model.reactions if 'atp_' in r.reaction]
    print(f"ATP-consuming reactions: {len(atp_consuming)}")
    
    # Find reactions with multiple genes
    multi_gene = [r for r in model.reactions if len(r.genes) > 1]
    print(f"Reactions with multiple genes: {len(multi_gene)}")


# ============================================================================
# MAIN: Run All Examples
# ============================================================================
def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("MODEL ANALYSIS CODE EXAMPLES")
    print("="*70)
    print("\nThese examples show how to analyze the Recon3D model")
    print("using Python and COBRApy. Copy and modify for your own analyses.\n")
    
    try:
        example_basic_properties()
        example_find_reaction()
        example_find_metabolites()
        example_reactions_in_pathway()
        example_gene_analysis()
        example_count_by_type()
        example_metabolites_in_compartment()
        example_check_annotations()
        example_metabolite_properties()
        example_pattern_search()
        
        print("\n" + "="*70)
        print("✓ All examples completed!")
        print("="*70)
        print("\nNow it's your turn to modify these examples for your analysis!\n")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure Recon3D.xml is in the current directory")


if __name__ == '__main__':
    main()
