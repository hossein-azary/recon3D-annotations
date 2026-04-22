#!/usr/bin/env python3
"""
VMH API Annotator for Recon3D-like metabolic models

This script annotates a Recon3D-like genome-scale metabolic model (GEM)
using the VMH (Virtual Metabolic Human) API.

It retrieves annotations for reactions, metabolites, and genes from external
databases and adds them to the model.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import cobra
import requests
from tqdm import tqdm


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VMHAnnotator:
    """Annotates metabolic models using the VMH API."""
    
    # VMH API endpoints
    VMH_API_BASE = "https://delta.vmh.life/api"
    
    # Database mapping for different entity types
    REACTION_DBS = {
        'rhea': 'rhea',
        'kegg': 'kegg.reaction',
        'metacyc': 'metacyc.reaction',
        'reactome': 'reactome.reaction',
        'seed': 'seed.reaction',
        'bigg': 'bigg.reaction',
        'ec': 'ec-code',
        'sbo': 'SBO'
    }
    
    METABOLITE_DBS = {
        'chebi': 'chebi.metabolite',
        'kegg': 'kegg.compound',
        'bigg': 'bigg.metabolite',
        'inchi': 'inchi',
        'inchikey': 'inchikey',
        'smiles': 'smiles',
        'formula': 'formula',
        'charge': 'charge',
        'sbo': 'SBO'
    }
    
    GENE_DBS = {
        'ncbi': 'ncbi.geneid',
        'uniprot': 'uniprot',
        'ensembl': 'ensembl',
        'sbo': 'SBO'
    }
    
    def __init__(self, cache_responses: bool = True):
        """
        Initialize the annotator.
        
        Args:
            cache_responses: Whether to cache API responses to avoid redundant calls
        """
        self.cache_responses = cache_responses
        self.response_cache = {}
        self.stats = {
            'reactions_annotated': 0,
            'metabolites_annotated': 0,
            'genes_annotated': 0,
            'api_calls': 0,
            'api_errors': 0
        }
    
    def _get_from_vmh(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make a request to the VMH API.
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            
        Returns:
            JSON response or None if error
        """
        # Check cache
        cache_key = f"{endpoint}:{json.dumps(params or {}, sort_keys=True)}"
        if self.cache_responses and cache_key in self.response_cache:
            return self.response_cache[cache_key]
        
        try:
            url = f"{self.VMH_API_BASE}{endpoint}"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            self.stats['api_calls'] += 1
            
            if self.cache_responses:
                self.response_cache[cache_key] = data
            
            return data
        except requests.RequestException as e:
            logger.warning(f"VMH API error for {endpoint}: {e}")
            self.stats['api_errors'] += 1
            return None
    
    def annotate_reaction(self, reaction: cobra.Reaction) -> bool:
        """
        Annotate a single reaction using VMH API.
        
        Args:
            reaction: COBRApy reaction object
            
        Returns:
            True if annotation was added, False otherwise
        """
        if reaction.annotation is None:
            reaction.annotation = {}
        
        # Try to get annotation using reaction ID or name
        annotated = False
        
        # Check for existing BiGG or MetaNetX identifiers
        existing_ids = reaction.annotation.copy()
        
        # Query VMH for reaction data
        try:
            # Try searching by BiGG ID if available
            if 'bigg.reaction' in existing_ids:
                bigg_id = existing_ids['bigg.reaction']
                vmh_data = self._get_from_vmh(f"/reactions/{bigg_id}")
                if vmh_data and 'data' in vmh_data:
                    reaction_data = vmh_data['data']
                    
                    # Add annotations from VMH response
                    if 'references' in reaction_data:
                        for ref_type, ref_value in reaction_data['references'].items():
                            if ref_type in self.REACTION_DBS:
                                reaction.annotation[self.REACTION_DBS[ref_type]] = ref_value
                                annotated = True
            
            # Add EC code if found in name or comments
            if 'ec-code' not in reaction.annotation:
                if 'EC' in reaction.name or 'EC' in reaction.notes:
                    # Try to extract EC code from name/notes
                    import re
                    ec_pattern = r'\b(\d+\.\d+\.\d+\.(?:\d+|-|n))\b'
                    match = re.search(ec_pattern, reaction.name + ' ' + str(reaction.notes))
                    if match:
                        reaction.annotation['ec-code'] = match.group(1)
                        annotated = True
            
            # Add SBO term for reaction classification
            if 'SBO' not in reaction.annotation:
                reaction_type = self._classify_reaction(reaction)
                if reaction_type:
                    reaction.annotation['SBO'] = reaction_type
                    annotated = True
            
            if annotated:
                self.stats['reactions_annotated'] += 1
        
        except Exception as e:
            logger.debug(f"Error annotating reaction {reaction.id}: {e}")
        
        return annotated
    
    def annotate_metabolite(self, metabolite: cobra.Metabolite) -> bool:
        """
        Annotate a single metabolite using VMH API.
        
        Args:
            metabolite: COBRApy metabolite object
            
        Returns:
            True if annotation was added, False otherwise
        """
        if metabolite.annotation is None:
            metabolite.annotation = {}
        
        annotated = False
        
        try:
            # Query by BiGG ID
            if 'bigg.metabolite' in metabolite.annotation:
                bigg_id = metabolite.annotation['bigg.metabolite']
                vmh_data = self._get_from_vmh(f"/metabolites/{bigg_id}")
                
                if vmh_data and 'data' in vmh_data:
                    met_data = vmh_data['data']
                    
                    # Add cross-references
                    if 'references' in met_data:
                        for ref_type, ref_value in met_data['references'].items():
                            if ref_type in self.METABOLITE_DBS:
                                metabolite.annotation[self.METABOLITE_DBS[ref_type]] = ref_value
                                annotated = True
                    
                    # Add chemical formula if not present
                    if 'formula' not in metabolite.annotation and 'formula' in met_data:
                        metabolite.annotation['formula'] = met_data['formula']
                        annotated = True
                    
                    # Add charge if not present
                    if 'charge' not in metabolite.annotation and 'charge' in met_data:
                        metabolite.annotation['charge'] = str(met_data['charge'])
                        annotated = True
            
            # Add SBO term
            if 'SBO' not in metabolite.annotation:
                metabolite.annotation['SBO'] = 'SBO:0000247'  # Simple chemical
                annotated = True
            
            if annotated:
                self.stats['metabolites_annotated'] += 1
        
        except Exception as e:
            logger.debug(f"Error annotating metabolite {metabolite.id}: {e}")
        
        return annotated
    
    def annotate_gene(self, gene: cobra.Gene) -> bool:
        """
        Annotate a single gene using VMH API.
        
        Args:
            gene: COBRApy gene object
            
        Returns:
            True if annotation was added, False otherwise
        """
        if gene.annotation is None:
            gene.annotation = {}
        
        annotated = False
        
        try:
            # Extract gene ID and look for NCBI/UniProt IDs
            gene_id = gene.id
            
            # Check for existing NCBI ID
            if 'ncbi.geneid' not in gene.annotation and gene_id:
                # Try to use gene ID directly if it looks like a gene identifier
                if gene_id.startswith('G_') or any(c.isdigit() for c in gene_id):
                    gene.annotation['ncbi.geneid'] = gene_id
                    annotated = True
            
            # Add SBO term for gene
            if 'SBO' not in gene.annotation:
                gene.annotation['SBO'] = 'SBO:0000243'  # Protein
                annotated = True
            
            if annotated:
                self.stats['genes_annotated'] += 1
        
        except Exception as e:
            logger.debug(f"Error annotating gene {gene.id}: {e}")
        
        return annotated
    
    def _classify_reaction(self, reaction: cobra.Reaction) -> Optional[str]:
        """
        Classify a reaction based on its name and properties.
        
        Returns:
            SBO term for the reaction or None
        """
        name_lower = reaction.name.lower()
        
        # Map common reaction types to SBO terms
        if 'transport' in name_lower or 'antiport' in name_lower or 'symport' in name_lower:
            return 'SBO:0000655'  # Transport reaction
        elif 'dehydrogenase' in name_lower:
            return 'SBO:0000657'  # Oxidoreductase reaction
        elif 'kinase' in name_lower:
            return 'SBO:0000661'  # Phosphorylation
        elif 'phosphatase' in name_lower:
            return 'SBO:0000330'  # Dephosphorylation
        elif 'isomerase' in name_lower:
            return 'SBO:0000659'  # Isomerization
        elif 'ligase' in name_lower:
            return 'SBO:0000662'  # Ligase
        elif 'hydrolase' in name_lower:
            return 'SBO:0000658'  # Hydrolysis
        
        # Default to generic biochemical reaction
        return 'SBO:0000167'
    
    def annotate_model(self, model: cobra.Model) -> Dict:
        """
        Annotate all reactions, metabolites, and genes in a model.
        
        Args:
            model: COBRApy model object
            
        Returns:
            Statistics dictionary
        """
        logger.info(f"Starting annotation of model: {model.id}")
        logger.info(f"  Reactions: {len(model.reactions)}")
        logger.info(f"  Metabolites: {len(model.metabolites)}")
        logger.info(f"  Genes: {len(model.genes)}")
        
        # Annotate reactions
        logger.info("Annotating reactions...")
        for reaction in tqdm(model.reactions, desc="Reactions"):
            self.annotate_reaction(reaction)
        
        # Annotate metabolites
        logger.info("Annotating metabolites...")
        for metabolite in tqdm(model.metabolites, desc="Metabolites"):
            self.annotate_metabolite(metabolite)
        
        # Annotate genes
        logger.info("Annotating genes...")
        for gene in tqdm(model.genes, desc="Genes"):
            self.annotate_gene(gene)
        
        logger.info("Annotation complete!")
        return self.stats
    
    def get_stats(self) -> Dict:
        """Get annotation statistics."""
        return self.stats.copy()
    
    def print_stats(self):
        """Print annotation statistics."""
        print("\n" + "="*60)
        print("ANNOTATION STATISTICS")
        print("="*60)
        print(f"Reactions annotated:    {self.stats['reactions_annotated']}")
        print(f"Metabolites annotated:  {self.stats['metabolites_annotated']}")
        print(f"Genes annotated:        {self.stats['genes_annotated']}")
        print(f"API calls made:         {self.stats['api_calls']}")
        print(f"API errors:             {self.stats['api_errors']}")
        print("="*60 + "\n")


def generate_html_report(model: cobra.Model, stats: Dict, output_path: Path):
    """
    Generate an HTML report with annotation statistics.
    
    Args:
        model: Annotated COBRApy model
        stats: Annotation statistics
        output_path: Path to save HTML report
    """
    # Count entities with annotations
    reactions_with_annotations = sum(
        1 for r in model.reactions 
        if r.annotation and len(r.annotation) > 0
    )
    metabolites_with_annotations = sum(
        1 for m in model.metabolites 
        if m.annotation and len(m.annotation) > 0
    )
    genes_with_annotations = sum(
        1 for g in model.genes 
        if g.annotation and len(g.annotation) > 0
    )
    
    # Calculate annotation coverage
    reaction_coverage = (reactions_with_annotations / len(model.reactions) * 100) if model.reactions else 0
    metabolite_coverage = (metabolites_with_annotations / len(model.metabolites) * 100) if model.metabolites else 0
    gene_coverage = (genes_with_annotations / len(model.genes) * 100) if model.genes else 0
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Recon3D Model Annotation Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
            .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
            .container {{ background-color: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .stat-box {{ display: inline-block; margin: 10px; padding: 15px; background-color: #ecf0f1; border-left: 4px solid #3498db; border-radius: 3px; }}
            .stat-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
            .stat-label {{ font-size: 12px; color: #7f8c8d; text-transform: uppercase; }}
            .progress-bar {{ width: 100%; height: 30px; background-color: #ecf0f1; border-radius: 3px; overflow: hidden; margin: 10px 0; }}
            .progress {{ height: 100%; background-color: #27ae60; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th {{ background-color: #34495e; color: white; padding: 10px; text-align: left; }}
            td {{ padding: 10px; border-bottom: 1px solid #ecf0f1; }}
            tr:hover {{ background-color: #ecf0f1; }}
            .footer {{ color: #7f8c8d; font-size: 12px; text-align: center; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Recon3D Model Annotation Report</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="container">
            <h2>Model Summary</h2>
            <div class="stat-box">
                <div class="stat-value">{len(model.reactions)}</div>
                <div class="stat-label">Reactions</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{len(model.metabolites)}</div>
                <div class="stat-label">Metabolites</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{len(model.genes)}</div>
                <div class="stat-label">Genes</div>
            </div>
        </div>
        
        <div class="container">
            <h2>Annotation Coverage</h2>
            
            <h3>Reactions</h3>
            <div class="progress-bar">
                <div class="progress" style="width: {reaction_coverage}%">
                    {reaction_coverage:.1f}%
                </div>
            </div>
            <p>{reactions_with_annotations} / {len(model.reactions)} reactions annotated</p>
            
            <h3>Metabolites</h3>
            <div class="progress-bar">
                <div class="progress" style="width: {metabolite_coverage}%">
                    {metabolite_coverage:.1f}%
                </div>
            </div>
            <p>{metabolites_with_annotations} / {len(model.metabolites)} metabolites annotated</p>
            
            <h3>Genes</h3>
            <div class="progress-bar">
                <div class="progress" style="width: {gene_coverage}%">
                    {gene_coverage:.1f}%
                </div>
            </div>
            <p>{genes_with_annotations} / {len(model.genes)} genes annotated</p>
        </div>
        
        <div class="container">
            <h2>Annotation Statistics</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Count</th>
                </tr>
                <tr>
                    <td>Reactions Annotated</td>
                    <td>{stats.get('reactions_annotated', 0)}</td>
                </tr>
                <tr>
                    <td>Metabolites Annotated</td>
                    <td>{stats.get('metabolites_annotated', 0)}</td>
                </tr>
                <tr>
                    <td>Genes Annotated</td>
                    <td>{stats.get('genes_annotated', 0)}</td>
                </tr>
                <tr>
                    <td>API Calls Made</td>
                    <td>{stats.get('api_calls', 0)}</td>
                </tr>
                <tr>
                    <td>API Errors</td>
                    <td>{stats.get('api_errors', 0)}</td>
                </tr>
            </table>
        </div>
        
        <div class="footer">
            <p>Generated by Recon3D Annotator using VMH API</p>
        </div>
    </body>
    </html>
    """
    
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    logger.info(f"HTML report generated: {output_path}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Annotate Recon3D-like metabolic models using the VMH API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Annotate a model with default settings
  python vmh_annotator.py Recon3D.xml

  # Annotate and save with custom output name
  python vmh_annotator.py Recon3D.xml -o Recon3D_annotated.xml

  # Generate HTML report
  python vmh_annotator.py Recon3D.xml --report report.html

  # Disable caching for fresh API calls
  python vmh_annotator.py Recon3D.xml --no-cache
        """
    )
    
    parser.add_argument(
        'model',
        help='Path to the SBML model file (e.g., Recon3D.xml)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output file path for annotated model (default: {input}_annotated.xml)',
        default=None
    )
    
    parser.add_argument(
        '--report',
        help='Generate HTML report at specified path',
        default=None
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable API response caching'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Verify input file exists
    model_path = Path(args.model)
    if not model_path.exists():
        logger.error(f"Model file not found: {args.model}")
        sys.exit(1)
    
    # Set default output path
    if args.output is None:
        output_path = model_path.with_stem(f"{model_path.stem}_annotated")
    else:
        output_path = Path(args.output)
    
    try:
        # Load model
        logger.info(f"Loading model from: {model_path}")
        model = cobra.io.read_sbml_model(str(model_path))
        logger.info(f"Model loaded: {model.id}")
        
        # Create annotator and annotate model
        annotator = VMHAnnotator(cache_responses=not args.no_cache)
        stats = annotator.annotate_model(model)
        
        # Print statistics
        annotator.print_stats()
        
        # Save annotated model
        logger.info(f"Saving annotated model to: {output_path}")
        cobra.io.write_sbml_model(model, str(output_path))
        logger.info("Model saved successfully!")
        
        # Generate HTML report if requested
        if args.report:
            generate_html_report(model, stats, Path(args.report))
        
        logger.info("Annotation complete!")
        
    except Exception as e:
        logger.error(f"Error during annotation: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
