# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

IRaMuTeQ 0.8 alpha7 — a GPL wxPython GUI application for textual statistics (Reinert/Alceste classification, specificities, similarity analysis, word clouds) and questionnaire/matrix analyses. Python handles corpus management and the GUI; **all statistics are computed by R** — Python generates R scripts and shells out to the R binary. Authored by Pierre Ratinaud; ported to Python 3 in May 2020 (Laurent Mérat). Comments, identifiers and log messages are largely in French.

## Running

```bash
python iramuteq.py            # launch the GUI (requires wxPython and a local R installation)
python iramuteq.py -f FILE    # open a corpus/matrix file at startup
```

- First run creates `~/.iramuteq/` (user copies of the `configuration/*.cfg` files, `history.db`, `path.cfg` pointing to the R binary). R discovery / R-package checks live in `checkinstall.py`.
- macOS app bundle: `python setup.py py2app`. Debian packaging files are in `autres/debian/`.
- There is no test suite and no linter configuration.

## Command-line usage (no GUI)

`autres/iracmd.py` is the historical CLI harness (`-f corpus -t alceste|stat|spec|simitxt ...`, config via `-c`/`-d`). **It is still Python 2** (print statements, `except Exception, txt`, `ConfigParser` imports) and contains a hardcoded developer path, so it must be ported and moved to the repo root (it imports `corpus`, `functions`, `chemins`, `textreinert`... from there) before it can run against the Python 3 codebase. It shows the minimal sequence to run an analysis headless: build a `Corpus` (`BuildFromAlceste`), `corpus.conn_all()` → `make_lems()` → `parse_active()`, then instantiate an analysis class such as `Reinert(parent, corpus, parametres)`.

## Architecture

### Python → R execution pipeline

Every analysis follows the same flow:

1. An analysis class collects parameters (from a wx dialog and/or a `.cfg` file read with `DoConf` in `functions.py`).
2. Python writes intermediate data (sparse matrices, word lists) into the analysis output directory.
3. A script-builder class in `PrintRScript.py` (one subclass per analysis) concatenates template code from `Rscripts/` with generated variable assignments into a temp R file.
4. `exec_rcode()` in `functions.py` spawns the R binary (path from `~/.iramuteq/path.cfg`); `check_Rresult()` polls for completion and errors.
5. `layout.py` / `HTML.py` build the result views from the files R wrote; `OpenAnalyse` (`openanalyse.py`) can re-open any saved analysis from its `Analyse.ira` config file.

### Two analysis families

- **Text analyses** — base class `AnalyseText` in `analysetxt.py`; subclasses in `text*.py` (`textreinert.py` for Reinert/Alceste clustering, `textstat.py`, `textaslexico.py` for specificities, `textsimi.py`, `textwordcloud.py`, `textlabbe.py`...). They operate on a `Corpus`.
- **Matrix analyses** — base class `AnalyseMatrix` in `analysematrix.py` operating on a `Tableau` (`tableau.py`, spreadsheet data via `sheet.py`); subclasses in `tab*.py` (`tabchi2.py`, `tabsimi.py`, `tabchddist.py`...).

### Corpus model (`corpus.py`)

A corpus is persisted as three SQLite databases in its output directory: `corpus.db` (text), `formes.db` (word forms/lemmas), `uces.db` (segment indices). Structure is Uci (document, with `****`-line metadata "étoiles" variables) → Uce (text segment) → Word/Lem. `BuildFromAlceste` parses the Alceste-format corpus file; `BuildSubCorpus` and `BuildMergeFromClusters` derive corpora. `copycorpus` clones a corpus for reuse across analyses. Lemmatization uses language dictionaries from `dictionnaires/` (`lexique_*.txt`, `expression_*.txt`); part-of-speech keys (active/supplementary forms) come from `key.cfg`.

### Paths and configuration

- `chemins.py` — `PathOut` maps logical file keys (e.g. `TableUc1`, `Analyse.ira`) to paths in the per-analysis output directory created next to the corpus file; each analysis type registers its file dictionary (e.g. `ChdTxtPathOut`).
- `configuration/*.cfg` — per-analysis default parameters (`reinert.cfg`, `simitxt.cfg`, `matrix.cfg`...), copied to `~/.iramuteq` and read/written via `DoConf`.
- Every corpus and analysis is identified by a uuid and recorded in `~/.iramuteq/history.db` (`History` in `functions.py`), which backs the history tree in the GUI (`tree.py`).

### GUI

`iramuteq.py` builds the main frame with wx AUI panes; dialogs live in `dialog.py`, `guifunct.py`, `OptionAlceste.py`; result tabs/lists in `ProfList.py`, `listlex.py`, `Liste.py`, `layout.py`. Translations use gettext catalogs in `locale/` (`langue.py`).

### Importers

`parse_factiva_*.py`, `parse_europress.py`, `parse_dmi.py`, `import_txm.py` convert external corpus formats to the Alceste format.

## Caveats

- `autres/` is a grab-bag of legacy/experimental scripts, mostly still Python 2 — do not assume they run.
- `configparser.py` and `configparser_helpers.py` at the repo root are a vendored copy of the stdlib module (bundled during the Python 3 port) that shadows `import configparser` for every script run from this directory.
- Windows path handling goes through `ffr()`/`normpath_win32()` in `chemins.py` when embedding paths in R scripts.
