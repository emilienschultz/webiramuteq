# -*- coding: utf-8 -*-
#Author: Pierre Ratinaud
#Copyright (c) 2008-2020 Pierre Ratinaud
#modification pour python 3 : Laurent Mérat, 6x7 - mai 2020
#License: GNU/GPL

#------------------------------------
# import des modules python
#------------------------------------
import os
import sys
import tempfile
import logging


log = logging.getLogger('iramuteq.chemins')


def normpath_win32(path) :
    if not sys.platform == 'win32' :
        return path
    while '\\\\' in path :
        path = path.replace('\\\\', '\\')
    if sys.platform == 'win32' and path.startswith('\\') and not path.startswith('\\\\') :
        path = '\\' + path
    return path

class PathOut :
    def __init__(self, filename = None, analyse_type = '', dirout = None) :
        if filename is not None :
            self.filepath = os.path.abspath(filename)
            self.filebasename = os.path.basename(filename)
            self.directory = os.path.abspath(os.path.dirname(filename))
            self.filename, self.fileext = os.path.splitext(self.filebasename)
        self.analyse = analyse_type
        #self.dirout = self.mkdirout(dirout)
        if dirout is not None:
            self.dirout = os.path.abspath(dirout)
        elif filename is not None and dirout is None:
            self.dirout = os.path.abspath(self.directory)
        self.d = {}

    def mkdirout(self) :
        dirout = os.path.join(self.dirout, self.filename + '_' + self.analyse + '_')
        nb = 1
        tdirout = dirout + repr(nb)
        while os.path.exists(tdirout) :
            nb += 1
            tdirout = dirout + repr(nb)
        self.name = os.path.splitext(tdirout)[1]
        return tdirout

    def makenew(self, filename, ext):
        nb = 1
        newfile = '_'.join([os.path.join(self.dirout, filename), '%i' % nb]) + '.' + ext
        while os.path.exists(newfile) :
            nb += 1
            newfile = '_'.join([os.path.join(self.dirout, filename), '%i' % nb]) + '.' + ext
        return newfile

    def createdir(self, tdirout) :
        if not os.path.exists(tdirout) :
            os.mkdir(tdirout)

    def basefiles(self, ndict) :
        self.d = ndict

    def __getitem__(self, key) :
        if key == 'temp' :
            self.temp = tempfile.mkstemp(prefix='iramuteq')[1].replace('\\', '\\\\')
            return self.temp
        elif key not in self.d :
            f = os.path.join(self.dirout, key).replace('\\', '\\\\')
            return normpath_win32(f)
            #return os.path.join(self.dirout, key).replace('\\', '\\\\')
        else :
            f = os.path.join(self.dirout, self.d[key]).replace('\\', '\\\\')
            return normpath_win32(f)
            #return os.path.join(self.dirout, self.d[key]).replace('\\', '\\\\')

    def getF(self, key) :
        return self.__getitem__(key).replace('\\', '/')

def ffr(filename):
    return filename.replace('\\', '\\\\')

def FFF(filename):
    return filename.replace('\\', '/')

RscriptsPath = {
        'Rfunct': 'Rfunct.R',
        'chdfunct': 'chdfunct.R',
        'Rgraph': 'Rgraph.R',
        'plotafcm': 'plotafcm.R',
        'afc_graph' : 'afc_graph.R',
        #'CHD': 'CHDPOND.R',
        'CHD': 'CHD.R',
        #'CHD' : 'NCHD.R',
        'chdtxt': 'chdtxt.R',
        'chdquest': 'chdquest.R',
        'pamtxt' : 'pamtxt.R',
        'anacor' : 'anacor.R',
        #'anacor' : 'Nanacor.R',
        'simi' : 'simi.R',
    }

def ConstructRscriptsPath(AppliPath):
    RScriptsPath = os.path.join(AppliPath, 'Rscripts')
    #print('@@@@@@@@@@@PONDERATION CHDPOND.R@@@@@@@@@@@@@@@@')
    #print('@@@@@@@@@@@ NEW SVD CHEMIN @@@@@@@@@@@@@@@@')
    #print '@@@@@@@@@@@ NEW NCHD CHEMIN @@@@@@@@@@@@@@@@'
    DictRscripts = {
        'Rfunct': ffr(os.path.join(RScriptsPath, 'Rfunct.R')),
        'chdfunct': ffr(os.path.join(RScriptsPath, 'chdfunct.R')),
        'Rgraph': ffr(os.path.join(RScriptsPath, 'Rgraph.R')),
        'plotafcm': ffr(os.path.join(RScriptsPath, 'plotafcm.R')),
        'afc_graph' : ffr(os.path.join(RScriptsPath, 'afc_graph.R')),
        #'CHD': ffr(os.path.join(RScriptsPath, 'CHDPOND.R')),
        'CHD': ffr(os.path.join(RScriptsPath, 'CHD.R')),
        #'CHD' : ffr(os.path.join(RScriptsPath, 'NCHD.R')),
        'chdtxt': ffr(os.path.join(RScriptsPath, 'chdtxt.R')),
        'chdquest': ffr(os.path.join(RScriptsPath, 'chdquest.R')),
        'pamtxt' : ffr(os.path.join(RScriptsPath, 'pamtxt.R')),
        'anacor' : ffr(os.path.join(RScriptsPath, 'anacor.R')),
        #'anacor' : ffr(os.path.join(RScriptsPath, 'Nanacor.R')),
        'simi' : ffr(os.path.join(RScriptsPath, 'simi.R')),
    }
    return DictRscripts

def ConstructPathOut(Filename, analyse_type):
    FileBaseName = os.path.basename(Filename)
    FileBasePath = os.path.dirname(Filename)
    PathFile = os.path.splitext(FileBaseName)
    PathFile = os.path.join(FileBasePath, PathFile[0] + '_' + analyse_type + '_1')
    splitpath = PathFile.split('_')
    number = int(splitpath[len(splitpath) - 1])
    while os.path.isdir(PathFile) :
        if number < 10:
            PathFile = PathFile[0:len(PathFile) - 1] + str(number + 1)
            pass
        elif (number >= 10) and (number < 100):
            PathFile = PathFile[0:len(PathFile) - 2] + str(number + 1)
            pass
        elif number >= 100 :
            PathFile = PathFile[0:len(PathFile) - 3] + str(number + 1)
            pass
        number += 1
    os.mkdir(os.path.join(FileBasePath, PathFile))
    return os.path.join(FileBasePath, PathFile)

def ConstructConfigPath(AppliPath, user=True):
    if not user:
        ConfigPath = os.path.join(AppliPath, 'configuration')
    else :
        ConfigPath = AppliPath
    DictConfigPath = {
        'reinert': os.path.join(ConfigPath, 'reinert.cfg'),
        #'key': os.path.join(ConfigPath, 'spacykeyfr.cfg'),
        'key': os.path.join(ConfigPath, 'key.cfg'),
        'path': os.path.join(ConfigPath, 'path.cfg'),
        'preferences' : os.path.join(ConfigPath, 'iramuteq.cfg'),
        'pam' : os.path.join(ConfigPath, 'pam.cfg'),
        'corpus' : os.path.join(ConfigPath, 'corpus.cfg'),
        'stat' : os.path.join(ConfigPath, 'stat.cfg'),
        'simitxt' : os.path.join(ConfigPath, 'simitxt.cfg'),
        'matrix' : os.path.join(ConfigPath, 'matrix.cfg'),
    }
    return DictConfigPath

def ConstructGlobalPath(AppliPath):
    ConfigPath = os.path.join(AppliPath, 'configuration')
    DictConfigPath = {
            'global': os.path.join(ConfigPath, 'global.cfg'),
            'preferences': os.path.join(ConfigPath, 'iramuteq.cfg'),
            }
    return DictConfigPath

def ConstructDicoPath(AppliPath):
    BasePath = os.path.join(AppliPath, 'dictionnaires')
    DictPath = {
        'french': os.path.join(BasePath, 'lexique_fr.txt'),
        'french_exp': os.path.join(BasePath, 'expression_fr.txt'),
        'english': os.path.join(BasePath, 'lexique_en.txt'),
        'english_exp': os.path.join(BasePath, 'expression_en.txt'),
        'german' :  os.path.join(BasePath, 'lexique_de.txt'),
        'german_exp' : os.path.join(BasePath, 'expression_de.txt'),
        'italian' : os.path.join(BasePath, 'lexique_it.txt'),
        'italian_exp' : os.path.join(BasePath, 'expression_it.txt'),
        'swedish' :  os.path.join(BasePath, 'lexique_sw.txt'),
        'swedish_exp' :  os.path.join(BasePath, 'expression_sw.txt'),
        'portuguese' : os.path.join(BasePath, 'lexique_pt.txt'),
        'portuguese_exp': os.path.join(BasePath, 'expression_pt.txt'),
        'greek' : os.path.join(BasePath, 'lexique_gr.txt'),
        'greek_exp' : os.path.join(BasePath, 'expression_gr.txt'),
        'spanish' :  os.path.join(BasePath, 'lexique_sp.txt'),
        'spanish_exp' :  os.path.join(BasePath, 'expression_sp.txt'),
        'galician' : os.path.join(BasePath, 'lexique_gl.txt'),
        'galician_exp' : os.path.join(BasePath, 'expression_gl.txt'),
        'dutch' : os.path.join(BasePath, 'lexique_nl.txt'),
        'norwegian' :  os.path.join(BasePath, 'lexique_nn.txt'),
    }
    return DictPath

def ConstructAfcmPath(FilePath):
    DictAfcmPath = {
        'Levels': ffr(os.path.join(FilePath, 'afcm-levels.csv')),
        'nd': ffr(os.path.join(FilePath, 'afcm-nd.csv')),
        'FileActTemp': ffr(os.path.join(FilePath, 'fileActTamp.csv')),
        'FileEtTemp': ffr(os.path.join(FilePath, 'FileEtTemp')),
        'resultat': os.path.join(FilePath, 'Resultats-afcm.html'),
        'Rafc3d': ffr(tempfile.mkstemp(prefix='iramuteq')[1])
    }
    return DictAfcmPath

def ConstructAfcUciPath(filepath):
    DictAfcUciPath = {
        'TableCont': ffr(os.path.join(filepath, 'TableCont.csv')),
        'TableSup': ffr(os.path.join(filepath, 'TableSup.csv')),
        'TableEt': ffr(os.path.join(filepath, 'TableEt.csv')),
        'AfcColAct': ffr(os.path.join(filepath, 'AfcColAct.png')),
        'AfcColSup': ffr(os.path.join(filepath, 'AfcColSup.png')),
        'AfcColEt': ffr(os.path.join(filepath, 'AfcColEt.png')),
        'afcdiv4': ffr(os.path.join(filepath, 'afcdiv4_')),
        'AfcRow': ffr(os.path.join(filepath, 'AfcRow.png')),
        'ListAct': ffr(os.path.join(filepath, 'ListAct.csv')),
        'ListSup': ffr(os.path.join(filepath, 'ListSup.csv')),
        'GraphAfcTot': os.path.join(filepath, 'GraphAfcTot.html'),
        'Rafcuci': ffr(tempfile.mkstemp(prefix='iramuteq')[1]),
        'afc_row': ffr(os.path.join(filepath, 'afc_row.csv')),
        'afc_col': ffr(os.path.join(filepath, 'afc_col.csv')),
        'ira' : os.path.join(filepath, 'Analyse.ira'),
    }
    return DictAfcUciPath

ChdTxtPathOut = {'TableUc1': 'TableUc1.csv',
        'TableUc2': 'TableUc2.csv',
        'listeuce1':  'listeUCE1.csv',
        'listeuce2':  'listeUCE2.csv',
        'DicoMots':  'DicoMots.csv',
        'DicoLem':  'DicoLem.csv',
        'profile':  'profiles.csv',
        'antiprofile':  'antiprofiles.csv',
        'afc':  'AFC.csv',
        'rapport':  'RAPPORT.txt',
        'pre_rapport' : 'info.txt',
        'uce':  'uce.csv',
        'Rchdtxt': tempfile.mkstemp(prefix='iramuteq')[1].replace('\\', '\\\\'),
        'arbre1':  'arbre_1.png',
        'arbre2':  'arbre_2.png',
        'dendro1':  'dendro1.png',
        'dendro2':  'dendro2.png',
        'Rdendro':  'dendrogramme.RData',
        'Contout':  'classe_mod.csv',
        'RData':  'RData.RData',
        'ContSupOut':  'tablesup.csv',
        'ContEtOut':  'tableet.csv',
        'PROFILE_OUT':  'profiles.csv',
        'ANTIPRO_OUT':  'antiprofiles.csv',
        'SbyClasseOut':  'SbyClasseOut.csv',
        'chisqtable' :  'chisqtable.csv',
        'ptable' :  'ptable.csv',
        'ira': 'Analyse.ira',
        'AFC2DL_OUT':  'AFC2DL.png',
        'AFC2DSL_OUT':  'AFC2DSL.png',
        'AFC2DEL_OUT':  'AFC2DEL.png',
        'AFC2DCL_OUT':  'AFC2DCL.png',
        'AFC2DCoul':  'AFC2DCoul.png',
        'AFC2DCoulSup':  'AFC2DCoulSup.png',
        'AFC2DCoulEt':  'AFC2DCoulEt.png',
        'AFC2DCoulCl':  'AFC2DCoulCl.png',
        'Rafc3d': tempfile.mkstemp(prefix='iramuteq')[1].replace('\\', '\\\\'),
        'R3DCoul': tempfile.mkstemp(prefix='iramuteq')[1].replace('\\', '\\\\'),
        'RESULT_CHD':  'resultats-chd.html',
        'RESULT_AFC':  'resultats-afc.html',
        'Et01':  'Et01.csv',
        'Rchdquest':tempfile.mkstemp(prefix='iramuteq')[1].replace('\\', '\\\\'),
        'RTxtProfGraph':tempfile.mkstemp(prefix='iramuteq')[1].replace('\\', '\\\\'),
        'typelist': 'typelist.csv',
        'concord':'concordancier.csv',
        'bduceforme':'bduceforme.csv',
        'uceuci': 'uceuci.csv',
        'uciet': 'uciet.csv',
        'ContTypeOut': 'tabletype.csv',
        'liste_graph_afc' : 'liste_graph_afc.txt',
        'liste_graph_chd' : 'liste_graph_chd.txt',
        'afc_row':  'afc_row.csv',
        'afc_col':  'afc_col.csv',
        'afc_facteur':  'afc_facteur.csv',
        'corpus_exp' : 'corpus_out.txt',
        'segments_classes' :  'segments_classes.csv',
        'prof_seg' :  'prof_segments.csv',
        'antiprof_seg' :  'antiprof_segments.csv',
        'prof_type' :  'profil_type.csv',
        'antiprof_type' :  'antiprof_type.csv',
        'type_cl' :  'type_cl.csv',
        'db' : 'analyse.db',
    }

def StatTxtPathOut(pathout):
    d = {'tableafcm':ffr(os.path.join(pathout, 'tableafcm.csv')),
          'tabletypem': ffr(os.path.join(pathout, 'tabletypem.csv')),
          'tablespecf': ffr(os.path.join(pathout, 'tablespecf.csv')),
          'tablespect': ffr(os.path.join(pathout, 'tablespect.csv')),
          'eff_relatif_forme': ffr(os.path.join(pathout, 'eff_relatif_forme.csv')),
          'eff_relatif_type': ffr(os.path.join(pathout, 'eff_relatif_type.csv')),
          'afcf_row' : ffr(os.path.join(pathout, 'afcf_row.png')),
          'afcf_col' : ffr(os.path.join(pathout, 'afcf_col.png')),
          'afct_row' : ffr(os.path.join(pathout, 'afct_row.png')),
          'afct_col' : ffr(os.path.join(pathout, 'afct_col.png')),
          'RData' : ffr(os.path.join(pathout, 'RData.RData')),
          'liste_graph_afcf' : os.path.join(pathout, 'liste_graph_afcf.txt'),
          'liste_graph_afct' : os.path.join(pathout, 'liste_graph_afct.txt'),
          'afcf_row_csv': ffr(os.path.join(pathout, 'afcf_row.csv')),
          'afcf_col_csv': ffr(os.path.join(pathout, 'afcf_col.csv')),
          'afcf_facteur_csv': ffr(os.path.join(pathout, 'afcf_facteur.csv')),
          'afct_row_csv': ffr(os.path.join(pathout, 'afct_row.csv')),
          'afct_col_csv': ffr(os.path.join(pathout, 'afct_col.csv')),
          'afct_facteur_csv': ffr(os.path.join(pathout, 'afct_facteur.csv')),
          'ira' : ffr(os.path.join(pathout, 'Analyse.ira')),
          'db' : os.path.join(pathout, 'analyse.db'),
          'zipf' : ffr(os.path.join(pathout, 'zipf.png')),
    }
    return d

# ???
#def construct_simipath(pathout):
#    d = {'mat01' : 'mat01.csv',
#          'matsimi' : 'matsimi.csv',
#          'eff' : 'eff.csv',
#          'RData' : 'RData.RData',
#          'liste_graph' : 'liste_graph.txt',
#          'ira' : 'Analyse.ira',
#          'film' : '',
#          'db' : 'analyse.db',
#        }

simipath = {'mat01' :  'mat01.csv',
          'matsimi' : 'matsimi.csv',
          'eff' : 'eff.csv',
          'RData' : 'RData.RData',
          'liste_graph' :'liste_graph.txt',
          'ira' : 'Analyse.ira',
          'film' : '',
          'db' : 'analyse.db',
          'corpus' : 'corpus.db',
        }

