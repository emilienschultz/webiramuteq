# -*- coding: utf-8 -*-
#Author: Pierre Ratinaud
#Copyright (c) 2008-2020 Pierre Ratinaud
#License: GNU/GPL

#------------------------------------
# import des modules python
#------------------------------------
import string
import os
import sys
import tempfile
from time import sleep

#------------------------------------
# import des modules wx
#------------------------------------
import wx

#------------------------------------
# import des fichiers du projet
#------------------------------------
from chemins import ffr
from layout import MakeHeader,MakeStudentTable
from functions import exec_rcode, check_Rresult


class StudentDialog(wx.Dialog):

    def __init__(
            self, parent, ID, title, size=wx.DefaultSize, pos=wx.DefaultPosition, 
            style=wx.DEFAULT_DIALOG_STYLE
            ):
        wx.Dialog.__init__(self)                       # 1
        self.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)    # 2
        self.Create(parent, ID, title)                 # 3
        Filename=parent.PATH[0]
        self.content=parent.table[:]
        self.HEADER=parent.header[:]
        fnb={}
        inb={}
        cnb={}
        vide={}
        #FIXME : assume une premiere ligne contenant les noms de colonnes
        for line in self.content:
            i=0
            for val in line :
                if val=='':
                    if i in vide:
                        vide[i]+=1
                    else:
                        vide[i]=1
                else:
                    try:
                        int(val)
                        if i in inb:
                            inb[i]+=1
                        else:
                            inb[i]=1
                    except:
                        try:
                            float(val)
                            if i in fnb:
                                fnb[i]+=1
                            else:
                                fnb[i]=1
                        except:
                            if i in cnb:
                                cnb[i]+=1
                            else:
                                cnb[i]=1
                i+=1
        dicttot={}
        for key,nb in vide.items():
            dicttot[key]=['vide',nb]
        print(dicttot)
        for key,nb in inb.items() :
            if key in dicttot:
                dicttot[key]=['int',dicttot[key][1]+nb]
            else:
                dicttot[key]=['int',nb]
        for key,nb in fnb.items():
            if key in dicttot:
                dicttot[key]=['float',dicttot[key][1]+nb]
            else:
                dicttot[key]=['float',nb]
        for key,nb in cnb.items():
            if key in dicttot:
                dicttot[key]=['char',dicttot[key][1]+nb]
            else:
                dicttot[key]=['char',nb]
        acontent=array(self.content)
        self.ListGrp=[]
        lg=[i for i,descr in dicttot.items() if descr[0]=='char']
        for i in lg:
            if len(unique(acontent[:,i]))==2:
                self.ListGrp.append(i)
            elif ('' in unique(acontent[:,i]).tolist()) and len(unique(acontent[:,i]))==3:
                self.ListGrp.append(i)
        li=[i for i,descr in dicttot.items() if descr[0]=='int']
        lf=[i for i,descr in dicttot.items() if descr[0]=='float']
        self.ListNum=li+lf
        print(self.ListGrp, self.ListNum)    
        LABELLIST=[]
        for i in self.HEADER:
            if len(i)>60 :
                LABELLIST.append(i[0:60])
            else:
                LABELLIST.append(i)
        self.LabelListGrp=[]
        self.LabelListNum=[]
        for i in self.ListGrp :
            self.LabelListGrp.append(LABELLIST[i])
        for i in self.ListNum :
            self.LabelListNum.append(LABELLIST[i])
        self.list_box_1 = wx.ListBox(self, -1, choices=self.LabelListGrp, style=wx.LB_MULTIPLE|wx.LB_HSCROLL)
        self.list_box_2 = wx.ListBox(self, -1, choices=self.LabelListNum, style=wx.LB_MULTIPLE|wx.LB_HSCROLL)
        self.button_1 = wx.Button(self, wx.ID_OK)
        self.button_cancel = wx.Button(self, wx.ID_CANCEL)
        self.__set_properties()
        self.__do_layout()
        self.Bind(wx.EVT_LISTBOX, self.Select1, self.list_box_1)
        # end wxGlade
        self.TEMPDIR=parent.TEMPDIR
        self.parent=parent
        self.Filename=parent.fileforR
        #--------------FIXME
        self.num=parent.FreqNum
        #-------------------------------

    def __set_properties(self):
        # begin wxGlade: ConfChi2.__set_properties
        self.SetTitle("Sélection des variables")
        self.list_box_1.SetSelection(0)
        self.list_box_2.SetSelection(0)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: ConfChi2.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3.Add(self.list_box_1, 0, wx.EXPAND, 0)
        sizer_3.Add(self.list_box_2, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 0)
        sizer_2.Add(sizer_3, 1, wx.EXPAND, 0)
        sizer_4.Add(self.button_cancel, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 0)
        sizer_4.Add(self.button_1, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 0)
        sizer_2.Add(sizer_4, 0, wx.ALIGN_CENTRE_HORIZONTAL, 0)
        sizer_1.Add(sizer_2, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()
        # end wxGlade

    def Select1(self, event): # wxGlade: ConfChi2.<event_handler>
        event.Skip()

    def ShowStudent(self,select1,select2):
        parent=self.parent
        self.encode=self.parent.SysEncoding
        #################################################
        #max = len(select1)*len(select2)
        #dlg = wx.ProgressDialog("Traitements",
        #                         "Veuillez patienter...",
        #                         maximum = max,
        #                         parent=self,
        #                         style = wx.PD_APP_MODAL
        #                       )
        #dlg.Center()
        #count = 0
        ###############################################
        Graph=True
        colgrp=[self.ListGrp[i] for i in select1]
        colnum=[self.ListNum[i] for i in select2]
        if len(select1)==1:
            strcolgrp=str(tuple(colgrp)).replace(',','')
        else:
            strcolgrp=str(tuple(colgrp))
        if len(select2)==1:
            strcolnum=str(tuple(colnum)).replace(',','')
        else:
            strcolnum=str(tuple(colnum))
        txtR=''
        txtR+="""
        source('%s')
        """%self.parent.RscriptsPath['Rfunct']
        if parent.g_id: rownames='1'
        else : rownames='NULL'
        if parent.g_header : header = 'TRUE'
        else : header = 'FALSE'
        #txtR+="""
        #datadm <- ReadData('%s', encoding='%s',header = %s, sep = '%s',quote = '%s', na.strings = '%s',rownames=%s)
        txtR += """
        datadm <- read.csv2('%s', encoding='%s',header = %s, sep = '%s',quote = '%s', na.strings = '%s',row.names=%s, dec='.')
        """%(ffr(self.Filename),parent.encode,header, parent.colsep,parent.txtsep,parent.nastrings,rownames)
        txtR+="""
        num<-%i
        """%self.num
        txtR+="""
        tmpdir<-'%s'
        """%ffr(self.TEMPDIR)
        txtR+="""
        out<-matrix(0,0,1)
        count<-0
        for (i in c%s) {
        """%strcolgrp
        txtR+="""
            for (j in c%s) {
        """%strcolnum
        txtR+="""
                datadm[,(j+1)]<-as.numeric(datadm[,(j+1)])
                count<-count+1
                fileout<-paste('student',num,sep='')
                fileout<-paste(fileout,'_',sep='')
                fileout<-paste(fileout,count,sep='')
                fileout<-paste(fileout,'.jpeg',sep='')
                fileout<-file.path(tmpdir,fileout)
                if (Sys.info()["sysname"]=='Darwin') {
                    quartz(file=fileout,type='jpeg')
                    par(cex=1)
                } else {
                    jpeg(fileout,res=200)
                    par(cex=0.4)
                }
                plot(datadm[,(j+1)] ~ datadm[,(i+1)],data=datadm)
                dev.off()
                student<-t.test(datadm[,(j+1)] ~ datadm[,(i+1)],data=datadm)
                pvalue<-student$p.value
                method<-student$method
                tvalue<-student$statistic
                df<-student$parameter
                grmean<-as.matrix(student$estimate)
                out<-rbind(out,round(grmean,digits=2))
                out<-rbind(out,pvalue)
                out<-rbind(out,method)
                out<-rbind(out,tvalue)
                out<-rbind(out,round(df,digits=2))
                out<-rbind(out,fileout)
                out<-rbind(out,"**")
            }
        }
        """
        restmp=tempfile.mktemp(dir=self.TEMPDIR)
        txtR+="""
        write.csv2(out,file='%s')
        """%ffr(restmp)
        tmpfile=tempfile.mktemp(dir=self.TEMPDIR)
        tmpscript=open(tmpfile,'w')
        tmpscript.write(txtR)
        tmpscript.close()
        pid = exec_rcode(self.parent.RPath, tmpfile, wait = False)
        while pid.poll() == None :
            sleep(0.2)
        check_Rresult(self.parent, pid)
        file=open(restmp,'r')
        res=file.readlines()
        file.close()
        resl=[line.replace('\n','').replace('"','').split(';') for line in res]
        resl.pop(0)
        i=0
        student={}
        listr=[]
        for line in resl :
            if i==8 :
                i=0
            if i==0 :
                student['grp1']=line[0].replace('mean in group ','')
                student['mean1']=float(line[1])
            if i==1 :
                student['grp2']=line[0].replace('mean in group ','')
                student['mean2']=float(line[1])     
            if i==2:
                student['p.value']=float(line[1]) 
            if i==3:
                student['method']=line[1]
            if i==4 :
                student['t']=float(line[1])
            if i==5 :
                student['df']=float(line[1])
            if i==6:
                student['graph']=line[1]
            if i==7:
                listr.append(student)
                student={}
            i+=1
        txt2=''
        ancre=0
        LISTFILE=[]
        LISTFILE.append(False)
        txt=MakeHeader('T de Student', self.encode)
        ListGraph=[]
        for i in select1 :
            for j in select2:
                ancre+=1
                Student=listr[ancre-1]
                pvalue=Student['p.value']
                Colname=self.LabelListNum[j]
                Colgrp=self.LabelListGrp[i]
                LISTFILE.append(Student['graph'])
                if pvalue<0.05:
                    color='green'
                else:
                    color='red'
                txt+="<a href=#%s><font color=%s>%s</font></a><br />"%(ancre,color,Colname+' / '+Colgrp) 
                txt2+=MakeStudentTable(Student,self.num,ancre,Graph,os.path.basename(Student['graph']),Colname,self.encode)                
        txt+=txt2
        fileout=os.path.join(self.TEMPDIR,'resultats-student_%s.html'%str(self.num))
        File=open(fileout,'w')
        File.write(txt)
        File.close()
        LISTFILE.append(fileout)
#        dlg.Destroy()
        return LISTFILE


class MakeStudent():

    def __init__(self,parent):
        dlg = StudentDialog(parent, -1, "Student", size=(350, 400),
                         style = wx.DEFAULT_DIALOG_STYLE
                         )
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        if val==wx.ID_OK :
            ColSel1=dlg.list_box_1.GetSelections()
            ColSel2=dlg.list_box_2.GetSelections()
            listfileout=dlg.ShowStudent(ColSel1,ColSel2)
            parent.FreqNum+=1
            parent.DictTab["t de student_%s*"%parent.FreqNum]=listfileout
            parent.FileTabList.append(listfileout)
            parent.newtab=wx.html.HtmlWindow(parent.nb, -1)
            if "gtk2" in wx.PlatformInfo:
                parent.newtab.SetStandardFonts()
            parent.newtab.LoadPage(listfileout[len(listfileout)-1])
            parent.nb.AddPage(parent.newtab,"t de student_%s*"%parent.FreqNum)
            parent.nb.SetSelection(parent.nb.GetPageCount()-1)
            parent.ShowTab(wx.EVT_BUTTON)
            parent.DisEnSaveTabAs(True)
