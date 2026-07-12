# -*- coding: utf-8 -*-
#Author: Pierre Ratinaud
#Copyright (c) 2008-2011 Pierre Ratinaud
#License: GNU/GPL

#------------------------------------
# import des modules python
#------------------------------------
import tempfile
import os
import locale
from datetime import datetime
import logging

#------------------------------------
# import des fichiers du projet
#------------------------------------
from chemins import ffr, PathOut


log = logging.getLogger('iramuteq.printRscript')


class PrintRScript:

    def __init__ (self, analyse, parametres = None):
        log.info('Rscript')
        self.pathout = analyse.pathout
        self.analyse = analyse
        if parametres is None:
            self.parametres = analyse.parametres
        else:
            self.parametres = parametres
        #self.scriptout = ffr(self.pathout['lastRscript.R'])
        self.scriptout = self.pathout['temp']
        self.script =  "#Script genere par IRaMuTeQ - %s\n" % datetime.now().ctime()

    def add(self, txt):
        self.script = '\n'.join([self.script, txt])

    def defvar(self, name, value):
        self.add(' <- '.join([name, value]))

    def defvars(self, lvars):
        for val in lvars:
            self.defvar(val[0],val[1])

    def sources(self, lsources):
        for source in lsources:
            self.add('source("%s", encoding = \'utf8\')' % ffr(source))

    def packages(self, lpks):
        for pk in lpks:
            self.add('library(%s)' % pk)

    def load(self, l):
        for val in l:
            self.add('load("%s")' % ffr(val))

    def write(self):
        with open(self.scriptout, 'w', encoding='utf8') as f:
            f.write(self.script)


# ???
class chdtxt(PrintRScript):
    pass


def Rcolor(color):
    return str(color).replace(')', ', max=255)')


class Alceste2(PrintRScript):

    def doscript(self):
        self.sources(['chdfunct'])
        self.load(['Rdata'])
        lvars = [['clnb', repr(self.analyse.clnb)], 
                ['Contout', '"%s"' % self.pathout['Contout']],
                ['ContSupOut', '"%s"' % self.pathout['ContSupOut']],
                ['ContEtOut', '"%s"' % self.pathout['ContEtOut']],
                ['profileout', '"%s"' % self.pathout['profils.csv']],
                ['antiout', '"%s"' % self.pathout['antiprofils.csv']],
                ['chisqtable', '"%s"' % self.pathout['chisqtable.csv']],
                ['ptable', '"%s"' % self.pathout['ptable.csv']]]
       
        self.defvars(lvars) 

#    txt = "clnb<-%i\n" % clnb
#    txt += """
#source("%s")
#load("%s")
#""" % (RscriptsPath['chdfunct'], DictChdTxtOut['RData'])
#    txt += """
#dataact<-read.csv2("%s", header = FALSE, sep = ';',quote = '\"', row.names = 1, na.strings = 'NA')
#datasup<-read.csv2("%s", header = FALSE, sep = ';',quote = '\"', row.names = 1, na.strings = 'NA')
#dataet<-read.csv2("%s", header = FALSE, sep = ';',quote = '\"', row.names = 1, na.strings = 'NA')
#""" % (DictChdTxtOut['Contout'], DictChdTxtOut['ContSupOut'], DictChdTxtOut['ContEtOut'])
#    txt += """
#tablesqrpact<-BuildProf(as.matrix(dataact),n1,clnb)
#tablesqrpsup<-BuildProf(as.matrix(datasup),n1,clnb)
#tablesqrpet<-BuildProf(as.matrix(dataet),n1,clnb)
#"""
#    txt += """
#PrintProfile(n1,tablesqrpact[4],tablesqrpet[4],tablesqrpact[5],tablesqrpet[5],clnb,"%s","%s",tablesqrpsup[4],tablesqrpsup[5])
#""" % (DictChdTxtOut['PROFILE_OUT'], DictChdTxtOut['ANTIPRO_OUT'])
#    txt += """
#colnames(tablesqrpact[[2]])<-paste('classe',1:clnb,sep=' ')
#colnames(tablesqrpact[[1]])<-paste('classe',1:clnb,sep=' ')
#colnames(tablesqrpsup[[2]])<-paste('classe',1:clnb,sep=' ')
#colnames(tablesqrpsup[[1]])<-paste('classe',1:clnb,sep=' ')
#colnames(tablesqrpet[[2]])<-paste('classe',1:clnb,sep=' ')
#colnames(tablesqrpet[[1]])<-paste('classe',1:clnb,sep=' ')
#chistabletot<-rbind(tablesqrpact[2][[1]],tablesqrpsup[2][[1]])
#chistabletot<-rbind(chistabletot,tablesqrpet[2][[1]])
#ptabletot<-rbind(tablesqrpact[1][[1]],tablesqrpet[1][[1]])
#"""
#    txt += """
#write.csv2(chistabletot,file="%s")
#write.csv2(ptabletot,file="%s")
#gbcluster<-n1
#write.csv2(gbcluster,file="%s")
#""" % (DictChdTxtOut['chisqtable'], DictChdTxtOut['ptable'], DictChdTxtOut['SbyClasseOut'])
#


def RchdTxt(DicoPath, RscriptPath, mincl, classif_mode, nbt = 9, svdmethod = 'svdR', libsvdc = False, libsvdc_path = None, R_max_mem = False, mode_patate = False, nbproc=10):
    txt = """
    source("%s")
    source("%s")
    source("%s")
    source("%s")
    """ % (ffr(RscriptPath['CHD']), ffr(RscriptPath['chdtxt']), ffr(RscriptPath['anacor']), ffr(RscriptPath['Rgraph']))
    if R_max_mem:
        txt += """
    memory.limit(%i)
        """ % R_max_mem
    txt += """
    nbt <- %i
    """ % nbt
    if svdmethod == 'svdlibc' and libsvdc:
        txt += """
        svd.method <- 'svdlibc'
        libsvdc.path <- "%s"
        """ % ffr(libsvdc_path)
    elif svdmethod == 'irlba':
        txt += """
        library(irlba)
        svd.method <- 'irlba'
        libsvdc.path <- NULL
        """
    else:
        txt += """
        svd.method = 'svdR'
        libsvdc.path <- NULL
        """
    if mode_patate:
        txt += """
        mode.patate = TRUE
        """
    else:
        txt += """
        mode.patate = FALSE
        """
    txt +="""
    library(Matrix)
    data1 <- readMM("%s")
    data1 <- as(data1, "dgCMatrix")
    row.names(data1) <- 1:nrow(data1)
    """ % ffr(DicoPath['TableUc1'])
    if classif_mode == 0:
        txt += """
        data2 <- readMM("%s")
        data2 <- as(data2, "dgCMatrix")
        row.names(data2) <- 1:nrow(data2)
        """ % ffr(DicoPath['TableUc2'])
    txt += """
    #log1 <- "%s"
    #print('FIXME : source newCHD')
    #source('/home/pierre/workspace/iramuteq/Rscripts/newCHD.R')
    #nbproc <- %s
    #chd1<-CHD(data1, x = nbt, mode.patate = mode.patate, svd.method = svd.method, libsvdc.path = libsvdc.path, find='matrix', select.next='size', sample=20, amp=500, proc.nb=nbproc)
    chd1<-CHD(data1, x = nbt, mode.patate = mode.patate, svd.method = svd.method, libsvdc.path = libsvdc.path)#, log.file = log1)
    """ % (ffr(DicoPath['log-chd1.txt']), nbproc)
    if classif_mode == 0:
        txt += """
    log2 <- "%s"
    chd2<-CHD(data2, x = nbt, mode.patate = mode.patate, svd.method =
    svd.method, libsvdc.path = libsvdc.path)#, log.file = log2)
    """ % ffr(DicoPath['log-chd2.txt'])
    txt += """
    #lecture des uce
    listuce1<-read.csv2("%s")
    """ % ffr(DicoPath['listeuce1'])
    if classif_mode == 0:
        txt += """
        listuce2<-read.csv2("%s")
        """ % ffr(DicoPath['listeuce2'])
    txt += """
    rm(data1)
    """
    if classif_mode == 0:
        txt += """
        rm(data2)
        """
    txt += """
    classif_mode <- %i
    mincl <- %i
    if (mincl == 0) {mincl <- round(nrow(chd1$n1)/(nbt+1))}
    uceout <- "%s"
    write.csv2(chd1$n1, file="%s")
    if (classif_mode == 0) {
        chd.result <- Rchdtxt(uceout, chd1, chd2 = chd2, mincl = mincl,classif_mode = classif_mode, nbt = nbt)
        classeuce1 <- chd.result$cuce1
        tree.tot1 <- make_tree_tot(chd1)
        tree.cut1 <- make_dendro_cut_tuple(tree.tot1$dendro_tuple, chd.result$coord_ok, classeuce1, 1, nbt)
    } else {
        #chd.result <- Rchdtxt(uceout, chd1, chd2 = chd1, mincl = mincl,classif_mode = classif_mode, nbt = nbt)
        tree.tot1 <- make_tree_tot(chd1)
        terminales <- find.terminales(chd1$n1, chd1$list_mere, chd1$list_fille, mincl)
        tree.cut1 <- make.classes(terminales, chd1$n1, tree.tot1$tree.cl, chd1$list_fille)
        write.csv2(tree.cut1$n1, uceout)
        chd.result <- tree.cut1
    }
    classes<-chd.result$n1[,ncol(chd.result$n1)]
    write.csv2(chd.result$n1, file="%s")
    """ % (classif_mode, mincl, ffr(DicoPath['uce']), ffr(DicoPath['n1-1.csv']), ffr(DicoPath['n1.csv']))
    txt += """
#    tree.tot1 <- make_tree_tot(chd1)
#    open_file_graph("%s", widt = 600, height=400)
#    plot(tree.tot1$tree.cl)
#    dev.off()
    """ % ffr(DicoPath['arbre1'])
    if classif_mode == 0:
        txt += """
        classeuce2 <- chd.result$cuce2
        tree.tot2 <- make_tree_tot(chd2)
#        open_file_graph("%s", width = 600, height=400)
#        plot(tree.tot2$tree.cl)
#        dev.off()
        """ % ffr(DicoPath['arbre2'] )
    txt += """
        save(tree.cut1, file="%s")

    open_file_graph("%s", width = 600, height=400)
    plot.dendropr(tree.cut1$tree.cl,classes, histo=TRUE)
    open_file_graph("%s", width = 600, height=400)
    plot(tree.cut1$dendro_tot_cl)
    dev.off()
    """ % (ffr(DicoPath['Rdendro']), ffr(DicoPath['dendro1']), ffr(DicoPath['arbre1']))
    if classif_mode == 0:
        txt += """
        tree.cut2 <- make_dendro_cut_tuple(tree.tot2$dendro_tuple, chd.result$coord_ok, classeuce2, 2, nbt)
        open_file_graph("%s", width = 600, height=400)
        plot(tree.cut2$tree.cl)
        dev.off()
        open_file_graph("%s", width = 600, height=400)
        plot(tree.cut2$dendro_tot_cl)
        dev.off()
        """ % (ffr(DicoPath['dendro2']), ffr(DicoPath['arbre2']))
    txt += """
    #save.image(file="%s")
    """ % (ffr(DicoPath['RData']))
    fileout = open(DicoPath['Rchdtxt'], 'w', encoding='utf8')
    fileout.write(txt)
    fileout.close()

def RPamTxt(corpus, RscriptPath):
    DicoPath = corpus.pathout
    param = corpus.parametres
    txt = """
    source("%s")
    """ % (RscriptPath['pamtxt'])
    txt += """
    source("%s")
    """ % (RscriptPath['Rgraph'])
    txt += """
    result <- pamtxt("%s", "%s", "%s", method = "%s", clust_type = "%s", clnb = %i)
    n1 <- result$uce
    """ % (DicoPath['TableUc1'], DicoPath['listeuce1'], DicoPath['uce'], param['method'], param['cluster_type'], param['nbcl'] )
    txt += """
    open_file_graph("%s", width=400, height=400)
    plot(result$cl)
    dev.off()
    """ % (DicoPath['arbre1'])
    txt += """
    save.image(file="%s")
    """ % DicoPath['RData']
    fileout = open(DicoPath['Rchdtxt'], 'w', encoding='utf8')
    fileout.write(txt)
    fileout.close()

def RchdQuest(DicoPath, RscriptPath, nbcl = 10, mincl = 10):
    txt = """
    source("%s")
    source("%s")
    source("%s")
    source("%s")
    """ % (ffr(RscriptPath['CHD']), ffr(RscriptPath['chdquest']), ffr(RscriptPath['anacor']),ffr(RscriptPath['Rgraph']))
    txt += """
    nbt <- %i - 1
    mincl <- %i
    """ % (nbcl, mincl)
    txt += """
    chd.result<-Rchdquest("%s","%s","%s", nbt = nbt, mincl = mincl)
    n1 <- chd.result$n1
    classeuce1 <- chd.result$cuce1
    """ % (ffr(DicoPath['mat01.csv']), ffr(DicoPath['listeuce1']), ffr(DicoPath['uce']))
    txt += """
    tree_tot1 <- make_tree_tot(chd.result$chd)
    open_file_graph("%s", width = 600, height=400)
    plot(tree_tot1$tree.cl)
    dev.off()
    """ % ffr(DicoPath['arbre1'])
    txt += """
    tree_cut1 <- make_dendro_cut_tuple(tree_tot1$dendro_tuple, chd.result$coord_ok, classeuce1, 1, nbt)
    tree.cut1 <- tree_cut1
    save(tree.cut1, file="%s")
    open_file_graph("%s", width = 600, height=400)
    classes<-n1[,ncol(n1)]
    plot.dendropr(tree_cut1$tree.cl,classes, histo = TRUE)
    """ % (ffr(DicoPath['Rdendro']), ffr(DicoPath['dendro1']))
    txt += """
    save.image(file="%s")
    """ % ffr(DicoPath['RData'])
    fileout = open(DicoPath['Rchdquest'], 'w', encoding='utf8')
    fileout.write(txt)
    fileout.close()
    
def ReinertTxtProf(DictChdTxtOut, RscriptsPath, clnb, taillecar):
    txt = "clnb<-%i\n" % clnb
    txt += """
source("%s")
#load("%s")
n1 <- read.csv2("%s")
""" % (ffr(RscriptsPath['chdfunct']), ffr(DictChdTxtOut['RData']), ffr(DictChdTxtOut['n1.csv']))
    txt += """
dataact<-read.csv2("%s", header = FALSE, sep = ';',quote = '\"', row.names = 1, na.strings = 'NA')
datasup<-read.csv2("%s", header = FALSE, sep = ';',quote = '\"', row.names = 1, na.strings = 'NA')
dataet<-read.csv2("%s", header = FALSE, sep = ';',quote = '\"', row.names = 1, na.strings = 'NA')
""" % (ffr(DictChdTxtOut['Contout']), ffr(DictChdTxtOut['ContSupOut']), ffr(DictChdTxtOut['ContEtOut']))
    txt += """
print('ATTENTION NEW BUILD PROF')
#tablesqrpact<-BuildProf(as.matrix(dataact),n1,clnb)
#tablesqrpsup<-BuildProf(as.matrix(datasup),n1,clnb)
#tablesqrpet<-BuildProf(as.matrix(dataet),n1,clnb)
tablesqrpact<-new.build.prof(as.matrix(dataact),n1,clnb)
tablesqrpsup<-new.build.prof(as.matrix(datasup),n1,clnb)
tablesqrpet<-new.build.prof(as.matrix(dataet),n1,clnb)
"""
    txt += """
PrintProfile(n1,tablesqrpact[4],tablesqrpet[4],tablesqrpact[5],tablesqrpet[5],clnb,"%s","%s",tablesqrpsup[4],tablesqrpsup[5])
""" % (ffr(DictChdTxtOut['PROFILE_OUT']), ffr(DictChdTxtOut['ANTIPRO_OUT']))
    txt += """
colnames(tablesqrpact[[2]])<-paste('classe',1:clnb,sep=' ')
colnames(tablesqrpact[[1]])<-paste('classe',1:clnb,sep=' ')
colnames(tablesqrpsup[[2]])<-paste('classe',1:clnb,sep=' ')
colnames(tablesqrpsup[[1]])<-paste('classe',1:clnb,sep=' ')
colnames(tablesqrpet[[2]])<-paste('classe',1:clnb,sep=' ')
colnames(tablesqrpet[[1]])<-paste('classe',1:clnb,sep=' ')
chistabletot<-rbind(tablesqrpact[2][[1]],tablesqrpsup[2][[1]])
chistabletot<-rbind(chistabletot,tablesqrpet[2][[1]])
ptabletot<-rbind(tablesqrpact[1][[1]],tablesqrpet[1][[1]])
"""
    txt += """
write.csv2(chistabletot,file="%s")
write.csv2(ptabletot,file="%s")
gbcluster<-n1
write.csv2(gbcluster,file="%s")
""" % (ffr(DictChdTxtOut['chisqtable']), ffr(DictChdTxtOut['ptable']), ffr(DictChdTxtOut['SbyClasseOut']))
    if clnb > 2:
        txt += """
    library(ca)
    colnames(dataact)<-paste('classe',1:clnb,sep=' ')
    colnames(datasup)<-paste('classe',1:clnb,sep=' ')
    colnames(dataet)<-paste('classe',1:clnb,sep=' ')
    rowtot<-nrow(dataact)+nrow(dataet)+nrow(datasup)
    afctable<-rbind(as.matrix(dataact),as.matrix(datasup))
    afctable<-rbind(afctable,as.matrix(dataet))
    colnames(afctable)<-paste('classe',1:clnb,sep=' ')
    afc<-ca(afctable,suprow=((nrow(dataact)+1):rowtot),nd=(ncol(afctable)-1))
    debsup<-nrow(dataact)+1
    debet<-nrow(dataact)+nrow(datasup)+1
    fin<-rowtot
    afc<-AddCorrelationOk(afc)
    """
    #FIXME : split this!!!
        txt += """
    source("%s")
    """ % ffr(RscriptsPath['Rgraph'])
        txt += """
        afc <- summary.ca.dm(afc)
        afc_table <- create_afc_table(afc)
        write.csv2(afc_table$facteur, file = "%s")
        write.csv2(afc_table$colonne, file = "%s")
        write.csv2(afc_table$ligne, file = "%s")
        """ % (ffr(DictChdTxtOut['afc_facteur']), ffr(DictChdTxtOut['afc_col']), ffr(DictChdTxtOut['afc_row']))
        txt += """
    PARCEX<-%s
    """ % taillecar
        txt += """
    xyminmax <- PlotAfc2dCoul(afc, as.data.frame(chistabletot), "%s", what='coord', deb=1, fin=(debsup-1), xlab = xlab, ylab = ylab)
    """ % (ffr(DictChdTxtOut['AFC2DL_OUT']))
        txt += """
    PlotAfc2dCoul(afc, as.data.frame(chistabletot), "%s", what='coord', deb=debsup, fin=(debet-1), xlab = xlab, ylab = ylab, xmin = xyminmax$xminmax[1], xmax = xyminmax$xminmax[2], ymin = xyminmax$yminmax[1], ymax = xyminmax$yminmax[2], active=FALSE)
    """ % (ffr(DictChdTxtOut['AFC2DSL_OUT']))
        txt += """
        if ((fin - debet) > 2) {
    PlotAfc2dCoul(afc, as.data.frame(chistabletot), "%s", what='coord', deb=debet, fin=fin, xlab = xlab, ylab = ylab, xmin = xyminmax$xminmax[1], xmax = xyminmax$xminmax[2], ymin = xyminmax$yminmax[1], ymax = xyminmax$yminmax[2], active = FALSE)
        }
    """ % (ffr(DictChdTxtOut['AFC2DEL_OUT']))
        txt += """
    PlotAfc2dCoul(afc, as.data.frame(chistabletot), "%s", col=TRUE, what='coord', xlab = xlab, ylab = ylab, xmin = xyminmax$xminmax[1], xmax = xyminmax$xminmax[2], ymin = xyminmax$yminmax[1], ymax = xyminmax$yminmax[2], active=FALSE)
    """ % (ffr(DictChdTxtOut['AFC2DCL_OUT']))
#        txt += """
#   PlotAfc2dCoul(afc, as.data.frame(chistabletot), "%s", what='crl', deb=1, fin=(debsup-1), xlab = xlab, ylab = ylab)
#   PlotAfc2dCoul(afc, as.data.frame(chistabletot), "%s", what='crl', deb=debsup, fin=(debet-1), xlab = xlab, ylab = ylab)
#  PlotAfc2dCoul(afc, as.data.frame(chistabletot), "%s", what='crl', deb=debet, fin=fin, xlab = xlab, ylab = ylab)
#   PlotAfc2dCoul(afc, as.data.frame(chistabletot), "%s", col=TRUE, what='crl', xlab = xlab, ylab = ylab)
#   """ % (DictChdTxtOut['AFC2DCoul'], DictChdTxtOut['AFC2DCoulSup'], DictChdTxtOut['AFC2DCoulEt'], DictChdTxtOut['AFC2DCoulCl'])
    txt += """
#rm(dataact)
#rm(datasup)
#rm(dataet)
rm(tablesqrpact)
rm(tablesqrpsup)
rm(tablesqrpet)
save.image(file="%s")
""" % ffr(DictChdTxtOut['RData'])
    file = open(DictChdTxtOut['RTxtProfGraph'], 'w', encoding='utf8')
    file.write(txt)
    file.close()

def write_afc_graph(self):
    if self.param['over']:
        over = 'TRUE'
    else:
        over = 'FALSE'
    if self.param['do_select_nb']:
        do_select_nb = 'TRUE'
    else:
        do_select_nb = 'FALSE'
    if self.param['do_select_chi']:
        do_select_chi = 'TRUE'
    else:
        do_select_chi = 'FALSE'
    if self.param['do_select_chi_classe']:
        do_select_chi_classe = 'TRUE'
    else:
        do_select_chi_classe = 'FALSE'
    if self.param['cex_txt']:
        cex_txt = 'TRUE'
    else:
        cex_txt = 'FALSE'
    if self.param['tchi']:
        tchi = 'TRUE'
    else:
        tchi = 'FALSE'
    if self.param['svg']:
        svg = 'TRUE'
    else:
        svg = 'FALSE'
    if self.param['typegraph'] == 4:
        nodesfile = os.path.join(os.path.dirname(self.fileout),'nodes.csv')
        edgesfile = os.path.join(os.path.dirname(self.fileout),'edges.csv')
    else:
        nodesfile = 'NULL'
        edgesfile = 'NULL'
    with open(self.RscriptsPath['afc_graph'], 'r', encoding='utf8') as f:
        txt = f.read()
#    self.DictPathOut['RData'], \
    scripts = txt % (ffr(self.RscriptsPath['Rgraph']),\
    self.param['typegraph'], \
    edgesfile, nodesfile, \
    self.param['what'], \
    self.param['facteur'][0],\
    self.param['facteur'][1], \
    self.param['facteur'][2], \
    self.param['qui'], \
    over,  do_select_nb, \
    self.param['select_nb'],  \
    do_select_chi, \
    self.param['select_chi'], \
    do_select_chi_classe, \
    self.param['nbchic'], \
    cex_txt, \
    self.param['txt_min'], \
    self.param['txt_max'], \
    self.fileout, \
    self.param['width'], \
    self.param['height'],\
    self.param['taillecar'], \
    self.param['alpha'], \
    self.param['film'], \
    tchi,\
    self.param['tchi_min'],\
    self.param['tchi_max'],\
    ffr(os.path.dirname(self.fileout)),\
    svg)
    return scripts

def print_simi3d(self):
    simi3d = self.parent.simi3dpanel
    txt = '#Fichier genere par Iramuteq'
    if simi3d.movie.GetValue():
        movie = "'" + ffr(os.path.dirname(self.DictPathOut['RData'])) + "'"
    else:
        movie = 'NULL'
    #if self.corpus.parametres['type'] == 'corpus':
    #    header = 'TRUE'
    #else:
    #    header = 'FALSE'
    header = 'FALSE'
    txt += """
    dm<-read.csv2("%s",row.names=1,header = %s)
    load("%s")
    """ % (self.DictPathOut['Contout'], header, self.DictPathOut['RData'])
    txt += """
    source("%s")
    """ % self.parent.RscriptsPath['Rgraph']
    txt += """
    make.simi.afc(dm,chistabletot, lim=%i, alpha = %.2f, movie = %s)
    """ % (simi3d.spin_1.GetValue(), float(simi3d.slider_1.GetValue())/100, movie)
    tmpfile = tempfile.mktemp(dir=self.parent.TEMPDIR)
    tmp = open(tmpfile,'w', encoding='utf8')
    tmp.write(txt)
    tmp.close()
    return tmpfile

def dendroandbarplot(table, rownames, colnames, rgraph, tmpgraph, intxt = False, dendro=False):
    if not intxt:
        txttable = 'c(' + ','.join([','.join(line) for line in table]) + ')'
    rownb = len(rownames)
    rownames = 'c("' + '","'.join(rownames) + '")'
    colnames = 'c("' + '","'.join(colnames) + '")'
    if not intxt:
        #FIXME
        txt = """
            di <- matrix(data=%s, nrow=%i, byrow = TRUE)
            rownames(di)<- %s
            colnames(di) <- %s
        """ % (txttable, rownb, rownames, colnames)
    else:
        txt = intxt
    txt += """
        load("%s")
        library(ape)
        source("%s")
        height <- (30*ncol(di)) + (15*nrow(di))
        height <- ifelse(height <= 400, 400, height)
        width <- 500
        open_file_graph("%s", width=width, height=height)
        plot.dendro.lex(tree.cut1$tree.cl, di)
        """ % (ffr(dendro),ffr(rgraph),  ffr(tmpgraph))
    return txt

def barplot(table, parametres, intxt = False):
    if not intxt:
        txttable = 'c(' + ','.join([','.join(line) for line in table]) + ')'
    #width = 100 + (15 * len(rownames)) + (100 * len(colnames))
    #height =  len(rownames) * 15
    rownb = len(parametres['rownames'])
    #if height < 400:
    #    height = 400
    rownames = 'c("' + '","'.join(parametres['rownames']) + '")'
    colnames = 'c("' + '","'.join(parametres['colnames']) + '")'
    if not intxt:
        #FIXME
        txt = """
            di <- matrix(data=%s, nrow=%i, byrow = TRUE)
            toinf <- which(di == Inf)
            tominf <- which(di == -Inf)
            if (length(toinf)) {
                di[toinf] <- NA
                valmax <- max(di, na.rm = TRUE)
                if (valmax <= 0) {
                    valmax <- 2
                } else {
                    valmax <- valmax + 2
                }
                di[toinf] <- valmax
            }
            if (length(tominf)) {
                di[tominf] <- NA
                valmin <- min(di, na.rm = TRUE)
                if (valmin >=0) {
                    valmin <- -2
                } else {
                    valmin <- valmin - 2
                }
                di[tominf] <- valmin
            }
            rownames(di)<- %s
            colnames(di) <- %s
        """ % (txttable, rownb, rownames, colnames)
    else:
        txt = intxt
    if not 'tree' in parametres:
        txt += """
            source("%s")
            color = rainbow(nrow(di))
            width <- %i
            height <- %i
            open_file_graph("%s",width = width, height = height, svg = %s)
            par(mar=c(0,0,0,0))
            layout(matrix(c(1,2),1,2, byrow=TRUE),widths=c(3,lcm(12)))
            par(mar=c(8,4,1,0))
            yp = ifelse(length(toinf), 0.2, 0)
            ym = ifelse(length(tominf), 0.2, 0)
            ymin <- ifelse(!length(which(di < 0)), 0, min(di) - ym)
            coord <- barplot(as.matrix(di), beside = TRUE, col = color, space = c(0.1,0.6), ylim=c(ymin, max(di) + yp), las = 2)
            if (length(toinf)) {
                coordinf <- coord[toinf]
                valinf <- di[toinf]
                text(x=coordinf, y=valinf + 0.1, 'i')
            }
            if (length(tominf)) {
                coordinf <- coord[toinf]
                valinf <- di[toinf]
                text(x=coordinf, y=valinf - 0.1, 'i')
            }
            c <- colMeans(coord)
            c1 <- c[-1]
            c2 <- c[-length(c)]
            cc <- cbind(c1,c2)
            lcoord <- apply(cc, 1, mean)
            abline(v=lcoord)
            if (min(di) < 0) {
                amp <- abs(max(di) - min(di))
            } else {
                amp <- max(di)
            }
            if (amp < 10) {
                d <- 2
            } else {
                d <- signif(amp%%/%%10,1)
            }
            mn <- round(min(di))
            mx <- round(max(di))
            for (i in mn:mx) {
                if ((i/d) == (i%%/%%d)) {
                    abline(h=i,lty=3)
                }
            }
            par(mar=c(0,0,0,0))
            plot(0, axes = FALSE, pch = '')
            legend(x = 'center' , rownames(di)            , fill = color)
            dev.off()
            """ % (ffr(parametres['rgraph']), parametres['width'], parametres['height'], ffr(parametres['tmpgraph']), parametres['svg'])
    else:
        txt += """
        load("%s")
        library(ape)
        source("%s")
        width = %i
        height = %i
        open_file_graph("%s", width=width, height=height, svg = %s)
        plot.dendro.lex(tree.cut1$tree.cl, di)
        """ % (ffr(parametres['tree']), ffr(parametres['rgraph']), parametres['width'], parametres['height'], ffr(parametres['tmpgraph']), parametres['svg'])
    return txt

#def RAfcUci(DictAfcUciOut, nd=2, RscriptsPath='', PARCEX='0.8'):
#    txt = """
#    library(ca)
#    nd<-%i
#    """ % nd
#    txt += """
#    dataact<-read.csv2("%s")
#    """ % (DictAfcUciOut['TableCont'])#, encoding)
#    txt += """
#    datasup<-read.csv2("%s")
#    """ % (DictAfcUciOut['TableSup'])#, encoding)
#    txt += """
#    dataet<-read.csv2("%s")
#    """ % (DictAfcUciOut['TableEt'])#, encoding)
#    txt += """
#    datatotsup<-cbind(dataact,datasup)
#    datatotet<-cbind(dataact,dataet)
#    afcact<-ca(dataact,nd=nd)
#    afcsup<-ca(datatotsup,supcol=((ncol(dataact)+1):ncol(datatotsup)),nd=nd)
#    afcet<-ca(datatotet,supcol=((ncol(dataact)+1):ncol(datatotet)),nd=nd)
#    afctot<-afcsup$colcoord
#    rownames(afctot)<-afcsup$colnames
#    colnames(afctot)<-paste('coord. facteur',1:nd,sep=' ')
#    afctot<-cbind(afctot,mass=afcsup$colmass)
#    afctot<-cbind(afctot,distance=afcsup$coldist)
#    afctot<-cbind(afctot,intertie=afcsup$colinertia)
#    rcolet<-afcet$colsup
#    afctmp<-afcet$colcoord[rcolet,]
#    rownames(afctmp)<-afcet$colnames[rcolet]
#    afctmp<-cbind(afctmp,afcet$colmass[rcolet])
#    afctmp<-cbind(afctmp,afcet$coldist[rcolet])
#    afctmp<-cbind(afctmp,afcet$colinertia[rcolet])
#    afctot<-rbind(afctot,afctmp)
#    write.csv2(afctot,file = "%s")
#    source("%s")
#    """ % (DictAfcUciOut['afc_row'], RscriptsPath['Rgraph'])
#    txt += """
#    PARCEX=%s
#    """ % PARCEX
#    #FIXME
#    txt += """
#    PlotAfc(afcet,filename="%s",toplot=c%s, PARCEX=PARCEX)
#    """ % (DictAfcUciOut['AfcColAct'], "('none','active')")
#    txt += """
#    PlotAfc(afcsup,filename="%s",toplot=c%s, PARCEX=PARCEX)
#    """ % (DictAfcUciOut['AfcColSup'], "('none','passive')")
#    txt += """PlotAfc(afcet,filename="%s", toplot=c%s, PARCEX=PARCEX)
#    """ % (DictAfcUciOut['AfcColEt'], "('none','passive')")
#    txt += """
#    PlotAfc(afcet,filename="%s", toplot=c%s, PARCEX=PARCEX)
#    """ % (DictAfcUciOut['AfcRow'], "('all','none')")
#    f = open(DictAfcUciOut['Rafcuci'], 'w')
#    f.write(txt)
#    f.close()


class PrintSimiScript(PrintRScript):

    def make_script(self):
        self.txtgraph = ''
        self.packages(['igraph', 'proxy', 'Matrix'])
        self.sources([self.analyse.parent.RscriptsPath['simi'], self.analyse.parent.RscriptsPath['Rgraph']])
        txt = ''
        if not self.parametres['keep_coord'] and not (self.parametres['type'] == 'simimatrix' or self.parametres['type'] == 'simiclustermatrix'):
            txt += """
            dm.path <- "%s"
            cn.path <- "%s"
            selected.col <- "%s"
            """ % (ffr(self.pathout['mat01.csv']), ffr(self.pathout['actives.csv']), ffr(self.pathout['selected.csv']))
            if 'word' in self.parametres:
                txt += """
                word <- TRUE
                index <- %i + 1
                """ % self.parametres['word']
            else:
                txt += """
                word <- FALSE
                index <- NULL
                """
            txt += """
            dm <-readMM(dm.path)
            cn <- read.table(cn.path, sep="\t", quote='"', comment.char="")
            colnames(dm) <- cn[,1]
            if (file.exists(selected.col)) {
                sel.col <- read.csv2(selected.col, header = FALSE)
                sel.col <- sel.col[,1] + 1
            } else {
                sel.col <- 1:ncol(dm)
            }
            if (!word) {
                dm <- dm[, sel.col]
            } else {
                forme <- colnames(dm)[index]
                if (!index %in% sel.col) {
                    sel.col <- append(sel.col, index)
                }
                dm <- dm[, sel.col]
                index <- which(colnames(dm) == forme)
            }
            """
        elif not self.parametres['keep_coord'] and (self.parametres['type'] == 'simimatrix' or self.parametres['type'] == 'simiclustermatrix'):
            txt += """
            dm.path <- "%s"
            selected.col <- "%s"
            """ % (ffr(self.pathout['mat01.csv']), ffr(self.pathout['selected.csv']))
            if 'word' in self.parametres:
                txt += """
                word <- TRUE
                index <- %i + 1
                """ % self.parametres['word']
            else:
                txt += """
                word <- FALSE
                """
            txt += """
            dm <-read.csv2(dm.path)
            dm <- as.matrix(dm)
            if (file.exists(selected.col)) {
                sel.col <- read.csv2(selected.col, header = FALSE)
                sel.col <- sel.col[,1] + 1
            } else {
                sel.col <- 1:ncol(dm)
            }
            if (!word) {
                dm <- dm[, sel.col]
            } else {
                forme <- colnames(dm)[index]
                if (!index %in% sel.col) {
                    sel.col <- append(sel.col, index)
                }
                dm <- dm[, sel.col]
                index <- which(colnames(dm) == forme)
            }
            """
        else:
            txt += """
            load("%s")
            """ % ffr(self.pathout['RData.RData'])
        if self.parametres['coeff'] == 0:
            method = 'cooc'
            if not self.parametres['keep_coord']:
                txt += """
                method <- 'cooc'
                mat <- make.a(dm)
                """
        elif self.analyse.indices[self.parametres['coeff']] == 'Jaccard':
            method = 'Jaccard'
            if not self.parametres['keep_coord']:
                txt += """
                method <- 'Jaccard'
                mat <- sparse.jaccard(dm)
                """
        else:
            if not self.parametres['keep_coord']:
                txt += """
                dm <- as.matrix(dm)
                """
        if self.parametres['coeff'] == 1:
            method = 'prcooc'
            txt += """
            method <- 'Russel'
            mat <- simil(dm, method = 'Russel', diag = TRUE, upper = TRUE, by_rows = FALSE)
            """
        elif self.analyse.indices[self.parametres['coeff']] == 'binomial':
            method = 'binomial'
            if not self.parametres['keep_coord']:
                txt += """
                method <- 'binomial'
                mat <- binom.sim(dm)
                """
        elif self.parametres['coeff'] != 0 and self.analyse.indices[self.parametres['coeff']] != 'Jaccard':
            method = self.analyse.indices[self.parametres['coeff']]
            if not self.parametres['keep_coord']:
                txt += """
                method <-"%s"
                mat <- simil(dm, method = method, diag = TRUE, upper = TRUE, by_rows = FALSE)
                """ % self.analyse.indices[self.parametres['coeff']]
        if not self.parametres['keep_coord']:
            txt += """
            mat <- as.matrix(stats::as.dist(mat,diag=TRUE,upper=TRUE))
            mat[is.na(mat)] <- 0
            if (length(which(mat == Inf))) {
                infp <- which(mat == Inf)
                mat[infp] <- NA
                maxmat <- max(mat, na.rm = TRUE)
                if (maxmat > 0) {
                maxmat <- maxmat + 1
                } else {
                    maxmat <- 0
                }
                mat[infp] <- maxmat
            }
            if (length(which(mat == -Inf))) {
                infm <- which(mat == -Inf)
                mat[infm] <- NA
                minmat <- min(mat, na.rm = TRUE)
                if (maxmat < 0) {
                minmat <- minmat - 1
                } else {
                    minmat <- 0
                }
                mat[infm] <- minmat
            }
            """
        if 'word' in self.parametres and not self.parametres['keep_coord']:
            txt += """
            mat <- graph.word(mat, index)
            cs <- colSums(mat)
            if (length(which(cs==0))) mat <- mat[,-which(cs==0)]
            rs <- rowSums(mat)
            if (length(which(rs==0))) mat <- mat[-which(rs==0),]
            if (length(which(cs==0))) dm <- dm[,-which(cs==0)]
            if (word) {
                index <- which(colnames(mat)==forme)
            }
            """
        if self.parametres['layout'] == 0:
            layout = 'random'
        if self.parametres['layout'] == 1:
            layout = 'circle'
        if self.parametres['layout'] == 2:
            layout = 'frutch'
        if self.parametres['layout'] == 3:
            layout = 'kawa'
        if self.parametres['layout'] == 4:
            layout = 'graphopt'
        if self.parametres['layout'] == 5:
            layout = 'spirale'
        if self.parametres['layout'] == 6:
            layout = 'spirale3D'
        self.filename=''
        if self.parametres['type_graph'] == 0:
            type = 'tkplot'
        if self.parametres['type_graph'] == 1: 
            graphnb = 1
            type = 'nplot'
            dirout = os.path.dirname(self.pathout['mat01.csv'])
            while os.path.exists(os.path.join(dirout,'graph_simi_'+str(graphnb)+'.png')):
                graphnb +=1
            self.filename = ffr(os.path.join(dirout,'graph_simi_'+str(graphnb)+'.png'))
        if self.parametres['type_graph'] == 2:
            type = 'rgl'
        if self.parametres['type_graph'] == 3:
            graphnb = 1
            type = 'web'
            dirout = os.path.dirname(self.pathout['mat01.csv'])
            while os.path.exists(os.path.join(dirout,'web_'+str(graphnb))):
                graphnb +=1
            self.filename = ffr(os.path.join(dirout,'web_'+str(graphnb)))
            os.mkdir(self.filename)
            self.filename = os.path.join(self.filename, 'gexf.gexf')
        if self.parametres['type_graph'] == 4: 
            graphnb = 1
            type = 'rglweb'
            dirout = os.path.dirname(self.pathout['mat01.csv'])
            while os.path.exists(os.path.join(dirout,'webrgl_'+str(graphnb))):
                graphnb +=1
            self.filename = ffr(os.path.join(dirout,'webrgl_'+str(graphnb)))
            os.mkdir(self.filename)
        if self.parametres['arbremax']: 
            arbremax = 'TRUE'
            self.txtgraph += ' - arbre maximum'
        else:
            arbremax = 'FALSE'

        if self.parametres['coeff_tv']: 
            coeff_tv = self.parametres['coeff_tv_nb']
            tvminmax = 'c(NULL,NULL)'
        elif not self.parametres['coeff_tv'] or self.parametres.get('sformchi', False):
            coeff_tv = 'NULL'
            tvminmax = 'c(%i, %i)' %(self.parametres['tvmin'], self.parametres['tvmax'])
        if self.parametres['coeff_te']:
            coeff_te = 'c(%i,%i)' % (self.parametres['coeff_temin'], self.parametres['coeff_temax'])
        else:
            coeff_te = 'NULL'
        if self.parametres['vcex'] or self.parametres.get('cexfromchi', False):
            vcexminmax = 'c(%i/10,%i/10)' % (self.parametres['vcexmin'],self.parametres['vcexmax'])
        else:
            vcexminmax = 'c(NULL,NULL)'
        if not self.parametres['label_v']:
            label_v = 'FALSE'
        else:
            label_v = 'TRUE'
        if not self.parametres['label_e']:
            label_e = 'FALSE'
        else:
            label_e = 'TRUE'
        if self.parametres['seuil_ok']:
            seuil = str(self.parametres['seuil'])
        else:
            seuil = 'NULL'
        if not self.parametres.get('edgecurved', False):
            ec = 'FALSE'
        else:
            ec = 'TRUE'
        txt += """
        edge.curved <- %s
        """ % ec
        cols = str(self.parametres['cols']).replace(')',', max=255)')
        cola = str(self.parametres['cola']).replace(')',',max=255)')
        txt += """
        minmaxeff <- %s
        """ % tvminmax
        txt += """
        vcexminmax <- %s
        """ % vcexminmax
        txt += """
        cex = %i/10
        """ % self.parametres['cex']
        if self.parametres['film']: 
            txt += """
            film <- "%s"
            """ % ffr(self.pathout['film'])
        else: 
            txt += """
            film <- NULL
            """
        txt += """
        seuil <- %s
        if (!is.null(seuil)) {
            if (method!='cooc') {
                seuil <- seuil/1000
            } 
        }
        """ % seuil
        txt += """
        label.v <- %s
        label.e <- %s
        """ % (label_v, label_e)
        txt += """
        cols <- rgb%s
        cola <- rgb%s
        """ % (cols, cola)
        txt += """
        width <- %i
        height <- %i
        """ % (self.parametres['width'], self.parametres['height'])
        if self.parametres['keep_coord']:
            txt += """
            coords <- try(coords, TRUE)
            if (!is.matrix(coords)) {
                coords<-NULL
            }
            """
        else:
            txt += """
            coords <- NULL
            """
        txt += """
        alpha <- %i/100
        """ % self.parametres['alpha']
        txt += """
        alpha <- %i/100
        """ % self.parametres['alpha']
        ######### ??? ##########
        if  self.parametres.get('bystar',False):
            txt += """
            et <- list()
            """
            for i, line in enumerate(self.parametres['listet']):
                txt+= """
                et[[%i]] <- c(%s)
                """ % (i+1, ','.join([repr(val + 1) for val in line]))
            txt+= """
            unetoile <- c('%s')
            """ % ("','".join([val for val in self.parametres['selectedstars']]))
            txt += """
            fsum <- NULL
            rs <- rowSums(dm)
            for (i in 1:length(unetoile)) {
                print(unetoile[i])
                tosum <- et[[i]]
                if (length(tosum) > 1) {
                    fsum <- cbind(fsum, colSums(dm[tosum,]))
                } else {
                    fsum <- cbind(fsum, dm[tosum,])
                }
            }
            source("%s")
            lex <- AsLexico2(fsum, chip=TRUE)
            dcol <- apply(lex[[4]],1,which.max)
            toblack <- apply(lex[[4]],1,max)
            gcol <- rainbow(length(unetoile))
            #gcol[2] <- 'orange'
            vertex.label.color <- gcol[dcol]
            vertex.label.color[which(toblack <= 3.84)] <- 'black'
            leg <- list(unetoile=unetoile, gcol=gcol)  
            cols <- vertex.label.color
            chivertex.size <- norm.vec(toblack, vcexminmax[1],  vcexminmax[2])
            
            """ % (ffr(self.analyse.parent.RscriptsPath['chdfunct']))
        else:
            txt += """
            vertex.label.color <- 'black' 
            chivertex.size <- 1
            leg<-NULL
            """
        ######### ??? ##########
#        txt += """
#        eff <- colSums(dm)
#        g.ori <- graph.adjacency(mat, mode='lower', weighted = TRUE)
#        w.ori <- E(g.ori)$weight
#        if (max.tree) {
#            if (method == 'cooc') {
#                E(g.ori)$weight <- 1 / w.ori
#            } else {
#                E(g.ori)$weigth <- 1 - w.ori
#            }
#            g.max <- minimum.spanning.tree(g.ori)
#            if (method == 'cooc') {
#                E(g.max)$weight <- 1 / E(g.max)$weight
#            } else {
#                E(g.max)$weight <- 1 - E(g.max)$weight
#            }
#            g.toplot <- g.max
#        } else {
#            g.toplot <- g.ori
#        }
#        """
        if self.parametres['com']:
            com = repr(self.parametres['communities'])
        else:
            com = 'NULL'
        if self.parametres['halo']:
            halo = 'TRUE'
        else:
            halo = 'FALSE'
        txt += """
        communities <- %s
        halo <- %s
        """ % (com, halo)
        txt += """
        eff <- colSums(dm)
        x <- list(mat = mat, eff = eff)
        graph.simi <- do.simi(x, method='%s', seuil = seuil, p.type = '%s', layout.type = '%s', max.tree = %s, coeff.vertex=%s, coeff.edge = %s, minmaxeff = minmaxeff, vcexminmax = vcexminmax, cex = cex, coords = coords, communities = communities, halo = halo, index.word=index)
        """ % (method, type, layout, arbremax, coeff_tv, coeff_te)
        if self.parametres.get('bystar',False):
            if self.parametres.get('cexfromchi', False):
                txt+="""
                    label.cex<-chivertex.size
                    """
            else:
                txt+="""
                label.cex <- cex
                """
            if self.parametres.get('sfromchi', False):
                txt += """
                vertex.size <- norm.vec(toblack, minmaxeff[1], minmaxeff[2])
                """
            else:
                txt += """
                vertex.size <- NULL
                """
        else:
            #print self.parametres
            if (self.parametres['type'] == 'clustersimitxt' and self.parametres.get('tmpchi', False)) or (self.parametres['type'] in ['simimatrix','simiclustermatrix'] and 'tmpchi' in self.parametres): 
                txt += """
                lchi <- read.table("%s")
                lchi <- lchi[,1]
                """ % ffr(self.parametres['tmpchi'])
                txt += """
                    lchi <- lchi[sel.col]
                    """
            if self.parametres['type'] in ['clustersimitxt', 'simimatrix', 'simiclustermatrix'] and self.parametres.get('cexfromchi', False):
                txt += """ 
                label.cex <- norm.vec(lchi, vcexminmax[1], vcexminmax[2])
                """
            else:
                txt += """
            if (is.null(vcexminmax[1])) {
                label.cex <- cex
            } else {
                label.cex <- graph.simi$label.cex
            }
            """
            if (self.parametres['type'] in ['clustersimitxt', 'simimatrix', 'simiclustermatrix']) and self.parametres.get('sfromchi', False):
                txt += """ 
                vertex.size <- norm.vec(lchi, minmaxeff[1], minmaxeff[2])
                if (!length(vertex.size)) vertex.size <- 0
                """
            else:
                txt += """
            if (is.null(minmaxeff[1])) {
                vertex.size <- 0
            } else {
                vertex.size <- graph.simi$eff
            }
            """
        #txt += """ vertex.size <- NULL """
        if self.parametres['svg']:
            svg = 'TRUE'
        else:
            svg = 'FALSE'
        txt += """
        svg <- %s
        """ % svg
        txt += """
        vertex.col <- cols
        col.from.proto <- F
        if (col.from.proto) {
            proto.col <- read.table('/tmp/matcol.csv')
            v.proto.names <- make.names(proto.col[,1])
            v.proto.col <- as.character(proto.col[,2])
            v.proto.col[which(v.proto.col=='black')] <- 'yellow'
            v.names <- V(graph.simi$graph)$name
            num.color <- sapply(v.names, function(x) {if (x %%in%% v.proto.names) {v.proto.col[which(v.proto.names==x)]} else {'pink'}})
            vertex.col <- num.color
            V(graph.simi$graph)$proto.color <- vertex.col
        }
        if (!is.null(graph.simi$com)) {
            com <- graph.simi$com
            colm <- rainbow(length(com))
            if (sum(vertex.size) != 0 || graph.simi$halo) {
                vertex.label.color <- 'black'
                vertex.col <- colm[membership(com)]
            } else {
                vertex.label.color <- colm[membership(com)]
            }
        }
        if (!length(graph.simi$elim)==0) {
            vertex.label.color <- vertex.label.color[-graph.simi$elim]
            if (length(label.cex > 1)) {
                 label.cex <- label.cex[-graph.simi$elim]
            }
        }
        coords <- plot.simi(graph.simi, p.type='%s',filename="%s", vertex.label = label.v, edge.label = label.e, vertex.col = vertex.col, vertex.label.color = vertex.label.color, vertex.label.cex=label.cex, vertex.size = vertex.size, edge.col = cola, leg=leg, width = width, height = height, alpha = alpha, movie = film, edge.curved = edge.curved, svg = svg)
        save.image(file="%s")
        """ % (type, self.filename, ffr(self.pathout['RData']))
        self.add(txt)
        self.write()


class WordCloudRScript(PrintRScript):

    def make_script(self):
        self.sources([self.analyse.parent.RscriptsPath['Rgraph']])
        self.packages(['wordcloud'])
        bg_col = Rcolor(self.parametres['col_bg'])
        txt_col = Rcolor(self.parametres['col_text'])
        if self.parametres['svg']:
            svg = 'TRUE'
        else:
            svg = 'FALSE'
        txt = """
        svg <- %s
        """ % svg
        txt += """
        act <- read.csv2("%s", header = FALSE, row.names=1, sep='\t')
        selected.col <- read.table("%s")
        toprint <- as.matrix(act[selected.col[,1] + 1,])
        rownames(toprint) <- rownames(act)[selected.col[,1] + 1]
        maxword <- %i
        if (nrow(toprint) > maxword) {
            toprint <- as.matrix(toprint[order(toprint[,1], decreasing=TRUE),])
            toprint <- as.matrix(toprint[1:maxword,])
        }
        open_file_graph("%s", width = %i, height = %i , svg = svg)
        par(bg=rgb%s)
        wordcloud(row.names(toprint), toprint[,1], scale=c(%f,%f), random.order=FALSE, colors=rgb%s)
        dev.off()
        """ % (ffr(self.analyse.pathout['actives_eff.csv']), ffr(self.analyse.pathout['selected.csv']), self.parametres['maxword'], ffr(self.parametres['graphout']), self.parametres['width'], self.parametres['height'], bg_col, self.parametres['maxcex'], self.parametres['mincex'], txt_col)
        self.add(txt)
        self.write()


class ProtoScript(PrintRScript):

    def make_script(self):
        self.sources([self.analyse.parent.RscriptsPath['Rgraph'], self.analyse.parent.RscriptsPath['prototypical.R']])
        self.packages(['wordcloud'])
        if self.parametres.get('cloud', False):
            cloud = 'TRUE'
        else:
            cloud = 'FALSE'
        txt = """
        errorn <- function(x) {
            qnorm(0.975)*sd(x)/sqrt(lenght(n))
        }
        errort <- function(x) {
            qt(0.975,df=lenght(x)-1)*sd(x)/sqrt(lenght(x))
        }
        mat <- read.csv2("%s", header = FALSE, row.names=1, sep='\t', quote='"', dec='.')
        open_file_graph("%s",height=800, width=1000)
        prototypical(mat, mfreq = %s, mrank = %s, cloud = FALSE, cexrange=c(1,2.4), cexalpha= c(0.4, 1), type = '%s')#, mat.col.path='/tmp/matcol.csv')
        dev.off()
        """ % (ffr(self.analyse.pathout['table.csv']), ffr(self.analyse.pathout['proto.png']), self.parametres['limfreq'], self.parametres['limrang'], self.parametres['typegraph'])
        self.add(txt)
        self.write()


class ExportAfc(PrintRScript):

    def make_script(self):
        self.source([self.analyse.parent.RscriptsPath['Rgraph']])
        self.packages(['rgexf'])
        txt = """
        """


class MergeGraphes(PrintRScript):

    def __init__(self, analyse):
        self.script = "#Script genere par IRaMuTeQ - %s\n" % datetime.now().ctime()
        self.pathout = PathOut()
        self.parametres = analyse.parametres
        self.scriptout = self.pathout['temp']
        self.analyse = analyse 

    def make_script(self):
        #FIXME
        txt = """
        library(igraph)
        library(Matrix)
        graphs <- list()
        """
        load = """
        load("%s")
        g <- graph.simi$graph
        V(g)$weight <- (graph.simi$mat.eff/nrow(dm))*100
        graphs[['%s']] <- g
        """
        for i, graph in enumerate(self.parametres['graphs']):
            path = os.path.dirname(graph)
            gname = ''.join(['g', repr(i)])
            RData = os.path.join(path,'RData.RData')
            txt += load % (ffr(RData), gname)
        self.add(txt)
        self.sources([self.analyse.parent.RscriptsPath['simi']])
        txt = """
        merge.type <- 'proto'
        if (merge.type == 'normal') {
            ng <- merge.graph(graphs)
        } else {
            ng <- merge.graph.proto(graphs)
        }
        ngraph <- list(graph=ng, layout=layout.fruchterman.reingold(ng, dim=3), labex.cex=V(ng)$weight)
        write.graph(ng, "%s", format = 'graphml')
        """ % ffr(self.parametres['grapheout'])
        self.add(txt)


class TgenSpecScript(PrintRScript):

    def make_script(self):
        self.packages(['textometry'])
        txt = """
        tgen <- read.csv2("%s", row.names = 1, sep = '\\t')
        """ % ffr(self.parametres['tgeneff'])
        txt += """
        tot <- tgen[nrow(tgen), ]
        result <- NULL
        tgen <- tgen[-nrow(tgen),]
        for (i in 1:nrow(tgen)) {
            mat <- rbind(tgen[i,], tot - tgen[i,])
            specmat <- specificities(mat)
            result <- rbind(result, specmat[1,])
        }
        colnames(result) <- colnames(tgen)
        row.names(result) <- rownames(tgen)
        write.table(result, file = "%s", sep='\\t', col.names = NA)
        """ % ffr(self.pathout['tgenspec.csv'])
        self.add(txt)


class TgenProfScript(PrintRScript):

    def make_script(self):
        self.sources([self.analyse.ira.RscriptsPath['chdfunct']])
        txt = """
        tgen <- read.csv2("%s", row.names = 1, sep = '\\t')
        """ % ffr(self.parametres['tgeneff'])
        txt += """
        tgenlem <- read.csv2("%s", row.names = 1, sep = '\\t')
        """ % ffr(self.parametres['tgenlemeff'])
        txt += """
        res <- build.prof.tgen(tgen)
        write.table(res$chi2, file = "%s", sep='\\t', col.names = NA)
        write.table(res$pchi2, file = "%s", sep='\\t', col.names = NA)
        """ % (ffr(self.pathout['tgenchi2.csv']), ffr(self.pathout['tgenpchi2.csv']))
        txt += """
        reslem <- build.prof.tgen(tgenlem)
        write.table(reslem$chi2, file = "%s", sep='\\t', col.names = NA)
        write.table(reslem$pchi2, file = "%s", sep='\\t', col.names = NA)
        """ % (ffr(self.pathout['tgenlemchi2.csv']), ffr(self.pathout['tgenlempchi2.csv']))
        self.add(txt)


class FreqMultiScript(PrintRScript):

    def make_script(self):
        self.sources([self.analyse.parent.RscriptsPath['Rgraph']])
        txt = """
        freq <- read.csv2("%s", row.names=1, sep='\\t', dec='.')
        """ % ffr(self.pathout['frequences.csv'])
        txt += """
        toplot <- freq[order(freq[,2]) ,2]
        toplot.names = rownames(freq)[order(freq[,2])]
        h <- 80 + (20 * nrow(freq))
        open_file_graph("%s",height=h, width=500)
        par(mar=c(3,20,3,3))
        barplot(toplot, names = toplot.names, horiz=TRUE, las =1, col = rainbow(nrow(freq)))
        dev.off()
        """ % ffr(self.pathout['barplotfreq.png'])
        txt += """
        toplot <- freq[order(freq[,4]) ,4]
        toplot.names = rownames(freq)[order(freq[,4])]
        open_file_graph("%s",height=h, width=500)
        par(mar=c(3,20,3,3))
        barplot(toplot, names = toplot.names, horiz=TRUE, las =1, col = rainbow(nrow(freq)))
        dev.off()
        """ % ffr(self.pathout['barplotrow.png'])
        self.add(txt)
        self.write()


class LabbeScript(PrintRScript):

    def make_script(self):
        self.sources([self.analyse.parent.RscriptsPath['distance-labbe.R'],
                      self.analyse.parent.RscriptsPath['Rgraph']])
        txt = """
        tab <- read.csv2("%s", header=TRUE, sep=';', row.names=1)
        """ % (ffr(self.pathout['tableafcm.csv']))
        txt += """
        cs <- colSums(tab)
        if (min(cs) == 0) {
            print('empty columns !!')
            vide <- which(cs==0)
            print(vide)
            tab <- tab[,-vide]
        }
        #print('#### RcppIramuteq for C++ Labbe ####')
        #library(RcppIramuteq)
        #dist.mat <- labbe(as.matrix(tab))
        #rownames(dist.mat) <- colnames(tab)
        dist.mat <- dist.labbe(tab)
        dist.mat <- as.dist(dist.mat, upper=F, diag=F)
        dist2list(dist.mat, "%s")
        write.csv2(as.matrix(dist.mat), "%s")
        library(cluster)
        library(ape)
        chd <- hclust(dist.mat, method="ward.D2")
        open_file_graph("%s", width=1000, height=1000, svg=F)
        par(cex=1.2)
        plot.phylo(as.phylo(chd), type='unrooted', lab4ut="axial")
        dev.off()
        """ % (ffr(self.pathout['listdist.csv']), ffr(self.pathout['distmat.csv']), ffr(self.pathout['labbe-tree.png']))
        txt +="""
        open_file_graph("%s", width=1000, height=1000, svg=F)
        par(mar=c(10,1,1,10))
        heatmap(as.matrix(dist.mat), symm = T, distfun=function(x) as.dist(x), margins=c(10,10))
        dev.off()
        """ % ffr(self.pathout['labbe-heatmap.png'])
        txt += """
        #http://stackoverflow.com/questions/3081066/what-techniques-exists-in-r-to-visualize-a-distance-matrix
        dst <- data.matrix(dist.mat)
        dim <- ncol(dst)
        rn <- row.names(as.matrix(dist.mat))
        open_file_graph("%s", width=1500, height=1000, svg=F)
        par(mar=c(10,10,3,3))
        image(1:dim, 1:dim, dst, axes = FALSE, xlab="", ylab="", col=heat.colors(99), breaks=seq(0.01,1,0.01))
        axis(1, 1:dim, rn, cex.axis = 0.9, las=3)
        axis(2, 1:dim, rn, cex.axis = 0.9, las=1)
        text(expand.grid(1:dim, 1:dim), sprintf("%%0.2f", dst), cex=0.6)
        dev.off()
        """  % ffr(self.pathout['labbe-matrix.png'])
        txt += """
        library(igraph)
        g <- graph.adjacency(as.matrix(1-dist.mat), mode="lower", weighted=T)
        write.graph(g, file="%s", format='graphml')
        open_file_graph("%s", width=1000, height=1000, svg=F)
        plot(g)
        dev.off()
        E(g)$weight <- 1 - E(g)$weight
        g <- minimum.spanning.tree(g)
        E(g)$weight <- 1 - E(g)$weight
        write.graph(g, file="%s", format='graphml')
        open_file_graph("%s", width=1000, height=1000, svg=F)
        plot(g)
        dev.off()
        """ % (ffr(self.pathout['graph_tot.graphml']), ffr(self.pathout['graph_tot.png']), ffr(self.pathout['graph_min.graphml']), ffr(self.pathout['graph_min.png']))
        self.add(txt)
        self.write()


class ChronoChi2Script(PrintRScript):

    def make_script(self):
        self.sources([self.analyse.parent.RscriptsPath['Rgraph']])
        print(self.parametres)
        txt = """
        inRData <- "%s"
        dendrof <- "%s"
        load(inRData)
        load(dendrof)
        """ % (ffr(self.pathout['RData.RData']), ffr(self.pathout['dendrogramme.RData']))
        txt += """
        svg <- %s
        """ % self.parametres['svg']
        txt += """
        tc <- which(grepl("%s",rownames(chistabletot)))
        rn <- rownames(chistabletot)[tc]
        tc <- tc[order(rn)]
        dpt <- chistabletot[tc,]
        tot <- afctable[tc,]
        tcp <- rowSums(tot)
        ptc <- tcp/sum(tcp)
        dpt <- t(dpt)
        dd <- dpt
        """ % self.parametres['var'].replace('*', "\\\\*")
        txt += """
        classes <- n1[,ncol(n1)]
        tcl <- table(classes)
        if ('0' %in% names(tcl)) {
            to.vire <- which(names(tcl) == '0')
            tcl <- tcl[-to.vire]
        }
        tclp <- tcl/sum(tcl)
        #chi2 colors
        library(ape)
        k <- 1e-02
        lcol <- NULL
        lk <- k
        for (i in 1:5) {
            lcol <- c(lcol, qchisq(1-k,1))
            k <- k/10
            lk <- c(lk,k)
        }
        lcol <- c(3.84, lcol)
        lcol <- c(-Inf,lcol)
        lcol <- c(lcol, Inf)
        lk <- c(0.05,lk)
        breaks <- lcol
        alphas <- seq(0,1, length.out=length(breaks))
        clod <- rev(as.numeric(tree.cut1$tree.cl$tip.label))
        #end
        """
        txt += """
        open_file_graph("%s", w=%i, h=%i, svg=svg)
        """ % (ffr(self.parametres['tmpgraph']), self.parametres['width'], self.parametres['height'])
        txt += """
        par(mar=c(3,3,3,3))
        mat.graphic <- matrix(c(rep(1,nrow(dd)),c(2:(nrow(dd)+1))), ncol=2)
        mat.graphic <- rbind(mat.graphic, c(max(mat.graphic) + 1 , max(mat.graphic) + 2))
        hauteur <- tclp[clod] * 0.9
        heights.graphic <- append(hauteur, 0.1)
        layout(mat.graphic, heights=heights.graphic, widths=c(0.15,0.85))
        par(mar=c(0,0,0,0))
        tree.toplot <- tree.cut1$tree.cl
        num.label <- as.numeric(tree.cut1$tree.cl$tip.label)
        col.tree <- rainbow(length(num.label))[num.label]
        #tree.toplot$tip.label <- paste('classe ', tree.toplot$tip.label)
        plot.phylo(tree.toplot,label.offset=0.1, cex=1.1, no.margin=T, tip.color = col.tree)
        for (i in clod) {
            print(i)
            par(mar=c(0,0,0,0))
            lcol <- cut(dd[i,], breaks, include.lowest=TRUE)
            ulcol <- names(table(lcol))
            lcol <- as.character(lcol)
            for (j in 1:length(ulcol)) {
                lcol[which(lcol==ulcol[j])] <- j
            }
            lcol <- as.numeric(lcol)
            mcol <- rainbow(nrow(dd))[i]
            last.col <- NULL
            for (k in alphas) {
                last.col <- c(last.col, rgb(r=col2rgb(mcol)[1]/255, g=col2rgb(mcol)[2]/255, b=col2rgb(mcol)[3]/255, a=k))
            }
            #print(last.col)
            barplot(rep(1,ncol(dd)), width=ptc, names.arg=FALSE, axes=FALSE, col=last.col[lcol], border=rgb(r=0, g=0, b=0, a=0.3))
        }
        plot(0,type='n',axes=FALSE,ann=FALSE)
        label.coords <- barplot(rep(1, ncol(dd)), width=ptc, names.arg = F, las=2, axes=F, ylim=c(0,1), plot=T, col='white')
        text(x=label.coords, y=0.5, labels=rn[order(rn)], srt=90)
        dev.off()
        """
        self.add(txt)
        self.write()


class ChronoPropScript(PrintRScript):

    def make_script(self):
        self.sources([self.analyse.parent.RscriptsPath['Rgraph']])
        print(self.parametres)
        txt = """
        inRData <- "%s"
        dendrof <- "%s"
        load(inRData)
        load(dendrof)
        """ % (ffr(self.pathout['RData.RData']), ffr(self.pathout['dendrogramme.RData']))
        txt += """
        svg <- %s
        """ % self.parametres['svg']
        txt += """
        tc <- which(grepl("%s",rownames(chistabletot)))
        rn <- rownames(chistabletot)[tc]
        tc <- tc[order(rn)]
        dpt <- chistabletot[tc,]
        tot <- afctable[tc,]
        tcp <- rowSums(tot)
        ptc <- tcp/sum(tcp)
        dpt <- t(dpt)
        dd <- dpt
        """ % self.parametres['var'].replace('*', "\\\\*")
        txt += """
        classes <- n1[,ncol(n1)]
        tcl <- table(classes)
        if ('0' %in% names(tcl)) {
            to.vire <- which(names(tcl) == '0')
            tcl <- tcl[-to.vire]
        }
        tclp <- tcl/sum(tcl)
        """
        txt += """
        open_file_graph("%s", w=%i, h=%i, svg=svg)
        """ % (ffr(self.parametres['tmpgraph']), self.parametres['width'], self.parametres['height'])
        txt+= """
        ptt <- prop.table(as.matrix(tot), 1)
        par(mar=c(10,2,2,2))
        barplot(t(ptt)[as.numeric(tree.cut1$tree.cl$tip.label),], col=rainbow(ncol(ptt))[as.numeric(tree.cut1$tree.cl$tip.label)], width=ptc, las=3, space=0.05, cex.axis=0.7, border=NA)
        dev.off()
        """
        self.add(txt)
        self.write()


class ChronoggScript(PrintRScript):

    def make_script(self):
        self.sources([self.analyse.parent.RscriptsPath['Rgraph']])
        print(self.parametres)
        txt = """
        library(ggplot2)
        inRData <- "%s"
        dendrof <- "%s"
        load(inRData)
        load(dendrof)
        """ % (ffr(self.pathout['RData.RData']), ffr(self.pathout['dendrogramme.RData']))
        txt += """
        svg <- %s
        """ % self.parametres['svg']
        txt += """
        tc <- which(grepl("%s",rownames(chistabletot)))
        rn <- rownames(chistabletot)[tc]
        tc <- tc[order(rn)]
        dpt <- chistabletot[tc,]
        tot <- afctable[tc,]
        tcp <- rowSums(tot)
        ptc <- tcp/sum(tcp)
        dpt <- t(dpt)
        dd <- dpt
        """ % self.parametres['var'].replace('*', "\\\\*")
        txt += """
        classes <- n1[,ncol(n1)]
        tcl <- table(classes)
        if ('0' %in% names(tcl)) {
            to.vire <- which(names(tcl) == '0')
            tcl <- tcl[-to.vire]
        }
        tclp <- tcl/sum(tcl)
        ptt <- prop.table(as.matrix(tot), 1)
        ptt <- ptt[,as.numeric(tree.cut1$tree.cl$tip.label)]
        rownames(ptt) <- cumsum(ptc)
        nptt<-as.data.frame(as.table(ptt))
        nptt[,1]<-as.numeric(as.character(nptt[,1]))
        col <- rainbow(ncol(ptt))[as.numeric(tree.cut1$tree.cl$tip.label)]
        """
        txt += """
        open_file_graph("%s", w=%i, h=%i, svg=svg)
        """ % (ffr(self.parametres['tmpgraph']), self.parametres['width'], self.parametres['height'])
        txt+= """
        par(mar=c(10,2,2,2))
        gg <- ggplot(data=nptt, aes(x=Var1,y=Freq,fill=Var2)) + geom_area(alpha=1 , size=0.5, colour="black")
        gg + scale_fill_manual(values=col)
        dev.off()
        """
        self.add(txt)
        self.write()


class DendroScript(PrintRScript):

    def make_script(self):
        if self.parametres['svg']:
            typefile = '.svg'
        else:
            typefile = '.png'
        fileout = self.parametres['fileout']
        width = self.parametres['width']
        height = self.parametres['height']
        type_dendro = self.parametres['dendro_type']
        if self.parametres['taille_classe']:
            tclasse = 'TRUE'
        else:
            tclasse = 'FALSE'
        if self.parametres['color_nb'] == 0:
            bw = 'FALSE'
        else:
            bw = 'TRUE'
        if self.parametres['type_tclasse'] == 0:
            histo='FALSE'
        else:
            histo = 'TRUE'
        if self.parametres['svg']:
            svg = 'TRUE'
        else:
            svg = 'FALSE'
        dendro_path = self.pathout['Rdendro']
        classe_path = self.pathout['uce']
        txt = """
        library(ape)
        load("%s")
        source("%s")
        classes <- read.csv2("%s", row.names=1)
        classes <- classes[,1]
        """ % (ffr(dendro_path), ffr(self.parametres['Rgraph']),  ffr(classe_path))
        if self.parametres['dendro'] == 'simple':
            txt += """
            open_file_graph("%s", width=%i, height=%i, svg=%s)
            plot.dendropr(tree.cut1$tree.cl, classes, type.dendro="%s", histo=%s, bw=%s, lab=NULL, tclasse=%s)
            """ % (ffr(fileout), width, height, svg, type_dendro, histo, bw, tclasse)
        elif self.parametres['dendro'] == 'texte':
            txt += """
            load("%s")
            source("%s")
            if (is.null(debsup)) {
                debsup <- debet
            }
            chistable <- chistabletot[1:(debsup-1),]
            """ % (ffr(self.pathout['RData.RData']), ffr(self.parametres['Rgraph']))
            if self.parametres.get('translation', False):
                txt += """
                rn <- read.csv2("%s", header=FALSE, sep='\t')
                rnchis <- row.names(chistable)
                commun <- intersect(rnchis, unique(rn[,2]))
                idrnchis <- sapply(commun, function(x) {which(rnchis==x)})
                idrn <- sapply(commun, function(x) {which(as.vector(rn[,2])==x)[1]})
                rownames(chistable)[idrnchis] <- as.vector(rn[idrn,1])
                """ % ffr(self.parametres['translation'])
            txt += """
            open_file_graph("%s", width=%i, height=%i, svg = %s)
            plot.dendro.prof(tree.cut1$tree.cl, classes, chistable, nbbycl = 60, type.dendro="%s", bw=%s, lab=NULL)
            """ % (ffr(fileout), width, height, svg, type_dendro, bw)
        elif self.parametres['dendro'] == 'cloud':
            txt += """
            load("%s")
            source("%s")
            if (is.null(debsup)) {
                debsup <- debet
            }
            chistable <- chistabletot[1:(debsup-1),]
            open_file_graph("%s", width=%i, height=%i, svg=%s)
            plot.dendro.cloud(tree.cut1$tree.cl, classes, chistable, nbbycl = 300, type.dendro="%s", bw=%s, lab=NULL)
            """ % (ffr(self.pathout['RData.RData']), ffr(self.parametres['Rgraph']), ffr(fileout), width, height, svg, type_dendro, bw)
        self.add(txt)
        self.write()


class ReDoProfScript(PrintRScript):

    def make_script(self):
        self.sources([self.analyse.parent.RscriptsPath['chdfunct.R']])
        print(self.parametres)
