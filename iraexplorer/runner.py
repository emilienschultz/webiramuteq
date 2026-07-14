# -*- coding: utf-8 -*-
#License: GNU/GPL
"""Exécution d'un calcul complet via iracmd.py.

Enchaîne la construction du corpus (``-f ... -b``) puis chaque analyse
(``-r <Corpus.cira> -t <type> -c <cfg>``), en sous-processus, avec le
même interpréteur Python que celui indiqué (qui doit disposer de
wxPython). Chaque étape est consignée dans un ``RunStep`` (commande
exacte, code retour, sorties) et, si demandé, dans un fichier journal —
de quoi rejouer ou auditer le calcul a posteriori.

Comme les autres modules du paquet : bibliothèque standard uniquement.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


@dataclass
class RunStep:
    """Une étape du pipeline : commande lancée et résultat."""
    label: str
    cmd: list
    returncode: int = None
    stdout: str = ''
    stderr: str = ''
    started: str = ''
    ended: str = ''

    @property
    def ok(self) :
        return self.returncode == 0

    def command_line(self) :
        return ' '.join(str(c) for c in self.cmd)

    def as_text(self) :
        return '\n'.join([
            '### %s [%s -> %s] code retour : %s' % (self.label, self.started,
                                                    self.ended, self.returncode),
            '$ %s' % self.command_line(),
            self.stdout or '',
            self.stderr or '',
        ])


def corpus_dirs_for(corpus_file) :
    """Répertoires <stem>_corpus_N déjà créés pour ce fichier corpus."""
    f = Path(corpus_file)
    return {p.parent for p in f.parent.glob(f.stem + '_corpus_*/Corpus.cira')}


def _run(label, cmd, cwd, timeout) :
    started = datetime.now().isoformat(' ', 'seconds')
    try :
        proc = subprocess.run([str(c) for c in cmd], cwd=str(cwd),
                              capture_output=True, text=True, timeout=timeout)
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as ex :
        rc, out, err = -1, ex.stdout or '', 'délai dépassé (%is)' % timeout
    except OSError as ex :
        rc, out, err = -1, '', str(ex)
    return RunStep(label, cmd, rc, out, err, started,
                   datetime.now().isoformat(' ', 'seconds'))


def run_pipeline(python, analyses, corpus_file=None, corpus_cira=None,
                 corpus_cfg=None, lang=None, encoding=None,
                 cwd=REPO, timeout=3600, log_path=None, on_step=None) :
    """Lance le calcul complet ; retourne (liste de RunStep, Corpus.cira).

    - `analyses` : liste de couples (type, chemin_du_cfg_ou_None) ;
    - `corpus_file` : fichier corpus au format Alceste -> le corpus est
      d'abord construit (avec `corpus_cfg` en -d le cas échéant) ;
    - `corpus_cira` : réutiliser un corpus déjà construit (exclusif de
      `corpus_file`) ;
    - `on_step(step)` : rappel après chaque étape (affichage progressif).
    """
    steps = []

    def emit(step) :
        steps.append(step)
        if log_path :
            Path(log_path).parent.mkdir(parents=True, exist_ok=True)
            Path(log_path).write_text(
                '\n\n'.join(s.as_text() for s in steps), encoding='utf8')
        if on_step :
            on_step(step)
        return step

    iracmd = Path(cwd) / 'iracmd.py'
    if corpus_cira is None :
        if corpus_file is None :
            raise ValueError('corpus_file ou corpus_cira est requis')
        before = corpus_dirs_for(corpus_file)
        cmd = [python, iracmd, '-f', corpus_file, '-b']
        if corpus_cfg :
            cmd += ['-d', corpus_cfg]
        if lang :
            cmd += ['-l', lang]
        if encoding :
            cmd += ['-e', encoding]
        step = emit(_run('construction du corpus', cmd, cwd, timeout))
        if not step.ok :
            return steps, None
        created = corpus_dirs_for(corpus_file) - before
        if not created :
            created = corpus_dirs_for(corpus_file)
        if not created :
            emit(RunStep('localisation du corpus construit', [], -1, '',
                         'aucun répertoire *_corpus_* trouvé après la construction'))
            return steps, None
        newest = max(created, key=lambda p : p.stat().st_mtime)
        corpus_cira = newest / 'Corpus.cira'

    for atype, cfg in analyses :
        cmd = [python, iracmd, '-r', corpus_cira, '-t', atype]
        if cfg :
            cmd += ['-c', cfg]
        if lang :
            cmd += ['-l', lang]
        emit(_run('analyse %s' % atype, cmd, cwd, timeout))
        # les analyses sont indépendantes : on continue même après un échec

    return steps, corpus_cira
