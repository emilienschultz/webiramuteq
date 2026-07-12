# -*- coding: utf-8 -*-
#Author: Pierre Ratinaud
#Copyright (c) 2008-2020 Pierre Ratinaud
#License: GNU/GPL

#------------------------------------
# import des modules python
#------------------------------------
import os
from time import time, sleep

#------------------------------------
# import des modules wx
#------------------------------------
import wx

#------------------------------------
# import des fichiers du projet
#------------------------------------
from chemins import ConstructPathOut, ConstructAfcUciPath
from layout import GraphPanel
#from PrintRScript import RAfcUci 
from corpus import Corpus
from listlex import *
from functions import ReadList, progressbar, exec_rcode, check_Rresult
from configparser import RawConfigParser


class AfcUci():

    def __init__(self, parent, cmd = False):
        #################################################################### 
        self.conf = None
        self.parent = parent
        self.type = 'afcuci'
        self.cmd = cmd
        self.corpus = Corpus(parent)        
        self.corpus.parametre['encodage'] = parent.corpus_encodage
        self.corpus.parametre['filename'] = parent.filename    
        self.corpus.parametre['lang'] = parent.corpus_lang
        self.corpus.content = self.parent.content
        self.ConfigPath = parent.ConfigPath
        self.DictPath = parent.DictPath
        self.AlcesteConf = RawConfigParser()
        self.AlcesteConf.read(self.ConfigPath['alceste'])
        self.KeyConf = RawConfigParser()
        self.KeyConf.read(self.ConfigPath['key'])
        pathout = ConstructPathOut(self.corpus.parametre['filename'], 'afcuci')
        self.corpus.dictpathout = ConstructAfcUciPath(pathout)        
        self.corpus.supplementaires = [option for option in self.KeyConf.options('KEYS') if self.KeyConf.get('KEYS', option) == "2"]
        self.corpus.typeactive = [option for option in self.KeyConf.options('KEYS') if self.KeyConf.get('KEYS', option) == "1"]        
        self.read_alceste_parametre()
        ################################
        if not self.cmd :
            self.dlg = progressbar(self, 6)
        else :
            self.dlg = None
        ucis_txt, ucis_paras_txt = self.corpus.start_analyse(self.parent, dlg = self.dlg, cmd = self.cmd)
        self.corpus.make_ucis_paras_uces(ucis_paras_txt, make_uce = False)
        uces, orderuces = self.corpus.make_forms_and_uces()
        self.corpus.make_lems(self.parent.lexique)
        self.corpus.min_eff_formes()
        self.corpus.make_var_actives() 
        self.corpus.make_var_supp()
        print(self.corpus.supp)
        self.corpus.make_pondtable_with_uci(self.corpus.actives, self.corpus.dictpathout['TableCont'])
        self.corpus.make_pondtable_with_uci(self.corpus.supp, self.corpus.dictpathout['TableSup'])
        self.corpus.parametre['para'] = False
        self.corpus.make_etoiles([])
        self.corpus.make_tableet_with_uci(self.corpus.dictpathout['TableEt'])
        RAfcUci(self.corpus.dictpathout, nd=3, RscriptsPath=self.parent.RscriptsPath, PARCEX='0.5')
        pid = exec_rcode(self.parent.RPath,self.corpus.dictpathout['Rafcuci'], wait = False)
        while pid.poll() == None :
            if not self.cmd :
                self.dlg.Pulse('CHD...')
                sleep(0.2)
            else :
                pass
        check_Rresult(self.parent, pid)
        if not self.cmd :
            self.dlg.Update(6, 'Affichage')
            self.DoLayout(parent, self.corpus.dictpathout)
            self.dlg.Destroy()

    def read_alceste_parametre(self) :
        self.conf = RawConfigParser()
        self.conf.read(self.parent.ConfigPath['alceste'])
        for option in self.conf.options('ALCESTE') :
            if self.conf.get('ALCESTE', option).isdigit() :
                self.corpus.parametre[option] = int(self.conf.get('ALCESTE', option))
            else :
                self.corpus.parametre[option] = self.conf.get('ALCESTE', option)
        list_bool = ['lem', 'expressions']
        for val in list_bool :
            if self.corpus.parametre[val] == 'True' :
                self.corpus.parametre[val] = True
            else : 
                self.corpus.parametre[val] = False

    def DoLayout(self, parent, DictAfcUciOut):
        self.TabAfcUci = wx.aui.AuiNotebook(parent.nb, -1, wx.DefaultPosition)
        #self.TabAfcTot = wx.html.HtmlWindow(self.TabAfcUci, -1)
        #txtafctot = MakeAfcUciPages(DictAfcUciOut, parent.encode)
        list_graph = [[os.path.basename(DictAfcUciOut['AfcColAct']),''],
                      [os.path.basename(DictAfcUciOut['AfcColSup']),''],
                      [os.path.basename(DictAfcUciOut['AfcColEt']),''],
                      [os.path.basename(DictAfcUciOut['AfcRow']),'']]
        self.TabAfcTot = GraphPanel(self.TabAfcUci, DictAfcUciOut, list_graph, txt = '')
        #self.TabAfcSplit = wx.html.HtmlWindow(self.TabAfcUci, -1)
        #txtafcsplit = MakeAfcSplitPage(1, 2, DictAfcUciOut, self.pathout, parent.encode)
        #if "gtk2" in wx.PlatformInfo:
        #    self.TabAfcSplit.SetStandardFonts()
        #self.TabAfcSplit.SetPage(txtafcsplit)
        dictrow, first = ReadList(self.corpus.dictpathout['afc_row'])
        panel_list = ListForSpec(parent, self, dictrow, first[1:])
        self.TabAfcUci.AddPage(self.TabAfcTot, 'Graph Afc totale')
        #self.TabAfcUci.AddPage(self.TabAfcSplit, 'Graph AFC Split')
        self.TabAfcUci.AddPage(panel_list, 'Colonnes')
        parent.nb.AddPage(self.TabAfcUci, 'AFC Sur UCI')
        parent.nb.SetSelection(parent.nb.GetPageCount() - 1)
        parent.ShowTab(True) 
