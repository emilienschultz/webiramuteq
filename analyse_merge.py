# -*- coding: utf-8 -*-
#Author: Pierre Ratinaud
#Copyright (c) 2008-2020 Pierre Ratinaud
#modification pour python 3 : Laurent Mérat, 6x7 - mai 2020
#License: GNU/GPL

#------------------------------------
# import des modules python
#------------------------------------
import os
from time import sleep

#------------------------------------
# import des modules wx
#------------------------------------
import wx

#------------------------------------
# import des fichiers du projet
#------------------------------------
from chemins import PathOut
from functions import exec_rcode, check_Rresult
from dialog import MergeDialog
from PrintRScript import MergeGraphes

def merge_graphes(lgraphes):
    script = MergeGraphes({'lgraphes':lgraphes, 'grapheout' : '/tmp/graphe.graphml'}) 
    script.make_script()
    script.write()
    return script

class AnalyseMerge :
    def __init__(self, ira, parametres, dlg = None):
        self.ira = ira
        self.dlg = dlg
        self.parametres = parametres
        if 'pathout' not in self.parametres :
            self.parametres['pathout'] = PathOut(self.parametres['fileout'], analyse_type = self.parametres['type'], dirout = os.path.dirname(self.parametres['fileout'])).mkdirout()
            self.pathout = PathOut(analyse_type = self.parametres['type'], dirout = self.parametres['pathout'])
        else :
            self.pathout = PathOut(dirout = self.parametres['pathout'], analyse_type = self.parametres['type'])
        if self.doparametres(dlg=dlg) is not None :
            script = merge_graphes(self.parametres['graphs'])
            self.doR(script.scriptout, dlg=False)
            print('fini')

    def doparametres(self, dlg=None):
        if dlg is not None :
            dial = MergeDialog(self.ira)
            res = dial.ShowModal()
            if res == wx.ID_OK :
                self.parametres['graphs'] = [graph.GetPath() for graph in dial.graphs if graph.GetPath() != '']
                return True
            # pas besoin d'un dial.Destroy() ???
        return True
            
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