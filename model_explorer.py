#!/usr/bin/env python3
"""
Interactive Model Explorer

An interactive script for exploring and analyzing Recon3D model
with various analysis and search capabilities.
"""

import cobra
from pathlib import Path
import json
from typing import List, Dict


class ModelExplorer:
    """Interactive model exploration utility."""
    
    def __init__(self, model_path="Recon3D.xml"):
        """Initialize the explorer."""
        if not Path(model_path).exists():
            print(f"Error: {model_path} not found")
            self.model = None
            return
        
        print(f"Loading model: {model_path}...", end=" ")
        self.model = cobra.io.read_sbml_model(model_path)
        print(f"✓ Loaded {self.model.id}\n")
    
    def search_reactions(self, query: str):
        """Search for reactions by ID or name."""
        query_lower = query.lower()
        results = [
            r for r in self.model.reactions 
            if query_lower in r.id.lower() or query_lower in r.name.lower()
        ]
        
        print(f"\nFound {len(results)} reactions matching '{query}':")
        for rxn in results[:10]:  # Limit to 10
            print(f"  {rxn.id:30s} - {rxn.name}")
        
        if len(results) > 10:
            print(f"  ... and {len(results)-10} more")
        
        return results
    
    def search_metabolites(self, query: str):
        """Search for metabolites by ID or name."""
        query_lower = query.lower()
        results = [
            m for m in self.model.metabolites 
            if query_lower in m.id.lower() or query_lower in m.name.lower()
        ]
        
        print(f"\nFound {len(results)} metabolites matching '{query}':")
        for met in results[:10]:  # Limit to 10
            print(f"  {met.id:30s} - {met.name} ({met.compartment})")
        
        if len(results) > 10:
            print(f"  ... and {len(results)-10} more")
        
        return results
    
    def get_reaction_details(self, reaction_id: str):
        """Get detailed information about a reaction."""
        try:
            rxn = self.model.reactions.get_by_id(reaction_id)
        except KeyError:
            print(f"Reaction '{reaction_id}' not found")
            return
        
        print(f"\n{'='*70}")
        print(f"REACTION: {rxn.id}")
        print(f"{'='*70}")
        print(f"Name:        {rxn.name}")
        print(f"Equation:    {rxn.reaction}")
        print(f"Reversible:  {rxn.reversibility}")
        print(f"Bounds:      [{rxn.lower_bound}, {rxn.upper_bound}]")
        print(f"Boundary:    {rxn.boundary}")
        print(f"Subsystem:   {rxn.subsystem if rxn.subsystem else 'N/A'}")
        
        print(f"\nGene Reaction Rule: {rxn.gene_reaction_rule if rxn.gene_reaction_rule else 'None'}")
        
        if rxn.genes:
            print(f"Genes ({len(rxn.genes)}):")
            for gene in rxn.genes:
                print(f"  - {gene.id}")
        
        print(f"\nMetabolites:")
        for met, coeff in rxn.metabolites.items():
            print(f"  {coeff:>7.1f} {met.id} ({met.name})")
        
        if rxn.annotation:
            print(f"\nAnnotations:")
            for key, value in rxn.annotation.items():
                print(f"  {key}: {value}")
        
        print(f"{'='*70}\n")
    
    def get_metabolite_details(self, metabolite_id: str):
        """Get detailed information about a metabolite."""
        try:
            met = self.model.metabolites.get_by_id(metabolite_id)
        except KeyError:
            print(f"Metabolite '{metabolite_id}' not found")
            return
        
        print(f"\n{'='*70}")
        print(f"METABOLITE: {met.id}")
        print(f"{'='*70}")
        print(f"Name:        {met.name}")
        print(f"Compartment: {met.compartment} ({self.model.compartments.get(met.compartment, 'Unknown')})")
        print(f"Formula:     {met.formula if met.formula else 'N/A'}")
        print(f"Charge:      {met.charge}")
        print(f"Reactions:   {len(met.reactions)}")
        
        print(f"\nUsed in reactions:")
        for rxn in list(met.reactions)[:10]:  # Show first 10
            coeff = rxn.metabolites[met]
            print(f"  {coeff:>7.1f} in {rxn.id}")
        
        if len(met.reactions) > 10:
            print(f"  ... and {len(met.reactions)-10} more")
        
        if met.annotation:
            print(f"\nAnnotations:")
            for key, value in met.annotation.items():
                print(f"  {key}: {value}")
        
        print(f"{'='*70}\n")
    
    def get_gene_details(self, gene_id: str):
        """Get detailed information about a gene."""
        try:
            gene = self.model.genes.get_by_id(gene_id)
        except KeyError:
            print(f"Gene '{gene_id}' not found")
            return
        
        print(f"\n{'='*70}")
        print(f"GENE: {gene.id}")
        print(f"{'='*70}")
        print(f"Name:        {gene.name if gene.name else 'N/A'}")
        print(f"Reactions:   {len(gene.reactions)}")
        
        if gene.reactions:
            print(f"\nAssociated reactions:")
            for rxn in list(gene.reactions)[:10]:
                print(f"  - {rxn.id} ({rxn.name})")
            
            if len(gene.reactions) > 10:
                print(f"  ... and {len(gene.reactions)-10} more")
        
        if gene.annotation:
            print(f"\nAnnotations:")
            for key, value in gene.annotation.items():
                print(f"  {key}: {value}")
        
        print(f"{'='*70}\n")
    
    def find_pathways(self, substrate_id: str, product_id: str, max_steps: int = 5):
        """Find pathways between two metabolites (simplified)."""
        try:
            substrate = self.model.metabolites.get_by_id(substrate_id)
            product = self.model.metabolites.get_by_id(product_id)
        except KeyError:
            print("One or both metabolites not found")
            return
        
        print(f"\nSearching for pathways from {substrate_id} to {product_id}...")
        
        # Simple BFS approach
        visited = {substrate_id}
        queue = [(substrate_id, [substrate_id])]
        paths = []
        
        while queue and len(paths) < 5:  # Find up to 5 paths
            current_met_id, path = queue.pop(0)
            
            if len(path) > max_steps + 1:
                continue
            
            try:
                current_met = self.model.metabolites.get_by_id(current_met_id)
            except KeyError:
                continue
            
            for rxn in current_met.reactions:
                for next_met in rxn.metabolites:
                    if next_met.id == product_id:
                        paths.append(path + [next_met.id])
                    elif next_met.id not in visited and len(path) < max_steps:
                        visited.add(next_met.id)
                        queue.append((next_met.id, path + [next_met.id]))
        
        if paths:
            print(f"Found {len(paths)} pathway(s):")
            for i, path in enumerate(paths, 1):
                print(f"  Path {i}: {' → '.join(path)}")
        else:
            print("No pathways found within the step limit")
    
    def find_reactions_by_subsystem(self, subsystem: str):
        """Find all reactions in a subsystem."""
        results = [
            r for r in self.model.reactions 
            if r.subsystem and subsystem.lower() in r.subsystem.lower()
        ]
        
        print(f"\nFound {len(results)} reactions in subsystem '{subsystem}':")
        for rxn in results[:20]:
            print(f"  {rxn.id:30s} - {rxn.name}")
        
        if len(results) > 20:
            print(f"  ... and {len(results)-20} more")
        
        return results
    
    def list_subsystems(self):
        """List all subsystems."""
        subsystems = set()
        for rxn in self.model.reactions:
            if rxn.subsystem:
                subsystems.add(rxn.subsystem)
        
        print(f"\nFound {len(subsystems)} subsystems:")
        for subsys in sorted(subsystems):
            count = sum(1 for r in self.model.reactions if r.subsystem == subsys)
            print(f"  {subsys:50s} ({count:>4} reactions)")
    
    def export_reaction(self, reaction_id: str, output_file: str = None):
        """Export reaction details to JSON."""
        try:
            rxn = self.model.reactions.get_by_id(reaction_id)
        except KeyError:
            print(f"Reaction '{reaction_id}' not found")
            return
        
        data = {
            'id': rxn.id,
            'name': rxn.name,
            'reaction': rxn.reaction,
            'reversible': rxn.reversibility,
            'bounds': [rxn.lower_bound, rxn.upper_bound],
            'subsystem': rxn.subsystem,
            'gene_reaction_rule': rxn.gene_reaction_rule,
            'genes': [g.id for g in rxn.genes],
            'metabolites': {met.id: coeff for met, coeff in rxn.metabolites.items()},
            'annotation': rxn.annotation if rxn.annotation else {}
        }
        
        if output_file is None:
            output_file = f"{reaction_id}_details.json"
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Exported to: {output_file}")
    
    def show_menu(self):
        """Show interactive menu."""
        menu = """
╔════════════════════════════════════════════════════════════════════════════╗
║                     RECON3D MODEL EXPLORER                                 ║
╚════════════════════════════════════════════════════════════════════════════╝

1. Search reactions (by ID or name)
2. Search metabolites (by ID or name)
3. Get reaction details
4. Get metabolite details
5. Get gene details
6. Find subsystems
7. Find reactions in subsystem
8. Find metabolite pathways
9. Export reaction details to JSON
0. Exit

"""
        print(menu)
    
    def interactive_mode(self):
        """Run interactive explorer."""
        if self.model is None:
            return
        
        print(f"Model: {self.model.id}")
        print(f"Reactions: {len(self.model.reactions)}")
        print(f"Metabolites: {len(self.model.metabolites)}")
        print(f"Genes: {len(self.model.genes)}\n")
        
        while True:
            self.show_menu()
            choice = input("Enter choice (0-9): ").strip()
            
            if choice == '0':
                print("Goodbye!")
                break
            
            elif choice == '1':
                query = input("Enter reaction ID or name to search: ").strip()
                if query:
                    self.search_reactions(query)
            
            elif choice == '2':
                query = input("Enter metabolite ID or name to search: ").strip()
                if query:
                    self.search_metabolites(query)
            
            elif choice == '3':
                rxn_id = input("Enter reaction ID: ").strip()
                if rxn_id:
                    self.get_reaction_details(rxn_id)
            
            elif choice == '4':
                met_id = input("Enter metabolite ID: ").strip()
                if met_id:
                    self.get_metabolite_details(met_id)
            
            elif choice == '5':
                gene_id = input("Enter gene ID: ").strip()
                if gene_id:
                    self.get_gene_details(gene_id)
            
            elif choice == '6':
                self.list_subsystems()
            
            elif choice == '7':
                subsys = input("Enter subsystem name: ").strip()
                if subsys:
                    self.find_reactions_by_subsystem(subsys)
            
            elif choice == '8':
                sub = input("Enter substrate metabolite ID: ").strip()
                prod = input("Enter product metabolite ID: ").strip()
                if sub and prod:
                    self.find_pathways(sub, prod)
            
            elif choice == '9':
                rxn_id = input("Enter reaction ID: ").strip()
                output = input("Enter output filename (leave blank for default): ").strip()
                if rxn_id:
                    self.export_reaction(rxn_id, output if output else None)
            
            input("\nPress Enter to continue...")


def main():
    """Main function."""
    explorer = ModelExplorer("Recon3D.xml")
    
    if explorer.model:
        explorer.interactive_mode()


if __name__ == '__main__':
    main()
