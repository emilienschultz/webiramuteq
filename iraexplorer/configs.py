# -*- coding: utf-8 -*-
#License: GNU/GPL
"""Préparation de fichiers de configuration pour iracmd.py.

Charge les paramètres par défaut d'une analyse (depuis
``~/.iramuteq-<version>/`` si présent, sinon depuis ``configuration/``
du dépôt), permet de les modifier, puis écrit un ``.cfg`` spécifique —
au format attendu par ``DoConf`` — à passer à ``iracmd.py`` avec ``-c``
(analyses) ou ``-d`` (import du corpus).

Comme model.py : bibliothèque standard uniquement, aucune dépendance à
wxPython ni au code d'IRaMuTeQ, pour rester utilisable derrière une API.
"""

from __future__ import annotations

import ast
import configparser
from pathlib import Path

#: racine du dépôt IRaMuTeQ (parent de ce paquet)
APPLI_PATH = Path(__file__).resolve().parent.parent

#: pour chaque cible : fichier de défauts, section écrite, option iracmd
CONFIG_TEMPLATES = {
    'alceste' : {'source' : 'reinert.cfg', 'section' : 'ALCESTE', 'flag' : '-c'},
    'stat' : {'source' : 'stat.cfg', 'section' : 'stat', 'flag' : '-c'},
    'spec' : {'source' : None, 'section' : 'spec', 'flag' : '-c'},
    'simitxt' : {'source' : 'simitxt.cfg', 'section' : 'simitxt', 'flag' : '-c'},
    'corpus' : {'source' : 'corpus.cfg', 'section' : 'corpus', 'flag' : '-d'},
}

#: défauts de spec (pas de .cfg livré : mêmes valeurs que iracmd.py)
SPEC_DEFAULTS = {
    'lem' : 1,
    'mineff' : 3,
    'indice' : 'hypergeo',
    'typeformes' : 0,
    'etoiles' : [],
}

#: clés d'exécution écrites par IRaMuTeQ, sans intérêt en entrée
EXCLUDED_KEYS = {'type', 'pathout', 'name', 'corpus', 'uuid', 'ira', 'time',
                 'date', 'ucinb', 'ucenb', 'occurrences', 'filename',
                 'originalpath', 'encoding', 'syscoding', 'nbactives',
                 'eff_min_forme', 'corpus_name'}

#: aide et, le cas échéant, valeurs possibles des principaux paramètres
PARAM_HELP = {
    # alceste
    'classif_mode' : ('mode de classification : 0 = double sur UC, 1 = simple '
                      'sur segments, 2 = simple sur textes', [0, 1, 2]),
    'nbcl_p1' : ('nombre de classes de la phase 1', None),
    'mincl' : ('nombre minimum de segments par classe (0 = automatique)', None),
    'max_actives' : ('nombre maximum de formes actives', None),
    'tailleuc1' : ('taille du premier tableau UC (classif_mode 0)', None),
    'tailleuc2' : ('taille du second tableau UC (classif_mode 0)', None),
    'svdmethod' : ('méthode de décomposition', ['irlba', 'svdR', 'svdlibc']),
    'mode.patate' : ('mode rapide mais moins précis', [0, 1]),
    'minforme' : ('effectif minimum d\'une forme', None),
    'nbforme_uce' : ('nombre minimum de formes par segment (0 = automatique)', None),
    'lem' : ('lemmatisation', [True, False]),
    'expressions' : ('utiliser le dictionnaire des expressions', [True, False]),
    # spec
    'mineff' : ('effectif minimum d\'une forme', None),
    'indice' : ('indice de spécificité', ['hypergeo', 'chi2']),
    'typeformes' : ('formes retenues : 0 = actives et supplémentaires, '
                    '1 = actives, 2 = supplémentaires', [0, 1, 2]),
    'etoiles' : ('modalités comparées, ex. [\'*annee_2001\', \'*annee_2002\'] '
                 '(vide = première variable du corpus)', None),
    # simitxt
    'max_actives_simi' : ('nombre de formes les plus fréquentes retenues', None),
    'coeff' : ('indice de similitude (0 = cooccurrence)', None),
    'layout' : ('disposition du graphe : 0 = aléatoire, 1 = cercle, 2 = fruchterman', [0, 1, 2, 3]),
    'type_graph' : ('sortie : 0 = tkplot, 1 = png/svg, 2 = 3D', [0, 1, 2]),
    'arbremax' : ('arbre maximum', [True, False]),
    'seuil_ok' : ('appliquer un seuil sur les liens', [True, False]),
    'seuil' : ('valeur du seuil', None),
    # corpus
    'ucemethod' : ('découpage des segments : 0 = caractères, 1 = occurrences', [0, 1]),
    'ucesize' : ('taille des segments (en occurrences si ucemethod = 1)', None),
    'lower' : ('passage en minuscules', [True, False]),
    'ucimark' : ('marqueur de texte : 0 = ****, 1 = numéros', [0, 1]),
    'keep_ponct' : ('conserver la ponctuation', [True, False]),
    'apos' : ('remplacer les apostrophes par des espaces', [True, False]),
    'tiret' : ('remplacer les tirets par des espaces', [True, False]),
}


def parse_value(raw) :
    """Interprète une valeur de .cfg comme DoConf : int, booléen, liste, str."""
    if isinstance(raw, (int, float, bool, list, tuple)) :
        return raw
    raw = str(raw).strip()
    if raw.isdigit() :
        return int(raw)
    if raw in ('True', 'False') :
        return raw == 'True'
    if (raw.startswith('[') and raw.endswith(']')) or \
       (raw.startswith('(') and raw.endswith(')')) :
        try :
            return ast.literal_eval(raw)
        except (ValueError, SyntaxError) :
            return raw
    return raw


def format_value(value) :
    """Formate une valeur pour un .cfg relisible par DoConf."""
    if isinstance(value, bool) :
        return 'True' if value else 'False'
    if isinstance(value, (list, tuple)) :
        return repr(list(value))
    return str(value)


def user_config_dir() :
    """~/.iramuteq-<version> (peut ne pas exister encore)."""
    conf = configparser.ConfigParser(interpolation=None)
    # str() : le configparser vendoré à la racine du dépôt (copie ancienne
    # du stdlib) peut être importé à sa place et n'accepte pas les Path
    conf.read(str(APPLI_PATH / 'configuration' / 'global.cfg'))
    version = conf.get('DEFAULT', 'version_nb', fallback='0.8.a7')
    return Path.home() / ('.iramuteq-%s' % version)


def load_defaults(target) :
    """Paramètres par défaut éditables pour `target` -> (dict, source).

    `target` est une clé de CONFIG_TEMPLATES. Les défauts sont lus dans
    le répertoire utilisateur s'il existe (ce sont eux qu'utilise
    iracmd.py sans -c), sinon dans configuration/ du dépôt.
    """
    tpl = CONFIG_TEMPLATES[target]
    if tpl['source'] is None :
        return dict(SPEC_DEFAULTS), 'défauts internes (identiques à iracmd.py)'
    candidates = [user_config_dir() / tpl['source'],
                  APPLI_PATH / 'configuration' / tpl['source']]
    for path in candidates :
        if path.exists() :
            conf = configparser.ConfigParser(interpolation=None)
            with open(path, encoding='utf8') as f :
                conf.read_file(f)
            section = tpl['section'] if conf.has_section(tpl['section']) else conf.sections()[0]
            params = {}
            for option in conf.options(section) :
                if option not in EXCLUDED_KEYS :
                    params[option] = parse_value(conf.get(section, option))
            return params, str(path)
    return {}, 'aucune source trouvée'


def write_config(params, target, path) :
    """Écrit un .cfg mono-section pour iracmd.py ; retourne le contenu écrit."""
    tpl = CONFIG_TEMPLATES[target]
    lines = ['[%s]' % tpl['section']]
    for key, value in params.items() :
        if value is None or (isinstance(value, (list, str)) and len(value) == 0) :
            continue        # une clé absente laisse iracmd choisir son défaut
        lines.append('%s = %s' % (key, format_value(value)))
    content = '\n'.join(lines) + '\n'
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf8')
    return content


def build_command(target, cfg_path=None, corpus_file=None, corpus_cira=None,
                  lang=None, python='python') :
    """Construit la ligne de commande iracmd.py correspondante."""
    parts = [python, 'iracmd.py']
    if corpus_cira :
        parts += ['-r', str(corpus_cira)]
    elif corpus_file :
        parts += ['-f', str(corpus_file)]
    if target == 'corpus' :
        if cfg_path :
            parts += ['-d', str(cfg_path)]
        parts += ['-b']
    else :
        parts += ['-t', target]
        if cfg_path :
            parts += [CONFIG_TEMPLATES[target]['flag'], str(cfg_path)]
    if lang :
        parts += ['-l', lang]
    return ' '.join(str(p) for p in parts)
