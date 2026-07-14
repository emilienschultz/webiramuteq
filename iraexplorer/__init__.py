# -*- coding: utf-8 -*-
"""iraexplorer : chargement et exploration des résultats IRaMuTeQ.

- model.py : couche de données (sans dépendance GUI) — Corpus, Analysis
- configs.py : préparation de fichiers .cfg pour iracmd.py
- app.py : interface Streamlit (`streamlit run iraexplorer/app.py`)
"""

from .model import Analysis, Corpus, discover_corpora        # noqa: F401
from .configs import build_command, load_defaults, write_config  # noqa: F401
