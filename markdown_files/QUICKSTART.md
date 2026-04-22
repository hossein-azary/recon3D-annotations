# Quick Start Guide for Recon3D Model Annotation

## Step 1: Install Dependencies

Open a terminal in the `recon3D-annotations` directory and run:

```bash
python setup_env.py
```

This will:
- Create a virtual environment (`recon3d-env`)
- Install all required packages (cobra, requests, tqdm, rich)

**Alternative (manual installation):**
```bash
pip install -r requirements.txt
```

## Step 2: Activate the Virtual Environment

### On Windows (PowerShell):
```powershell
.\recon3d-env\Scripts\Activate.ps1
```

### On Windows (Command Prompt):
```cmd
.\recon3d-env\Scripts\activate.bat
```

### On Linux/macOS:
```bash
source recon3d-env/bin/activate
```

## Step 3: Annotate Your Model

### Basic annotation:
```bash
python vmh_annotator.py Recon3D.xml
```

### With HTML report:
```bash
python vmh_annotator.py Recon3D.xml --report annotation_report.html
```

### With custom output name:
```bash
python vmh_annotator.py Recon3D.xml -o my_annotated_model.xml
```

## Output

The tool will:
1. Load the Recon3D model
2. Annotate reactions, metabolites, and genes using VMH API
3. Save the annotated model as `Recon3D_annotated.xml`
4. Print annotation statistics
5. (Optionally) Generate an HTML report

## Example Output

```
INFO - Loading model from: Recon3D.xml
INFO - Model loaded: Recon3D
INFO - Starting annotation of model: Recon3D
INFO -   Reactions: 9000
INFO -   Metabolites: 8000
INFO -   Genes: 6000
INFO - Annotating reactions...
Reactions: 100%|████████████| 9000/9000 [00:45<00:00, 200/s]
INFO - Annotating metabolites...
Metabolites: 100%|████████████| 8000/8000 [00:40<00:00, 200/s]
INFO - Annotating genes...
Genes: 100%|████████████| 6000/6000 [00:30<00:00, 200/s]
INFO - Annotation complete!

============================================================
ANNOTATION STATISTICS
============================================================
Reactions annotated:    8500
Metabolites annotated:  7800
Genes annotated:        5900
API calls made:         250
API errors:             15
============================================================

INFO - Model saved successfully!
```

## Using as a Python Library

```python
from vmh_annotator import VMHAnnotator
import cobra

# Load model
model = cobra.io.read_sbml_model("Recon3D.xml")

# Create annotator
annotator = VMHAnnotator(cache_responses=True)

# Annotate
stats = annotator.annotate_model(model)

# Save
cobra.io.write_sbml_model(model, "annotated_model.xml")

# View results
print(f"Reactions annotated: {stats['reactions_annotated']}")
print(f"Metabolites annotated: {stats['metabolites_annotated']}")
print(f"Genes annotated: {stats['genes_annotated']}")
```

## Common Commands

| Command | Purpose |
|---------|---------|
| `python vmh_annotator.py Recon3D.xml` | Basic annotation |
| `python vmh_annotator.py Recon3D.xml -o output.xml` | Custom output filename |
| `python vmh_annotator.py Recon3D.xml --report report.html` | Generate HTML report |
| `python vmh_annotator.py Recon3D.xml --no-cache` | Disable API caching |
| `python vmh_annotator.py Recon3D.xml -v` | Verbose/debug mode |
| `python vmh_annotator.py -h` | Show help message |

## Troubleshooting

**Problem: "ModuleNotFoundError: No module named 'cobra'"**
- Solution: Run `pip install -r requirements.txt`

**Problem: "Model file not found: Recon3D.xml"**
- Solution: Make sure Recon3D.xml is in the current directory

**Problem: API errors**
- Solution: Try with `--no-cache` flag to get fresh API responses

**Problem: Slow annotation**
- Solution: The tool caches responses by default. Subsequent runs will be faster.

## Files Generated

- `Recon3D_annotated.xml` - Annotated model (SBML format)
- `annotation_report.html` - Visual report (if `--report` flag used)
- `annotation_report.json` - JSON report (if `--report` flag used)

## Next Steps

1. Check the generated HTML report to see annotation coverage
2. Use the annotated model in your enzyme-constrained models
3. Retrieve kcat values using the new annotations
4. Integrate with COBRAMod or other tools

## Support Files

- `data_annotation.py` - Utilities for cross-reference handling
- `example_usage.py` - Examples of how to use the library
- `setup_env.py` - Environment setup script
- `requirements.txt` - Package dependencies

## For More Information

- See `README.md` for detailed documentation
- See `example_usage.py` for code examples
- Run `python vmh_annotator.py -h` for command-line help

---

Happy annotating! 🧬
