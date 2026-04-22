# Model Statistics & Analysis Scripts

A collection of Python scripts for understanding and exploring the Recon3D metabolic model.

## 📋 Available Scripts

### 1. **quick_analysis.py** - Quick Overview
**Best for:** Getting a fast summary of model statistics

```bash
python quick_analysis.py
```

**Output includes:**
- Basic model information (reactions, metabolites, genes)
- Reaction breakdown (reversible, boundary, exchange, transport)
- Metabolite statistics
- Gene information
- Annotation coverage
- Compartment information
- Top subsystems
- Annotation types
- Metabolite/gene counts per reaction
- Summary table
- JSON export (model_summary.json)

**Example output:**
```
╔════════════════════════════════════════════════════════════════════════════╗
║                     RECON3D MODEL QUICK ANALYSIS                           ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 BASIC INFORMATION
────────────────────────────────────────────────────────────────────────────
  Model ID:              Recon3D
  Reactions:                 9,000
  Metabolites:               8,000
  Genes:                     6,000
  Compartments:                  9

⚗️ REACTION BREAKDOWN
────────────────────────────────────────────────────────────────────────────
  Total:                     9,000
  Reversible:                5,000 ( 55.6%)
  Boundary:                  1,000 ( 11.1%)
  Exchange:                    500 ( 5.6%)
  Transport:                   800 ( 8.9%)
...
```

---

### 2. **model_stats.py** - Detailed Analysis
**Best for:** Comprehensive model analysis with all details

```bash
python model_stats.py
```

**Output includes:**
- Basic statistics
- Compartment details
- Reaction statistics
  - Types (reversible, boundary, exchange, transport)
  - Reactions with gene associations
  - Annotation coverage
- Metabolite statistics
  - Per compartment breakdown
  - Charged vs uncharged
  - With/without formulas
  - Annotation coverage
- Gene statistics
  - Used vs unused genes
  - Genes per reaction
  - Annotation coverage
- Example reactions (first 5)
- Example metabolites (first 5)
- Example genes (first 5)
- Annotation summary by type
- Mass balance information
- JSON export (model_stats.json)

**Example sections:**
```
======================================================================
BASIC MODEL STATISTICS
======================================================================
Model ID:           Recon3D
Total Reactions:              9000
Total Metabolites:            8000
Total Genes:                  6000
Total Compartments:              9
======================================================================

======================================================================
EXAMPLE REACTIONS (first 3)
======================================================================

1. R_ACALD
   Name:      Acetaldehyde dehydrogenase
   Reversible: True
   Equation:  acald_c + nad_c + h2o_c <=> ac_c + nadh_c + 2.0 h_c
   GPR:       G_ADH1 or G_ADH2
   Bounds:    [-1000.0, 1000.0]
   Annotations: ['rhea.reaction', 'kegg.reaction', 'ec-code', 'SBO']
...
```

---

### 3. **model_explorer.py** - Interactive Explorer
**Best for:** Searching and exploring specific model components

```bash
python model_explorer.py
```

**Interactive menu options:**

```
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
```

**Example commands:**

```bash
# Search for a reaction
Enter choice: 1
Enter reaction ID or name: phosphofructokinase
Found 5 reactions matching 'phosphofructokinase':
  R_PFK → Phosphofructokinase
  R_PFK_2 → Phosphofructokinase 2
  ...

# Get reaction details
Enter choice: 3
Enter reaction ID: R_PFK
═════════════════════════════════════════════════════════════════════════════
REACTION: R_PFK
═════════════════════════════════════════════════════════════════════════════
Name:        Phosphofructokinase
Equation:    f6p_c + atp_c ⇄ fdp_c + adp_c + h_c
Reversible:  True
Bounds:      [-1000, 1000]
Subsystem:   Glycolysis
Gene Reaction Rule: ENSG00000067057
...

# Find subsystems
Enter choice: 6
Found 115 subsystems:
  Glycolysis                                  (  12 reactions)
  Citric acid cycle                           (  10 reactions)
  Fatty acid synthesis                        (  18 reactions)
  ...
```

---

## 🚀 Usage Examples

### Example 1: Quick Model Overview
```bash
# Get a fast summary with nice formatting
python quick_analysis.py

# This generates: model_summary.json
```

### Example 2: Detailed Analysis Report
```bash
# Get comprehensive statistics and examples
python model_stats.py

# This generates: model_stats.json
```

### Example 3: Explore a Specific Reaction
```bash
python model_explorer.py
# Then select option 3 and enter reaction ID like "R_PFK"
```

### Example 4: Find Pathways Between Metabolites
```bash
python model_explorer.py
# Then select option 8 and enter two metabolite IDs
# e.g., glucose → pyruvate
```

### Example 5: List All Reactions in a Pathway
```bash
python model_explorer.py
# Then select option 7 and enter subsystem like "Glycolysis"
```

---

## 📊 Output Files Generated

| Script | Output File | Format | Content |
|--------|------------|--------|---------|
| quick_analysis.py | model_summary.json | JSON | Summary statistics |
| model_stats.py | model_stats.json | JSON | Detailed statistics |
| model_explorer.py | *_details.json | JSON | Exported reaction details |

---

## 🎯 What Each Script Shows

### quick_analysis.py (⚡ Fastest)
```
✓ Model size overview
✓ Reaction types breakdown
✓ Metabolite properties
✓ Gene statistics
✓ Annotation coverage
✓ Top subsystems
✓ Pretty formatted table
```

### model_stats.py (📊 Most Detailed)
```
✓ All info from quick_analysis
✓ Examples of reactions/metabolites/genes
✓ Annotation types breakdown
✓ Mass balance info
✓ Detailed statistics
✓ JSON export for programmatic use
```

### model_explorer.py (🔍 Interactive)
```
✓ Search reactions/metabolites
✓ Get detailed entity information
✓ Find pathways between metabolites
✓ List subsystems
✓ Export specific data to JSON
✓ Explore relationships
```

---

## 💡 Quick Tips

### Tip 1: Get Quick Stats
```bash
python quick_analysis.py
```
Takes 10 seconds, shows summary in nice format.

### Tip 2: Get All Details
```bash
python model_stats.py | head -100
```
See first 100 lines of detailed analysis.

### Tip 3: Search for a Reaction
```bash
python model_explorer.py
# Enter option 1, then search term
```

### Tip 4: Analyze with Python
```python
import cobra
model = cobra.io.read_sbml_model("Recon3D.xml")
reaction = model.reactions.get_by_id("R_PFK")
print(reaction.reaction)  # See the equation
```

---

## 📈 Understanding the Output

### Model Size
```
Reactions:     ~9,000    ← Biochemical reactions
Metabolites:   ~8,000    ← Chemical compounds
Genes:         ~6,000    ← Genetic information
Compartments:      9     ← Cellular locations
```

### Reaction Types
```
Reversible:    Reactions that can go both directions (↔)
Boundary:      Reactions at model boundary
Exchange:      Input/output reactions (EX_)
Transport:     Movement of metabolites between compartments
```

### Annotation Coverage
```
70% annotated = 70% of items have database references
```

### Subsystems
```
Pathways/modules that reactions belong to
e.g., Glycolysis, Krebs Cycle, Fatty Acid Synthesis
```

---

## 🔧 Requirements

All scripts require:
- Python 3.8+
- COBRApy (install: `pip install cobra`)

Install if needed:
```bash
pip install cobra
```

---

## 📝 Examples of What You Can Learn

### Quick Facts
- How many reactions in glycolysis? → Use model_explorer, option 7
- Which genes are involved in a reaction? → Use model_explorer, option 3
- What metabolites are charged? → Use quick_analysis.py
- Annotation coverage? → Use quick_analysis.py

### Detailed Analysis
- Top annotation types? → Use model_stats.py
- Subsystem breakdown? → Use quick_analysis.py
- Examples of model entities? → Use model_stats.py
- Mass balance status? → Use model_stats.py

### Interactive Exploration
- Search for specific reaction? → Use model_explorer, option 1
- Find pathways? → Use model_explorer, option 8
- Get reaction details? → Use model_explorer, option 3
- Export data? → Use model_explorer, option 9

---

## 🎓 Advanced Usage

### Export Specific Reactions
```bash
python model_explorer.py
# Option 9: Export reaction details to JSON
# Useful for creating reports
```

### Combine Scripts
```bash
# Get quick overview
python quick_analysis.py

# Then explore specific items
python model_explorer.py
```

### Parse Output JSON
```python
import json

# Load summary
with open('model_summary.json') as f:
    summary = json.load(f)

print(f"Total reactions: {summary['num_reactions']}")
print(f"Top subsystem: {list(summary['subsystems'].keys())[0]}")
```

---

## ❓ FAQ

**Q: Which script should I run first?**
A: Start with `python quick_analysis.py` for a quick overview, then use `model_explorer.py` to explore specific items.

**Q: Can I automate these scripts?**
A: Yes! The JSON exports can be parsed by other scripts or tools.

**Q: How long do they take?**
A: quick_analysis.py: ~10 sec, model_stats.py: ~20 sec, model_explorer.py: interactive

**Q: Can I use this data for my analyses?**
A: Yes! The JSON files contain all statistics you might need.

**Q: What if I want custom analysis?**
A: Look at the scripts for examples and write your own analysis using COBRApy.

---

## 🚀 Get Started Now

```bash
# Quick overview (fastest)
python quick_analysis.py

# Detailed analysis
python model_stats.py

# Interactive exploration
python model_explorer.py
```

Enjoy exploring your metabolic model! 🧬
