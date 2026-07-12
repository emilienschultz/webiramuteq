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
import shutil
from time import sleep
import logging
import tempfile

#------------------------------------
# import des modules wx
#------------------------------------
import wx

#------------------------------------
# import des fichiers du projet
#------------------------------------
from chemins import ConstructConfigPath, ConstructDicoPath
from functions import exec_rcode, exec_RCMD
from configparser import *

log = logging.getLogger('iramuteq.checkinstall')


def IsNew(self):
    version_glob = self.ConfigGlob.get('DEFAULT', 'version_nb').split('.')
    try :
        version_user = self.pref.get('iramuteq','version_nb').split('.')
    except NoOptionError :
        return True
    userab = False
    globab = False
    if version_user :
        version_user[0] = int(version_user[0])
        version_user[1] = int(version_user[1])
        version_glob[0] = int(version_glob[0])
        version_glob[1] = int(version_glob[1])
        if len(version_user) == 3 :
            if 'a' in version_user[2] :
                userab = 'a'
                version_user[2] = int(version_user[2].replace('a', ''))
            elif 'b' in version_user[2] :
                userab = 'b'
                version_user[2] = int(version_user[2].replace('b', ''))
            else :
                version_user[2] = int(version_user[2])
        if len(version_glob) == 3 :
            if 'a' in version_glob[2] :
                globab = 'a'
                version_glob[2] = int(version_glob[2].replace('a', ''))
            elif 'b' in version_glob[2] :
                globab = 'b'
                version_glob[2] = int(version_glob[2].replace('b', ''))
            else :
                version_glob[2] = int(version_glob[2])
        if len(version_user) == len(version_glob) :
            if version_glob > version_user :
                return True
            elif version_glob == version_user :
                if globab == userab :
                    return False
                elif globab > userab :
                    return True
                else :
                    return False
            else :
                return False
        else :
            if version_glob > version_user :
                return True
            else :
                return False

def UpgradeConf(self) :
    log.info('upgrade conf')
    dictuser = self.ConfigPath
    dictappli = ConstructConfigPath(self.AppliPath, user = False)
    for item,filein in dictuser.items():
        if not item == 'global' and not item == 'history':
            shutil.copyfile(dictappli[item], filein)
    dicoUser = self.DictPath
    dicoAppli = ConstructDicoPath(self.AppliPath)
    for fi in dicoUser :
        if not os.path.exists(dicoUser[fi]) and os.path.exists(dicoAppli[fi]):
            shutil.copyfile(dicoAppli[fi], dicoUser[fi])

def CreateIraDirectory(UserConfigPath,AppliPath):
    if not os.path.exists(UserConfigPath):
        os.mkdir(UserConfigPath)
    if not os.path.exists(os.path.join(UserConfigPath, 'dictionnaires')) :
        os.mkdir(os.path.join(UserConfigPath, 'dictionnaires'))

def CopyConf(self) :
    DictUser = self.ConfigPath
    DictAppli = ConstructConfigPath(self.AppliPath,user=False)
    for item, filein in DictUser.items():
        if not item == 'global' and not item == 'path' and not item == 'preferences' and not item == 'history' :
            shutil.copyfile(DictAppli[item],filein)
        if item == 'path':
            if not os.path.exists(filein):
                shutil.copyfile(DictAppli[item],filein)
        if item == 'preferences' :
            if not os.path.exists(filein) :
                shutil.copyfile(DictAppli[item],filein)
    dicoUser = self.DictPath
    dicoAppli = ConstructDicoPath(self.AppliPath)
    for fi in dicoUser :
        if not os.path.exists(dicoUser[fi]) and os.path.exists(dicoAppli[fi]):
            shutil.copyfile(dicoAppli[fi], dicoUser[fi])

def CheckRPath(PathPath):
    if not os.path.exists(PathPath.get('PATHS','rpath')):
        return False
    else :
        return True

def FindRPAthWin32():
    BestPath=False
    progpaths=[]
    if 'ProgramFiles' in os.environ :
        progpaths.append(os.environ['ProgramFiles'])
    if 'ProgramFiles(x86)' in os.environ :
        progpaths.append(os.environ['ProgramFiles(x86)'])
    if 'ProgramW6432' in os.environ :
        progpaths.append(os.environ['ProgramW6432'])
    progpaths = list(set(progpaths))
    if progpaths != [] :
        for progpath in progpaths :
            rpath = os.path.join(progpath, "R")
            if os.path.exists(rpath) :
                for maj in range(3,5) :
                    for i in range(0,30):
                        for j in range(0,20):
                            for poss in ['', 'i386', 'x64'] :
                                path=os.path.join(rpath,"R-%i.%i.%i" % (maj, i, j),'bin',poss,'R.exe')
                                if os.path.exists(path):
                                    BestPath=path
    return BestPath

def FindRPathNix():
    BestPath=False
    if os.path.exists('/usr/bin/R'):
        BestPath='/usr/bin/R'
    elif os.path.exists('/usr/local/bin/R'):
        BestPath='/usr/local/bin/R'
    return BestPath

def RLibsAreInstalled(self) :
    rlibs = self.pref.get('iramuteq', 'rlibs')
    if rlibs == 'false' or rlibs == 'False' :
        return False
    else :
        return True

def CheckRPackages(self):
    listdep = ['ca', 'gee', 'ape', 'igraph','proxy', 'wordcloud', 'irlba', 'textometry', 'sna', 'network', 'intergraph', 'rgl']
    nolib = []
    i=0
    dlg = wx.ProgressDialog("Test des librairies de R", "test en cours...", maximum = len(listdep), parent=self, style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT)
    for bib in listdep :
        dlg.Center()
        i+=1
        dlg.Update(i, "test de %s" % bib)
        txt = """library("%s")""" % bib
        tmpscript = tempfile.mktemp(dir=self.TEMPDIR)
        with open(tmpscript, 'w') as f :
            f.write(txt)
        test = exec_rcode(self.RPath, tmpscript, wait = True)
        if test :
            log.info('packages %s : NOT INSTALLED' % bib)
            nolib.append(bib)
        else :
            log.info('packages %s : OK' % bib)
    dlg.Update(len(listdep),'fini')
    dlg.Destroy()
    if nolib != [] :
        txt = '\n'.join(nolib)
        msg = """Les bibliothèques de R suivantes sont manquantes :
%s

Sans ces bibliothèques, IRamuteq ne fonctionnera pas.

- Vous pouvez installer ces bibliothèques manuellement :
        Cliquez sur Annuler
        Lancez R
        Tapez install.packages('nom de la bibiothèque')

- ou laisser IRamuteq les installer automatiquement en cliquant sur VALIDER .
        Les bibliothèques seront téléchargées depuis le site miroir de R %s.
        """ % (txt, self.pref.get('iramuteq','rmirror'))
        dial = wx.MessageDialog(self, msg, "Installation incomplète", wx.OK | wx.CANCEL | wx.ICON_WARNING)
        dial.CenterOnParent()
        val = dial.ShowModal()
        if val == wx.ID_OK :
            dlg = wx.ProgressDialog("Installation",
                                       "Veuillez patientez...",
                                       maximum=len(nolib) + 1,
                                       parent=self,
                                       style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT
                                       )
            dlg.Center()
            dlg.Update(1, "installation...")
            compt = 0

            for bib in nolib :
                compt += 1
                dlg.Update(compt, "installation librairie %s" % bib)
                txt = """
                userdir <- unlist(strsplit(Sys.getenv("R_LIBS_USER"), .Platform$path.sep))[1]
                if (!file.exists(userdir)) {
                    if (!dir.create(userdir, recursive = TRUE))
                        print('pas possible')
                    lib <- userdir
                    .libPaths(c(userdir, .libPaths()))
                }
                print(userdir)
                .libPaths
                """
                if sys.platform in ['win32','darwin'] :
                    txt += """
                    install.packages("%s", repos = "%s", type='binary')
                    """ % (bib, self.pref.get('iramuteq','rmirror'))
                else :
                    txt += """
                    install.packages("%s", repos = "%s")
                    """ % (bib, self.pref.get('iramuteq','rmirror'))

                tmpscript = tempfile.mktemp(dir=self.TEMPDIR)
                with open(tmpscript, 'w') as f :
                    f.write(txt)
                test = exec_rcode(self.RPath, tmpscript, wait = False)
                while test.poll() == None :
                    dlg.Pulse("installation librairie %s" % bib)
                    sleep(0.2)
            dlg.Update(len(nolib) + 1, 'fin')
            dlg.Destroy()
        dial.Destroy()
    if nolib == [] :
        self.pref.set('iramuteq', 'rlibs', True)
        with open(self.ConfigPath['preferences'], 'w') as f :
            self.pref.write(f)
        return True
