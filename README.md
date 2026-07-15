# IRaMuTeQ 0.8 alpha 7

IRaMuTeQ (Interface de R pour les Analyses Multidimensionnelles de Textes et
de Questionnaires) is a GPL tool for textual statistics: Reinert/Alceste
clustering, specificities, similarity analysis, word clouds, and
questionnaire/matrix analyses. Python handles corpus management and the GUI;
all statistics are computed by R.

Author: Pierre Ratinaud (Université de Toulouse). Python 3 port: Laurent
Mérat (May 2020). Website: <http://www.iramuteq.org>

The changes made on top of the preliminary sources (command-line entry
point, web explorer, dependency tooling) are traced in `EVOLUTIONS.md`.

## Requirements

- Python 3 with the packages listed in `requirements.txt` (wxPython and
  xlrd for the GUI/CLI; streamlit, pandas and altair for the web explorer)
- **R** (<https://www.r-project.org>), plus the R packages used by the
  analyses: `ca`, `gee`, `ape`, `igraph`, `proxy`, `wordcloud`, `irlba`,
  `textometry`, `sna`, `network`, `intergraph`, `rgl` (optional, 3D only)

`./install_deps.sh` installs both sides (`--python /path/to/python` to
target a virtualenv, `--skip-python` / `--skip-r` to restrict, `--help`
for details; on Ubuntu see the wxPython note at the top of the script).

On first run, IRaMuTeQ creates `~/.iramuteq-0.8.a7/` with user copies of the
configuration files and dictionaries, plus `path.cfg` which stores the path
to the R binary (auto-detected when possible — edit `rpath` there if R is
not found).

## Graphical interface

```bash
python iramuteq.py            # launch the GUI
python iramuteq.py -f FILE    # open a corpus/matrix file at startup
```

## Command line (no GUI): `iracmd.py`

`iracmd.py` builds a corpus and runs text analyses headless — no window is
opened, results are written to disk exactly as with the GUI.

### Corpus format

A plain-text file in the Alceste format: each text starts with a `****` line
carrying starred metadata variables (`*variable_modality`), followed by the
text itself:

```
**** *annee_2009 *sexe_f
Text of the first document...

**** *annee_2010 *sexe_h
Text of the second document...
```

### Usage

```bash
# build the corpus only (creates <corpus>_corpus_1/ next to the file)
python iracmd.py -f data/theses-socio-1000.txt -b

# build the corpus and run an analysis
python iracmd.py -f data/theses-socio-1000.txt -t stat

# reuse an already-built corpus (no re-import) for further analyses
python iracmd.py -r data/theses-socio-1000_corpus_1/Corpus.cira -t alceste
python iracmd.py -r data/theses-socio-1000_corpus_1/Corpus.cira -t spec
python iracmd.py -r data/theses-socio-1000_corpus_1/Corpus.cira -t simitxt
```

### Options

| Option | Description |
|---|---|
| `-f`, `--file FILE` | corpus file (Alceste format) |
| `-t`, `--type TYPE` | analysis type: `alceste` (= `reinert`), `stat`, `spec`, `simitxt` |
| `-r`, `--read Corpus.cira` | reuse a corpus built previously (path to its `Corpus.cira`) |
| `-b`, `--build` | build the corpus without running an analysis |
| `-c`, `--conf FILE` | configuration file for the analysis (overrides the defaults) |
| `-d`, `--confcorp FILE` | configuration file for the corpus import |
| `-e`, `--enc ENC` | corpus encoding (default: `utf-8`) |
| `-l`, `--lang LANG` | corpus language: `french` (default), `english`, `german`, `italian`, `spanish`, `portuguese`, `greek`, `swedish`, `galician`, or `other` |

### Analysis types

- **`alceste` / `reinert`** — Reinert/Alceste descending hierarchical
  classification. Writes the dendrogram, class profiles/antiprofiles, the
  chi2 tables, plus two extra graphics that the GUI only draws on demand:
  `dendrogramme_texte_1.png` (dendrogram with class profiles) and
  `dendrogramme_cloud_1.png` (dendrogram with per-class word clouds — needs
  the R package `wordcloud`). The correspondence analysis (`AFC2D*.png`,
  `afc_facteur/col/row.csv`) is computed automatically whenever the
  classification keeps more than 2 classes; raising `nbcl_p1` in a `-c`
  file is the usual way to obtain more classes.
- **`stat`** — basic textual statistics: frequencies of active/supplementary
  forms, hapax, Zipf plot, segment sizes, summary (`glob.txt`).
- **`spec`** — specificities and correspondence analysis. Compares the
  modalities of **one** starred variable; by default the first variable of
  the corpus with several modalities is used (logged at runtime). To choose
  another, pass a `-c` file containing e.g.
  `etoiles = ['*annee_2009', '*annee_2010']`.
- **`simitxt`** — similarity analysis (co-occurrence graph). Without the
  GUI's word-selection dialog, the 200 most frequent active forms are used;
  adjust with `max_actives_simi = 500` in a `-c` file.

### Analysis parameters

Each analysis reads its default parameters from `~/.iramuteq-0.8.a7/`
(`reinert.cfg`, `stat.cfg`, `simitxt.cfg`); corpus import parameters
(segment size, lemmatisation, punctuation...) come from `corpus.cfg` (or a
`-d` file). A `-c` file **overrides** those defaults, so it only needs to
contain the parameters you change, e.g. for the Reinert classification:

```ini
[ALCESTE]
classif_mode = 1        ; 0 = double on UC, 1 = simple on segments, 2 = on texts
nbcl_p1 = 10            ; number of classes in phase 1
mincl = 0               ; minimum segments per class (0 = automatic)
max_actives = 20000
lem = True
svdmethod = irlba
mode.patate = 0
```

### Outputs

Every run creates a numbered directory next to the corpus file
(`<name>_corpus_N/`, then `<name>_<type>_N/` inside it) containing the result
files (`.csv`, `.png`, `Analyse.ira`...). Analyses are also recorded in
`~/.iramuteq-0.8.a7/history.db` and can be re-opened from the GUI's history
tree.

## Web explorer (Streamlit): `iraexplorer/`

A web interface to run IRaMuTeQ computations and browse their results,
organised in **projects**:

```bash
./install_deps.sh                     # or: pip install -r requirements.txt
streamlit run iraexplorer/app.py
```

All projects live in a single folder (default: `projects/` at the repo
root, configurable on the home page). A project is a self-contained
directory holding the corpus source file, the run-specific `.cfg` files,
the `run.log` journal and the result directories.

- **Home page** — list of existing projects (corpus count, analyses,
  last-modified), with three actions: *create a new analysis* (button),
  *open* a project, or *delete* one (with confirmation).
- **Create page** — upload or point to a corpus `.txt` (copied into the
  project folder), name the project, pick the treatments (alceste, stat,
  spec, simitxt) and edit every parameter (corpus import included). The
  parameters are written as `.cfg` files **inside the project folder**,
  then the whole pipeline (corpus build + each analysis) runs with live
  step-by-step status — the chosen Python interpreter must have wxPython.
- **Project view** — one page per analysis (Reinert classes with info.txt
  summary, dendrograms including the word-cloud variant, AFC, profiles and
  sample segments; specificities per modality; similarity graph; textual
  statistics), a *new treatment* page to launch further computations on
  the project corpus, and per-analysis deletion. Every page has an
  **audit panel**: inventory of the files behind the view (path, size,
  mtime, parse status, optional SHA-256) and a JSON export.

The package is layered so it can back an API later:

- `iraexplorer/model.py` — data layer: loads `Corpus.cira`, the SQLite
  databases and every analysis directory into plain objects (pandas +
  stdlib only; no wxPython, no Streamlit, no imports from the IRaMuTeQ
  code). Each expected file is declared in a manifest with a description;
  loading never raises — missing/corrupt files are recorded with their
  status. Everything is serializable via `to_dict()`/`to_json()`.
- `iraexplorer/configs.py` — reads the default `.cfg` parameters and writes
  run-specific `.cfg` files compatible with `iracmd.py -c/-d`.
- `iraexplorer/runner.py` — runs the full pipeline (`-f ... -b` build, then
  `-r ... -t <type> -c <cfg>` for each analysis) in subprocesses, recording
  each command, return code and output in `RunStep` objects and a
  `run.log` file.
- `iraexplorer/app.py` — the Streamlit UI (one renderer per analysis type,
  generic fallback for unknown types, plus the run page).

## Repository layout

- `iramuteq.py` — GUI entry point; `iracmd.py` — command-line entry point
- `corpus.py` — corpus model (SQLite persistence, Alceste parser)
- `analysetxt.py`, `text*.py` — text analyses; `analysematrix.py`, `tab*.py` —
  matrix analyses
- `PrintRScript.py`, `Rscripts/` — R script generation
- `dictionnaires/` — lemmatisation dictionaries; `configuration/` — default
  configuration files
- `autres/` — legacy/experimental scripts (mostly still Python 2)

## License

GNU GPL v2 — see `gpl-2.0.txt`. Copyright (c) 2008-2020 Pierre Ratinaud.
