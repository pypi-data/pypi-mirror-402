# Python Page Rank

Static dependency analysis and PageRank-style importance scoring for Python modules.

This tool scans a Python codebase, builds a directed import graph between modules, and computes a PageRank-like score indicating which modules are most *structurally important* based on how much other code depends on them.

No code execution and no imports.

## Quickstart
Install from PyPI: 
```
pip install python-page-rank
```
- Run on a project directory: `python-page-rank .`    
- Show the top 5 ranked modules: `python-page-rank . --n 5`    
- Emit JSON instead of a table: `python-page-rank . --json` 

Run from src: 
```
python cli.py /path/to/project
```

## Example

```
python-page-rank /path/to/project
```

output:

```
Module                                     LOC  Importers   PageRank
----------------------------------------------------------------------
MyApp\authentication\models.py              29         12   0.114471
MyApp\common\utils.py                       66          6   0.094118
MyApp\payments\models.py                   168         15   0.053272
...
```

## CLI usage

The tool is intended to be run from the command line.

### Syntax
```
python-page-rank [path] [--n N] [--alpha A] [--iters I] [--json] [--include-init] 
```

### Arguments

path  
Project root directory to scan.  
Optional. Defaults to the current directory (`.`).

--n N  
Number of top-ranked files to display.  
Optional. Default is `10`.

--alpha A  
PageRank damping factor.  
Optional. Default is `0.85`.

--iters ITERS  
Number of PageRank iterations to run.  
Optional. Default is `50`.

--json  
Prints results as JSON instead of a text table.

--include-init  
Include `__init__.py` files in the output.  
By default, package initializer files are hidden to reduce noise.

### Examples

Analyze the current directory with default settings: `python-page-rank`  
Analyze a specific project directory: `python-page-rank MyApp`  
Show only the top 10 ranked files: `python-page-rank --n 10`  
Use a custom damping factor and iteration count: `python-page-rank --alpha 0.9 --iters 100`  
Analyze a directory and output results as JSON: `python-page-rank MyApp --json`  
Combine options: `python-page-rank MyApp --n 20 --alpha 0.8 --iters 75 --json`  

## What it does

- Recursively scans a project directory for `.py` files
- Parses files using `AST` (no code execution)
- Builds a **module-level dependency graph** from `import` / `from X import Y`
- Computes PageRank over that graph
- Outputs per-file:
  - lines of code (LOC)
  - number of importers
  - PageRank score

Typical uses:
- identify central / risky modules
- guide refactors
- estimate blast radius of changes
- understand large or unfamiliar codebases

## What it does **not** do (by design)

- Execute or import any project code
- Modify files
- Resolve runtime-dependent imports
- Guess ambiguous dependencies

This is a **conservative static analyzer**.

## How imports are handled

### Supported

- `import package.module`
- `import package.module as alias`
- `from package import module`
- `from package.subpackage import thing`

All resolved to absolute module paths and mapped to files when possible.

### Intentionally ignored

- `from . import models`   
- `from .. import utils`

These produce **no edge** in the graph.   
Relative imports with an explicit module (e.g. from .models import X) are handled.

**Why:**  
The AST provides no absolute module path (`node.module is None`). Resolving these requires guessing project roots and can be wrong in multi-root or namespace-package layouts. This behavior is deliberate and covered by tests.

## Directory handling

The scanner:

- automatically detects multiple import roots
- prefers the **shortest valid module path** when duplicates exist
- skips common junk directories:
  - `.git`, `.venv`, `venv`, `node_modules`, `__pycache__`, etc.

This allows it to work on:

- monorepos
- Django / FastAPI projects
- repos with multiple top-level packages

## PageRank details

- Standard iterative PageRank
- Damping factor: `0.85`
- Teleportation distributes rank uniformly
- Ranks are normalized to sum to `1.0`

**Interpretation:**  
A module is "important" if many important modules depend on it.

This measures **structural importance**, not runtime usage frequency.

## Notes

- The analysis is fully static
- No code is executed
- Imports are resolved via AST parsing only
- `PYTHONPATH` and runtime environment are ignored

## Tests

Tests cover:

- absolute import resolution
- multi-root handling
- preference of shortest module paths
- ignored relative dot-imports
- stability of PageRank output

Run tests with:

```
python -m pytest
```

## Limitations (read before filing issues)

- Relative imports without explicit module paths are ignored
- Namespace packages may require manual root layout
- Large repos may take time due to full AST parsing
- No attempt is made to infer dynamic imports

These are **tradeoffs**, not bugs.

## License

MIT License

## Disclaimer / Caveat

If you need aggressive inference, this tool is intentionally not that.