# ChemFig Editor

A browser-based GUI built with **NiceGUI** to write, compile, and preview **ChemFig / LaTeX** chemical-structure code in real time. Output is rendered as a high-resolution PNG directly in the browser.

---

## Features

- **Live Preview** — enter `\schemestart … \schemestop` (or any standalone LaTeX body) and see the rendered structure instantly.
- **Auto-Preview** — optional 2-second polling that recompiles whenever the code changes.
- **Folder Picker** — browse the server filesystem to choose an output directory without typing paths.
- **Save Options** — configure output folder, image filename, and optionally save the full `.tex` source alongside the PNG.
- **Download** — download the compiled PNG directly from the browser after a successful compilation.
- **Editable LaTeX Header** — customize the preamble (packages, colours, global `\setchemfig` settings) from within the UI.
- **Dependency Check** — one-click button verifies that `pdflatex` and `pdftoppm` are available on PATH.

---

## Requirements

### System dependencies

| Tool | Purpose | Minimum version |
|------|---------|-----------------|
| **TeX Live** (or MiKTeX / MacTeX) | `pdflatex` compiler | TeX Live 2022+ recommended |
| **Poppler** | `pdftoppm` — converts PDF → PNG | 22.0+ |

The following **LaTeX packages** must be available in your TeX distribution:

| Package | Use |
|---------|-----|
| `chemfig` | Drawing chemical structures |
| `mhchem` | Chemical formula notation (`\ce{}`) |
| `tikz` | Underlying graphics engine |
| `tikzlibrary{arrows.meta, calc}` | Arrow styles and coordinate math |
| `xcolor` | Custom colour definitions |
| `standalone` | Document class for borderless output |

> [!TIP]
> A full **TeX Live** installation (`texlive-full` on Linux, **MacTeX** on macOS) ships all packages above. If using a minimal install, add the missing packages with `tlmgr install chemfig mhchem`.

### Installing system tools

**macOS (Homebrew)**
```bash
# LaTeX
brew install --cask mactex        # full MacTeX (~5 GB), includes all packages
# or a lighter alternative:
brew install --cask basictex      # minimal; then: sudo tlmgr install chemfig mhchem

# Poppler (pdftoppm)
brew install poppler
```

**Linux (Debian / Ubuntu)**
```bash
sudo apt-get update
sudo apt-get install texlive-full poppler-utils
```

**Linux (Fedora / RHEL)**
```bash
sudo dnf install texlive-scheme-full poppler-utils
```

**Windows**
1. Install [MiKTeX](https://miktex.org/download) — it auto-installs missing packages on first compile.
2. Install [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases) and add its `bin/` folder to `PATH`.

---

### Python environment

The project ships with a **conda** environment file. Python 3.14 is used (3.10+ also works).

**Option A — Conda / Miniforge (recommended)**

```bash
# Create the environment from the lock file
conda env create -f environment.yml

# Activate it
conda activate chemfig_editor
```

**Option B — pip + venv**

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install nicegui
```

Core Python dependencies (all installed automatically):

| Package | Version (tested) | Role |
|---------|-----------------|------|
| `nicegui` | 3.12+ | Web UI framework |
| `fastapi` | 0.136+ | ASGI server (bundled with NiceGUI) |
| `uvicorn` | 0.47+ | HTTP server |

---

## Project structure

```
chemfig_editor/
├── src/
│   ├── chemfig_editor.py      # Main application (web UI entry point)
│   └── test_chemfig.py        # Unit / integration tests
├── assets/
│   └── structures/            # Compiled PNG files (auto-created, git-ignored)
├── environment.yml            # Conda environment lock file
├── requirements.txt           # pip requirements
├── .gitignore
└── README.md
```

---

## Installation

```bash
# 1. Clone the repository
git clone 
cd chemfig_editor

# 2. Create and activate the Python environment (choose one option above)
conda env create -f environment.yml
conda activate chemfig_editor

# 3. Verify system tools are on PATH
which pdflatex   # should return a path
which pdftoppm   # should return a path
```

---

## Usage

### Starting the application

```bash
python src/chemfig_editor.py
```

NiceGUI starts a local web server. Open your browser at:

```
http://localhost:8080
```

### Checking dependencies

Click **Verify Dependencies** in the header bar. The status label turns green if both `pdflatex` and `pdftoppm` are found, or red listing whichever is missing.

### Writing ChemFig code

Enter your LaTeX body in the **code editor**. The default template uses `\schemestart … \schemestop`:

```latex
\schemestart
    \chemfig{*6(=-=(-(=[2]O)-[:-30]OH)-=(-Cl)-)}
\schemestop
```

Any valid standalone LaTeX body (e.g. a bare `\chemfig{…}` or a `tikzpicture`) also works — the preamble is added automatically.

### Compiling

- Click **Generate** (blue button above the code editor) to compile immediately.
- Enable **Auto-Preview** (checkbox beside the Preview panel) to recompile automatically 2 seconds after you stop typing.

### Save options

Expand the **Save Options** section in the left panel:

| Field | Description |
|-------|-------------|
| **Output folder** | Directory where the PNG is saved. Type a path or click 📁 to browse. Relative paths are resolved from the project root. |
| **Image filename** | Name of the output `.png` file (extension added automatically if omitted). |
| **Save .tex source** | Check to also copy the full compiled `.tex` file next to the PNG. |
| **.tex filename** | Name for the saved `.tex` file (only active when the checkbox is ticked). |

### Downloading the image

After a successful compilation a **Download Image** button appears below the preview. Click it to download the PNG to your local machine.

### Downloading the .tex source on demand

Click **Download .tex** in the header bar at any time to download the current code (with the full preamble) as a `.tex` file, regardless of the "Save .tex source" checkbox.

### Editing the LaTeX header

Expand **Edit LaTeX Header** to modify the document preamble (packages, colour definitions, global `\setchemfig` settings). Click **Save Header** to apply changes for the current session.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `pdflatex` not found | TeX Live not installed or not on PATH | Install MacTeX / TeX Live; restart terminal |
| `pdftoppm` not found | Poppler not installed | `brew install poppler` / `apt install poppler-utils` |
| Blank preview, no error | Missing LaTeX package | Run `tlmgr install <package>` or install `texlive-full` |
| `RuntimeError: Directory … does not exist` | `assets/` missing | The app creates it automatically; ensure write permissions in the project root |
| Compilation hangs | `pdflatex` in interactive mode | The app passes `-interaction=nonstopmode`; check the log panel for the real error |

---

## License

MIT — see `LICENSE` for details.
