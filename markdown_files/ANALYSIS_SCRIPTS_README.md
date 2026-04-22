# 🧬 Model Analysis Scripts - Complete Guide

A comprehensive collection of Python scripts for understanding, analyzing, and exploring the Recon3D metabolic model.

## 📚 Scripts Overview

| Script | Purpose | Speed | Use Case |
|--------|---------|-------|----------|
| **quick_analysis.py** | Fast overview with statistics | ⚡ 10 sec | Quick summary |
| **model_stats.py** | Detailed analysis with examples | 📊 20 sec | Comprehensive report |
| **model_explorer.py** | Interactive search & exploration | 🔍 Manual | Specific queries |
| **analysis_examples.py** | Code examples for common tasks | 📖 30 sec | Learning & templates |

---

## 🚀 Quick Start

### Run Them Right Now!

```bash
# Option 1: Quick summary (fastest)
python quick_analysis.py

# Option 2: Detailed analysis
python model_stats.py

# Option 3: Interactive explorer
python model_explorer.py

# Option 4: See code examples
python analysis_examples.py
```

---

## 📋 Script Details

### 1. **quick_analysis.py** ⚡
**Best for:** Getting a quick summary

```bash
python quick_analysis.py
```

**What you get:**
```
✓ Model dimensions (reactions, metabolites, genes)
✓ Reaction types (reversible, boundary, exchange, transport)
✓ Metabolite properties (charged, with formula)
✓ Gene statistics
✓ Annotation coverage percentages
✓ Top 10 subsystems
✓ Annotation types breakdown
✓ Pretty formatted table
✓ JSON export (model_summary.json)
```

**Output time:** ~10 seconds

---

### 2. **model_stats.py** 📊
**Best for:** Comprehensive analysis

```bash
python model_stats.py
```

**What you get:**
```
✓ Everything from quick_analysis
✓ Example reactions (name, equation, genes)
✓ Example metabolites (formula, charge, compartment)
✓ Example genes (names, reaction count)
✓ Annotation summary by type
✓ Mass balance information
✓ Detailed statistics
✓ JSON export (model_stats.json)
```

**Output time:** ~20 seconds

---

### 3. **model_explorer.py** 🔍
**Best for:** Interactive exploration

```bash
python model_explorer.py
```

**Interactive Menu:**
```
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

**Example session:**
```bash
python model_explorer.py
Enter choice: 1
Enter reaction ID or name: glucose
Found 12 reactions matching 'glucose'...

Enter choice: 3
Enter reaction ID: R_HK1
═════════════════════════════════════════
REACTION: R_HK1
Name: Hexokinase
Equation: glc_c + atp_c ⇄ g6p_c + adp_c + h_c
...
```

---

### 4. **analysis_examples.py** 📖
**Best for:** Learning by example

```bash
python analysis_examples.py
```

**Examples included:**
```
✓ Example 1: Basic model properties
✓ Example 2: Find and examine reactions
✓ Example 3: Find metabolites
✓ Example 4: Get all reactions in pathway
✓ Example 5: Gene-reaction relationships
✓ Example 6: Count reactions by type
✓ Example 7: Metabolites in compartment
✓ Example 8: Check annotation coverage
✓ Example 9: Metabolite properties
✓ Example 10: Search for patterns
```

Output shows actual code and results you can copy/modify.

---

## 💡 Common Use Cases & Solutions

### "I want a quick summary"
```bash
python quick_analysis.py
```
Takes 10 seconds, shows formatted table with all key stats.

### "I need a detailed report"
```bash
python model_stats.py
```
Takes 20 seconds, shows everything including examples.

### "I want to search for a reaction"
```bash
python model_explorer.py
# Then select option 1 or 3
```

### "I want to find all reactions in Glycolysis"
```bash
python model_explorer.py
# Then select option 7
# Enter "Glycolysis"
```

### "I want to understand the model structure"
```bash
python analysis_examples.py
```
Shows 10 code examples you can adapt.

### "I want to find ATP-consuming reactions"
Copy Example 10 from analysis_examples.py and modify.

### "I want to export data"
```bash
python model_explorer.py
# Option 9 to export reaction details
```

---

## 📊 Sample Output

### quick_analysis.py Output:
```
╔════════════════════════════════════════════════════════════════════════════╗
║                     RECON3D MODEL QUICK ANALYSIS                           ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 BASIC INFORMATION
────────────────────────────────────────────────────────────────────────────
  Model ID:              Recon3D
  Reactions:             9,000
  Metabolites:           8,000
  Genes:                 6,000
  Compartments:              9

⚗️ REACTION BREAKDOWN
────────────────────────────────────────────────────────────────────────────
  Total:                 9,000
  Reversible:            5,500 ( 61.1%)
  Boundary:              1,200 ( 13.3%)
  Exchange:                650 ( 7.2%)
  Transport:               850 ( 9.4%)

[... more sections ...]

✓ Summary saved to: model_summary.json
```

### model_explorer.py Output:
```
═════════════════════════════════════════════════════════════════════════════
REACTION: R_PFK
═════════════════════════════════════════════════════════════════════════════
Name:        Phosphofructokinase
Equation:    f6p_c + atp_c <=> fdp_c + adp_c + h_c
Reversible:  True
Bounds:      [-1000.0, 1000.0]
Boundary:    False
Subsystem:   Glycolysis/Gluconeogenesis
Gene Reaction Rule: (G_ENSG00000067057)

Genes (1):
  - ENSG00000067057

Metabolites:
  1.0 f6p_c (Fructose 6-phosphate (cytoplasm))
  1.0 atp_c (ATP (cytoplasm))
 -1.0 fdp_c (Fructose 1,6-bisphosphate (cytoplasm))
 -1.0 adp_c (ADP (cytoplasm))
 -1.0 h_c (H+ (cytoplasm))

Annotations:
  rhea.reaction: RHEA:15421
  kegg.reaction: R01070
  ec-code: 2.7.1.11
═════════════════════════════════════════════════════════════════════════════
```

---

## 🎯 What You'll Learn

### About Model Size
- Total reactions, metabolites, genes
- Distribution across compartments
- Boundary vs internal reactions

### About Reaction Types
- Reversible vs irreversible
- Exchange reactions
- Transport reactions
- By subsystem/pathway

### About Metabolites
- Chemical properties (charge, formula)
- Compartment distribution
- Usage frequency
- Annotation coverage

### About Genes
- Gene-reaction associations
- Used vs unused genes
- Annotation status

### About Annotations
- Coverage percentages
- Annotation types present
- Database references

---

## 📁 Generated Output Files

| Script | Output File | Format | Size |
|--------|------------|--------|------|
| quick_analysis.py | model_summary.json | JSON | ~5 KB |
| model_stats.py | model_stats.json | JSON | ~10 KB |
| model_explorer.py | *_details.json | JSON | Varies |

---

## 🔧 Requirements

```bash
# Required packages
pip install cobra requests

# Or use requirements.txt
pip install -r requirements.txt
```

All scripts require:
- Python 3.8+
- COBRApy library
- Recon3D.xml file

---

## 📖 Reading the Output

### Percentages
```
85% annotated = 85 out of 100 have annotations
```

### Metabolites per Reaction
```
Min: 1, Max: 50, Avg: 5.5
= reactions have anywhere from 1-50 metabolites
= average reaction has ~5.5 metabolites
```

### Subsystems
```
Pathways like Glycolysis, Krebs Cycle, Fatty Acid Synthesis
= functional categories of reactions
```

---

## 💻 Code Snippets You Can Use

All available in `analysis_examples.py`:

```python
# Load model
import cobra
model = cobra.io.read_sbml_model("Recon3D.xml")

# Get a reaction
reaction = model.reactions.get_by_id("R_PFK")

# Find metabolites
glucose = [m for m in model.metabolites if 'glucose' in m.name.lower()]

# Count by type
transport = sum(1 for r in model.reactions if 'transport' in r.name.lower())

# Get annotation coverage
annotated = sum(1 for r in model.reactions if r.annotation)
coverage = annotated / len(model.reactions) * 100
```

---

## 🎓 Learning Path

### Beginner
1. Run `quick_analysis.py` → Get overview
2. Read output carefully → Understand model
3. Run `model_explorer.py` → Explore specific items

### Intermediate
1. Run `analysis_examples.py` → See code
2. Modify examples → Your own analysis
3. Check JSON outputs → Parse programmatically

### Advanced
1. Use COBRApy directly → Custom analysis
2. Combine scripts → Powerful workflows
3. Export data → Integration with other tools

---

## ❓ FAQ

**Q: Which script should I run first?**
A: `quick_analysis.py` for 10-second overview

**Q: Can I use these with other tools?**
A: Yes! JSON exports can be imported to other tools

**Q: How can I modify the scripts?**
A: See `analysis_examples.py` for templates

**Q: Do I need internet?**
A: No, all scripts work locally with just the model file

**Q: Can I run them in a script?**
A: Yes, import and call functions

**Q: Where can I learn more?**
A: See MODEL_ANALYSIS_GUIDE.md

---

## 🚀 Advanced Usage

### Batch Processing
```python
from quick_analysis import quick_analysis
import os

for model_file in os.listdir("."):
    if model_file.endswith(".xml"):
        quick_analysis(model_file)
```

### Parse Results
```python
import json

with open('model_summary.json') as f:
    stats = json.load(f)

print(f"Total reactions: {stats['num_reactions']}")
```

### Custom Analysis
```python
from analysis_examples import *
import cobra

model = cobra.io.read_sbml_model("Recon3D.xml")
# Now write your own analysis!
```

---

## 📞 Getting Help

### Stuck?
1. Try `python script.py -h` (if available)
2. Check MODEL_ANALYSIS_GUIDE.md
3. Look at analysis_examples.py for code
4. Check inline comments in scripts

### Want to Learn More?
1. Read inline comments in scripts
2. Check docstrings: `python -c "import script; help(script)"`
3. Modify analysis_examples.py
4. Visit COBRApy documentation

---

## ✨ What Makes These Scripts Great

✅ **Easy to Use** - Just run them, see results  
✅ **Comprehensive** - Cover all aspects of the model  
✅ **Multiple Formats** - Choose by your need  
✅ **Educational** - Learn from code examples  
✅ **Exportable** - Save results as JSON  
✅ **Well-Documented** - Every function explained  
✅ **No Dependencies** - Only needs COBRApy  

---

## 🎉 Start Now!

```bash
# Fastest overview
python quick_analysis.py

# Full analysis
python model_stats.py

# Interactive exploration
python model_explorer.py

# Learn by example
python analysis_examples.py
```

Choose the one that fits your need! 🧬

---

## 📚 Additional Resources

- `MODEL_ANALYSIS_GUIDE.md` - Detailed guide for each script
- `analysis_examples.py` - 10 runnable code examples
- COBRApy docs: https://cobrapy.readthedocs.io/
- Recon3D paper: https://www.nature.com/articles/nbt.3956

---

**Happy analyzing!** 🚀

For questions or suggestions, check the documentation or examine the code directly.
