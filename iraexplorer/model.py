# -*- coding: utf-8 -*-
#License: GNU/GPL
"""Couche de données de l'explorateur de résultats IRaMuTeQ.

Charge en objets Python les résultats écrits sur disque par IRaMuTeQ
(GUI ou iracmd.py) : le répertoire de corpus (Corpus.cira + bases
SQLite) et les répertoires d'analyses (Analyse.ira + fichiers produits
par R).

Choix de conception :

- **découplage** — ce module ne dépend que de la bibliothèque standard
  et de pandas : ni wxPython, ni Streamlit, ni le code d'IRaMuTeQ. Il
  est directement réutilisable derrière une API (FastAPI...) ou en
  notebook ;
- **auditabilité** — chaque fichier attendu est déclaré dans un
  manifeste (`ANALYSIS_FILES`) avec sa description ; le chargement d'un
  fichier n'écrase jamais une erreur : chaque `LoadedFile` garde son
  chemin, sa taille, sa date, son statut (`ok`/`missing`/`error`), le
  message d'erreur éventuel et peut calculer une empreinte SHA-256.
  `Analysis.manifest()` restitue l'inventaire complet, y compris les
  fichiers présents mais non répertoriés ;
- **tolérance** — un fichier manquant ou illisible ne fait jamais
  échouer le chargement global : il est simplement marqué comme tel ;
- **lecture seule** — les bases SQLite sont ouvertes en mode
  ``mode=ro`` ; rien n'est écrit dans les répertoires de résultats.

Point d'entrée :

    from iraexplorer.model import Corpus, discover_corpora
    corpus = Corpus('data/theses-socio-1000_corpus_1')
    corpus.analyses[0].table('profiles')
"""

from __future__ import annotations

import configparser
import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------------
# manifeste des fichiers produits par chaque type d'analyse
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FileSpec:
    """Description déclarative d'un fichier attendu dans une analyse."""
    key: str            # identifiant stable (utilisable par une future API)
    filename: str       # nom du fichier dans le répertoire d'analyse
    kind: str           # 'table' | 'image' | 'text'
    description: str    # à quoi sert ce fichier
    reader: str = 'csv'         # nom du lecteur dans READERS
    names: tuple = None         # noms de colonnes si le csv n'a pas d'entête
    decimal: str = '.'          # séparateur décimal ('.' ou ',')
    sep: str = ';'


ANALYSIS_FILES = {
    'stat': [
        FileSpec('summary', 'glob.txt', 'text', 'résumé global (textes, occurrences, hapax...)', reader='text'),
        FileSpec('total', 'total.csv', 'table', 'formes non hapax : effectif et catégorie',
                 reader='csv_noheader', names=('forme', 'freq', 'gram')),
        FileSpec('actives', 'formes_actives.csv', 'table', 'formes actives : effectif et catégorie',
                 reader='csv_noheader', names=('forme', 'freq', 'gram')),
        FileSpec('supplementaires', 'formes_supplémentaires.csv', 'table',
                 'formes supplémentaires : effectif et catégorie',
                 reader='csv_noheader', names=('forme', 'freq', 'gram')),
        FileSpec('hapax', 'hapax.csv', 'table', 'formes n\'apparaissant qu\'une fois',
                 reader='csv_noheader', names=('forme', 'freq', 'gram')),
        FileSpec('segment_sizes', 'stsize.csv', 'table', 'taille (nb de formes) de chaque segment',
                 reader='csv_noheader', names=('taille',)),
        FileSpec('zipf', 'zipf.png', 'image', 'diagramme rang/fréquence (loi de Zipf)'),
        FileSpec('segments_size_plot', 'segments_size.png', 'image', 'histogramme des tailles de segments'),
    ],
    'spec': [
        FileSpec('spec_formes', 'tablespecf.csv', 'table',
                 'spécificités des formes par modalité (score, signe = sur/sous-représentation)',
                 reader='csv_rownames', decimal=','),
        FileSpec('spec_types', 'tablespect.csv', 'table',
                 'spécificités des catégories grammaticales par modalité',
                 reader='csv_rownames', decimal=','),
        FileSpec('banalites', 'banalites.csv', 'table',
                 'formes banales (spécifiques d\'aucune modalité) et leur effectif',
                 reader='csv_rownames', decimal=','),
        FileSpec('freq_formes', 'tableafcm.csv', 'table', 'effectifs des formes par modalité',
                 reader='csv_rownames'),
        FileSpec('freq_types', 'tabletypem.csv', 'table',
                 'effectifs des catégories grammaticales par modalité', reader='csv_rownames'),
        FileSpec('stat_modalites', 'statbyet.csv', 'table',
                 'occurrences, formes, hapax et segments par modalité', reader='tsv'),
        FileSpec('eff_relatif_forme', 'eff_relatif_forme.csv', 'table',
                 'effectifs relatifs des formes', reader='csv_rownames', decimal=','),
        FileSpec('eff_relatif_type', 'eff_relatif_type.csv', 'table',
                 'effectifs relatifs des catégories', reader='csv_rownames', decimal=','),
        FileSpec('afc_formes_lignes', 'afcf_row.png', 'image', 'AFC sur les formes : plan des lignes'),
        FileSpec('afc_formes_colonnes', 'afcf_col.png', 'image', 'AFC sur les formes : plan des colonnes'),
        FileSpec('afc_types_lignes', 'afct_row.png', 'image', 'AFC sur les catégories : plan des lignes'),
        FileSpec('afc_types_colonnes', 'afct_col.png', 'image', 'AFC sur les catégories : plan des colonnes'),
    ],
    'simitxt': [
        FileSpec('graphe', 'graph_simi_1.png', 'image', 'graphe de similitude (cooccurrences)'),
        FileSpec('actives', 'actives.csv', 'table', 'formes actives retenues pour l\'analyse',
                 reader='csv_noheader', names=('forme',)),
        FileSpec('selected', 'selected.csv', 'table',
                 'indices (dans actives trié par fréquence) des formes sélectionnées',
                 reader='csv_noheader', names=('indice',)),
        FileSpec('matrice', 'mat01.csv', 'table',
                 'matrice segments x formes (présence/absence) — non chargée par défaut',
                 reader='skip'),
    ],
    'alceste': [
        FileSpec('profiles', 'profiles.csv', 'table',
                 'profil des classes : formes sur-représentées (chi2 d\'association)',
                 reader='profile'),
        FileSpec('antiprofiles', 'antiprofiles.csv', 'table',
                 'antiprofil des classes : formes sous-représentées', reader='profile'),
        FileSpec('uce_classes', 'uce.csv', 'table',
                 'classe affectée à chaque segment (0 = non classé)', reader='csv_rownames'),
        FileSpec('chi2_table', 'chisqtable.csv', 'table', 'chi2 forme x classe',
                 reader='csv_rownames', decimal=','),
        FileSpec('p_table', 'ptable.csv', 'table', 'p-values forme x classe',
                 reader='csv_rownames', decimal=','),
        FileSpec('classe_mod', 'classe_mod.csv', 'table', 'modalités associées aux classes',
                 reader='csv_noheader', names=('modalite', 'v1', 'v2')),
        FileSpec('dendrogramme', 'dendro1.png', 'image', 'dendrogramme de la classification'),
        FileSpec('dendro_texte', 'dendrogramme_texte_1.png', 'image',
                 'dendrogramme avec les profils des classes'),
        FileSpec('dendro_cloud', 'dendrogramme_cloud_1.png', 'image',
                 'dendrogramme avec les nuages de mots des classes'),
        FileSpec('arbre', 'arbre_1.png', 'image', 'arbre de la classification descendante'),
        FileSpec('afc_actives', 'AFC2DL.png', 'image',
                 'AFC : formes actives (si plus de 2 classes)'),
        FileSpec('afc_sup', 'AFC2DSL.png', 'image', 'AFC : formes supplémentaires'),
        FileSpec('afc_etoiles', 'AFC2DEL.png', 'image', 'AFC : variables étoilées'),
        FileSpec('afc_classes', 'AFC2DCL.png', 'image', 'AFC : classes'),
        FileSpec('afc_facteur', 'afc_facteur.csv', 'table',
                 'AFC : valeurs propres et inertie des facteurs',
                 reader='csv_rownames', decimal=','),
        FileSpec('afc_colonnes', 'afc_col.csv', 'table',
                 'AFC : coordonnées et contributions des classes',
                 reader='csv_rownames', decimal=','),
        FileSpec('afc_lignes', 'afc_row.csv', 'table',
                 'AFC : coordonnées et contributions des formes',
                 reader='csv_rownames', decimal=','),
        FileSpec('info', 'info.txt', 'text', 'journal de l\'analyse', reader='text'),
    ],
}
ANALYSIS_FILES['reinert'] = ANALYSIS_FILES['alceste']

#: correspondance entre catégories grammaticales et étiquettes lisibles
#: (non exhaustif — les clés viennent de key.cfg)


# ---------------------------------------------------------------------------
# lecteurs
# ---------------------------------------------------------------------------

def _read_csv(path, spec) :
    return pd.read_csv(path, sep=spec.sep, decimal=spec.decimal)

def _read_csv_noheader(path, spec) :
    return pd.read_csv(path, sep=spec.sep, decimal=spec.decimal,
                       header=None, names=list(spec.names) if spec.names else None)

def _read_csv_rownames(path, spec) :
    df = pd.read_csv(path, sep=spec.sep, decimal=spec.decimal, index_col=0)
    df.columns = [clean_r_name(c) for c in df.columns]
    return df

def _read_tsv(path, spec) :
    return pd.read_csv(path, sep='\t')

def _read_text(path, spec) :
    return Path(path).read_text(encoding='utf8', errors='replace')

def _read_profile(path, spec) :
    """profiles.csv / antiprofiles.csv : format en blocs écrit par R.

    ``***;nb classes;N`` puis, pour chaque classe, ``**;classe;i`` suivi
    de ``****;<nb segments classe>;<nb segments total>;<pourcentage>``
    puis les lignes de formes : eff. segments classe ; eff. segments
    total ; % ; chi2 ; forme ; p-value. Dans chaque bloc, ``*****``
    sépare les formes actives des supplémentaires, puis ``*`` introduit
    les variables étoilées.

    Retourne un DataFrame long (une ligne par forme et par classe, avec
    la colonne `categorie`) ; le résumé des classes est dans
    ``df.attrs['classes']``.
    """
    rows = []
    classes = []
    current = None
    categorie = 'active'
    with open(path, encoding='utf8') as f :
        for line in f :
            cells = [c.strip().strip('"') for c in line.rstrip('\n\r').split(';')]
            if not cells or cells[0] in ('V1', '***') :
                continue
            if cells[0] == '**' :          # entête de classe
                current = int(cells[2])
                categorie = 'active'
            elif cells[0] == '****' :      # effectifs de la classe
                classes.append({'classe' : current,
                                'segments' : int(cells[1]),
                                'segments_total' : int(cells[2]),
                                'pourcentage' : float(cells[3])})
            elif cells[0] == '*****' :     # début des formes supplémentaires
                categorie = 'supplémentaire'
            elif cells[0] == '*' :         # début des variables étoilées
                categorie = 'étoile'
            elif current is not None and len(cells) >= 6 and cells[0] != '' :
                rows.append({'classe' : current,
                             'categorie' : categorie,
                             'eff_seg_classe' : int(cells[0]),
                             'eff_seg_total' : int(cells[1]),
                             'pourcentage' : float(cells[2]),
                             'chi2' : float(cells[3]),
                             'forme' : cells[4],
                             'p' : float(cells[5])})
    df = pd.DataFrame(rows)
    df.attrs['classes'] = classes
    return df

READERS = {
    'csv' : _read_csv,
    'csv_noheader' : _read_csv_noheader,
    'csv_rownames' : _read_csv_rownames,
    'tsv' : _read_tsv,
    'text' : _read_text,
    'profile' : _read_profile,
    'skip' : None,      # fichier répertorié mais volontairement non chargé
}


def clean_r_name(name) :
    """R remplace '*' par 'X.' dans les noms de colonnes ; on restitue."""
    name = str(name)
    if name.startswith('X.') :
        return '*' + name[2:]
    return name


def read_ira(path) :
    """Lit un fichier .ira/.cira (format ini) -> (type, dict des paramètres)."""
    conf = configparser.ConfigParser(interpolation=None)
    with open(path, encoding='utf8') as f :
        conf.read_file(f)
    section = conf.sections()[0]
    parametres = dict(conf.items(section))
    return parametres.get('type', section), parametres


# ---------------------------------------------------------------------------
# fichiers chargés (avec provenance)
# ---------------------------------------------------------------------------

@dataclass
class LoadedFile:
    """Un fichier d'analyse : provenance, statut et contenu (chargé à la demande)."""
    spec: FileSpec
    path: Path
    expected: bool = True       # False : présent sur disque mais hors manifeste
    status: str = 'ok'          # 'ok' | 'missing' | 'error' | 'not_loaded'
    error: str = ''
    _data: object = field(default=None, repr=False)
    _loaded: bool = False

    @property
    def exists(self) :
        return self.path.exists()

    def load(self) :
        """Charge (et met en cache) le contenu ; None si absent/illisible."""
        if self._loaded :
            return self._data
        self._loaded = True
        if not self.exists :
            self.status = 'missing'
            return None
        if self.spec.kind == 'image' :
            self._data = self.path
            self.status = 'ok'
            return self._data
        reader = READERS.get(self.spec.reader)
        if reader is None :
            self.status = 'not_loaded'
            return None
        try :
            self._data = reader(self.path, self.spec)
            self.status = 'ok'
        except Exception as ex :
            self.status = 'error'
            self.error = '%s: %s' % (type(ex).__name__, ex)
        return self._data

    def sha256(self) :
        if not self.exists :
            return None
        h = hashlib.sha256()
        with open(self.path, 'rb') as f :
            for chunk in iter(lambda : f.read(1 << 20), b'') :
                h.update(chunk)
        return h.hexdigest()

    def manifest_row(self, checksum=False) :
        st = self.path.stat() if self.exists else None
        return {
            'clé' : self.spec.key,
            'fichier' : self.spec.filename,
            'type' : self.spec.kind,
            'description' : self.spec.description,
            'répertorié' : self.expected,
            'présent' : self.exists,
            'statut' : self.status if self._loaded or not self.exists else 'non chargé',
            'erreur' : self.error,
            'taille (octets)' : st.st_size if st else None,
            'modifié le' : datetime.fromtimestamp(st.st_mtime).isoformat(' ', 'seconds') if st else None,
            'sha256' : self.sha256() if checksum else None,
            'chemin' : str(self.path),
        }


# ---------------------------------------------------------------------------
# une analyse
# ---------------------------------------------------------------------------

_IGNORED_EXTRA = {'Analyse.ira', 'RData.RData', 'dendrogramme.RData'}
_KIND_BY_EXT = {'.png' : 'image', '.svg' : 'image', '.csv' : 'table', '.txt' : 'text'}


class Analysis :
    """Un répertoire d'analyse IRaMuTeQ (contenant un Analyse.ira)."""

    def __init__(self, path) :
        self.path = Path(path)
        self.ira = self.path / 'Analyse.ira'
        self.type, self.parametres = read_ira(self.ira)
        self.name = self.parametres.get('name', self.path.name)
        specs = ANALYSIS_FILES.get(self.type, [])
        self.files = {}
        for spec in specs :
            self.files[spec.key] = LoadedFile(spec, self.path / spec.filename)
        # fichiers présents mais absents du manifeste : répertoriés quand même
        known = {spec.filename for spec in specs} | _IGNORED_EXTRA
        for f in sorted(self.path.iterdir()) :
            if f.is_file() and f.name not in known :
                kind = _KIND_BY_EXT.get(f.suffix.lower(), 'text')
                spec = FileSpec(key='extra:' + f.name, filename=f.name, kind=kind,
                                description='fichier non répertorié dans le manifeste',
                                reader='skip')
                self.files[spec.key] = LoadedFile(spec, f, expected=False)

    # --- accès au contenu ------------------------------------------------
    def table(self, key) :
        """DataFrame du fichier `key`, ou None."""
        lf = self.files.get(key)
        return lf.load() if lf is not None else None

    def text(self, key) :
        lf = self.files.get(key)
        return lf.load() if lf is not None else None

    def image_path(self, key) :
        lf = self.files.get(key)
        if lf is not None and lf.exists :
            return lf.path
        return None

    def images(self) :
        """[(clé, chemin, description)] des images présentes."""
        return [(k, lf.path, lf.spec.description) for k, lf in self.files.items()
                if lf.spec.kind == 'image' and lf.exists]

    # --- audit / export ---------------------------------------------------
    def manifest(self, checksum=False) :
        """Inventaire complet des fichiers de l'analyse (DataFrame)."""
        return pd.DataFrame([lf.manifest_row(checksum=checksum)
                             for lf in self.files.values()])

    def to_dict(self, include_tables=False, checksum=False) :
        """Représentation sérialisable (base d'une future API)."""
        d = {
            'type' : self.type,
            'name' : self.name,
            'path' : str(self.path),
            'parametres' : self.parametres,
            'files' : [lf.manifest_row(checksum=checksum) for lf in self.files.values()],
        }
        if include_tables :
            d['tables'] = {}
            for key, lf in self.files.items() :
                if lf.spec.kind == 'table' and lf.spec.reader != 'skip' :
                    data = lf.load()
                    if isinstance(data, pd.DataFrame) :
                        d['tables'][key] = json.loads(
                            data.reset_index().to_json(orient='records', force_ascii=False))
        return d

    def to_json(self, **kwargs) :
        return json.dumps(self.to_dict(**kwargs), ensure_ascii=False, indent=2, default=str)


# ---------------------------------------------------------------------------
# le corpus
# ---------------------------------------------------------------------------

class Corpus :
    """Un répertoire de corpus IRaMuTeQ (Corpus.cira + bases SQLite + analyses)."""

    def __init__(self, path) :
        self.path = Path(path)
        self.cira = self.path / 'Corpus.cira'
        if not self.cira.exists() :
            raise FileNotFoundError('pas de Corpus.cira dans %s' % self.path)
        _, self.parametres = read_ira(self.cira)
        self.name = self.parametres.get('corpus_name', self.path.name)
        self.analyses = []
        for sub in sorted(self.path.iterdir()) :
            if sub.is_dir() and (sub / 'Analyse.ira').exists() :
                try :
                    self.analyses.append(Analysis(sub))
                except Exception as ex :
                    # une analyse illisible n'empêche pas de charger le reste
                    print('analyse ignorée (%s) : %s' % (sub, ex))

    # --- accès SQLite (lecture seule) --------------------------------------
    def _connect(self, dbname) :
        uri = 'file:%s?mode=ro' % (self.path / dbname)
        return sqlite3.connect(uri, uri=True)

    def variables(self) :
        """DataFrame [variable, modalite, textes] à partir des lignes étoilées."""
        rows = []
        with self._connect('corpus.db') as conn :
            for uci, et in conn.execute('SELECT uci, et FROM etoiles') :
                for etoile in str(et).split() :
                    if etoile.startswith('*') and etoile != '****' :
                        var = etoile.rsplit('_', 1)[0] if '_' in etoile else etoile
                        rows.append({'texte' : uci, 'variable' : var, 'modalite' : etoile})
        df = pd.DataFrame(rows)
        if df.empty :
            return pd.DataFrame(columns=['variable', 'modalite', 'textes'])
        return (df.groupby(['variable', 'modalite']).agg(textes=('texte', 'nunique'))
                  .reset_index())

    def forms(self) :
        """DataFrame des formes du corpus : forme, lemme, catégorie, effectif."""
        with self._connect('corpus.db') as conn :
            return pd.read_sql_query(
                'SELECT forme, lem, gram, freq FROM formes ORDER BY freq DESC', conn)

    def segments(self, ids=None, limit=None) :
        """Texte des segments (uces.db) ; `ids` = liste d'identifiants 0-based."""
        with self._connect('uces.db') as conn :
            if ids is not None :
                marks = ','.join('?' * len(ids))
                cur = conn.execute(
                    'SELECT id, uces FROM uces WHERE id IN (%s)' % marks, list(ids))
            elif limit is not None :
                cur = conn.execute('SELECT id, uces FROM uces LIMIT ?', (limit,))
            else :
                cur = conn.execute('SELECT id, uces FROM uces')
            return pd.DataFrame(cur.fetchall(), columns=['segment', 'texte'])

    def manifest(self, checksum=False) :
        rows = []
        for name, desc in [('Corpus.cira', 'paramètres du corpus'),
                           ('corpus.db', 'textes : variables étoilées et formes'),
                           ('formes.db', 'index formes -> segments'),
                           ('uces.db', 'texte des segments')] :
            p = self.path / name
            st = p.stat() if p.exists() else None
            rows.append({'fichier' : name, 'description' : desc, 'présent' : p.exists(),
                         'taille (octets)' : st.st_size if st else None,
                         'modifié le' : datetime.fromtimestamp(st.st_mtime).isoformat(' ', 'seconds') if st else None,
                         'sha256' : (hashlib.sha256(p.read_bytes()).hexdigest()
                                     if checksum and p.exists() else None),
                         'chemin' : str(p)})
        return pd.DataFrame(rows)

    def to_dict(self) :
        return {
            'name' : self.name,
            'path' : str(self.path),
            'parametres' : self.parametres,
            'analyses' : [{'type' : a.type, 'name' : a.name, 'path' : str(a.path)}
                          for a in self.analyses],
        }


def discover_corpora(root) :
    """Cherche les répertoires de corpus (contenant Corpus.cira) sous `root`."""
    root = Path(root)
    if not root.exists() :
        return []
    found = []
    if (root / 'Corpus.cira').exists() :
        found.append(root)
    for cira in sorted(root.glob('*/Corpus.cira')) :
        found.append(cira.parent)
    for cira in sorted(root.glob('*/*/Corpus.cira')) :
        if cira.parent not in found :
            found.append(cira.parent)
    return found


# ---------------------------------------------------------------------------
# projets : un sous-répertoire du dossier `projects/` qui regroupe le
# fichier corpus source, les fichiers .cfg du calcul, le journal run.log
# et les répertoires de résultats
# ---------------------------------------------------------------------------

def project_info(path) :
    """Description d'un répertoire de projet (pour la page d'accueil)."""
    path = Path(path)
    corpora = discover_corpora(path)
    analyses = [ira.parent for c in corpora for ira in Path(c).glob('*/Analyse.ira')]
    mtimes = [p.stat().st_mtime for p in [path] + corpora + analyses]
    return {
        'name' : path.name,
        'path' : str(path),
        'corpora' : [str(c) for c in corpora],
        'n_corpora' : len(corpora),
        'n_analyses' : len(analyses),
        'analyses_types' : sorted({read_ira(p / 'Analyse.ira')[0] for p in analyses}),
        'sources' : [str(p) for p in sorted(path.glob('*.txt'))],
        'configs' : [str(p) for p in sorted(path.glob('*.cfg'))],
        'modified' : datetime.fromtimestamp(max(mtimes)).isoformat(' ', 'seconds'),
    }


def discover_projects(root) :
    """Les projets = sous-répertoires (non cachés) du dossier `root`."""
    root = Path(root)
    if not root.exists() :
        return []
    out = []
    for child in sorted(root.iterdir()) :
        if child.is_dir() and not child.name.startswith('.') :
            try :
                out.append(project_info(child))
            except Exception as ex :
                out.append({'name' : child.name, 'path' : str(child),
                            'corpora' : [], 'n_corpora' : 0, 'n_analyses' : 0,
                            'analyses_types' : [], 'sources' : [], 'configs' : [],
                            'modified' : '', 'error' : str(ex)})
    return out


def _ensure_inside(target, root) :
    target = Path(target).resolve()
    root = Path(root).resolve()
    if target == root or root not in target.parents :
        raise ValueError('%s n\'est pas dans %s : suppression refusée'
                         % (target, root))
    return target


def delete_project(path, projects_root) :
    """Supprime un répertoire de projet (doit être DANS projects_root)."""
    import shutil
    target = _ensure_inside(path, projects_root)
    shutil.rmtree(target)


def delete_analysis(path) :
    """Supprime un répertoire d'analyse (doit contenir un Analyse.ira)."""
    import shutil
    path = Path(path).resolve()
    if not (path / 'Analyse.ira').exists() :
        raise ValueError('%s ne contient pas de Analyse.ira : suppression refusée'
                         % path)
    shutil.rmtree(path)
