# -*- coding: utf-8 -*-
#Author: Pierre Ratinaud
#Copyright (c) 2008-2020 Pierre Ratinaud
#License: GNU/GPL

#------------------------------------
# import des modules python
#------------------------------------
import os
import sys
from time import time, sleep

#------------------------------------
# import des modules wx
#------------------------------------
import wx

#------------------------------------
# import des fichiers du projet
#------------------------------------
from chemins import ConstructPathOut, ConstructAfcUciPath, ChdTxtPathOut
from corpus import Corpus
from OptionAlceste import OptionPam
from analysetxt import AnalyseText
from configparser import *
from functions import print_liste, exec_rcode, CreateIraFile, progressbar, check_Rresult, BugDialog
from layout import PrintRapport
from PrintRScript import ReinertTxtProf, RPamTxt
from openanalyse import OpenAnalyse


class AnalysePam(AnalyseText) :

#    def __init__(self, parent, corpus, cmd = False):

    def doanalyse(self) :
        self.parametres['type'] = 'pamtxt'
        self.pathout.basefiles(ChdTxtPathOut)
        self.actives, lim = self.corpus.make_actives_nb(self.parametres['max_actives'], 1)
        self.parametres['eff_min_forme'] = lim
        self.parametres['nbactives'] = len(self.actives)
        if self.parametres['classif_mode'] == 0 :
            self.corpus.make_and_write_sparse_matrix_from_uces(self.actives, self.pathout['TableUc1'], self.pathout['listeuce1'])
        elif self.parametres['classif_mode'] == 1 :
            self.corpus.make_and_write_sparse_matrix_from_uci(self.actives, self.pathout['TableUc1'], self.pathout['listeuce1'])
        RPamTxt(self.corpus, self.parent.RscriptsPath) 
        #t1 = time()
        #self.parent = parent
        #self.corpus = corpus
        #self.cmd = cmd
        if not self.cmd :
            self.dlg = progressbar(self, 9)
        #else :
        #    self.dlg = None
        #ucis_txt, ucis_paras_txt = self.corpus.start_analyse(self.parent, dlg = self.dlg, cmd = self.cmd)
        #self.corpus.make_len_uce(self.corpus.get_tot_occ_from_ucis_txt(ucis_txt))
        #del ucis_txt
        #if not self.cmd :
        #    self.dlg.Update(5, '%i ucis - Construction des uces' % len(self.corpus.ucis))        
        #if self.corpus.parametre['type'] == 0 :
        #    self.corpus.make_ucis_paras_uces(ucis_paras_txt, make_uce = True)
        #else :
        #    self.corpus.make_ucis_paras_uces(ucis_paras_txt, make_uce = False)
        #del ucis_paras_txt
        #if not self.cmd :
        #    self.dlg.Update(6, u'Dictionnaires')        
        #uces, orderuces = self.corpus.make_forms_and_uces()
        #self.corpus.ucenb = len(uces)
        #self.corpus.make_lems(self.parent.lexique)
        #self.corpus.min_eff_formes()
        #self.corpus.make_var_actives() 
        #self.corpus.make_var_supp()
        #if not self.cmd :
        #    self.dlg.Update(7, u'Creation des tableaux')
        if self.corpus.parametre['type'] == 0:
            tabuc1 = self.corpus.make_table_with_uce(orderuces)
            uc1 = None
            uces1 = [[uce, i] for i,uce in enumerate(orderuces)]
            self.corpus.write_tab([['uce','uc']] + [[i, i] for i in range(0,len(uces))], self.corpus.dictpathout['listeuce1'])
        else :
            tabuc1 = self.corpus.make_table_with_uci()
            uc1 = None
            uces1 = [[uce, i] for i, uce in enumerate(orderuces)]
            self.corpus.write_tab([['uce','uc']] + [[i, i] for i in range(0,len(orderuces))], self.corpus.dictpathout['listeuce1'])
        self.corpus.write_tab(tabuc1,self.corpus.dictpathout['TableUc1'])
        self.corpus.lenuc1 = len(tabuc1)
        del tabuc1, uc1
        RPamTxt(self, self.parent.RscriptsPath)
        self.DoR(self.pathout['Rchdtxt'], dlg = self.dlg, message = 'R...')
        #pid = exec_rcode(self.parent.RPath,self.pathout['Rchdtxt'], wait = False)
        #while pid.poll() == None :
        #    if not self.cmd :
        #        self.dlg.Pulse(u'CHD...')
        #        sleep(0.2)
        #    else :
        #        pass
        #check_Rresult(self.parent, pid)
        self.corpus.make_ucecl_from_R(self.pathout['uce'])
        #ucecl0 = [cl for uce,cl in ucecl if cl != 0]
        #clnb = len(list(set(ucecl0)))
        #classes = [cl for uce, cl in ucecl]
        #uces1 = [val for val, i in uces1] 
        #self.corpus.make_lc(uces1, classes, clnb)
        #self.corpus.build_profile(clnb, classes, self.corpus.actives, self.corpus.dictpathout['Contout']) 
        self.corpus.make_and_write_profile(self.actives, self.corpus.lc, self.pathout['Contout'])
        self.sup, lim = self.corpus.make_actives_nb(self.parametres['max_actives'], 2)
        self.corpus.make_and_write_profile(self.sup, self.corpus.lc, self.pathout['ContSupOut'])
        self.corpus.make_and_write_profile_et(self.corpus.lc, self.pathout['ContEtOut'])
        self.clnb = len(self.corpus.lc)
        self.parametres['clnb'] = self.clnb
        #passives = [lem for lem in self.corpus.lems if lem not in self.corpus.actives]
        #self.corpus.build_profile(clnb, classes, self.corpus.supp, self.corpus.dictpathout['ContSupOut'])
        #self.corpus.make_etoiles(self.corpus.para_coords)
        #self.corpus.build_profile_et(clnb, classes, uces1, self.corpus.dictpathout['ContEtOut'])
        AlcesteTxtProf(self.pathout, self.parent.RscriptsPath, clnb, '0.9')
        self.doR(self.pathout['RTxtProfGraph'], dlg = self.dlg, message = 'profils et A.F.C. ...')
        #pid = exec_rcode(self.parent.RPath, self.corpus.dictpathout['RTxtProfGraph'], wait = False)
        #while pid.poll() == None :
        #    if not self.cmd :
        #        self.dlg.Pulse(u'AFC...')
        #        sleep(0.2)
        #    else :
        #        pass
        #check_Rresult(self.parent, pid)
        #temps = time() - t1
        #self.corpus.minutes, self.corpus.seconds = divmod(temps, 60)
        #self.corpus.hours, self.corpus.minutes = divmod(self.corpus.minutes, 60)
        PrintRapport(self, self.corpus, self.parametres)
        #CreateIraFile(self.corpus.dictpathout, clnb, os.path.basename(self.corpus.parametre['filename']))
        self.corpus.save_corpus(self.corpus.dictpathout['db'])
        afc_graph_list = [[os.path.basename(self.corpus.dictpathout['AFC2DL_OUT']), 'Variables actives - coordonnées - facteurs 1 / 2'],
          [os.path.basename(self.corpus.dictpathout['AFC2DSL_OUT']), 'variables supplémentaires - coordonnées - facteurs 1 / 2'],
          [os.path.basename(self.corpus.dictpathout['AFC2DEL_OUT']), 'Variables illustratives - Coordonnées - facteur 1 / 2'],
          [os.path.basename(self.corpus.dictpathout['AFC2DCL_OUT']), 'Classes - Coordonnées - facteur 1 / 2']]
        chd_graph_list = [[os.path.basename(self.corpus.dictpathout['arbre1']), 'résultats de la classification']]
        print_liste(self.pathout['liste_graph_afc'],afc_graph_list)
        print_liste(self.pathout['liste_graph_chd'],chd_graph_list)
        #if not self.cmd :
        #    self.dlg.Update(9, u'fin')
        #    self.dlg.Destroy()
        #print 'fini'


class PamTxt:

    def __init__(self, parent, cmd = False):       
        print('pam txt')
        self.type = 'pamsimple'
        self.parent = parent
        self.ConfigPath = parent.ConfigPath
        self.DictPath = parent.DictPath
        self.pamconf = ConfigParser()
        self.pamconf.read(self.ConfigPath['pam'])
        self.KeyConf = ConfigParser()
        self.KeyConf.read(self.ConfigPath['key'])
        self.corpus = Corpus(parent)
        try :
            self.corpus.content = self.parent.content
            self.corpus.parametre['encodage'] = parent.corpus_encodage
            self.corpus.parametre['filename'] = parent.filename
            self.corpus.parametre['lang'] = parent.corpus_lang
            if not cmd :
                self.dial = OptionPam(self, parent)
                self.dial.CenterOnParent()
                self.val = self.dial.ShowModal()
                self.print_param()
            else :
                self.val = wx.ID_OK
            if self.val == wx.ID_OK :
                file = open(self.ConfigPath['key'], 'w')
                self.KeyConf.write(file)
                file.close()
                self.read_param()
                #self.corpus.parametre.update(param)
                self.corpus.supplementaires = [option for option in self.KeyConf.options('KEYS') if self.KeyConf.get('KEYS', option) == "2"]
                self.corpus.typeactive = [option for option in self.KeyConf.options('KEYS') if self.KeyConf.get('KEYS', option) == "1"]
                self.corpus.dictpathout =  ChdTxtPathOut(ConstructPathOut(self.corpus.parametre['filename'], 'PamSimple'))
                AnalysePam(parent, self.corpus ,cmd = cmd)
        except AttributeError :
            wx.MessageBox('Vous devez charger un corpus\nFichier -> Ouvrir un texte', 'Pas de corpus', wx.OK|wx.ICON_INFORMATION)
            self.val = False

    def print_param(self) :
        self.pamconf = RawConfigParser()
        self.pamconf.read(self.parent.ConfigPath['pam'])
        vallem = self.dial.radio_1.GetSelection()
        if vallem == 0 : vallem = True
        else : vallem = False
        expressions = self.dial.radio_exp.GetSelection()
        if expressions == 0 : expressions = True
        else: expressions = False
        if self.dial.cltype[self.dial.radio_box_3.GetSelection()] == 'k-means (pam)' : cluster_type = 'pam'
        else : cluster_type = 'fanny'
        self.pamconf.set('pam', 'lem', vallem)
        self.pamconf.set('pam', 'expressions', expressions)
        self.pamconf.set('pam', 'type', self.dial.radio_box_classif.GetSelection())
        self.pamconf.set('pam', 'method', self.dial.distance[self.dial.choice_1.GetSelection()])
        self.pamconf.set('pam', 'cluster_type', cluster_type)
        self.pamconf.set('pam', 'nbforme_uce', str(self.dial.spin_ctrl_3.GetValue()))
        self.pamconf.set('pam', 'nbcl', str(self.dial.spin_ctrl_4.GetValue()))
        self.pamconf.set('pam', 'expressions', expressions)
        self.pamconf.set('pam', 'max_actives', str(self.dial.spin_max_actives.GetValue()))
        with open(self.ConfigPath['pam'], 'w') as fileout :
            self.pamconf.write(fileout)

    def read_param(self) :
        conf = RawConfigParser()
        conf.read(self.parent.ConfigPath['pam'])
        for option in conf.options('pam') :
            if conf.get('pam', option).isdigit() :
                self.corpus.parametre[option] = int(conf.get('pam', option))
            else :
                self.corpus.parametre[option] = conf.get('pam', option)
        list_bool = ['lem', 'expressions']
        for val in list_bool :
            if self.corpus.parametre[val] == 'True' :
                self.corpus.parametre[val] = True
            else : 
                self.corpus.parametre[val] = False
        if self.corpus.parametre['type'] == 0 :
            self.corpus.parametre['classif_mode'] = 1
        else :
            self.corpus.parametre['classif_mode'] = 2
