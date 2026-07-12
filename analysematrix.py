# -*- coding: utf-8 -*-
#Author: Pierre Ratinaud
#Copyright (c) 2008-2020 Pierre Ratinaud
#modification pour python 3 : Laurent Mérat, 6x7 - mai 2020
#License: GNU/GPL

#------------------------------------
# import des modules python
#------------------------------------
import logging
import os
from uuid import uuid4
from time import time, sleep

#------------------------------------
# import des modules wx
#------------------------------------

#------------------------------------
# import des fichiers du projet
#------------------------------------
from chemins import PathOut
from functions import exec_rcode, check_Rresult, DoConf, progressbar
from openanalyse import OpenAnalyse


class AnalyseMatrix :
    def __init__(self, ira, tableau, parametres = None, dlg = None) :
        self.tableau = tableau
        if self.tableau.csvtable is None :
            self.tableau.open()
        self.ira = ira
        self.parent = ira
        self.dlg = dlg
        self.parametres = parametres
        self.val = False
        if not 'pathout' in self.parametres :
            self.parametres['pathout'] = PathOut(tableau.parametres['originalpath'], analyse_type = self.parametres['type'], dirout = tableau.parametres['pathout']).mkdirout()
            self.pathout = PathOut(analyse_type = self.parametres['type'], dirout = self.parametres['pathout'])
        else :
            self.pathout = PathOut(filename = tableau.parametres['originalpath'], dirout = self.parametres['pathout'], analyse_type = self.parametres['type'])

        #self.parametres['pathout'] = self.pathout.dirout
        self.parametres['uuid'] = str(uuid4())
        self.parametres['name'] = os.path.split(self.parametres['pathout'])[1]
        self.parametres['encoding'] = self.ira.syscoding
        self.parametres['matrix'] = self.tableau.parametres['uuid']
        self.tableau.pathout.dirout = self.parametres['pathout']
        self.doparametres(dlg = dlg)
        if self.dlg is not None :
            self.dlg = progressbar(self.ira, self.dlg)
        if self.parametres is not None :
            self.t1 = time()
            if not os.path.exists(self.parametres['pathout']) :
                self.pathout.createdir(self.parametres['pathout'])
            result_analyse = self.doanalyse()
        else :
            result_analyse = False
        if result_analyse is None :
            if self.parametres.get('tohistory', True) :
                self.time = time() - self.t1
                minutes, seconds = divmod(self.time, 60)
                hours, minutes = divmod(minutes, 60)
                self.parametres['time'] = '%.0fh %.0fm %.0fs' % (hours, minutes, seconds)
                self.parametres['ira'] = self.pathout['Analyse.ira']
                DoConf().makeoptions([self.parametres['type']], [self.parametres], self.pathout['Analyse.ira'])
                self.ira.history.addMatrixAnalyse(self.parametres)
            if self.dlg is not None :
                self.dlg.Destroy()
                if self.parametres.get('tohistory', True) :
                    OpenAnalyse(self.parent, self.parametres['ira'])
                    self.ira.tree.AddMatAnalyse(self.parametres)
                self.val = 5100
        else :
            self.val = False
            if self.dlg is not None :
                try :
                    self.dlg.Destroy()
                except :
                    pass
 
    def doanalyse(self) :
        pass

    def doparametres(self, dlg = None):
        pass

    def doR(self, Rscript, wait = False, dlg = None, message = '') :
        #log.info('R code...')
        pid = exec_rcode(self.ira.RPath, Rscript, wait = wait)
        while pid.poll() is None :
            if dlg :
                self.dlg.Pulse(message)
                sleep(0.2)
            else :
                sleep(0.2)
        return check_Rresult(self.ira, pid)
