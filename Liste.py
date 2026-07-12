# -*- coding: utf-8 -*-
#Author: Pierre Ratinaud
#Copyright (c) 2008-2020 Pierre Ratinaud
#modification pour python 3 : Laurent Mérat, 6x7 - mai 2020
#License: GNU/GPL

# ----------------------------------------------------------------------------
# Name:         ListCtrl.py
# comes from ListCtrl.py from the demo tool of wxPython:
# Author:       Robin Dunn & Gary Dumer
# Created:
# Copyright:    (c) 1998 by Total Control Software
# Licence:      wxWindows license
# ----------------------------------------------------------------------------

#------------------------------------
# import des modules python
#------------------------------------
import os
import sys
import operator

import langue
langue.run()


#------------------------------------
# import des modules wx
#------------------------------------
import wx

#------------------------------------
# import des fichiers du projet
#------------------------------------
from dialog import SearchDial, message
import wx.lib.mixins.listctrl as listmix
from functions import doconcorde


# ---------------------------------------------------------------------------
 # wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS)
# ---------------------------------------------------------------------------


class ListPanel(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin, listmix.ColumnSorterMixin):
    def __init__(self, parent, gparent, dlist, context='stat'):
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_HRULES | wx.LC_VRULES)
        self.parent = parent
        self.gparent = gparent
        self.source = gparent
        self.dlist = dlist
        search_id = wx.NewId()
        self.parent.Bind(wx.EVT_MENU, self.onsearch, id=search_id)
        self.accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('F'), search_id)])
        self.SetAcceleratorTable(self.accel_tbl)
        self.il = wx.ImageList(16, 16)
        a = {"sm_up": "GO_UP", "sm_dn": "GO_DOWN", "w_idx": "WARNING", "e_idx": "ERROR", "i_idx": "QUESTION"}
        for k, v in list(a.items()):
            s = "self.%s= self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_%s,wx.ART_TOOLBAR,(16,16)))" % (k, v)
            exec(s)
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
        tID = wx.NewId()
        # -----------------------------------------------------------------------------------------
        self.attr1 = wx.ItemAttr()
        self.attr1.SetBackgroundColour((230, 230, 230))
        self.attr2 = wx.ItemAttr()
        self.attr2.SetBackgroundColour("light blue")
        if context == 'stat' :
            first = [ _('Form'),  _('Freq.'),  _('POS')]
            sortcol = 1
            sens = False
            sizes = [300, 150, 150]
        elif context == 'labbe' :
            first = ['X1','X2', _('Distance')]
            sortcol = 2
            sens = True
            sizes = [300,300,350]
        self.InsertColumn(0, first[0], wx.LIST_FORMAT_RIGHT)
        self.InsertColumn(1, first[1], wx.LIST_FORMAT_RIGHT)
        self.InsertColumn(2, first[2], wx.LIST_FORMAT_RIGHT)
        # self.InsertColumn(3, '', wx.LIST_FORMAT_RIGHT)
        self.SetColumnWidth(0, sizes[0])
        self.SetColumnWidth(1, sizes[1])
        self.SetColumnWidth(2, sizes[2])
        # self.SetColumnWidth(3, wx.LIST_AUTOSIZE)
        self.itemDataMap = dlist
        self.itemIndexMap = list(dlist.keys())
        self.SetItemCount(len(dlist))
        # self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick, self)
        if context == 'stat' :
            self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self)
            self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnPopupTwo, self)
            # for wxMSW
            self.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.OnRightClick)
            # for wxGTK
            self.Bind(wx.EVT_RIGHT_UP, self.OnRightClick)
        # listmix.ListCtrlAutoWidthMixin.__init__(self)
        listmix.ColumnSorterMixin.__init__(self, 3)
        self.SortListItems(sortcol, sens) #indice de la colonne pour le tri + sens du tri
        # self.do_greyline()
        # self.currentItem = 0

    def OnGetItemColumnImage(self, item, col):
        return -1

    def OnGetItemImage(self, item):
        pass

    def OnGetItemText(self, item, col):
        index = self.itemIndexMap[item]
        s = self.itemDataMap[index][col]
        if isinstance(s, (int, float)):
            return str(s)
        else:
            return s #modification pour python 3

    def OnGetItemAttr(self, item):
        # index=self.itemIndexMap[item]
        # genre=self.itemDataMap[index][2]
        if item % 2:
            return self.attr1
        else:
            return self.attr2

    def OnColClick(self, event):
        pass
        # self.do_greyline()

    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self

    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)

    # anciennement : def SortItems(self,sorter=cmp), mais plus 'cmp' en python 3
    def SortItems(self, sorter=None):
        listTemp = sorted(self.itemDataMap.items(),
            key=lambda x:x[1][self._col], reverse= (self._colSortFlag[self._col]!=True))
        dlist = dict([[line[0],line[1]] for line in listTemp])
        self.itemDataMap = dlist
        self.itemIndexMap = list(dlist.keys())
        self.Refresh() # redraw the list

    def OnRightDown(self, event):
        x = event.GetX()
        y = event.GetY()
        item, flags = self.HitTest((x, y))
        if flags & wx.LIST_HITTEST_ONITEM:
            self.Select(item)
        event.Skip()

    def getColumnText(self, index, col):
        item = self.GetItem(index, col)
        return item.GetText()

    def OnItemSelected(self, event):
        self.currentItem = event.GetIndex()
        event.Skip()

    def onsearch(self, evt):
        self.dial = SearchDial(self, self, 0, True)
        self.dial.CenterOnParent()
        self.dial.Show()
        # self.dial.Destroy()

    def OnRightClick(self, event):
        # only do this part the first time so the events are only bound once
        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewId()
            self.popupID2 = wx.NewId()
        #    self.popupID3 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.OnPopupOne, id=self.popupID1)
            self.Bind(wx.EVT_MENU, self.OnPopupTwo, id=self.popupID2)
        #    self.Bind(wx.EVT_MENU, self.OnPopupThree, id=self.popupID3)
        # make a menu
        menu = wx.Menu()
        # add some items
        menu.Append(self.popupID1, _("Associated forms"))
        menu.Append(self.popupID2, _("Concordance"))
        #menu.Append(self.popupID3, "recharger")
        self.PopupMenu(menu)
        menu.Destroy()

    def OnPopupOne(self, event):
        corpus = self.gparent.corpus
        word = self.getColumnText(self.GetFirstSelected(), 0)
        lems = corpus.getlems()
        rep = []
        for forme in lems[word].formes:
            rep.append([corpus.getforme(forme).forme, corpus.getforme(forme).freq])
        rep.sort( key= lambda x:x[1], reverse=True)
        items = dict(
            [[i, '<font face="courier">' + '\t:\t'.join([str(val) for val in forme]) + '</font>'] for i, forme in
             enumerate(rep)])
        win = message(self, items, _("Associated forms"), (300, 200))
        # win.html = '<html>\n' + '<br>'.join([' : '.join([str(val) for val in forme]) for forme in rep]) + '\n</html>'
        # win.HtmlPage.SetPage(win.html)
        win.Show(True)

    def OnPopupTwo(self, event):
        corpus = self.gparent.corpus
        item = self.getColumnText(self.GetFirstSelected(), 0)
        uce_ok = corpus.getlemuces(item)
        ucis_txt, ucestxt = doconcorde(corpus, uce_ok, [item])
        items = dict([[i, '<br><br>'.join([ucis_txt[i], ucestxt[i]])] for i in range(0, len(ucestxt))])
        win = message(self, items, ' - '.join([_("Concordance"), "%s" % item]), (800, 500), uceids=uce_ok)
        # win = message(self, u"Concordancier", (750, 600))
        # win.html = ('<html>\n<h1>%s</h1>' % item) + '<br>'.join(['<br>'.join([ucis_txt[i], ucestxt[i]]) for i in range(0,len(ucestxt))]) + '\n</html>'
        # win.HtmlPage.SetPage(win.html)
        win.Show(True)
