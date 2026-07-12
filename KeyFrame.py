# -*- coding: utf-8 -*-
#Author: Pierre Ratinaud
#Copyright (c) 2008-2020 Pierre Ratinaud
#modification pour python 3 : Laurent Mérat, 6x7 - mai 2020
#License: GNU/GPL

#------------------------------------
# import des modules python
#------------------------------------

#------------------------------------
# import des modules wx
#------------------------------------
import wx

#------------------------------------
# import des fichiers du projet
#------------------------------------
from functions import sortedby, DoConf

# begin wxGlade: extracode
# end wxGlade

class AlcOptFrame(wx.Dialog):
    def __init__(self,parent, *args, **kwds):
        # begin wxGlade: AlcOptFrame.__init__
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        self.cle={
        'adj_sup': [wx.NewId(),wx.NewId(),"Adjectif supplémentaire"],
        'art_ind': [wx.NewId(),wx.NewId(),"Article indéfini"],
        'adj_pos': [wx.NewId(),wx.NewId(),"Adjectif possessif"],
        'adv_sup': [wx.NewId(),wx.NewId(),"Adverbe supplémentaire"],
        'pro_dem': [wx.NewId(),wx.NewId(),"Pronom démonstratif"],
        'art_def': [wx.NewId(),wx.NewId(),"Article défini"],
        'con': [wx.NewId(),wx.NewId(),"Conjonction"],
        'pre': [wx.NewId(),wx.NewId(),"Préposition"],
        'ono': [wx.NewId(),wx.NewId(),"Onomatopée"],
        'adj_dem': [wx.NewId(),wx.NewId(),"Adjectif démonstratif"],
        'nom_sup': [wx.NewId(),wx.NewId(),"Nom supplémentaire"],
        'adv': [wx.NewId(),wx.NewId(),"Adverbe"],
        'pro_per': [wx.NewId(),wx.NewId(),"Pronom personnel"],
        'ver': [wx.NewId(),wx.NewId(),"Verbe"],
        'adj_num': [wx.NewId(),wx.NewId(),"Adjectif numérique"],
        'pro_rel': [wx.NewId(),wx.NewId(),"Pronom relatif"],
        'adj_ind': [wx.NewId(),wx.NewId(),"Adjectif indéfini"],
        'pro_ind': [wx.NewId(),wx.NewId(),"Pronom indéfini"],
        'pro_pos': [wx.NewId(),wx.NewId(),"Pronom possessif"],
        'aux': [wx.NewId(),wx.NewId(),"Auxiliaire"],
        'ver_sup': [wx.NewId(),wx.NewId(),"Verbe supplémentaire"],
        'adj': [wx.NewId(),wx.NewId(),"Adjectif"],
        'adj_int': [wx.NewId(),wx.NewId(),"Adjectif interrogatif"],
        'nom': [wx.NewId(),wx.NewId(),"Nom commun"],
        'num' : [wx.NewId(),wx.NewId(),"Chiffre"],
        'nr' : [wx.NewId(),wx.NewId(),"Formes non reconnues"],
        }
        self.parent=parent
        self.keys=self.parent.keys
        self.listlabel=[]
        self.listspin=[]
        self.listbutton=[]
        self.listcle=[]
        self.listids=[]
        self.listidb=[]
        
        self.label_1 = wx.StaticText(self, -1, "        Choix des clés d'analyse\n0=éliminé ; 1=active ; 2=supplémentaire\n")
        self.listcleori=[[cle]+self.cle[cle] for cle in self.cle]
        self.listcleori=sortedby(self.listcleori,1,3)

        for line in self.listcleori:
            cle,ids,idb,label=line
            self.listlabel.append(wx.StaticText(self, -1, label))
            self.listspin.append(wx.SpinCtrl(self, ids,repr(self.keys[cle]), min=0, max=2))
            #if cle != 'nr' and cle!= 'num' : 
            self.listbutton.append(wx.Button(self, idb, "voir liste"))
            self.listids.append(ids)
            self.listidb.append(idb)
            self.listcle.append(cle)
            

        self.button_val = wx.Button(self, wx.ID_OK)
        
        for button in self.listbutton :
            self.Bind(wx.EVT_BUTTON,self.OnShowList,button)
        
        #self.Bind(wx.EVT_BUTTON, self.OnApply, self.button_val)
        
        self.dico=self.parent.parent.lexique#'dictionnaires/lexique.txt')

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: AlcOptFrame.__set_properties
        self.SetTitle("Clés d'analyse")
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: AlcOptFrame.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_1 = wx.GridSizer(14, 3, 0, 0)
        grid_sizer_2 = wx.GridSizer(14, 3, 0, 0)
        sizer_2.Add(self.label_1, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
        for i in range(0,14):
            grid_sizer_1.Add(self.listlabel[i], 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
            grid_sizer_1.Add(self.listspin[i], 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
            grid_sizer_1.Add(self.listbutton[i], 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
        for i in range(14,len(self.listlabel)):
            grid_sizer_2.Add(self.listlabel[i], 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
            grid_sizer_2.Add(self.listspin[i], 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
            grid_sizer_2.Add(self.listbutton[i], 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_3.Add(grid_sizer_1, 1, wx.EXPAND, 0)
        sizer_3.Add(grid_sizer_2, 1, wx.EXPAND, 0)
        sizer_2.Add(sizer_3, 1, wx.EXPAND, 8)
        sizer_2.Add(self.button_val,0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        sizer_1.Add(sizer_2, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()
        # end wxGlade

    def OnShowList(self,evt):
        id=evt.GetEventObject().GetId()
        pos=self.listidb.index(id)
        type=self.listcle[pos]
        self.CreateList(type)
        
    def CreateList(self,type):
        if type=='ver_sup' or type=='ver':
            #liste=[descr[0] for item,descr in self.dico.iteritems() if descr[1]==type]
            liste = [forme for forme in self.corpus.formes if self.corpus.formes[forme].gram==type]
            liste=list(set(liste))
        else:
            #liste=[item for item,descr in self.dico.iteritems() if descr[1]==type]
            liste = [forme for forme in self.corpus.formes if self.corpus.formes[forme].gram==type]
        liste.sort()
        txt=('\n').join(liste)
        ListViewFrame=ListView(self.parent)
        ListViewFrame.text_ctrl_1.WriteText(txt)
        ListViewFrame.text_ctrl_1.SetSelection(0,0)
        ListViewFrame.text_ctrl_1.SetInsertionPoint(0)
        ListViewFrame.CenterOnParent()
        val=ListViewFrame.ShowModal()
    
class ListView(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, size=wx.Size(200, 400),style=wx.DEFAULT_DIALOG_STYLE)
        self.text_ctrl_1 = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE|wx.TE_RICH2)
        self.text_ctrl_1.SetMinSize(wx.Size(200, 400))
        self.btn = wx.Button(self, wx.ID_OK)
        self.SetMinSize(wx.Size(200, 400))
        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.SetTitle("Liste")

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(self.text_ctrl_1, 1, wx.EXPAND, 0)
        sizer_1.Add(self.btn,0,wx.EXPAND,0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()

