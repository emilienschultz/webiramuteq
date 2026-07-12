# -*- coding: utf-8 -*-
#Author: Pierre Ratinaud
#Copyright (c) 2008-2020 Pierre Ratinaud
#modification pour python 3 : Laurent Mérat, 6x7 - mai 2020
#License: GNU/GPL

#----------------------------------------------------------------------------
# Name:         ListCtrl.py
# comes from ListCtrl.py from the demo tool of wxPython:
# Author:       Robin Dunn & Gary Dumer
#
# Created:
# Copyright:    (c) 1998 by Total Control Software
# Licence:      wxWindows license
#----------------------------------------------------------------------------

#------------------------------------
# import des modules python
#------------------------------------
import os
import codecs
from operator import itemgetter
from copy import copy
import webbrowser
import tempfile

import langue
langue.run()

#------------------------------------
# import des modules wx
#------------------------------------
import wx
import wx.lib.mixins.listctrl as listmix

#------------------------------------
# import des fichiers du projet
#------------------------------------
from listlex import ListForSpec
from chemins import ConstructPathOut, ffr
from dialog import PrefUCECarac, SearchDial, message, BarFrame, ChronoFrame
from tableau import copymatrix
from search_tools import SearchFrame
from functions import progressbar, treat_var_mod, doconcorde


class ProfListctrlPanel(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin, listmix.ColumnSorterMixin):

    def __init__(self, parent, gparent, profclasse, Alceste=False, cl=0, translation = False):
        wx.ListCtrl.__init__( self, parent, -1, style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES)
        self.parent = parent
        self.Alceste = Alceste
        self.Source = gparent
        self.translation = translation
        self.cl = cl
        self.var_mod = {}
        self.them_mod = {}
        self.ira = wx.GetApp().GetTopWindow()
        line1 = profclasse.pop(0)
        classen = [line for line in profclasse if line[0] != '*' and line[0] != '*****']
        try :
            self.lenact = profclasse.index(['*****', '*', '*', '*', '*', '*', '', ''])
            profclasse.pop(self.lenact)
        except ValueError:
            try :
                self.lenact = profclasse.index(['*', '*', '*', '*', '*', '*', '', ''])
                profclasse.pop(self.lenact)
            except ValueError:
                self.lenact = len(profclasse)
        try :
            self.lensup = profclasse.index(['*', '*', '*', '*', '*', '*', '', ''])
            self.lensup = self.lensup - self.lenact
            profclasse.pop(self.lensup)
        except ValueError: 
            self.lensup = len(profclasse) - self.lenact
        self.lenet = len(profclasse) - (self.lenact + self.lensup)
#        print self.lenact, self.lensup, self.lenet
        for i,  line in enumerate(classen) :
            line[0] = i
        dictdata = dict(list(zip([i for i in range(0,len(classen))], classen)))
        if self.lenact != 0 :
            self.la = [dictdata[i][6] for i in range(0, self.lenact)]
            self.lchi = [dictdata[i][4] for i in range(0, self.lenact)]
            self.lfreq = [dictdata[i][1] for i in range(0, self.lenact)]
        else :
            self.la = []
            self.lchi = []
            self.lfreq = []
        self.tmpchi = None
        #adding some art
        self.il = wx.ImageList(16, 16)
        a={"sm_up":"GO_UP","sm_dn":"GO_DOWN","w_idx":"WARNING","e_idx":"ERROR","i_idx":"QUESTION"}
        for k,v in list(a.items()):
            s="self.%s= self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_%s,wx.ART_TOOLBAR,(16,16)))" % (k,v)
            exec(s)
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
        #adding some attributes (colourful background for each item rows)
        self.attr1 = wx.ItemAttr()
        self.attr1.SetBackgroundColour((220, 220, 220))
        self.attrsg = wx.ItemAttr()
        self.attrsg.SetBackgroundColour((230, 230, 230))
        self.attr2 = wx.ItemAttr()
        self.attr2.SetBackgroundColour((190, 249, 236))
        self.attr2s = wx.ItemAttr()
        self.attr2s.SetBackgroundColour((211, 252, 244))
        self.attr3 = wx.ItemAttr()
        self.attr3.SetBackgroundColour((245, 180, 180))
        self.attr3s = wx.ItemAttr()
        self.attr3s.SetBackgroundColour((245, 190, 190))
        self.InsertColumn(0, "num", wx.LIST_FORMAT_RIGHT)
        self.InsertColumn(1, "eff. s.t.", wx.LIST_FORMAT_RIGHT)
        self.InsertColumn(2, "eff. total", wx.LIST_FORMAT_RIGHT)
        self.InsertColumn(3, "pourcentage", wx.LIST_FORMAT_RIGHT)
        self.InsertColumn(4, "chi2", wx.LIST_FORMAT_RIGHT)
        self.InsertColumn(5, "Type", wx.LIST_FORMAT_RIGHT)
        self.InsertColumn(6, "forme", wx.LIST_FORMAT_RIGHT)
        self.InsertColumn(7, "p", wx.LIST_FORMAT_RIGHT)
        self.SetColumnWidth(0, 60)
        self.SetColumnWidth(1, 100)
        self.SetColumnWidth(2, 100)
        self.SetColumnWidth(3, 120)
        self.SetColumnWidth(4, 150)
        self.SetColumnWidth(5, 100)
        self.SetColumnWidth(6, 300)
        self.SetColumnWidth(7, wx.LIST_AUTOSIZE)
        #These two should probably be passed to init more cleanly
        #setting the numbers of items = number of elements in the dictionary
        self.itemDataMap = dictdata
        self.itemIndexMap = list(dictdata.keys())
        self.SetItemCount(len(dictdata))
        #mixins
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        listmix.ColumnSorterMixin.__init__(self, len(classen[0]))
        self.SortListItems(0, True)
        #sort by genre (column 2), A->Z ascending order (1)


        #events
        #self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnPopupTwo, self)
        #self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)
        # for wxMSW
        self.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.OnRightClick)
        # for wxGTK
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightClick)
        #for searching
        search_id = wx.NewId()
        searchall_id = wx.NewId()
        concord_id = wx.NewId()
        self.parent.Bind(wx.EVT_MENU, self.onsearch, id = search_id)
        self.parent.Bind(wx.EVT_MENU, self.onsearchall, id = searchall_id)
        self.accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('F'), search_id),
                                              (wx.ACCEL_CTRL|wx.ACCEL_SHIFT, ord('F'), searchall_id)])
        self.SetAcceleratorTable(self.accel_tbl)

    def OnGetItemColumnImage(self, item, col):
        return -1

    def OnGetItemImage(self, item):
        pass

    def OnColClick(self,event):
        event.Skip()

    def OnItemSelected(self, event):
        self.currentItem = event.GetIndex() #event.m_itemIndex

    def OnItemActivated(self, event):
        self.currentItem = event.GetIndex() #event.m_itemIndex

    def getColumnText(self, index, col):
        item = self.GetItem(index, col)
        return item.GetText()

    def OnItemDeselected(self, evt):
        pass
    #---------------------------------------------------
    # These methods are callbacks for implementing the
    # "virtualness" of the list...

    def OnGetItemText(self, item, col):
        index=self.itemIndexMap[item]
        s = self.itemDataMap[index][col]
        if isinstance(s, (int, float)):
            return str(s)
        else:
            return s #modification pour python 3

    def OnGetItemAttr(self, item):
        index=self.itemIndexMap[item]
        if index < self.lenact :
            if item % 2 :
                return self.attr1
            else :
                return self.attrsg
        elif index >= self.lenact and index < (self.lenact + self.lensup) :
            if item % 2 :
                return self.attr2
            else :
                return self.attr2s
        elif index >= (self.lenact + self.lensup) :
            if item % 2 :
                return self.attr3
            else :
                return self.attr3s
        else :
            return None

    #---------------------------------------------------
    # Matt C, 2006/02/22
    # Here's a better SortItems() method --
    # the ColumnSorterMixin.__ColumnSorter() method already handles the ascending/descending,
    # and it knows to sort on another column if the chosen columns have the same value.

#    def SortItems(self,sorter=cmp): en version python2
    def SortItems(self, sorter=None):
        listTemp = sorted(self.itemDataMap.items(),
            key=lambda x:x[1][self._col], reverse= (self._colSortFlag[self._col]!=True))
        dlist = dict([[line[0],line[1]] for line in listTemp])
        self.itemDataMap = dlist
        self.itemIndexMap = list(dlist.keys())
        self.Refresh() # redraw the list

    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self

    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)

    def onsearch(self, evt) :
        self.dial = SearchDial(self, self, 6, True)
        self.dial.CenterOnParent()
        self.dial.Show()
        #self.dial.Destroy()

    def onsearchall(self, evt) :
        if 'FrameSearch' not in dir(self.Source) :
            self.Source.FrameSearch = SearchFrame(self.parent, -1, _("Search..."), self.Source.corpus)
        self.dial = SearchDial(self, self.Source.FrameSearch.liste, 1, False)
        self.dial.CenterOnParent()
        self.dial.Show()
        #self.dial.Destroy()

    def OnRightClick(self, event):
        # only do this part the first time so the events are only bound once
        if self.Alceste:
            if not hasattr(self, "popupID1"):
                self.popupID1 = wx.NewId()
                self.popupID2 = wx.NewId()
                self.popupID3 = wx.NewId()
                self.popupID4 = wx.NewId()
                self.popupID5 = wx.NewId()
                self.popupID6 = wx.NewId()
                self.popupID7 = wx.NewId()
                self.popupID8 = wx.NewId()
                self.popupID9 = wx.NewId()
                #self.popupID10 = wx.NewId()
                self.popupIDgraph = wx.NewId()
                self.idseg = wx.NewId()
                self.iducecarac = wx.NewId()
                self.idtablex = wx.NewId()
                self.idchimod = wx.NewId()
                self.idwordgraph = wx.NewId()
                self.popup_proxe = wx.NewId()
                self.idlexdendro = wx.NewId()
                self.idcloud = wx.NewId()
                self.idexport = wx.NewId()
                self.idexporttropes = wx.NewId()
                self.idexportowledge = wx.NewId()
                self.onmaketgen = wx.NewId()
                self.onchronochi2 = wx.NewId()
                self.onchronoprop = wx.NewId()
                #self.export_classes = wx.NewId()
                self.Bind(wx.EVT_MENU, self.OnPopupOne, id=self.popupID1)
                self.Bind(wx.EVT_MENU, self.OnPopupTwo, id=self.popupID2)
                self.Bind(wx.EVT_MENU, self.OnPopupThree, id=self.popupID3)
                self.Bind(wx.EVT_MENU, self.OnPopupFour, id=self.popupID4)
                self.Bind(wx.EVT_MENU, self.OnPopupFive, id=self.popupID5)
                self.Bind(wx.EVT_MENU, self.OnPopupSix, id=self.popupID6)
                self.Bind(wx.EVT_MENU, self.OnPopupSeven, id=self.popupID7)
                self.Bind(wx.EVT_MENU, self.OnPopupHeight, id=self.popupID8)
                self.Bind(wx.EVT_MENU, self.OnPopupNine, id=self.popupID9)
                #self.Bind(wx.EVT_MENU, self.OnPopupSpec, id=self.popupID10)
                self.Bind(wx.EVT_MENU, self.on_graph, id=self.popupIDgraph)
                self.Bind(wx.EVT_MENU, self.on_segments, id=self.idseg)
                self.Bind(wx.EVT_MENU, self.on_uce_carac, id = self.iducecarac)
                self.Bind(wx.EVT_MENU, self.on_tablex, id = self.idtablex)
                self.Bind(wx.EVT_MENU, self.quest_var_mod, id = self.idchimod)
                self.Bind(wx.EVT_MENU, self.onwordgraph, id = self.idwordgraph)
                self.Bind(wx.EVT_MENU, self.onproxe, id = self.popup_proxe)
                self.Bind(wx.EVT_MENU, self.onlexdendro, id = self.idlexdendro)
                self.Bind(wx.EVT_MENU, self.oncloud, id = self.idcloud)
                self.Bind(wx.EVT_MENU, self.onexport, id = self.idexport)
                self.Bind(wx.EVT_MENU, self.onexporttropes, id = self.idexporttropes)
                self.Bind(wx.EVT_MENU, self.onexportowledge, id = self.idexportowledge)
                self.Bind(wx.EVT_MENU, self.OnMakeTgen, id=self.onmaketgen)
                self.Bind(wx.EVT_MENU, self.OnChronoChi2, id=self.onchronochi2)
                self.Bind(wx.EVT_MENU, self.OnChronoProp, id=self.onchronoprop)
                #self.Bind(wx.EVT_MENU, self.on_export_classes, id = self.export_classes)
                #self.Bind(wx.EVT_MENU, self.OnPopupThree, id=self.popupID3)
            # make a menu
            menu = wx.Menu()
            menu.Append(self.popupID1, _("Associated forms"))
            menu.Append(self.idtablex, _("Chi2 by cluster"))
            menu.Append(self.idlexdendro, _("Chi2 by cluster on dendrogram"))
            menu.Append(self.idchimod, _("Chi2 modalities of variable"))
            menu_chrono = wx.Menu()
            menu_chrono.Append(self.onchronochi2, _('Chi2'))
            menu_chrono.Append(self.onchronoprop, _('Proportion'))
            menu.Append(-1, _("Chronological view"), menu_chrono)
            menu.Append(self.idwordgraph, _("Word graph"))
            #menu.Append(self.export_classes, u"Exporter le corpus...") 
            #menu.Append(self.popupID10, u"Spécificités")
            menu_conc = wx.Menu()
            menu_conc.Append(self.popupID2, _("In segments of this cluster"))
            menu_conc.Append(self.popupID3, _("In segments of this clustering"))
            menu_conc.Append(self.popupID4, _("In all segments"))
            menu.Append(-1, _("Concordance"), menu_conc)
            menu.Append(self.onmaketgen, _("Make Tgen"))
            menu_cnrtl = wx.Menu()
            menu_cnrtl.Append(self.popupID5, _("Definition"))
            menu_cnrtl.Append(self.popupID6, _("Etymology"))
            menu_cnrtl.Append(self.popupID7, _("Synonymous"))
            menu_cnrtl.Append(self.popupID8, _("Antonym"))
            menu_cnrtl.Append(self.popupID9, _("Morphology"))
            menu_cnrtl.Append(self.popup_proxe, _("Proxemy"))
            menu.Append(-1, _("Tools from CNRTL (french only)"), menu_cnrtl)
            menu.AppendSeparator()
            menu.Append(self.popupIDgraph, _("Graph of cluster"))
            menu.Append(self.idseg, _("Repeated segments"))
            menu.Append(self.iducecarac, _("Typical text segments"))
            menu.Append(self.idcloud, _("Word cloud of cluster"))
            menu.Append(self.idexport, _('Export...'))
            menu.Append(self.idexporttropes, _('Export for Tropes'))
            menu.Append(self.idexportowledge, _('Exporter for Owledge'))
            #menu.Append(self.popupID2, u"Concordancier")
            #menu.Append(self.popupID3, "recharger")
            self.PopupMenu(menu)
            menu.Destroy()
        elif 'tableau' in dir(self.Source):
            if not hasattr(self, "pop1"):
                self.pop1 = wx.NewId()
                self.pop2 = wx.NewId()
                self.pop3 = wx.NewId()
                self.Bind(wx.EVT_MENU, self.quest_simi, id=self.pop1)
                self.Bind(wx.EVT_MENU, self.on_tablex, id=self.pop2)
                self.Bind(wx.EVT_MENU, self.quest_var_mod, id=self.pop3)
            menu = wx.Menu()
            menu.Append(self.pop2, _("Chi2 by cluster"))
            menu.Append(self.pop3, _("Chi2 modalities of variable"))
            menu.AppendSeparator()
            menu.Append(self.pop1, _("Graph of cluster"))
            self.PopupMenu(menu)
            menu.Destroy()

    def oncloud(self, evt):
        if 'corpus' in dir(self.Source):
            corpus = self.Source.corpus
        prof = [[self.la[i], self.lchi[i], self.lfreq[i]] for i, val in enumerate(self.la)]
        parametres = copy(self.Source.parametres)
        parametres['clusterprof'] = prof
        parametres['type'] = 'clustercloud'
        parametres['prof'] = self.Source.pathout['actprof_classe_%i.csv' % self.cl]
        del  parametres['uuid']
        self.parent.OnClusterCloud(self.Source.corpus, parametres = parametres)

    def onexport(self, evt) :
        if 'corpus' in dir(self.Source):
            corpus = self.Source.corpus
        if self.Source.parametres['classif_mode'] != 2 :
            uci = False
        else :
            uci = True
        corpus.export_classe(self.Source.pathout['classe_%i_export.txt' % self.cl], self.cl, uci = uci)
        dial = wx.MessageDialog(self, self.Source.pathout['classe_%i_export.txt' % self.cl], "Export", wx.OK|wx.ICON_INFORMATION)
        dial.ShowModal()
        dial.Destroy()

    def onexporttropes(self, evt) :
        if 'corpus' in dir(self.Source):
            corpus = self.Source.corpus
        if self.Source.parametres['classif_mode'] != 2 :
            uci = False
        else :
            uci = True
        fileout = self.Source.pathout['export_tropes_classe_%i.txt' % self.cl]
        corpus.export_tropes(fileout, self.cl, uci = uci)

    def onexportowledge(self, evt):
        if 'corpus' in dir(self.Source):
            corpus = self.Source.corpus
        if self.Source.parametres['classif_mode'] != 2 :
            uci = False
        else :
            uci = True
        repout = self.Source.pathout['export_owledge_classe_%i' % self.cl]
        if not os.path.exists(repout) :
            os.mkdir(repout)
        corpus.export_owledge(repout, self.cl, uci = uci)

    def getselectedwords(self) :
        words = [self.getColumnText(self.GetFirstSelected(), 6)]
        last = self.GetFirstSelected()
        while self.GetNextSelected(last) != -1:
            last = self.GetNextSelected(last)
            words.append(self.getColumnText(last, 6))
        return words

    def quest_var_mod(self, evt) :
        word = self.getselectedwords()[0]
        if len(word.split('_')) <= 1 :
            dial = wx.MessageDialog(self, _("This is not a variable_modality form"), _("Problem"), wx.OK | wx.ICON_WARNING)
            dial.CenterOnParent()
            dial.ShowModal()
            dial.Destroy()
            return
        if 'corpus' in dir(self.Source):
            corpus = self.Source.corpus
            if word.startswith('-*') :
                if self.them_mod == {} :
                    self.them_mod = self.Source.corpus.make_theme_dict()
                var_mod = self.them_mod
            else :
                if self.var_mod == {} :
                    self.var_mod = self.Source.corpus.make_etoiles_dict()
                var_mod = self.var_mod
        else :
            corpus = self.Source.tableau
            if self.var_mod == {} :
                self.var_mod = treat_var_mod([val for val in corpus.actives] + [val for val in corpus.sups])
            var_mod = self.var_mod
        with open(self.Source.pathout['chisqtable'], 'r', encoding='utf8') as f :
            chistable = [line.replace('\n','').replace('\r','').replace('"','').replace(',','.').split(';') for line in f]
        title = chistable[0]
        title.pop(0)
        chistable.pop(0)
        vchistable = [line[1:] for line in chistable]
        fchistable = [line[0] for line in chistable]
        var = word.split('_')
        #words = ['_'.join([var[0],word]) for word in self.var_mod[var[0]]]
        try :
            words = [word for word in var_mod[var[0]]]
        except KeyError:
            dial = wx.MessageDialog(self, _("This is not a meta-data"), _("Problem"), wx.OK | wx.ICON_WARNING)
            dial.CenterOnParent()
            dial.ShowModal()
            dial.Destroy()
            return
        words.sort()
        tableout = []
        kwords = []
        for word in words :
            if word in fchistable :
                tableout.append(vchistable[fchistable.index(word)])
                kwords.append(word)
        BarFrame(self.Source.parent, tableout, title, kwords)

    def OnChronoChi2(self, evt) :
        word = self.getselectedwords()[0]
        if len(word.split('_')) <= 1 :
            dial = wx.MessageDialog(self, _("This is not a variable_modality form"), _("Problem"), wx.OK | wx.ICON_WARNING)
            dial.CenterOnParent()
            dial.ShowModal()
            dial.Destroy()
            return
        if 'corpus' in dir(self.Source):
            corpus = self.Source.corpus
            if word.startswith('-*') :
                if self.them_mod == {} :
                    self.them_mod = self.Source.corpus.make_theme_dict()
                var_mod = self.them_mod
            else :
                if self.var_mod == {} :
                    self.var_mod = self.Source.corpus.make_etoiles_dict()
                var_mod = self.var_mod
        else :
            corpus = self.Source.tableau
            if self.var_mod == {} :
                self.var_mod = treat_var_mod([val for val in corpus.actives] + [val for val in corpus.sups])
            var_mod = self.var_mod
        var = word.split('_')
        #words = ['_'.join([var[0],word]) for word in self.var_mod[var[0]]]
        try :
            words = [word for word in var_mod[var[0]]]
        except KeyError:
            dial = wx.MessageDialog(self, _("This is not a meta-data"), _("Problem"), wx.OK | wx.ICON_WARNING)
            dial.CenterOnParent()
            dial.ShowModal()
            dial.Destroy()
            return
        words.sort()
        vartoplot = var[0] + '_'
        parametres = {'var' : vartoplot}
        ChronoFrame(self.Source.parent, parametres, self.Source.pathout, which = 'chi2')

    def OnChronoProp(self, evt) :
        word = self.getselectedwords()[0]
        if len(word.split('_')) <= 1 :
            dial = wx.MessageDialog(self, _("This is not a variable_modality form"), _("Problem"), wx.OK | wx.ICON_WARNING)
            dial.CenterOnParent()
            dial.ShowModal()
            dial.Destroy()
            return
        if 'corpus' in dir(self.Source):
            corpus = self.Source.corpus
            if word.startswith('-*') :
                if self.them_mod == {} :
                    self.them_mod = self.Source.corpus.make_theme_dict()
                var_mod = self.them_mod
            else :
                if self.var_mod == {} :
                    self.var_mod = self.Source.corpus.make_etoiles_dict()
                var_mod = self.var_mod
        else :
            corpus = self.Source.tableau
            if self.var_mod == {} :
                self.var_mod = treat_var_mod([val for val in corpus.actives] + [val for val in corpus.sups])
            var_mod = self.var_mod
        var = word.split('_')
        #words = ['_'.join([var[0],word]) for word in self.var_mod[var[0]]]
        try :
            words = [word for word in var_mod[var[0]]]
        except KeyError:
            dial = wx.MessageDialog(self, _("This is not a meta-data"), _("Problem"), wx.OK | wx.ICON_WARNING)
            dial.CenterOnParent()
            dial.ShowModal()
            dial.Destroy()
            return
        words.sort()
        vartoplot = var[0] + '_'
        parametres = {'var' : vartoplot}
        ChronoFrame(self.Source.parent, parametres, self.Source.pathout, which = 'prop')

    def quest_simi(self, evt) :
        tableau = self.Source.tableau
        tab = tableau.make_table_from_classe(self.cl, self.la)
        pathout = ConstructPathOut(self.Source.pathout.dirout, 'simi_classe_%i' %self.cl)
        if self.tmpchi is None :
            self.tmpchi = os.path.join(pathout,'chi.csv')
            with open(self.tmpchi, 'w', encoding='utf8') as f:
                f.write('\n'.join([str(val) for val in self.lchi]))
        self.filename = os.path.join(pathout,'mat01.csv')
        tableau.printtable(self.filename, tab)
        del tab
        paramsimi = {'coeff' : 0,
                          'layout' : 2,
                          'type_graph' : 1,
                          'arbremax' : 1,
                          'coeff_tv' : 1,
                          'coeff_tv_nb' : 0,
                          'tvprop' : 0,
                          'tvmin' : 5,
                          'tvmax' : 30,
                          'coeff_te' : 1,
                          'coeff_temin' : 1,
                          'coeff_temax' : 10,
                          'label_v': 1,
                          'label_e': 1,
                          'vcex' : 0,
                          'vcexmin' : 10,
                          'vcexmax' : 25,
                          'cex' : 10,
                          'cexfromchi' : True,
                          'sfromchi': False,
                          'seuil_ok' : 0,
                          'seuil' : 1,
                          'cols' : (255,0,0),
                          'cola' : (200,200,200),
                          'width' : 1000,
                          'height' : 1000,
                          'first' : True,
                          'keep_coord' : True,
                          'alpha' : 20,
                          'film': False,
                          'com' : 0,
                          'communities' : 0,
                          'halo' : 0,
                          'tmpchi': self.tmpchi,
                          'fromprof' : True,
                          'edgecurved' : True,
                          }
        act = {}
        tableau = copymatrix(tableau)
        tableau.chi = {}
        tableau.lchi = self.lchi
        #tableau.parametres['fromprof'] = True
        for i, val in enumerate(self.la) :
            act[val] = [self.lfreq[i]]
            tableau.chi[val] = [self.lchi[i]]
        paramsimi['listactives'] = copy(self.la)
        paramsimi['actives'] = copy(act)
        paramsimi['pathout'] = pathout
        self.parent.SimiCluster(parametres = paramsimi, fromprof = ffr(self.filename), tableau = tableau)

    def onwordgraph(self, evt):
        word = self.getColumnText(self.GetFirstSelected(), 6)
        if self.tmpchi is None :
            self.tmpchi = os.path.join(self.Source.parametres['pathout'],'chi_%i.csv' % self.cl)
            with open(self.tmpchi, 'w', encoding='utf8') as f:
                f.write('\n'.join([str(val) for val in self.lchi]))
        index = self.la.index(word)
        parametres = {'type' : 'clustersimitxt',
                        'pathout' : self.Source.parametres['pathout'],
                        'word' : index ,
                        'lem' : self.Source.parametres['lem'],
                        'tmpchi' : self.tmpchi}
        #try :
        self.parent.SimiFromCluster(self.parent, self.Source.corpus, self.la, self.lfreq, self.lchi, self.cl - 1, parametres = parametres, dlg = progressbar(self.ira, 4))
        #except :
        #    print 'not acitve'

    def on_graph(self, evt):
        if self.tmpchi is None :
            self.tmpchi = os.path.join(self.Source.parametres['pathout'],'chi_%i.csv' % self.cl)
            with open(self.tmpchi, 'w', encoding='utf8') as f:
                f.write('\n'.join([str(val) for val in self.lchi]))
        parametres = {'type' : 'clustersimitxt',
                        'pathout' : self.Source.parametres['pathout'],
                        'lem' : self.Source.parametres['lem'],
                        'tmpchi' : self.tmpchi}
        self.parent.SimiFromCluster(self.parent, self.Source.corpus, self.la, self.lfreq, self.lchi, self.cl - 1, parametres = parametres, dlg = progressbar(self.ira, 4))

    def on_segments(self,evt) :
        dlg = progressbar(self, 2)
        corpus = self.Source.corpus
        uces = corpus.lc[self.cl-1]
        if self.Source.parametres['classif_mode'] != 2 :
            uci = False
        else :
            uci = True
        l = []
        dlg.Update(1, 'Segments...')
        for i in range(2,10) :
            li = corpus.find_segments_in_classe(uces, i, 1000, uci = uci)
            if li == [] :
                break
            else :
                l += li
        l.sort(reverse = True)
        d = {}
        dlg.Update(2, 'Tri...')
        for i, line in enumerate(l) :
            d[i] = [line[1],line[0], line[2]]
        first = ['','','']
        para={'dico': d,'fline':first}
        dlg.Destroy()
        win = wliste(self, -1, ' - '.join([_("Repeated segments"), "Classe %i" % self.cl]), d, first, size=(600, 500))
        win.Show(True)

    def on_uce_carac(self,evt) :
        dial = PrefUCECarac(self, self.parent)
        dial.CenterOnParent()
        if dial.ShowModal() == wx.ID_OK :
            limite = dial.spin_eff.GetValue()
            atype = dial.radio_type.GetSelection()
            dlg = progressbar(self.ira,maxi = 4)
            corpus = self.Source.corpus
            uces = corpus.lc[self.cl-1]
            if self.Source.parametres['classif_mode'] != 2 :
                uci = False
            else :
                uci = True
            tab = corpus.make_table_with_classe(uces, self.la, uci = uci)
            tab.pop(0)
            dlg.Update(2, 'score...')
            if atype == 0 :
                ntab = [round(sum([self.lchi[i] for i, word in enumerate(line) if word == 1]),2) for line in tab]
            else :
                ntab = [round(sum([self.lchi[i] for i, word in enumerate(line) if word == 1])/float(sum(line)),2) if sum(line)!=0 else 0 for line in tab]
            ntab2 = [[ntab[i], uces[i]] for i, val in enumerate(ntab)]
            del ntab
            ntab2.sort(reverse = True)
            ntab2 = ntab2[:limite]
            nuces = [val[1] for val in ntab2]
            dlg.Update(3, 'concordancier...')
            ucis_txt, ucestxt = doconcorde(corpus, nuces, self.la, uci = uci)
            items = dict([[i, '<br>'.join([ucis_txt[i], '<table bgcolor = #1BF0F7 border=0><tr><td><b>score : %.2f</b></td></tr></table><br>' % ntab2[i][0], ucestxt[i]])] for i, uce in enumerate(nuces)])
            dlg.Destroy()
            win = message(self, items, ' - '.join([_("Typical text segments"), "Classe %i" % self.cl]), (750, 600), uceids = nuces)
            #win.SetWindowStyle(wx.STAY_ON_TOP)
            #win.html = '<html>\n' + '<br>'.join(['<br>'.join([ucis_txt[i], '<table bgcolor = #1BF0F7 border=0><tr><td><b>score : %.2f</b></td></tr></table>' % ntab2[i][0], ucestxt[i]]) for i in range(0,len(ucestxt))]) + '\n</html>'
            #win.HtmlPage.SetPage(win.html)
            win.Show(True)

    def on_tablex(self, evt):
        if 'corpus' in dir(self.Source):
            corpus = self.Source.corpus
        else :
            corpus = self.Source.tableau
        with open(self.Source.pathout['chisqtable'], 'r', encoding='utf8') as f :
            chistable = [line.replace('\n','').replace('\r','').replace('"','').replace(',','.').split(';') for line in f]
        title = chistable[0]
        title.pop(0)
        chistable.pop(0)
        vchistable = [line[1:] for line in chistable]
        fchistable = [line[0] for line in chistable]
        words = self.getselectedwords()
        tableout = [vchistable[fchistable.index(self.getword(word))] for word in words]
        tmpgraph = tempfile.mktemp(dir=self.Source.parent.TEMPDIR)
        nbcl = len(title)
        nbwords = len(words)
        BarFrame(self.Source.parent, tableout, title, words)

    def onlexdendro(self, evt):
        if 'corpus' in dir(self.Source):
            corpus = self.Source.corpus
        else :
            corpus = self.Source.tableau
        with open(self.Source.pathout['chisqtable'], 'r', encoding='utf8') as f :
            chistable = [line.replace('\n','').replace('\r','').replace('"','').replace(',','.').split(';') for line in f]
        title = chistable[0]
        title.pop(0)
        chistable.pop(0)
        vchistable = [line[1:] for line in chistable]
        fchistable = [line[0] for line in chistable]
        words = self.getselectedwords()
        tableout = [vchistable[fchistable.index(self.getword(word))] for word in words]
        BarFrame(self.Source.parent, tableout, title, words, tree = self.Source.pathout['Rdendro'])

    def getword(self, word) :
        if self.translation :
            return self.lems[word]
        else :
            return word

    def make_concord(self, uces, title, color = 'red') :
        corpus = self.Source.corpus
        ListWord = [self.getColumnText(self.GetFirstSelected(), 6)]
        last = self.GetFirstSelected()
        while self.GetNextSelected(last) != -1:
            last = self.GetNextSelected(last)
            ListWord.append(self.getColumnText(last, 6))
        ucef = []
        ListWord = [self.getword(word) for word in ListWord]
        if self.Source.parametres['classif_mode'] != 2 :
            for word in ListWord :
                uci = False
                ucef += list(set(corpus.getlemuces(word)).intersection(uces))
        else :
            for word in ListWord :
                ucef += list(set(corpus.getlemucis(word)).intersection(uces))
                uci = True
        ucis_txt, ucestxt = doconcorde(corpus, ucef, ListWord, uci = uci)
        items = dict([[i, '<br><br>'.join([ucis_txt[i], ucestxt[i]])] for i in range(0,len(ucestxt))])
        win = message(self, items, title, (800, 500), uceids = ucef)
        return win

    def OnPopupTwo(self, event):
        if 'corpus' in dir(self.Source) :
            corpus = self.Source.corpus
            uces = corpus.lc[self.cl-1]
            win = self.make_concord(uces, ' - '.join([_("Concordance"), "Classe %i" % self.cl]))
            win.Show(True)

    def OnPopupThree(self, event):
        corpus = self.Source.corpus
        uces = [classe[i] for classe in corpus.lc for i in range(0,len(classe))]
        win = self.make_concord(uces, ' - '.join([_("Concordance"), _("Segments of this clustering")]))
        win.Show(True)

    def OnPopupFour(self, event):
        corpus = self.Source.corpus
        uces = [classe[i] for classe in corpus.lc for i in range(0,len(classe))] + corpus.lc0
        win = self.make_concord(uces, ' - '.join([_("Concordance"), _("All segments")]))
        win.Show(True)

    def OnPopupFive(self, event):
        word = self.getColumnText(self.GetFirstSelected(), 6)
        lk = "http://www.cnrtl.fr/definition/" + word
        webbrowser.open(lk)

    def OnPopupSix(self, event):
        word = self.getColumnText(self.GetFirstSelected(), 6)
        lk = "http://www.cnrtl.fr/etymologie/" + word
        webbrowser.open(lk)

    def OnPopupSeven(self, event):
        word = self.getColumnText(self.GetFirstSelected(), 6)
        lk = "http://www.cnrtl.fr/synonymie/" + word
        webbrowser.open(lk)

    def OnPopupHeight(self, event):
        word = self.getColumnText(self.GetFirstSelected(), 6)
        lk = "http://www.cnrtl.fr/antonymie/" + word
        webbrowser.open(lk)

    def OnPopupNine(self, event):
        word = self.getColumnText(self.GetFirstSelected(), 6)
        lk = "http://www.cnrtl.fr/morphologie/" + word
        webbrowser.open(lk)

    def onproxe(self, evt) :
        word = self.getColumnText(self.GetFirstSelected(), 6)
        lk = "http://www.cnrtl.fr/proxemie/" + word
        webbrowser.open(lk)

    def OnPopupOne(self, event):
        corpus = self.Source.corpus
        #print 'ATTENTION PRINT ET TABLE'
        #corpus.make_et_table()
        word = self.getColumnText(self.GetFirstSelected(), 6)
        word = self.getword(word)
        lems = corpus.getlems()
        uces = corpus.lc[self.cl-1]
        rep = []
        #FIXME : donner aussi eff reel a la place de nb uce
        for forme in lems[word].formes :
            if self.Source.parametres['classif_mode'] != 2 :
                ucef = list(set(corpus.getworduces(forme)).intersection(uces))
            else :
                ucef = list(set(corpus.getworducis(forme)).intersection(uces))
            #ucef = [uce for uce in corpus.formes[forme][1] if uce in uces]
            if ucef != [] :
                nb = len(ucef)
                rep.append([corpus.getforme(forme).forme, nb])
        rep.sort(key = itemgetter(1), reverse = True)
        #win = message(self, u"Formes associées", wx.Size(300, 200))
        items = dict([[i, '\t:\t'.join([str(val) for val in forme])] for i, forme in enumerate(rep)])
        win = message(self, items, _("Associated forms"), (300, 200))
        #win.html = '<html>\n' + '<br>'.join([' : '.join([str(val) for val in forme]) for forme in rep]) + '\n</html>'
        #win.HtmlPage.SetPage(win.html)
        win.Show(True)

    def OnMakeTgen(self, evt):
        self.parent.tree.OnTgenEditor(self.getselectedwords())


class wliste(wx.Frame):

    def __init__(self, parent, id, title, d, fline, size=(600, 500)):
        wx.Frame.__init__(self, parent, id)
        self.liste = ListForSpec(self, parent, d, fline[1:], menu = False)
        self.button_1 = wx.Button(self, -1, _("Close"))
        self.Bind(wx.EVT_BUTTON, self.OnCloseMe, self.button_1)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.__do_layout()

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.liste, 1, wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        sizer_2.Add(self.button_1, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ADJUST_MINSIZE, 0)
        sizer_1.Add(sizer_2, 1, wx.EXPAND, 0)
        self.SetAutoLayout(True)
        self.SetSizer(sizer_1)
        self.Layout()

    def OnCloseMe(self, event):
        self.Close(True)

    def OnCloseWindow(self, event):
        self.Destroy()
