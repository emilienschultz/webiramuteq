#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#Author: Pierre Ratinaud
#Copyright (c) 2008-2020 Pierre Ratinaud
#portage Python 3 du harnais en ligne de commande (iracmd)
#License: GNU/GPL

"""Interface en ligne de commande de IRaMuTeQ (sans interface graphique).

Construit un corpus au format Alceste et lance une analyse de texte :

    python iracmd.py -f corpus.txt -b                 # construire le corpus
    python iracmd.py -f corpus.txt -t alceste         # classification Reinert
    python iracmd.py -f corpus.txt -t stat            # statistiques
    python iracmd.py -f corpus.txt -t spec            # spécificités et AFC
    python iracmd.py -f corpus.txt -t simitxt         # analyse de similitudes
    python iracmd.py -r chemin/Corpus.cira -t stat    # réutiliser un corpus

R doit être installé ; son chemin est lu (ou détecté puis écrit) dans
~/.iramuteq-<version>/path.cfg, comme pour l'interface graphique.
"""

import argparse
import locale
import logging
import os
import shutil
import sys
import tempfile

from configparser import ConfigParser, RawConfigParser

from chemins import (ConstructConfigPath, ConstructDicoPath, PathOut,
                     RscriptsPath)
from checkinstall import (CreateIraDirectory, CheckRPath, FindRPAthWin32,
                          FindRPathNix)
import functions
from functions import DoConf, History, ReadDicoAsDico, ReadLexique, treat_var_mod

log = logging.getLogger('iramuteq')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
log.addHandler(ch)
log.setLevel(logging.INFO)


#-----------------------------------------------------------------------
# mode sans fenêtre : les classes d'analyse créent des wx.ProgressDialog
# et un dialogue de rapport de bug sans condition ; on les remplace avant
# que les modules d'analyse ne lient ces noms à l'import.
#-----------------------------------------------------------------------
class FakeProgressDialog :

    def Update(self, *args, **kwargs) :
        return (True, True)

    def Pulse(self, *args, **kwargs) :
        return (True, True)

    def Destroy(self) :
        pass


def cmd_progressbar(parent, maxi=None) :
    return FakeProgressDialog()


def cmd_bugreport(parent, error=None) :
    rerror = getattr(parent, 'Rerror', '')
    if rerror :
        log.error('erreur R :\n%s' % rerror)
        parent.Rerror = ''
    else :
        log.error('une erreur est survenue (voir les messages ci-dessus)')

functions.progressbar = cmd_progressbar
functions.BugReport = cmd_bugreport

from corpus import Corpus, BuildFromAlceste, copycorpus
from textreinert import Reinert
from textaslexico import Lexico
from textstat import Stat
from textsimi import SimiTxt


#-----------------------------------------------------------------------
# chemins de l'application et de l'utilisateur (comme iramuteq.py)
#-----------------------------------------------------------------------
AppliPath = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

ConfigGlob = ConfigParser()
ConfigGlob.read(os.path.join(AppliPath, 'configuration', 'global.cfg'))

user_home = os.getenv('HOME')
if user_home is None :
    user_home = os.path.expanduser('~')
UserConfigPath = os.path.abspath(os.path.join(user_home, '.iramuteq-%s' %
                                 ConfigGlob.get('DEFAULT', 'version_nb')))

# les analyses accessibles en ligne de commande et le fichier de
# configuration qui porte leurs paramètres par défaut
ANALYSES = {
    'alceste' : 'reinert',
    'reinert' : 'reinert',
    'stat' : 'stat',
    'spec' : None,
    'simitxt' : 'simitxt',
}


class LexicoCmd(Lexico) :
    """Spécificités sans dialogue : les modalités comparées viennent des
    parametres ('etoiles') ; à défaut, celles de la première variable
    étoilée du corpus. Chaque texte ne doit porter qu'une seule des
    modalités comparées (ce sont les modalités d'une même variable)."""

    def doanalyse(self) :
        listet = self.parametres.get('etoiles', [])
        if not listet :
            var_mod = treat_var_mod(self.corpus.make_etoiles())
            variables = sorted([v for v in var_mod if len(var_mod[v]) > 1])
            if not variables :
                log.error("aucune variable étoilée avec plusieurs modalités ;"
                          " renseigner 'etoiles' dans le fichier -c")
                return 'NOK'
            listet = var_mod[variables[0]]
            log.info("modalités comparées (variable '%s') : %s -- pour en choisir"
                     " d'autres, renseigner 'etoiles' dans le fichier -c"
                     % (variables[0], ', '.join(sorted(listet))))
        listet.sort()
        self.listet = listet
        self.parametres['clnb'] = len(listet)
        return Lexico.doanalyse(self)


class CmdLine :

    def __init__(self, args=None) :
        self.AppliPath = AppliPath
        self.UserConfigPath = UserConfigPath
        self.makeuserconf()
        self.ConfigPath = ConstructConfigPath(UserConfigPath)
        self.DictPath = ConstructDicoPath(UserConfigPath)
        self.ConfigGlob = ConfigGlob
        self.syscoding = sys.getdefaultencoding()
        self.TEMPDIR = tempfile.mkdtemp('iramuteq')
        self.RscriptsPath = PathOut(dirout=os.path.join(AppliPath, 'Rscripts'))
        self.RscriptsPath.basefiles(RscriptsPath)
        self.pref = RawConfigParser()
        self.pref.read(self.ConfigPath['preferences'])
        self.Rerror = ''
        if not os.path.exists(os.path.join(UserConfigPath, 'history.db')) :
            with open(os.path.join(UserConfigPath, 'history.db'), 'w', encoding='utf8') as f :
                f.write('{}')
        self.history = History(os.path.join(UserConfigPath, 'history.db'))

        options = self.doparse(args)

        config = self.getconfig(options)
        if config is None and not (options.build and options.filename) and not options.read :
            log.info('rien à faire (voir --help)')
            return

        self.corpus_encodage = options.encodage
        self.corpus_lang = options.language
        self.keys = DoConf(self.ConfigPath['key']).getoptions()
        gramact = [k for k in self.keys if self.keys[k] == 1]
        gramsup = [k for k in self.keys if self.keys[k] == 2]

        ReadLexique(self, lang=options.language)
        expath = self.DictPath.get(options.language + '_exp', self.DictPath['french_exp'])
        if options.language != 'other' and os.path.exists(expath) :
            self.expressions = ReadDicoAsDico(expath)
        else :
            self.expressions = {}

        if options.filename :
            corpus = self.buildcorpus(options)
        elif options.read :
            corpus = self.readcorpus(options)
        else :
            log.info('aucun corpus (utiliser -f ou -r)')
            return

        if corpus is None or config is None :
            return

        self.checkrpath()
        corpus.conn_all()
        corpus.make_lems()
        corpus.parse_active(gramact, gramsup)

        type_analyse = options.type_analyse
        if type_analyse in ('alceste', 'reinert') :
            config['type'] = 'alceste'
            self.Text = Reinert(self, corpus, parametres=config)
        elif type_analyse == 'stat' :
            config['type'] = 'stat'
            self.Text = Stat(self, corpus, parametres=config)
        elif type_analyse == 'spec' :
            config['type'] = 'spec'
            self.Text = LexicoCmd(self, corpus, parametres=config)
        elif type_analyse == 'simitxt' :
            config['type'] = 'simitxt'
            if 'selected' not in config :
                # sans dialogue de sélection des formes, on garde les plus
                # fréquentes pour éviter une matrice de similitude énorme
                nbmax = config.pop('max_actives_simi', 200)
                actives = corpus.make_actives_limit(3)
                config['selected'] = list(range(min(len(actives), nbmax)))
                if len(actives) > nbmax :
                    log.info('similitudes sur les %i formes actives les plus'
                             ' fréquentes (sur %i) ; ajuster avec'
                             " 'max_actives_simi' dans le fichier -c" % (nbmax, len(actives)))
            for key, val in [('svg', 0), ('com', 0), ('communities', 0), ('halo', 0)] :
                config.setdefault(key, val)
            self.Text = SimiTxt(self, corpus, parametres=config)
        if getattr(self, 'Text', None) is not None and self.Text.parametres.get('time', False) :
            log.info('analyse terminée (%s) : %s' % (self.Text.parametres['time'],
                     self.Text.parametres.get('pathout', '')))

    def doparse(self, args) :
        parser = argparse.ArgumentParser(
            prog='iracmd',
            description="analyses textuelles de IRaMuTeQ en ligne de commande")
        parser.add_argument('-f', '--file', dest='filename', metavar='FILE',
                            default=None, help='chemin du corpus (format Alceste)')
        parser.add_argument('-t', '--type', dest='type_analyse', metavar='TYPE',
                            default=None, choices=sorted(ANALYSES),
                            help="type d'analyse : %s" % ', '.join(sorted(ANALYSES)))
        parser.add_argument('-c', '--conf', dest='configfile', metavar='CONF',
                            default=None, help="fichier de configuration de l'analyse")
        parser.add_argument('-d', '--confcorp', dest='corpusconfigfile', metavar='CONF',
                            default=None, help='fichier de configuration du corpus')
        parser.add_argument('-e', '--enc', dest='encodage', metavar='ENC',
                            default='utf-8', help='encodage du corpus (défaut : utf-8)')
        parser.add_argument('-l', '--lang', dest='language', metavar='LANG',
                            default='french', help='langue du corpus (défaut : french)')
        parser.add_argument('-r', '--read', dest='read', metavar='CORPUS.cira',
                            default=None, help='réutiliser un corpus déjà construit (fichier Corpus.cira)')
        parser.add_argument('-b', '--build', action='store_true', dest='build',
                            default=False, help='construire le corpus sans lancer d\'analyse')
        return parser.parse_args(args)

    def makeuserconf(self) :
        """création de ~/.iramuteq-<version> et copie des fichiers de
        configuration et des dictionnaires manquants (sans écraser)"""
        CreateIraDirectory(UserConfigPath, AppliPath)
        userconf = ConstructConfigPath(UserConfigPath)
        appliconf = ConstructConfigPath(AppliPath, user=False)
        for item, filein in userconf.items() :
            if not os.path.exists(filein) and os.path.exists(appliconf[item]) :
                shutil.copyfile(appliconf[item], filein)
        userdico = ConstructDicoPath(UserConfigPath)
        applidico = ConstructDicoPath(AppliPath)
        for fi in userdico :
            if not os.path.exists(userdico[fi]) and os.path.exists(applidico[fi]) :
                shutil.copyfile(applidico[fi], userdico[fi])

    def checkrpath(self) :
        """chemin du binaire R : lu dans path.cfg, sinon détecté puis écrit"""
        self.PathPath = ConfigParser()
        self.PathPath.read(self.ConfigPath['path'])
        if not CheckRPath(self.PathPath) :
            if sys.platform == 'win32' :
                BestRPath = FindRPAthWin32()
            else :
                BestRPath = FindRPathNix()
                if not BestRPath and sys.platform == 'darwin' :
                    for path in ['/Library/Frameworks/R.framework/Resources/bin/R', '/opt/homebrew/bin/R'] :
                        if os.path.exists(path) :
                            BestRPath = path
                            break
            if BestRPath :
                self.PathPath.set('PATHS', 'rpath', BestRPath)
                with open(self.ConfigPath['path'], 'w', encoding='utf8') as f :
                    self.PathPath.write(f)
            else :
                log.error("R introuvable. Installer R (http://www.r-project.org) ou renseigner"
                          " rpath dans %s" % self.ConfigPath['path'])
                sys.exit(1)
        self.RPath = self.PathPath.get('PATHS', 'rpath')

    def getconfig(self, options) :
        """paramètres de l'analyse : fichier -c, sinon défauts de ~/.iramuteq-<version>"""
        if options.type_analyse is None :
            return None
        if options.configfile is not None :
            config = DoConf(os.path.abspath(options.configfile)).getoptions()
        elif options.type_analyse == 'spec' :
            config = {'type' : 'spec', 'lem' : 1, 'mineff' : 3,
                      'indice' : 'hypergeo', 'typeformes' : 0}
        else :
            config = DoConf(self.ConfigPath[ANALYSES[options.type_analyse]]).getoptions()
        # les .cfg livrés contiennent des valeurs vides (pathout, name...)
        # qui ne doivent pas masquer les valeurs calculées par l'analyse
        return dict([(k, v) for k, v in config.items() if v != ''])

    def buildcorpus(self, options) :
        self.filename = os.path.abspath(options.filename)
        if options.corpusconfigfile is not None :
            corpus_parametres = DoConf(os.path.abspath(options.corpusconfigfile)).getoptions('corpus')
        else :
            corpus_parametres = DoConf(self.ConfigPath['corpus']).getoptions()
        dire, corpus_parametres['filename'] = os.path.split(self.filename)
        corpus_parametres['originalpath'] = self.filename
        corpus_parametres['encoding'] = self.corpus_encodage
        corpus_parametres['lang'] = self.corpus_lang
        corpus_parametres['syscoding'] = sys.getdefaultencoding()
        corpus_parametres['pathout'] = PathOut(self.filename, 'corpus').mkdirout()
        if not corpus_parametres.get('corpus_name', '') :
            corpus_parametres['corpus_name'] = os.path.split(corpus_parametres['pathout'])[1]
        try :
            corpus = BuildFromAlceste(self.filename, corpus_parametres,
                                      self.lexique, self.expressions).corpus
        except Exception as txt :
            log.error('problème lors de la construction : %s' % txt)
            raise
        self.history.add(corpus.parametres)
        log.info('corpus construit dans %s' % corpus_parametres['pathout'])
        return copycorpus(corpus)

    def readcorpus(self, options) :
        cira = os.path.abspath(options.read)
        corpus_parametres = DoConf(cira).getoptions('corpus')
        corpus_parametres['pathout'] = os.path.dirname(cira)
        corpus = Corpus(self, parametres=corpus_parametres, read=True)
        log.info('corpus %s (%s)' % (corpus_parametres.get('corpus_name', '?'),
                 corpus_parametres['pathout']))
        return corpus


if __name__ == '__main__' :
    CmdLine()
