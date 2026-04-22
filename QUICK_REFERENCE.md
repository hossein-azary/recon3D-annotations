# 🧬 Model Analysis Scripts - Quick Reference

A one-page cheat sheet for using the analysis scripts.

---

## ⚡ 30-Second Start

```bash
# Get a quick summary (recommended for first-time use)
python quick_analysis.py
```

That's it! You'll get:
- Model dimensions
- Reaction types
- Metabolite properties  
- Gene statistics
- Annotation coverage
- Top subsystems

---

## 🎯 Choose Your Script

### I want a **QUICK SUMMARY** → `quick_analysis.py`
```bash
python quick_analysis.py
# Output: Nice formatted table + model_summary.json
# Time: ~10 seconds
```

### I want **DETAILED ANALYSIS** → `model_stats.py`
```bash
python model_stats.py
# Output: Everything + examples + model_stats.json
# Time: ~20 seconds
```

### I want **INTERACTIVE SEARCH** → `model_explorer.py`
```bash
python model_explorer.py
# Output: Interactive menu, type commands
# Time: Manual
```

### I want **CODE EXAMPLES** → `analysis_examples.py`
```bash
python analysis_examples.py
# Output: 10 runnable examples you can copy
# Time: ~30 seconds
```

---

## 📊 What Each Script Shows

### quick_analysis.py
```
✓ Model size (reactions, metabolites, genes, compartments)
✓ Reaction breakdown (reversible, boundary, exchange, transport)
✓ Metabolite statistics (with formula, charged)
✓ Gene statistics (used, annotated)
✓ Annotation coverage percentages
✓ Top 10 subsystems
✓ Annotation types
✓ Statistics table
✓ JSON export
```

### model_stats.py
```
✓ All from quick_analysis
✓ Example reactions with full details
✓ Example metabolites with properties
✓ Example genes with associations
✓ Annotation summary by type
✓ Mass balance info
✓ Detailed breakdowns
```

### model_explorer.py
```
✓ Search reactions by ID/name
✓ Search metabolites by ID/name
✓ View reaction details
✓ View metabolite details
✓ View gene details
✓ List subsystems
✓ Find reactions in subsystem
✓ Find pathways between metabolites
✓ Export data to JSON
```

### analysis_examples.py
```
✓ 10 code examples
✓ How to find reactions
✓ How to find metabolites
✓ How to analyze pathways
✓ How to check genes
✓ How to count by type
✓ How to analyze compartments
✓ How to check annotations
✓ How to search patterns
```

---

## 🔍 Common Queries & Solutions

| Question | Solution |
|----------|----------|
| How many reactions? | `python quick_analysis.py` |
| Reaction types breakdown? | `python quick_analysis.py` |
| Find a specific reaction? | `python model_explorer.py` → Option 1 |
| Get reaction equation? | `python model_explorer.py` → Option 3 |
| Find glucose metabolites? | `python model_explorer.py` → Option 2 |
| List subsystems? | `python model_explorer.py` → Option 6 |
| Get all glycolysis reactions? | `python model_explorer.py` → Option 7 |
| Find ATP production pathways? | `python analysis_examples.py` (Example 10) |
| How annotated is the model? | `python quick_analysis.py` |
| Which database references? | `python model_stats.py` |
| Export reaction data? | `python model_explorer.py` → Option 9 |

---

## 💻 Quick Code Snippets

### Load and explore model
```python
import cobra
model = cobra.io.read_sbml_model("Recon3D.xml")
print(f"Model: {model.id}")
print(f"Reactions: {len(model.reactions)}")
```

### Find a reaction
```python
reaction = model.reactions.get_by_id("R_PFK")
print(reaction.reaction)  # See equation
print(reaction.gene_reaction_rule)  # See genes
```

### Find metabolites
```python
glucose = [m for m in model.metabolites if 'glucose' in m.name.lower()]
for met in glucose:
    print(f"{met.id}: {met.name} ({met.compartment})")
```

### Count reactions by type
```python
reversible = sum(1 for r in model.reactions if r.reversibility)
transport = sum(1 for r in model.reactions if 'transport' in r.name.lower())
print(f"Reversible: {reversible}, Transport: {transport}")
```

### Check annotations
```python
annotated = sum(1 for r in model.reactions if r.annotation)
pct = annotated / len(model.reactions) * 100
print(f"Annotated: {pct:.1f}%")
```

---

## 📈 Understanding the Numbers

| Metric | Typical Value | Meaning |
|--------|---------------|---------|
| Reactions | ~9,000 | Biochemical reactions in model |
| Metabolites | ~8,000 | Chemical compounds |
| Genes | ~6,000 | Associated genetic data |
| Reversible | ~60% | Can go both directions |
| Boundary | ~13% | Model boundaries |
| Exchange | ~7% | External inputs/outputs |
| Annotated | 70-90% | Have database references |

---

## 📁 Output Files

After running scripts, you get:

```
model_summary.json      ← From quick_analysis.py
model_stats.json        ← From model_stats.py
*_details.json          ← From model_explorer.py (option 9)
```

All are JSON format, can be opened with any text editor.

---

## ⌨️ model_explorer.py Commands

```
1 = Search reactions
2 = Search metabolites  
3 = Get reaction details
4 = Get metabolite details
5 = Get gene details
6 = List all subsystems
7 = Find reactions in subsystem
8 = Find pathways between metabolites
9 = Export reaction to JSON
0 = Exit
```

---

## 🎯 Recommended Workflow

### First Time Users
```bash
1. python quick_analysis.py          # Get overview (10 sec)
2. python analysis_examples.py       # See code examples (30 sec)
3. python model_explorer.py          # Explore interactively
```

### Detailed Analysis
```bash
1. python quick_analysis.py          # Quick summary
2. python model_stats.py             # Detailed report
3. python model_explorer.py          # Specific queries
```

### Custom Analysis
```bash
1. python analysis_examples.py       # Copy examples
2. Modify in Python IDE
3. Run your custom analysis
```

---

## ⚙️ Requirements

Install once:
```bash
pip install cobra requests
```

Then just run scripts:
```bash
python quick_analysis.py
```

---

## 🔗 Key Information

### Model Compartments
```
c = cytoplasm
m = mitochondria
e = extracellular
r = endoplasmic reticulum
l = lysosome
x = peroxisome
n = nucleus
g = golgi
i = inner mitochondrial
```

### Reaction Types
```
Exchange (EX_) = External inputs/outputs
Transport = Movement between compartments
Boundary = Model edges
Reversible (↔) = Both directions
Irreversible (→) = One direction
```

---

## 📊 Statistics Explained

```
Coverage 85% = 85 out of 100 items have that property

Min/Max/Avg: 
  Min = smallest value
  Max = largest value  
  Avg = average (sum ÷ count)

Reversible:
  True = reaction can go both directions
  False = one direction only
```

---

## 🆘 Troubleshooting

### "ModuleNotFoundError: cobra"
```bash
pip install cobra
```

### "Recon3D.xml not found"
```bash
# Make sure file exists in current directory
ls Recon3D.xml  (or dir Recon3D.xml on Windows)
```

### Script hangs
```bash
# Normal, especially for model_stats.py (takes ~20 sec)
# Press Ctrl+C to stop
```

### Want different format
```bash
# Check model_summary.json, model_stats.json
# Can be opened in any text editor
# Can be imported into other tools
```

---

## 💡 Pro Tips

✅ Save outputs: Redirect to file
```bash
python quick_analysis.py > output.txt
```

✅ Parse JSON results:
```python
import json
with open('model_summary.json') as f:
    data = json.load(f)
    print(data['num_reactions'])
```

✅ Run multiple scripts:
```bash
python quick_analysis.py && python model_stats.py
```

✅ View JSON pretty:
```bash
python -m json.tool model_summary.json
```

---

## 🎓 Learning Resources

- **CODE EXAMPLES**: Run `python analysis_examples.py`
- **DETAILED GUIDE**: Read `MODEL_ANALYSIS_GUIDE.md`
- **FULL DOCS**: Check docstrings in each script
- **COBRAPY**: https://cobrapy.readthedocs.io/

---

## 🚀 Get Started Now

### Option A: Fastest
```bash
python quick_analysis.py
```
→ 10-second overview

### Option B: Most Popular  
```bash
python model_explorer.py
```
→ Interactive exploration

### Option C: Most Complete
```bash
python model_stats.py
```
→ Full detailed report

### Option D: Learn by Example
```bash
python analysis_examples.py
```
→ 10 runnable code examples

---

## 📞 Quick Answers

**What's the model size?**
→ Run `python quick_analysis.py`

**Is it well annotated?**
→ Check "Annotation coverage" from quick_analysis

**Which pathways are there?**
→ See "TOP SUBSYSTEMS" from quick_analysis

**What reaction can I search for?**
→ Run model_explorer, option 1

**How do I export data?**
→ Run model_explorer, option 9

---

## ✨ Summary

| If you want... | Run this... | Time |
|---|---|---|
| Quick summary | `quick_analysis.py` | 10 sec |
| Full report | `model_stats.py` | 20 sec |
| Search interactively | `model_explorer.py` | varies |
| Learn coding | `analysis_examples.py` | 30 sec |

**Pick one and start exploring!** 🧬

---

**Last Updated:** April 2026  
**Status:** Ready to use ✅
