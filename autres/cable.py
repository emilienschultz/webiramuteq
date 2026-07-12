# -*- coding: utf-8 -*-
#Author: Pierre Ratinaud
#Copyright (c) 2008-2020 Pierre Ratinaud
#Lisense: GNU/GPL
# usage ?
# encodage est utilisé - mais utf-8 est par défaut dans PY3

#------------------------------------
# import des modules python
#------------------------------------
import codecs


filein = '/home/pierre/fac/cablegate/allcables-all.txt'
enc = 'utf-8'

infile = codecs.open(filein, 'r', enc)
content = []

class BigCorpus :
    def __init__(self, parent) :
        self.parent = parent
        self.parametre = {'syscoding': sys.getdefaultencoding()}
        self.content = None
        self.ucis = None
        self.formes = {}
        self.lems = {}
        self.ucenb = None
        self.etoiles = None
        self.etintxt = {}
        self.ucis_paras_uces = None
        self.lc = None
        self.lc0 = None
        self.actives = None
        self.supp = None
        #self.supplementaires = []
        self.lenuc1 = None
        self.lenuc2 = None
        self.lexique = None
    
    def open_corpus(self) :
        return codecs.open(self.parametre['filename'], "r", self.parametre['encodage'])
    
    def buildcorpus(self) :
        i = 0
        ucifile = os.path.join(os.path.basedir(self.parametre['filename']), 'ucis.txt')
        uci = open(ucifile, 'w')
        ucinb = 0
        for line in self.open_corpus() :
            if line.startswith(u'****') and i==0 :
                uci.write(line)
                i += 1
            elif line.startswith(u'****') and i=!0 :
                uci.write(line)
                parse_uci()

                write_uci()
                uci[ucinb] = i
                ucinb += 1
                i += 1
            else :
                addlinetouci(uci, prepare(line))
                line = line.lower().replace(u'\'','\' ').replace(u'’','\' ').replace('...',u' £ ').replace('?',' ? ').replace('.',' . ').replace('!', ' ! ').replace(',',' , ').replace(';', ' ; ').replace(':', ' : ').strip()
                line = line.replace('\n', ' ').replace('\r', ' ')
                line = line.split()
                content[-1].append(line)
            i += 1
print len(content)
