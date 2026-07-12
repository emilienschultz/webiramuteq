#!/bin/env python
# -*- coding: utf-8 -*-
#Author: Pierre Ratinaud
#Copyright (c) 2008-2020 Pierre Ratinaud
#Lisense: GNU/GPL

import os
from optparse import OptionParser
import sys
reload(sys)
import locale
import codecs
sys.setdefaultencoding(locale.getpreferredencoding())
from chemins import ConstructConfigPath, ConstructDicoPath, ConstructRscriptsPath, ChdTxtPathOut
from functions import ReadLexique
from ConfigParser import *
#######################################
from textchdalc import AnalyseAlceste
from textdist import PamTxt
#from textafcuci import AfcUci
from textstat import Stat
from corpus import Corpus
import tempfile
import pickle
from word_stat import *
from textclassechd import ClasseCHD

AppliPath = os.path.abspath(os.path.dirname(os.path.realpath(sys.argv[0])))
if os.getenv('HOME') != None:
    user_home = os.getenv('HOME')
else:
    user_home = os.getenv('HOMEPATH')
UserConfigPath = os.path.abspath(os.path.join(user_home, '.iramuteq'))

class CmdLine :
    def __init__(self) :
        self.DictPath = ConstructDicoPath(AppliPath)
        self.ConfigPath = ConstructConfigPath(UserConfigPath)
      
        parser = OptionParser()
    
        parser.add_option("-f", "--file", dest="filename", help="chemin du corpus", metavar="FILE", default=False)
        parser.add_option("-t", "--type", dest="type_analyse", help="type d'analyse", metavar="TYPE D'ANALYSE", default='alceste')

        parser.add_option("-c", "--conf", dest="configfile", help="chemin du fichier de configuration", metavar="CONF", default=False)
        parser.add_option("-e", "--enc", dest="encodage", help="encodage du corpus", metavar="ENC", default=locale.getpreferredencoding())
        parser.add_option("-l", "--lang", dest="language", help="langue du corpus", metavar="LANG", default='french')
        (options, args) = parser.parse_args()
        print args
        print options
        if options.filename :
            self.filename = os.path.abspath(options.filename)
            self.conf = RawConfigParser()
            self.conf.read(self.filename)
            print self.conf.sections()

            if 'analyse' in self.conf.sections() :
                print 'zerzerz'
                DictPathOut=ChdTxtPathOut(os.path.dirname(self.filename))
                self.pathout = os.path.dirname(self.filename)
                self.DictPathOut=DictPathOut
                self.corpus = Corpus(self)
                self.corpus.dictpathout = self.DictPathOut
                self.corpus.read_corpus_from_shelves(self.DictPathOut['db'])
                self.corpus.parametre['analyse'] = 'alceste'
                self.corpus.make_lem_type_list()
                for i in range(1,18) :
                    ClasseCHD(self, self.corpus, i, True)
                zerzerzer
                #ll = self.corpus.find_segments_doublon(15,1000000)
                #with open('extrait_doublons.csv' ,'w') as f :
                #    f.write('\n'.join([';'.join([`v[0]`,v[1]]) for v in ll]))
                #print ll
                #self.corpus.count_uci_from_list('/home/pierre/fac/lerass/bouquin_indentite/liste_mot_chercher_uci.txt')
                #print 'start pickle'
                #output = open('testpickle.pkl', 'r')
                #pickle.dump(self.corpus.formes, output, -1)
                #formes = pickle.load(output)
                #output.close()
                #print 'finish pickle'
                #sdfsdfs
                #listin = '/home/pierre/fac/identite/Personnages.csv'
                #with codecs.open(listin, 'r', 'cp1252') as f :
                #    content = f.read()
                #content = content.replace('"','').splitlines()
                #print content
                #self.corpus.make_and_write_sparse_matrix_from_uce_list(content, '/home/pierre/fac/identite/personnages.mm')
                #print 'zerzer'
    #            print 'EXTRACT NR'
    #            self.corpus.extractnr()
                #listin = [u'droit', u'devoir']
                #make_word_stat(self.corpus, listin)
                Alceste=True
            fsdfsdfd
            self.filename = os.path.abspath(options.filename)
            self.corpus_encodage = options.encodage
            self.corpus_lang = options.language
            if options.configfile :
                self.ConfigPath[options.type_analyse] = os.path.abspath(options.configfile)
            self.TEMPDIR = tempfile.mkdtemp('iramuteq') 
            self.RscriptsPath = ConstructRscriptsPath(AppliPath)
            self.PathPath = ConfigParser()
            self.PathPath.read(self.ConfigPath['path'])        
            self.RPath = self.PathPath.get('PATHS', 'rpath')
            self.pref = RawConfigParser()
            self.pref.read(self.ConfigPath['preferences'])
            #print 'PAS DE CODECS POUR CABLE'
            with codecs.open(self.filename, 'r', self.corpus_encodage) as f:
                self.content = f.read()
            self.content = self.content.replace('\r','')
            ReadLexique(self, lang = options.language)
            if options.type_analyse == 'alceste' :
            #    print 'ATTENTION : BIGGGGGGGGGGGGGGGGGGG'
            #    self.Text = AnalyseAlceste(self, cmd = True, big = True)
                self.Text = AnalyseAlceste(self, cmd = True)
            elif options.type_analyse == 'pam' :
                self.Text = PamTxt(self, cmd = True)
            elif options.type_analyse == 'afcuci' :
                self.Text = AfcUci(self, cmd = True)
            elif options.type_analyse == 'stat' :
                self.Text = Stat(self, cmd = True)
            #print self.Text.corpus.hours, 'h', self.Text.corpus.minutes,'min', self.Text.corpus.seconds, 's'
#            self.Text.corpus.make_colored_corpus('colored.html')

if __name__ == '__main__':
    __name__ = 'Main'
    CmdLine()

