#!/usr/bin/env python3
"""
Example script demonstrating how to use the VMH annotator
and data annotation utilities.

This script shows various ways to annotate the Recon3D model.
"""

import logging
from pathlib import Path
import cobra
from vmh_annotator import VMHAnnotator, generate_html_report
from data_annotation import (
    CrossReferenceMapper,
    enrich_model_from_mappings,
    print_model_summary,
    save_annotation_report
)


def example_basic_annotation():
    """Example 1: Basic annotation using VMH API."""
    print("\n" + "="*60)
    print("Example 1: Basic VMH API Annotation")
    print("="*60 + "\n")
    
    # Load model
    model = cobra.io.read_sbml_model("Recon3D.xml")
    print_model_summary(model)
    
    # Create annotator and annotate
    annotator = VMHAnnotator(cache_responses=True)
    stats = annotator.annotate_model(model)
    
    # Print statistics
    annotator.print_stats()
    
    # Save annotated model
    output_path = "Recon3D_annotated_basic.xml"
    cobra.io.write_sbml_model(model, output_path)
    print(f"✓ Model saved to: {output_path}\n")


def example_with_cross_references():
    """Example 2: Annotation using cross-reference data."""
    print("\n" + "="*60)
    print("Example 2: Annotation with Cross-References")
    print("="*60 + "\n")
    
    # Load model
    model = cobra.io.read_sbml_model("Recon3D.xml")
    
    # Load cross-reference data
    mapper = CrossReferenceMapper()
    
    # Note: reac_xref.tsv is very large, we'll try to load it
    xref_file = "reac_xref.tsv"
    if Path(xref_file).exists():
        print(f"Loading cross-references from: {xref_file}")
        mapper.load_from_tsv(xref_file, entity_type='reaction')
        
        # Enrich model annotations
        enrich_model_from_mappings(model, mapper)
    else:
        print(f"Note: {xref_file} not found, skipping cross-reference enrichment")
    
    # Print summary
    print_model_summary(model)
    
    # Save annotated model
    output_path = "Recon3D_annotated_with_refs.xml"
    cobra.io.write_sbml_model(model, output_path)
    print(f"✓ Model saved to: {output_path}\n")


def example_full_annotation_with_report():
    """Example 3: Full annotation with HTML report."""
    print("\n" + "="*60)
    print("Example 3: Full Annotation with HTML Report")
    print("="*60 + "\n")
    
    # Load model
    model = cobra.io.read_sbml_model("Recon3D.xml")
    print_model_summary(model)
    
    # Create annotator
    annotator = VMHAnnotator(cache_responses=True)
    
    # Annotate model
    print("Annotating model with VMH API...")
    stats = annotator.annotate_model(model)
    
    # Print statistics
    annotator.print_stats()
    
    # Save annotated model
    model_output = "Recon3D_annotated_full.xml"
    cobra.io.write_sbml_model(model, model_output)
    print(f"✓ Model saved to: {model_output}")
    
    # Generate HTML report
    report_output = "annotation_report.html"
    generate_html_report(model, stats, Path(report_output))
    print(f"✓ Report saved to: {report_output}")
    
    # Save JSON report
    json_report = "annotation_report.json"
    save_annotation_report(model, json_report)
    print(f"✓ JSON report saved to: {json_report}\n")


def example_selective_annotation():
    """Example 4: Selective annotation of specific reactions/metabolites."""
    print("\n" + "="*60)
    print("Example 4: Selective Annotation")
    print("="*60 + "\n")
    
    # Load model
    model = cobra.io.read_sbml_model("Recon3D.xml")
    
    # Create annotator
    annotator = VMHAnnotator(cache_responses=True)
    
    # Annotate only first 10 reactions as example
    print("Annotating first 10 reactions...\n")
    for i, reaction in enumerate(model.reactions[:10]):
        annotator.annotate_reaction(reaction)
        print(f"  {i+1}. {reaction.id}: {reaction.name}")
    
    # Print statistics
    stats = annotator.get_stats()
    print(f"\nAnnotated {stats['reactions_annotated']} reactions")
    print(f"API calls: {stats['api_calls']}")
    print(f"API errors: {stats['api_errors']}\n")


def main():
    """Run all examples."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("Recon3D Annotation Examples")
    print("="*60)
    
    # Run examples
    try:
        # Uncomment the examples you want to run
        
        # Example 1: Basic annotation
        example_basic_annotation()
        
        # Example 2: With cross-references
        # example_with_cross_references()
        
        # Example 3: Full annotation with HTML report
        # example_full_annotation_with_report()
        
        # Example 4: Selective annotation
        # example_selective_annotation()
        
        print("\n" + "="*60)
        print("All examples completed!")
        print("="*60 + "\n")
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("Please ensure Recon3D.xml exists in the current directory")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise


if __name__ == '__main__':
    main()
