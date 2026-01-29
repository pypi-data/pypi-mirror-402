depsgraph is a minimal command-line tool that shows which Python modules a single file depends on *within your project*. It ignores stdlib and third-party imports by default, so you see only your own code’s coupling.

### Features
- Static analysis via AST (fast, no imports executed)
- ASCII tree printed to stdout
- Mermaid mindmap generated as `.mmd` and self-contained `.html`
- Configurable recursion depth and ignore patterns
- Detects import cycles and marks them

### Install

pip install depsgraph

### Usage

depsgraph path/to/file.py --project-dir /path/to/project

Example:

$ depsgraph src/handlers/api.py --project-dir .
src/handlers/api.py
+-- src/models/user.py
+-- src/utils/auth.py
|   +-- src/config.py
+-- src/db/conn.py
    +-- src/config.py

The command also creates `deps_graph.html` in the project directory; open it in a browser to view an interactive Mermaid mindmap.

### Options
- --project-dir: root of the project to scan (default ".")
- --max-depth: limit graph depth (default 50)
- --show-missing: list unresolved imports (stdlib, missing files)
- --no-mermaid: skip Mermaid file generation
- --ignored-dir: repeatable, e.g. `--ignored-dir generated`

### Requirements
Python 3.9+

### License
MIT