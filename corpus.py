# -*- coding: utf-8 -*-
#Author: Pierre Ratinaud
#Copyright (c) 2008-2020 Pierre Ratinaud
#modification pour python 3 : Laurent Mérat, 6x7 - mai 2020
#License: GNU/GPL

#------------------------------------
# import des modules python
#------------------------------------
import codecs
import os
import locale
import sys
from time import time
import re
import sqlite3
import itertools
import logging
from operator import itemgetter
from uuid import uuid4
import datetime
from copy import copy
#------test spacy------------
#import spacy
#nlp = spacy.load("fr_core_news_lg")

#------------------------------------
# import des fichiers du projet
#------------------------------------
from functions import decoupercharact, ReadDicoAsDico, DoConf, ReadLexique, progressbar
from chemins import PathOut
from dialog import CorpusPref, SubTextFromMetaDial, MergeClusterFrame
from colors import colors

import langue
langue.run()


log = logging.getLogger('iramuteq.corpus')


def copycorpus(corpus) :
    log.info('copy corpus')
    copy_corpus = Corpus(corpus.parent, parametres = corpus.parametres)
    copy_corpus.ucis = corpus.ucis
    copy_corpus.formes = corpus.formes
    copy_corpus.pathout = corpus.pathout
    copy_corpus.conn_all()
    return copy_corpus

def CopyUce(uce) :
    return Uce(uce.ident, uce.para, uce.uci)

def CopyUci(uci):
    nuci = Uci(uci.ident, '')
    nuci.etoiles = copy(uci.etoiles)
    nuci.uces = [CopyUce(uce) for uce in uci.uces]
    nuci.paras = copy(uci.paras)
    return nuci


class Corpus :

    """Corpus class
    list of text
    """
    def __init__(self, parent, parametres = {}, read = False) :
        self.parent = parent
        self.parametres = parametres
        self.cformes = None
        self.connformes = None
        self.connuces = None
        self.conncorpus = None
        self.islem = False
        self.cuces = None
        self.ucis = []
        self.formes = {}
        self.flems = {}
        self.lems = None
        self.idformesuces = {}
        self.iduces = None
        self.idformes = None
        self.uceuci = None
        if read :
            self.pathout = PathOut(dirout = parametres['pathout'])
            self.read_corpus()

    def add_word(self, word) :
        if word in self.formes :
            self.formes[word].freq += 1
            if self.formes[word].ident in self.idformesuces :
                if self.ucis[-1].uces[-1].ident in self.idformesuces[self.formes[word].ident] :
                    self.idformesuces[self.formes[word].ident][self.ucis[-1].uces[-1].ident] += 1
                else :
                    self.idformesuces[self.formes[word].ident][self.ucis[-1].uces[-1].ident] = 1
            else :
                self.idformesuces[self.formes[word].ident] = {self.ucis[-1].uces[-1].ident: 1}
        else :
            if word in self.parent.lexique :
                gramtype = self.parent.lexique[word][1]
                lem = self.parent.lexique[word][0]
            elif word.isdigit() :
                gramtype = 'num'
                lem = word
            else :
                gramtype = 'nr'
                lem = word
            self.formes[word] =  Word(word, gramtype, len(self.formes), lem)
            self.idformesuces[self.formes[word].ident] = {self.ucis[-1].uces[-1].ident : 1}

    def add_word_from_forme(self, word, stident):
        if word.forme in self.formes :
            self.formes[word.forme].freq += 1
            if self.formes[word.forme].ident in self.idformesuces :
                if stident in self.idformesuces[self.formes[word.forme].ident] :
                    self.idformesuces[self.formes[word.forme].ident][stident] += 1
                else :
                    self.idformesuces[self.formes[word.forme].ident][stident] = 1
            else :
                self.idformesuces[self.formes[word.forme].ident] = {stident: 1}
        else :
            self.formes[word.forme] = Word(word.forme, word.gram, len(self.formes), word.lem)
            self.idformesuces[self.formes[word.forme].ident] = {stident : 1}

    def conn_all(self): 
        """connect corpus to db"""
        if self.connformes is None :
            log.info('connexion corpus')
            self.connuces = sqlite3.connect(self.pathout['uces.db'])
            self.cuces = self.connuces.cursor()
            self.connformes = sqlite3.connect(self.pathout['formes.db'])
            self.cformes = self.connformes.cursor()
            self.conncorpus = sqlite3.connect(self.pathout['corpus.db'])
            self.ccorpus = self.conncorpus.cursor()
            self.cformes.execute('PRAGMA temp_store=MEMORY;')
            self.cformes.execute('PRAGMA journal_mode=MEMORY;')
            self.cformes.execute('PRAGMA  synchronous = OFF;')
            self.cuces.execute('PRAGMA temp_store=MEMORY;')
            self.cuces.execute('PRAGMA journal_mode=MEMORY;')
            self.cuces.execute('PRAGMA  synchronous = OFF;')
            self.ccorpus.execute('PRAGMA temp_store=MEMORY;')
            self.ccorpus.execute('PRAGMA journal_mode=MEMORY;')
            self.ccorpus.execute('PRAGMA  synchronous = OFF;')

    def read_corpus(self) :
        log.info('read corpus')
        self.parametres['syscoding'] = 'utf8'
        if self.conncorpus is None :
            self.conn_all()
        res = self.ccorpus.execute('SELECT * FROM etoiles;')
        for row in res :
            self.ucis.append(Uci(row[0], row[1], row[2]))
            uces = self.conncorpus.cursor().execute('SELECT * FROM luces where uci=?;',(repr(self.ucis[-1].ident),))
            for uce in uces:
                self.ucis[-1].uces.append(Uce(uce[2], uce[1], uce[0]))
        res = self.ccorpus.execute('SELECT * FROM formes;')
        self.formes = dict([[forme[1], Word(forme[1], forme[3], forme[0], lem = forme[2], freq = forme[4])] for forme in res])
        self.ccorpus.close()

    def getworduces(self, wordid) :
        if isinstance(wordid, str) :
            wordid = self.formes[wordid].ident
        res = self.cformes.execute('SELECT uces FROM uces where id=? ORDER BY id;', (repr(wordid),))
        return list(itertools.chain(*[[int(val) for val in row[0].split()] if not isinstance(row[0], int) else [row[0]] for row in res]))

    def getworducis(self, wordid) :
        res = self.getworduces(wordid)
        return list(set([self.getucefromid(uce).uci for uce in res]))

    def getformeuceseff(self, formeid) :
        if isinstance(formeid, str) :
            formeid = self.formes[formeid].ident
        res = self.cformes.execute('SELECT uces FROM uces where id=? ORDER BY id;', (repr(formeid),))
        uces = list(itertools.chain(*[[int(val) for val in row[0].split()] if not isinstance(row[0], int) else [row[0]] for row in res]))
        query = 'SELECT eff FROM eff where id=%i ORDER BY id' % formeid
        res = self.cformes.execute(query)
        eff = list(itertools.chain(*[[int(val) for val in row[0].split()] if not isinstance(row[0], int) else [row[0]] for row in res]))
        formeuceeff = {}
        for i, uce in enumerate(uces) :
            formeuceeff[uce] = formeuceeff.get(uce, 0) + eff[i]
        return formeuceeff

    def getlemuces(self, lem) :
        formesid = ', '.join([repr(val) for val in self.lems[lem].formes])
        query = 'SELECT uces FROM uces where id IN (%s) ORDER BY id' % formesid
        res = self.cformes.execute(query)
        return list(set(list(itertools.chain(*[[int(val) for val in row[0].split()] if not isinstance(row[0], int) else [row[0]] for row in res]))))

    def gettgenst(self, tgen):
        formesid = []
        for lem in tgen :
            if lem in self.lems :
                formesid += self.lems[lem].formes
            else :
                print('abscent : %s' % lem)
        query = 'SELECT uces FROM uces where id IN %s ORDER BY id' % str(tuple(formesid))
        res = self.cformes.execute(query)
        return list(set(list(itertools.chain(*[[int(val) for val in row[0].split()] if not isinstance(row[0], int) else [row[0]] for row in res]))))

    def gettgenstprof(self, tgen, classe, i, clnb):
        tgenst = []
        for lem in tgen :
            if lem in self.lems :
                lemst = self.getlemuces(lem)
                tgenst += lemst
                if not lem in self.tgenlem :
                    self.tgenlem[lem] = [0] * clnb
                self.tgenlem[lem][i] = len(set(lemst).intersection(classe))
            else :
                print('abscent: ',lem)
        return list(set(tgenst))

    def gettgentxt(self, tgen):
        sts = self.gettgenst(tgen)
        return list(set([self.getucefromid(val).uci for val in sts]))

    def getlemucis(self, lem) :
        uces = self.getlemuces(lem)
        return list(set([self.getucefromid(val).uci for val in uces]))

    def getlemuceseff(self, lem, luces = None) :
        formesid = ', '.join([repr(val) for val in self.lems[lem].formes])
        query = 'SELECT uces FROM uces where id IN (%s) ORDER BY id' % formesid
        res = self.cformes.execute(query)
        uces = list(itertools.chain(*[[int(val) for val in row[0].split()] if not isinstance(row[0], int) else [row[0]] for row in res]))
        query = 'SELECT eff FROM eff where id IN (%s) ORDER BY id' % formesid
        res = self.cformes.execute(query)
        eff = list(itertools.chain(*[[int(val) for val in row[0].split()] if not isinstance(row[0], int) else [row[0]] for row in res]))
        lemuceeff = {}
        for i, uce in enumerate(uces) :
            lemuceeff[uce] = lemuceeff.get(uce, 0) + eff[i]
        return lemuceeff

    def getlemclustereff(self, lem, cluster) :
        return len(list(set(self.lc[cluster]).intersection(self.getlemuces(lem))))

    def getlemeff(self, lem) :
        return self.lems[lem].freq

    def getlems(self) :
        return self.lems

    def getforme(self, formeid) :
        if self.idformes is None : self.make_idformes()
        return self.idformes[formeid]

    def gettotocc(self) :
        return sum([self.formes[forme].freq for forme in self.formes])

    def getucemean(self) :
        return float(self.gettotocc())/self.getucenb()

    def getucenb(self) :
        return self.ucis[-1].uces[-1].ident + 1

    def getucinb(self) :
        return self.ucis[-1].ident + 1

    def getucisize(self) :
        ucesize = self.getucesize()
        return [sum(ucesize[uci.uces[0].ident:(uci.uces[-1].ident + 1)]) for uci in self.ucis if len(uci.uces) != 0]

    def getucesize(self) :
        res = self.getalluces()
        return [len(uce[1].split()) for uce in res]

    def getconcorde(self, uces) :
        return self.cuces.execute('select * from uces where id IN (%s) ORDER BY id;' % ', '.join([repr(i) for i in uces]))

    def getuciconcorde(self, ucis) :
        uces = [[val,[uce.ident for uce in self.ucis[val].uces]] for val in ucis]
        uces = [[val[0], '\n'.join([row[1] for row in self.getconcorde(val[1])])] for val in uces]
        return uces

    def getuciconcorde_uces(self, uciid, uceid) :
        uces = [uce.ident for uce in self.ucis[uciid].uces]
        uces = [row for row in self.getconcorde(uces)]
        return uces

    def getwordconcorde(self, word) :
        return self.getconcorde(self.getworduces(word))

    def getlemconcorde(self, lem) :
        return self.getconcorde(self.getlemuces(lem))

    def getalluces(self) :
        return self.cuces.execute('SELECT * FROM uces')

    def getallucis(self):
        uces = [row[1] for row in self.getalluces()]
        return [[uci.ident, '\n'.join([uces[uce.ident] for uce in uci.uces])] for uci in self.ucis]

    def getucesfrometoile(self, etoile) :
        return [uce.ident for uci in self.ucis for uce in uci.uces if etoile in uci.etoiles]

    def getucisfrometoile(self, etoile):
        uces = [uce.ident for uci in self.ucis for uce in uci.uces if etoile in uci.etoiles]
        return list(set([self.getucefromid(val).uci for val in uces]))


    def getetoileuces(self) :
        log.info('get uces etoiles')
        etoileuces = {}
        idpara = 0
        for uci in self.ucis :
            etoiles = uci.etoiles[1:]
            for et in etoiles :
                if et in etoileuces :
                    etoileuces[et] += [uce.ident for uce in uci.uces]
                else :
                    etoileuces[et] = [uce.ident for uce in uci.uces]
            if uci.paras != [] :
                for et in uci.paras :
                    if et in etoileuces :
                        etoileuces[et] += [uce.ident for uce in uci.uces if uce.para == idpara]
                    else :
                        etoileuces[et] = [uce.ident for uce in uci.uces if uce.para == idpara]
                    idpara += 1
            else :
                idpara += 1
        return etoileuces

    def getetoileucis(self):
        etoileuces = {}
        for uci in self.ucis :
            etoiles = uci.etoiles[1:]
            for et in etoiles :
                if et in etoileuces :
                    etoileuces[et] += [uci.ident]
                else :
                    etoileuces[et] = [uci.ident]
        return etoileuces

    def getucefromid(self, uceid) :
        if self.iduces is None : self.make_iduces()
        return self.iduces[uceid]

    def gethapaxnb(self) :
        return len([None for forme in self.formes if self.formes[forme].freq == 1])

    def getactivesnb(self, key) :
        return len([lem for lem in self.lems if self.lems[lem].act == key])

# fonction inactive mais avec une incertitude concernant l'indentation sur le dernier else
#    def make_lems(self, lem = True) :
#        log.info('make lems')
#        self.lems = {}
#        for forme in self.formes :
#            if self.formes[forme].lem in self.lems :
#                if self.formes[forme].ident not in self.lems[self.formes[forme].lem] :
#                    self.lems[self.formes[forme].lem][self.formes[forme].ident] = 0
#            else :
#                    self.lems[self.formes[forme].lem] = {self.formes[forme].ident : 0}

    def getetbyuceid(self, uceid) :
        if self.uceuci is None : self.uceuci = dict([[uce.ident,uci.ident] for uci in self.ucis for uce in uci.uces])
        return self.ucis[self.uceuci[uceid]].etoiles

    def make_lems(self, lem = True) :
        log.info('make lems')
        self.lems = {}
        if lem :
            for forme in self.formes :
                if self.formes[forme].lem in self.lems :
                    if self.formes[forme].ident not in self.lems[self.formes[forme].lem].formes :
                        self.lems[self.formes[forme].lem].add_forme(self.formes[forme])
                else :
                    self.lems[self.formes[forme].lem] = Lem(self, self.formes[forme])
        else :
            self.lems = dict([[forme, Lem(self, self.formes[forme])] for forme in self.formes])

    def make_lems_from_dict(self, dictionnaire, dolem = True) :
        log.info('make lems from dict')
        self.lems = {}
        for forme in self.formes :
            if self.formes[forme].forme in dictionnaire :
                lem = dictionnaire[forme][0]
                gram = dictionnaire[forme][1]
            elif forme.isdigit() :
                gram = 'num'
                lem = forme
            else :
                gram = 'nr'
                lem = forme
            self.formes[forme].lem = lem
            self.formes[forme].gram = gram
            if dolem :
                if self.formes[forme].lem in self.lems :
                    if self.formes[forme].ident not in self.lems[self.formes[forme].lem].formes :
                        self.lems[self.formes[forme].lem].add_forme(self.formes[forme])
                else :
                    self.lems[self.formes[forme].lem] = Lem(self, self.formes[forme])
            else :
                self.lems[forme] = Lem(self, self.formes[forme])

    def make_idformes(self) :
        self.idformes = dict([[self.formes[forme].ident, self.formes[forme]] for forme in self.formes])

    def make_iduces(self) :
        if self.iduces is None :
            self.iduces = dict([[uce.ident, uce] for uci in self.ucis for uce in uci.uces])

    def make_lexitable(self, mineff, etoiles, gram = 0) :
        if gram == 0 :
            grams = {1:'', 2:''}
        else :
            grams = {gram :''}
        tokeep = [lem for lem in self.lems if self.lems[lem].freq >= mineff and self.lems[lem].act in grams]
        etuces = [[] for et in etoiles]
        for uci in self.ucis :
            get = list(set(uci.etoiles).intersection(etoiles))
            if len(get) > 1 :
                log.info('2 variables sur une ligne')
            if get != [] :
                etuces[etoiles.index(get[0])] += [uce.ident for uce in uci.uces]
        etuces = [set(val) for val in etuces]
        tab = []
        for lem in tokeep :
            deff = self.getlemuceseff(lem)
            ucesk = list(deff.keys())
            line = [lem] + [sum([deff[uce] for uce in et.intersection(ucesk)]) for et in etuces]
            if sum(line[1:]) >= mineff :
                tab.append(line)
        tab.insert(0, [''] + etoiles)
        return tab

    def make_tgen_table(self, tgen, etoiles, tot = None):
        lclasses = [self.getucesfrometoile(etoile) for etoile in etoiles]
        sets = [set(cl) for cl in lclasses]
        totoccurrences = dict([[val, 0] for val in etoiles])
        if tot is None :
            for forme in self.formes :
                formeuceeff = self.getformeuceseff(forme)
                for i, classe in enumerate(lclasses) :
                    concern = sets[i].intersection(list(formeuceeff.keys()))
                    if len(concern) :
                        totoccurrences[etoiles[i]] += sum([formeuceeff[uce] for uce in concern])
        #tgenoccurrences = dict([[val, 0] for val in etoiles])
        tgenoccurrences = {}
        for t in tgen.tgen :
            tgenoccurrences[t] = dict([[val, 0] for val in etoiles])
            for lem in tgen[t] :
                lemuceeff = self.getlemuceseff(lem)
                for i, classe in enumerate(lclasses) :
                    concern = sets[i].intersection(list(lemuceeff.keys()))
                    if len(concern) :
                        tgenoccurrences[t][etoiles[i]] += sum([lemuceeff[uce] for uce in concern])
        return tgenoccurrences, totoccurrences

    def make_tgen_profile(self, tgen, ucecl, uci = False) :
        log.info('tgen/classes')
        self.tgenlem = {}
        clnb = len(ucecl)
        if uci :
            #FIXME :  NE MARCHE PLUS CHANGER CA
            tab = [[lem] + [len(set(self.gettgentxt(tgen[lem])).intersection(classe)) for i, classe in enumerate(ucecl)] for lem in tgen]
        else :
            tab = [[lem] + [len(set(self.gettgenstprof(tgen[lem], classe, i, clnb)).intersection(classe)) for i, classe in enumerate(ucecl)] for lem in tgen]
        tab = [[line[0]] + [val for val in line[1:]] for line in tab if sum(line[1:]) >= 3]
        return tab

        #i = 0
        #nam = 'total'
        #while nam + `i` in tgen :
        #    i += 1
        #nam = nam + `i`
        #last = [nam] + [`len(classe)` for classe in ucecl]
        #tab += [last]
        #line0 = ['tgen'] + ['_'.join(['cluster', `i+1`]) for i in range(len(ucecl))]
        #tab = [line0] + tab
        #with open(fileout, 'w') as f :
        #    f.write('\n'.join(['\t'.join(line) for line in tab]).encode(self.parametres['syscoding']))        

    def make_efftype_from_etoiles(self, etoiles) :
        dtype = {}
        etuces = [[] for et in etoiles]
        for uci in self.ucis :
            get = list(set(uci.etoiles).intersection(etoiles))
            if len(get) > 1 :
                return '2 variables sur la meme ligne'
            elif get != [] :
                etuces[etoiles.index(get[0])] += [uce.ident for uce in uci.uces]
        etuces = [set(val) for val in etuces]
        for lem in self.lems :
            deff = self.getlemuceseff(lem)
            ucesk = list(deff.keys())
            gram = self.lems[lem].gram
            if gram in dtype :
                dtype[gram] = [i + j for i, j in zip(dtype[gram], [sum([deff[uce] for uce in et.intersection(ucesk)]) for et in etuces])]
            else :
                dtype[gram] = [sum([deff[uce] for uce in et.intersection(ucesk)]) for et in etuces]
        tabout = [[gram] + dtype[gram] for gram in dtype]
        tabout.insert(0, [''] + etoiles)
        return tabout

    def make_uceactsize(self, actives) :
        res = self.getalluces()
        ucesize = {}
        for lem in actives: 
            deff = self.getlemuceseff(lem)
            for uce in deff :
                ucesize[uce] = ucesize.get(uce, 0) + 1
        return ucesize

    def make_uc(self, actives, lim1, lim2) :
        uceactsize = self.make_uceactsize(actives)
        last1 = 0
        last2 = 0
        uc1 = [[]]
        uc2 = [[]]
        lastpara = 0
        for uce in [uce for uci in self.ucis for uce in uci.uces] :
            if uce.para == lastpara :
                if last1 <= lim1 :
                    last1 += uceactsize.get(uce.ident,0)
                    uc1[-1].append(uce.ident)
                else :
                    uc1.append([uce.ident])
                    last1 = 0
                if last2 <= lim2 :
                    last2 += uceactsize.get(uce.ident, 0)
                    uc2[-1].append(uce.ident)
                else :
                    uc2.append([uce.ident])
                    last2 = 0
            else :
                last1 = uceactsize.get(uce.ident, 0)
                last2 = uceactsize.get(uce.ident, 0)
                lastpara = uce.para
                uc1.append([uce.ident])
                uc2.append([uce.ident])
        return uc1, uc2

    def make_and_write_sparse_matrix_from_uc(self, actives, sizeuc1, sizeuc2, uc1out, uc2out, listuce1out, listuce2out) :
        uc1, uc2 = self.make_uc(actives, sizeuc1, sizeuc2)
        log.info('taille uc1 : %i - taille uc2 : %i' % (len(uc1), len(uc2)))
        self.write_ucmatrix(uc1, actives, uc1out)
        self.write_ucmatrix(uc2, actives, uc2out)
        listuce1 = [['uce', 'uc']] + [[repr(uce), repr(i)] for i, ucl in enumerate(uc1) for uce in ucl]
        listuce2 = [['uce', 'uc']] + [[repr(uce), repr(i)] for i, ucl in enumerate(uc2) for uce in ucl]
        with open(listuce1out, 'w') as f :
            f.write('\n'.join([';'.join(line) for line in listuce1]))
        with open(listuce2out, 'w') as f :
            f.write('\n'.join([';'.join(line) for line in listuce2]))
        return len(uc1), len(uc2)

    def write_ucmatrix(self, uc, actives, fileout) :
        log.info('write uc matrix %s' % fileout)
        uces_uc = dict([[uce, i] for i, ucl in enumerate(uc) for uce in ucl])
        deja_la = {}
        nbl = 0
        with open(fileout + '~', 'w+') as f :
            for i, lem in enumerate(actives) :
                for uce in self.getlemuces(lem):
                    if (uces_uc[uce], i) not in deja_la :
                        nbl += 1
                        f.write(''.join([' '.join([repr(uces_uc[uce]+1),repr(i+1),repr(1)]),'\n']))
                        deja_la[(uces_uc[uce], i)] = 0
            f.seek(0)
            with open(fileout, 'w') as ffin :        
                ffin.write("%%%%MatrixMarket matrix coordinate integer general\n%i %i %i\n" % (len(uc), len(actives), nbl))
                for line in f :
                    ffin.write(line)
        os.remove(fileout + '~')
        del(deja_la)

    def export_corpus(self, outf) :
        #outf = 'export_corpus.txt'
        self.make_iduces()
        res = self.getalluces()
        self.make_iduces()
        actuci = ''
        actpara = False
        with open(outf,'w', encoding='utf8') as f :
            for uce in res :
                if self.iduces[uce[0]].uci == actuci and self.iduces[uce[0]].para == actpara :
                    f.write(uce[1] + '\n')
                elif self.iduces[uce[0]].uci != actuci :
                    actuci = self.iduces[uce[0]].uci
                    if self.ucis[self.iduces[uce[0]].uci].paras == [] :
                        actpara = self.iduces[uce[0]].para
                        f.write('\n' + ' '.join(self.ucis[self.iduces[uce[0]].uci].etoiles) + '\n' + uce[1] + '\n')
                    else :
                        ident = 0
                        actpara = self.iduces[uce[0]].para
                        f.write('\n'.join([' '.join(self.ucis[self.iduces[uce[0]].uci].etoiles), self.ucis[self.iduces[uce[0]].uci].paras[ident], uce[1]] + '\n'))
                elif self.iduces[uce[0]].para != actpara :
                    actpara = self.iduces[uce[0]].para
                    ident += 1
                    f.write('\n'.join([self.ucis[self.iduces[uce[0]].uci].paras[ident], uce[1]]) + '\n')

    def export_meta_table(self, outf) :
        metas = [[repr(i)] + text.etoiles[1:] for i, text in enumerate(self.ucis)]
        longueur_max = max([len(val) for val in metas])
        first = ['column_%i' % i for i in range(longueur_max)]
        metas.insert(0, first)
        with open(outf, 'w', encoding='utf8') as f :
            f.write('\n'.join(['\t'.join(line) for line in metas]))

    def export_corpus_classes(self, outf, alc = True, lem = False, uci = False) :
        ucecl = {}
        for i, lc in enumerate(self.lc) :
            for uce in lc : 
                ucecl[uce] = i + 1
        for uce in self.lc0 :
            ucecl[uce] = 0
        if not uci :
            res = self.getalluces()
            self.make_iduces()
        else :
            res = self.getallucis()
        with open(outf, 'w', encoding='utf8') as f :
            for uce in res :
                guce = uce[1]
                if not uci :
                    actuci = self.iduces[uce[0]].uci
                else :
                    actuci = uce[0]
                if lem :
                    guce = ' '.join([self.formes[forme].lem for forme in guce.split()])
                if alc :
                    etline = ' '.join(self.ucis[actuci].etoiles + ['*classe_%i' % ucecl[uce[0]]])
                else :
                    etline = ' '.join(['<' + '='.join(et.split('_')) + '>' for et in self.ucis[actuci].etoiles[1:]])
                f.write(etline + '\n')
                f.write(guce + '\n\n')

    def export_classe(self, outf, classe, lem = False, uci = False) :
        sts = self.lc[classe - 1]
        if not uci :
            res = self.getconcorde(sts)
            self.make_iduces()
        else :
            res = self.getuciconcorde(sts)
        with open(outf, 'w', encoding='utf8') as f :
            for uce in res :
                guce = uce[1]
                if not uci :
                    f.write(' '.join(self.ucis[self.iduces[uce[0]].uci].etoiles) + '\n')
                else :
                    f.write(' '.join(self.ucis[uce[0]].etoiles) + '\n')
                if lem :
                    guce = ' '.join([self.formes[forme].lem for forme in guce.split()])
                f.write(guce + '\n\n')

    def export_owledge(self, rep, classe, lem = False, uci = False) :
        sts = self.lc[classe - 1]
        if not uci :
            res = self.getconcorde(sts)
            self.make_iduces()
        else :
            res = self.getuciconcorde(sts)
        for uce in res :
            ident = uce[0]
            guce = uce[1]
            outf = '.'.join([repr(ident), 'txt'])
            outf = os.path.join(rep, outf)
            if lem :
                guce = ' '.join([self.formes[forme].lem for forme in guce.split()])
            with open(outf, 'w', encoding='utf8') as f :
                f.write(guce) #.encode('cp1252', errors = 'replace'))

    def export_tropes(self, fileout, classe, lem = False, uci = False) :
        sts = self.lc[classe - 1]
        if not uci :
            res = self.getconcorde(sts)
            self.make_iduces()
        else :
            res = self.getuciconcorde(sts)
        with open(fileout, 'w', encoding='utf8') as f :
            for uce in res :
                guce = uce[1]
                if lem :
                    guce = ' '.join([self.formes[forme].lem for forme in guce.split()])
                f.write(guce) #.encode('cp1252', errors = 'replace'))
                f.write('\n')

    def make_and_write_sparse_matrix_from_uces(self, actives, outfile, listuce = False) :
        log.info('make_and_write_sparse_matrix_from_uces %s' % outfile)
        nbl = 0
        with open(outfile + '~', 'w+') as f :
            for i, lem in enumerate(actives) :
                for uce in sorted(self.getlemuces(lem)) :
                    nbl += 1
                    f.write(''.join([' '.join([repr(uce+1), repr(i+1),repr(1)]),'\n']))
            f.seek(0)
            with open(outfile, 'w') as ffin :
                ffin.write("%%%%MatrixMarket matrix coordinate integer general\n%i %i %i\n" % (self.getucenb(), len(actives), nbl))
                for line in f :
                    ffin.write(line)
        os.remove(outfile + '~')
        if listuce :
            with open(listuce, 'w') as f :
                f.write('\n'.join(['uce;uc'] + [';'.join([repr(i),repr(i)]) for i in range(0, self.getucenb())]))

    def make_and_write_sparse_matrix_from_uci(self, actives, outfile, listuci = False) :
        log.info('make_and_write_sparse_matrix_from_ucis %s' % outfile)
        nbl = 0
        with open(outfile + '~', 'w+') as f :
            for i, lem in enumerate(actives) :
                for uci in sorted(self.getlemucis(lem)) :
                    nbl += 1
                    f.write(''.join([' '.join([repr(uci+1), repr(i+1),repr(1)]),'\n']))
            f.seek(0)
            with open(outfile, 'w') as ffin :
                ffin.write("%%%%MatrixMarket matrix coordinate integer general\n%i %i %i\n" % (self.getucinb(), len(actives), nbl))
                for line in f :
                    ffin.write(line)
        os.remove(outfile + '~')
        if listuci :
            with open(listuci, 'w') as f :
                f.write('\n'.join(['uci;uc'] + [';'.join([repr(i),repr(i)]) for i in range(0, self.getucinb())]))

    def make_and_write_sparse_matrix_from_classe(self, actives, uces, outfile) :
        log.info('make_and_write_sparse_matrix_from_classe %s' % outfile)
        nbl = 0
        duces = dict([[uce, i] for i, uce in enumerate(uces)])
        with open(outfile + '~', 'w+') as f :
            for i, lem in enumerate(actives) :
                uces_ok = list(set(self.getlemuces(lem)).intersection(uces))
                for uce in uces_ok :
                    f.write(''.join([' '.join([repr(duces[uce]+1),repr(i+1),repr(1)]),'\n']))
            f.seek(0)
            with open(outfile, 'w') as ffin :
                ffin.write("%%%%MatrixMarket matrix coordinate integer general\n%i %i %i\n" % (len(uces), len(actives), nbl))
                for line in f :
                    ffin.write(line)
        os.remove(outfile + '~')

    def make_table_with_classe(self, uces, list_act, uci = False) :
        table_uce = [[0 for val in list_act] for line in range(0,len(uces))]
        uces = dict([[uce, i] for i, uce in enumerate(uces)])
        if uci :
            getlem = self.getlemucis
        else :
            getlem = self.getlemuces
        for i, lem in enumerate(list_act) :
            lemuces = list(set(getlem(lem)).intersection(uces))
            for uce in lemuces :
                table_uce[uces[uce]][i] = 1
        table_uce.insert(0, list_act)
        return table_uce

    def make_pondtable_with_classe(self, uces, list_act) :
        table_uce = [[0 for val in list_act] for line in range(0,len(uces))]
        uces = dict([[uce, i] for i, uce in enumerate(uces)])
        for i, lem in enumerate(list_act) :
            uceseff = self.getlemuceseff(lem)
            lemuces = list(set(uceseff.keys()).intersection(uces))
            for uce in lemuces :
                table_uce[uces[uce]][i] = uceseff[uce]
        table_uce.insert(0, list_act)
        return table_uce

    def parse_active(self, gramact, gramsup = None) :
        log.info('parse actives')
        for lem in self.lems :
            if lem.startswith('_') and lem.endswith('_') :
                self.lems[lem].act = 2
            elif self.lems[lem].gram in gramact :
                self.lems[lem].act = 1
            elif gramsup is not None and self.lems[lem].gram not in gramact:
                if self.lems[lem].gram in gramsup :
                    self.lems[lem].act = 2
                else :
                    self.lems[lem].act =  0
            else :
                self.lems[lem].act = 2

    def make_actives_limit(self, limit, key = 1) :
        if self.idformes is None :
            self.make_idformes()
        return [lem for lem in self.lems if self.getlemeff(lem) >= limit and self.lems[lem].act == key]

    def make_actives_nb(self, nbmax, key) :
        log.info('make_actives_nb : %i - %i' % (nbmax,key))
        if self.idformes is None :
            self.make_idformes()
        allactives = [[self.lems[lem].freq, lem] for lem in self.lems if self.lems[lem].act == key and self.lems[lem].freq >= 3]
        self.activenb = len(allactives)
        allactives = sorted(allactives, reverse = True)
        if self.activenb == 0 :
            return [], 0
        if len(allactives) <= nbmax :
            log.info('nb = %i - eff min = %i ' % (len(allactives), allactives[-1][0]))
            return [val[1] for val in allactives], allactives[-1][0]
        else :
            effs = [val[0] for val in allactives]
            if effs.count(effs[nbmax - 1]) > 1 :
                lim = effs[nbmax - 1] + 1
                nok = True
                while nok :
                    try :
                        stop = effs.index(lim)
                        nok = False
                    except ValueError:
                        lim -= 1
            else :
                stop = nbmax - 1
                lim = effs[stop]
        log.info('nb actives = %i - eff min = %i ' % (stop + 1, lim))
        return [val[1] for val in allactives[0:stop]], lim

    def make_and_write_profile(self, actives, ucecl, fileout, uci = False) :
        log.info('formes/classes')
        if uci :
            tab = [[lem] + [len(set(self.getlemucis(lem)).intersection(classe)) for classe in ucecl] for lem in actives]
        else :
            tab = [[lem] + [len(set(self.getlemuces(lem)).intersection(classe)) for classe in ucecl] for lem in actives]
        tab = [[line[0]] + [repr(val) for val in line[1:]] for line in tab if sum(line[1:]) >= 3]
        with open(fileout, 'w', encoding='utf8') as f :
            f.write('\n'.join([';'.join(line) for line in tab]))

    def make_etoiles(self) :
        etoiles = set([])
        for uci in self.ucis :
            etoiles.update(uci.etoiles[1:])
        return list(etoiles)

    def make_themes(self):
        themes = set([])
        for uci in self.ucis :
            themes.update(uci.paras)
        return list(themes)

    def make_etoiles_dict(self) :
        etoiles = [et for uci in self.ucis for et in uci.etoiles[1:]]
        det = {}
        for etoile in etoiles :
            et = etoile.split('_')
            if et[0] in det :
                try :
                    endet = '_'.join(et[1:])
                    if etoile in det[et[0]] :
                        det[et[0]][etoile] += 1
                    else :
                        det[et[0]][etoile] = 1
                except IndexError :
                    det[et[0]] += 1
            else :
                try :
                    endet = '_'.join(et[1:])
                    det[et[0]] = {etoile :1}
                except IndexError :
                    det[et[0]] = 1
        return det

    def make_theme_dict(self):
        themes = [val for uci in self.ucis for val in uci.paras]
        det = {}
        for theme in themes :
            th = theme.split('_')
            if th[0] in det :
                try :
                    endth = '_'.join(th[1:])
                    if theme in det[th[0]] :
                        det[th[0]][theme] += 1
                    else :
                        det[th[0]][theme] = 1
                except IndexError :
                    det[th[0]] += 1
            else :
                try :
                    endth = '_'.join(th[1:])
                    det[th[0]] = {theme:1}
                except IndexError :
                    det[th[0]] = 1
        return det

    def make_etline(self, listet) :
        etuces = [[] for et in listet]
        for uci in self.ucis :
            get = list(set(uci.etoiles).intersection(listet))
            if len(get) > 1 :
                return '2 variables sur la meme ligne'
            elif get != [] :
                etuces[listet.index(get[0])] += [uce.ident for uce in uci.uces]
        return etuces

    def make_and_write_profile_et(self, ucecl, fileout, uci = False) :
        log.info('etoiles/classes')
        if not uci :
            etoileuces = self.getetoileuces()
        else :
            etoileuces = self.getetoileucis()
        etoileuces = dict([[et, etoileuces[et]] for et in etoileuces if len(etoileuces[et]) > 0])
        with open(fileout, 'w', encoding='utf8') as f :
            f.write('\n'.join([';'.join([et] + [repr(len(set(etoileuces[et]).intersection(classe))) for classe in ucecl]) for et in etoileuces])) #.encode(self.parametres['syscoding'])
        #etoiles = self.make_etoiles()
        #with open(fileout, 'w') as f :
        #    f.write('\n'.join([';'.join([etoile] + [`len(set(self.getucesfrometoile(etoile)).intersection(classe))` for classe in ucecl]) for etoile in etoiles]).encode(self.parametres['syscoding']))

    def make_colored_corpus(self, uci = False) :
        ucecl = {}
        for i, lc in enumerate(self.lc) :
            for uce in lc :
                ucecl[uce] = i + 1
        for uce in self.lc0 :
            ucecl[uce] = 0
        color = ['black'] + colors[len(self.lc) - 1]
        txt = '''<html>
        <meta http-equiv="content-Type" content="text/html; charset=utf8" />
        <body>
'''
        if not uci :
            res = self.getalluces()
            self.make_iduces()
            actuci = ''
            actpara = False
            for uce in res :
                if self.iduces[uce[0]].uci != actuci :
                    actuci = self.iduces[uce[0]].uci
                    txt += '<br><hr>' + ' '.join(self.ucis[self.iduces[uce[0]].uci].etoiles) + '<br><br>'
                    txt += '<font color="%s">' % (color[ucecl[uce[0]]]) + uce[1] + '</font><br><br>'
                else :
                    txt += '<font color="%s">' % (color[ucecl[uce[0]]]) + uce[1] + '</font><br><br>'
        else :
            res = self.getallucis()
            actuci = ''
            for uce in res :
                if self.ucis[uce[0]].ident != actuci :
                    actuci = self.ucis[uce[0]].ident
                    txt += '<br><hr>' + ' '.join(self.ucis[self.ucis[uce[0]].ident].etoiles) + '<br><br>'
                    txt += '<font color="%s">' % (color[ucecl[uce[0]]]) + uce[1] + '</font><br><br>'
                else :
                    txt += '<font color="%s">' % (color[ucecl[uce[0]]]) + uce[1] + '</font><br><br>'
        return txt + '\n</body></html>'

    def make_cut_corpus(self, uci = False) :
        txt = ''
        if not uci :
            res = self.getalluces()
            self.make_iduces()
            actuci = ''
            actpara = False
            for uce in res :
                if self.iduces[uce[0]].uci != actuci :
                    actuci = self.iduces[uce[0]].uci
                    txt += '\n' + ' '.join(self.ucis[self.iduces[uce[0]].uci].etoiles) + '\n'
                    txt += ''.join(['\n',uce[1],'\n'])
                else :
                    txt +=  ''.join(['\n',uce[1],'\n'])
        else :
            res = self.getallucis()
            actuci = ''
            for uce in res :
                if self.ucis[uce[0]].ident != actuci :
                    actuci = self.ucis[uce[0]].ident
                    txt += '\n' + ' '.join(self.ucis[self.ucis[uce[0]].ident].etoiles) + '\n'
                    txt +=  ''.join(['\n',uce[1],'\n'])
                else :
                    txt += ''.join(['\n',uce[1],'\n'])
        return txt

    def count_from_list(self, l, d) :
        for val in l :
            if val in d :
                d[val] += 1
            else :
                d[val] = 1
        return d

    def count_from_list_cl(self, l, d, a, clnb) :
        for val in l :
            if val in d :
                d[val][a] += 1
            else :
                d[val] = [0] * clnb
                d[val][a] = 1
        return d

    def find_segments(self, taille_segment, taille_limite) :
        d = {}
        for uce in self.getalluces() :
            uce = uce[1].split()
            d = self.count_from_list([' '.join(uce[i:i+taille_segment]) for i in range(len(uce)-(taille_segment - 1))], d)
        l = [[d[val], val] for val in d if d[val] >= 3]
        del(d)
        l.sort()
        if len(l) > taille_limite :
            l = l[-taille_limite:]
        return l

    def find_segments_in_classe(self, list_uce, taille_segment, taille_limite, uci = False):
        d={}
        if not uci :
            concorde = self.getconcorde
        else :
            concorde = self.getuciconcorde
        for uce in concorde(list_uce) :
            uce = uce[1].split()
            d =self.count_from_list([' '.join(uce[i:i+taille_segment]) for i in range(len(uce)-(taille_segment - 1))], d)
        l = [[d[val], val, taille_segment] for val in d if d[val] >= 3]
        del(d)
        l.sort()
        if len(l) > taille_limite :
            l = l[-taille_limite:]
        return l

    def make_segments_profile(self, fileout, lenmin = 3, lenmax = 10, effmin = 50, lem = False) :
        d = {}
        for b, classe in enumerate(self.lc) :
            for uce in self.getconcorde(classe) :
                uce = uce[1].split()
                if lem :
                    uce = [self.formes[forme].lem for forme in uce]
                for taille_segment in range(lenmin,lenmax) :
                    d =self.count_from_list_cl([' '.join(uce[i:i+taille_segment]) for i in range(len(uce)-(taille_segment - 1))], d, b, len(self.lc))
        result = [[seg] + [str(val) for val in d[seg]] for seg in d if sum(d[seg]) >= effmin]
        with open(fileout, 'w', encoding='utf8') as f :
            f.write('\n'.join([';'.join(line) for line in result]))

    def make_proftype(self, outf) :
        res = {}
        for lem in self.lems :
            gram = self.lems[lem].gram
            if not gram in res :
                res[gram] = [0 for val in self.lc]
            lemuceeff = self.getlemuceseff(lem)
            for i, classe in enumerate(self.lc) :
                concern = set(classe).intersection(list(lemuceeff.keys()))
                res[gram][i] += sum([lemuceeff[uce] for uce in concern])
        res = [[gram] + [repr(val) for val in res[gram]] for gram in res]
        res.sort()
        with open(outf, 'w', encoding='utf8') as f :
            f.write('\n'.join([';'.join(line) for line in res]))

    def make_ucecl_from_R(self, filein) :
        with open(filein, 'r') as f :
            c = f.readlines()
        c.pop(0)
        self.lc = []
        for line in c :
            line = line.replace('\n', '').replace('"', '').split(';')
            self.lc.append([int(line[0]) - 1, int(line[1])])
        classesl = [val[1] for val in self.lc]
        clnb = max(classesl)
        self.lc = sorted(self.lc, key=itemgetter(1))
        self.lc = [[uce[0] for uce in self.lc if uce[1] == i] for i in range(clnb+1)]
        self.lc0 = self.lc.pop(0)
        #return ucecl

    def get_stat_by_cluster(self, outf, lclasses = None) :
        log.info('get_stat_by_cluster')
        if lclasses is None :
            lclasses = self.lc
        t1 = time()
        occurrences = dict([[i + 1, 0] for i in range(len(lclasses))])
        formescl = dict([[i + 1, 0] for i in range(len(lclasses))])
        hapaxcl = dict([[i + 1, 0] for i in range(len(lclasses))])
        lenclasses = dict([[i+1,len(cl)] for i, cl in enumerate(lclasses)])
        sets = [set(cl) for cl in lclasses]
        for forme in self.formes :
            formeuceeff = self.getformeuceseff(forme)
            for i, classe in enumerate(lclasses) :
                concern = sets[i].intersection(list(formeuceeff.keys()))
                if len(concern) :
                    occurrences[i+1] += sum([formeuceeff[uce] for uce in concern])
                    formescl[i+1] += 1
                    if self.formes[forme].freq == 1 :
                        hapaxcl[i+1] += 1
        log.info('%f' % (time() - t1))
        if outf is not None :
            toprint = '\n'.join([';'.join([repr(i), repr(occurrences[i]), repr(formescl[i]), repr(hapaxcl[i]), repr(lenclasses[i]), repr(float(hapaxcl[i])/float(formescl[i]))]) for i in occurrences])
            with open(outf, 'w', encoding='utf8') as f :
                f.write(toprint)
        else :
            return [[repr(occurrences[i]), repr(formescl[i]), repr(hapaxcl[i]), repr(lenclasses[i]), repr(float(hapaxcl[i])/float(formescl[i]))] for i in occurrences]

    def get_stat_by_et(self, outf, etoiles) :
        lclasses = [self.getucesfrometoile(etoile) for etoile in etoiles]
        stats = self.get_stat_by_cluster(None, lclasses)
        stats = [[etoiles[i]] + val for i, val in enumerate(stats)]
        first = [_('variable'), _('occurences'), _('formes'), _('hapax'), _('segments'), _('hapax/formes')]
        if outf is not None :
            toprint = '\t'.join(first) + "\n"
            toprint += '\n'.join(['\t'.join(line) for line in stats])
            with open(outf, 'w', encoding='utf8') as f :
                f.write(toprint)
        else :
            return stats

    def gethapaxbyet(self, etoiles) :
        hapaxuces = [self.getlemuces(forme)[0] for forme in self.lems if self.lems[forme].freq == 1]
        hucesdict = {}
        for uce in hapaxuces :
            if uce in hucesdict :
                hucesdict[uce] += 1
            else :
                hucesdict[uce] = 1
        etuces = [[] for et in etoiles]
        for uci in self.ucis :
            get = list(set(uci.etoiles).intersection(etoiles))
            if len(get) > 1 :
                return '2 variables sur la meme ligne'
            elif get != [] :
                etuces[etoiles.index(get[0])] += [uce.ident for uce in uci.uces]
        etuces = [set(val) for val in etuces]
        return [sum([hucesdict[uce] for uce in list(etuce.intersection(hapaxuces))]) for etuce in etuces]

    def gethapaxuces(self) :
        hapaxuces = [self.getlemuces(forme)[0] for forme in self.lems if self.lems[forme].freq == 1]
        hapax = [forme for forme in self.lems if self.lems[forme].freq == 1]
        hucesdict = {}
        for i,uce in enumerate(hapaxuces) :
            if uce in hucesdict :
                hucesdict[uce][0] += 1
                hucesdict[uce][1].append(hapax[i])
            else :
                hucesdict[uce] = [1,[hapax[i]]]
        huces = {}
        for uce in hucesdict :
            if hucesdict[uce][0] in huces :
                huces[hucesdict[uce][0]].append(uce)
            else :
                huces[hucesdict[uce][0]] = [uce]
        huces = list(zip(huces, list(huces.values())))
        huces.sort(reverse=True)
        txt = """
        <html><body>
        """
        for nb in huces[0:4] :
            txt += "<p><h2>%i hapax par uce</h2><p>\n" % nb[0]
            for uce in nb[1] :
                res = self.getconcorde([uce])
                for row in res :
                    ucetxt = ' ' + row[1] + ' '
                    uceid = row[0]
                for hap in hucesdict[uce][1] :
                    laforme = self.getforme([forme for forme in self.lems[hap].formes][0]).forme
                    ucetxt = ucetxt.replace(' '+laforme+' ', ' <font color=red>'+laforme+'</font> ')
                txt += '<p><b>' + ' '.join(self.getetbyuceid(uceid)) + '</b></p>'
                txt += '<p>'+ucetxt+'</p>\n'
        txt += """
        </body></html>
        """
        with open('/tmp/testhapxuce.html','w', encoding='utf8') as f :
            f.write(txt)

    def export_dictionary(self, fileout, syscoding) :
        listformes = [[self.formes[forme].freq, forme, self.formes[forme].lem, self.formes[forme].gram] for forme in self.formes]
        listformes.sort(reverse = True)
        listformes = [forme[1:] + [repr(forme[0])] for forme in listformes]
        with open(fileout, 'w', encoding='utf8') as f :
            f.write('\n'.join(['\t'.join(forme) for forme in listformes]))

    def export_lems(self, fileout, syscoding) :
        self.make_idformes()
        listlem = [[lem, '\t'.join(['\t'.join([self.idformes[forme].forme, repr(self.lems[lem].formes[forme])]) for forme in self.lems[lem].formes])] for lem in self.lems]
        listlem.sort()
        with open(fileout, 'w', encoding='utf8') as f :
            f.write('\n'.join(['\t'.join(lem) for lem in listlem]))


class MakeUciStat :
    def __init__(self, corpus) :
        ucinb = corpus.getucinb()
        ucisize = corpus.getucisize()
        ucimean = float(sum(ucisize))/float(ucinb)
        detoile = corpus.make_etoiles_dict()

class Uci :
    def __init__(self, iduci, line, paraset = None) :
        self.ident = iduci
        self.etoiles = line.split()
        self.uces = []
        if paraset is not None :
            self.paras = paraset.split()
        else :
            self.paras = []

class Uce :
    def __init__(self, iduce, idpara, iduci) :
        self.ident = iduce
        self.para = idpara
        self.uci = iduci

class Word :
    def __init__(self, word, gramtype, idword, lem = None, freq = None) :
        self.forme = word
        self.lem = lem
        self.gram = gramtype
        self.ident = idword
        self.act = 1
        if freq is not None :
            self.freq = freq
        else :
            self.freq = 1

class Lem :
    def __init__(self, parent, forme) :
        self.formes = {forme.ident : forme.freq}
        self.gram = forme.gram
        self.freq = forme.freq
        self.act = forme.act

    def add_forme(self, forme) :
        self.formes[forme.ident] = forme.freq
        self.freq += forme.freq


def decouperlist(chaine, longueur, longueurOptimale) :
    """
        on part du dernier caractère, et on recule jusqu'au début de la chaîne.
        Si on trouve un '$', c'est fini.
        Sinon, on cherche le meilleur candidat. C'est-à-dire le rapport poids/distance le plus important.
    """
    separateurs = [['.', 6.0], ['?', 6.0], ['!', 6.0], ['£$£', 6.0], [':', 5.0], [';', 4.0], [',', 1.0], [' ', 0.01]]
    dsep = dict([[val[0],val[1]] for val in separateurs])
    trouve = False                 # si on a trouvé un bon séparateur
    iDecoupe = 0                # indice du caractere ou il faut decouper
    longueur = min(longueur, len(chaine) - 1)
    chaineTravail = chaine[:longueur + 1]
    nbCar = longueur
    meilleur = ['', 0, 0]        # type, poids et position du meilleur separateur
    try :
        indice = chaineTravail.index('$')
        trouve = True
        iDecoupe = indice - 1
    except ValueError :
        pass
    if not trouve:
        while nbCar >= 0:
            caractere = chaineTravail[nbCar]
            distance = abs(longueurOptimale - nbCar) + 1
            meilleureDistance = abs(longueurOptimale - meilleur[2]) + 1
            if caractere in dsep :
                if (float(dsep[caractere]) / distance) > (float(meilleur[1]) / meilleureDistance) :
                    meilleur[0] = caractere
                    meilleur[1] = dsep[caractere]
                    meilleur[2] = nbCar
                    trouve = True
                    iDecoupe = nbCar
            else :
                if (float(dsep[' ']) / distance) > (float(meilleur[1]) / meilleureDistance) :
                    meilleur[0] = ' '
                    meilleur[1] = dsep[' ']
                    meilleur[2] = nbCar
                    trouve = True
                    iDecoupe = nbCar
            nbCar = nbCar - 1
    # si on a trouvé
    if trouve:

        #if meilleur[0] != ' ' :
        #    fin = chaine[iDecoupe + 1:]
        #    retour = chaineTravail[:iDecoupe]
        #else :

        fin = chaine[iDecoupe + 1:]
        retour = chaineTravail[:iDecoupe + 1]
        return len(retour) > 0, retour, fin
    # si on a rien trouvé
    return False, chaine, ''

def testetoile(line) :
    return line.startswith('****')

def testint(line) :
    return line[0:4].isdigit() and '*' in line

def prep_txtlist(txt) :
    return txt.split() + ['$']

def prep_txtcharact(txt) :
    return txt + '$'


class BuildCorpus :
    """
    Class for building a corpus
    """

    def __init__(self, infile, parametres_corpus, lexique = None, expressions = None, dlg = None) :
        log.info('begin building corpus...')
        self.lexique = lexique
        self.expressions = expressions
        self.dlg = dlg
        self.corpus = Corpus(self, parametres_corpus)
        self.infile = infile
        self.last = 0
        self.lim = parametres_corpus.get('lim', 1000000)
        self.encoding = parametres_corpus['encoding']
        self.corpus.pathout = PathOut(filename = parametres_corpus['originalpath'], dirout = parametres_corpus['pathout'])
        self.corpus.pathout.createdir(parametres_corpus['pathout'])
        self.corpus.parametres['uuid'] = str(uuid4())
        self.corpus.parametres['corpus_name'] = parametres_corpus['corpus_name'] #os.path.split(self.corpus.parametres['pathout'])[1]
        self.corpus.parametres['type'] = 'corpus'
        if self.corpus.parametres['keep_ponct'] :
            self.ponctuation_espace = [' ', '']
        else :
            self.ponctuation_espace =  [' ','.', '£$£', ';', '?', '!', ',', ':','']
        self.cleans = []
        self.tolist = self.corpus.parametres.get('tolist', 0)
        self.buildcleans()
        self.prep_makeuce()
        #create database
        self.connect()
        self.dobuild()

    def prep_makeuce(self) :
        method = self.corpus.parametres.get('ucemethod', 0)
        if method == 1 :
            self.decouper = decouperlist
            self.prep_txt = prep_txtlist
            self.ucesize = self.corpus.parametres.get('ucesize', 40)
        elif method == 0 :
            self.decouper = decoupercharact
            self.prep_txt = prep_txtcharact
            self.ucesize = self.corpus.parametres.get('ucesize', 240)
        log.info('method uce : %s' % method)

    def dobuild(self) :
        t1 = time()
        try :
            self.read_corpus(self.infile)
        except Warning as args :
            log.info('pas kool %s' % args)
            raise Warning
        else :
            self.indexdb()
            self.corpus.parametres['ira'] = self.corpus.pathout['Corpus.cira']
            self.time = time() - t1
            self.dofinish()
            DoConf().makeoptions(['corpus'],[self.corpus.parametres], self.corpus.pathout['Corpus.cira'])
            log.info('time : %f' % (time() - t1))

    def connect(self) :
        self.conn_f = sqlite3.connect(self.corpus.pathout['formes.db'])
        self.cf = self.conn_f.cursor()
        self.cf.execute('CREATE TABLE IF NOT EXISTS uces (id INTEGER, uces TEXT);')
        self.cf.execute('CREATE TABLE IF NOT EXISTS eff (id INTEGER, eff TEXT);')
        self.conn_f.commit()
        self.cf = self.conn_f.cursor()
        self.cf.execute('PRAGMA temp_store=MEMORY;')
        self.cf.execute('PRAGMA journal_mode=MEMORY;')
        self.cf.execute('PRAGMA  synchronous = OFF;')
        self.cf.execute('begin')
        self.conn = sqlite3.connect(self.corpus.pathout['uces.db'])
        self.c = self.conn.cursor()
        self.c.execute('CREATE TABLE IF NOT EXISTS uces (id INTEGER, uces TEXT);')
        self.conn.commit()
        self.c = self.conn.cursor()
        self.c.execute('PRAGMA temp_store=MEMORY;')
        self.c.execute('PRAGMA journal_mode=MEMORY;')
        self.c.execute('PRAGMA  synchronous = OFF;')
        self.c.execute('begin')

    def indexdb(self) :
        #commit index and close db
        self.conn.commit()
        self.conn_f.commit()
        self.cf.execute('CREATE INDEX iduces ON uces (id);')
        self.cf.execute('CREATE INDEX ideff ON eff (id);')
        self.c.close()
        self.cf.close()
        #backup corpus
        self.conn_corpus = sqlite3.connect(self.corpus.pathout['corpus.db'])
        self.ccorpus = self.conn_corpus.cursor()
        self.ccorpus.execute('CREATE TABLE IF NOT EXISTS etoiles (uci INTEGER, et TEXT, paras TEXT);')
        self.ccorpus.execute('CREATE TABLE IF NOT EXISTS luces (uci INTEGER, para INTEGER, uce INTEGER);')
        self.ccorpus.execute('CREATE TABLE IF NOT EXISTS formes (ident INTEGER, forme TEXT, lem TEXT, gram TEXT, freq INTEGER);')
        self.conn_corpus.commit()
        self.ccorpus = self.conn_corpus.cursor()
        self.ccorpus.execute('PRAGMA temp_store=MEMORY;')
        self.ccorpus.execute('PRAGMA journal_mode=MEMORY;')
        self.ccorpus.execute('PRAGMA  synchronous = OFF;')
        self.ccorpus.execute('begin')
        self.backup_corpus()
        self.ccorpus.execute('CREATE INDEX iduci ON luces (uci);')
        self.conn_corpus.commit()
        self.conn_corpus.close()
        #self.corpus.parametres['corpus_ira'] = self.corpus.pathout['corpus.cira']

    def buildcleans(self) :
        if self.corpus.parametres.get('lower', 1) :
            self.cleans.append(self.dolower)
        if self.corpus.parametres.get('firstclean', 1) :
            self.cleans.append(self.firstclean)
        if self.corpus.parametres['charact'] :
            self.rule = self.corpus.parametres.get('keep_caract', "^a-zA-Z0-9àÀâÂäÄáÁéÉèÈêÊëËìÌîÎïÏòÒôÔöÖùÙûÛüÜçÇßœŒ’ñ.:,;!?*'_")
            self.cleans.append(self.docharact)
        if self.corpus.parametres.get('expressions', 1) :
            self.cleans.append(self.make_expression)
        if self.corpus.parametres.get('apos', 1) :
            self.cleans.append(self.doapos)
        if self.corpus.parametres.get('tiret', 1):
            self.cleans.append(self.dotiret)

    def make_expression(self,txt) :
        exp = list(self.expressions.keys())
        exp.sort(reverse=True)
        for expression in exp :
            if expression in txt :
                txt = txt.replace(expression, self.expressions[expression][0])
        return txt

    def dolower(self, txt) :
        return txt.lower()

    def docharact(self, txt) :
        #rule = u"^a-zA-Z0-9àÀâÂäÄáÁéÉèÈêÊëËìÌîÎïÏòÒôÔöÖùÙûÛüÜçÇßœŒ’ñ.:,;!?*'_-"
        list_keep = "[" + self.rule + "]+"
        return re.sub(list_keep, ' ', txt)

    def doapos(self, txt) :
        return txt.replace('\'', ' ')

    def dotiret(self, txt) :
        return txt.replace('-', ' ')

    def firstclean(self, txt) :
        txt = txt.replace('’',"'")
        txt = txt.replace('œ', 'oe')
        return txt.replace('...',' £$£ ').replace('?',' ? ').replace('.',' . ').replace('!', ' ! ').replace(',',' , ').replace(';', ' ; ').replace(':',' : ').replace('…', ' £$£ ')

    def make_cleans(self, txt) :
        for clean in self.cleans :
            txt = clean(txt)
        return txt

    def backup_uce(self) :
        if self.corpus.idformesuces != {} :
            log.info('backup %i' % len(self.corpus.idformesuces))
            touce = [(repr(forme), ' '.join([repr(val) for val in  list(self.corpus.idformesuces[forme].keys())])) for forme in self.corpus.idformesuces]
            toeff = [(repr(forme), ' '.join([repr(val) for val in  list(self.corpus.idformesuces[forme].values())])) for forme in self.corpus.idformesuces]
            self.cf.executemany('INSERT INTO uces VALUES (?,?);', touce)
            self.cf.executemany('INSERT INTO eff VALUES (?,?);', toeff)
        self.corpus.idformesuces = {}
        self.count = 1

    def backup_corpus(self) :
        log.info('start backup corpus')
        t = time()
        for uci in self.corpus.ucis :
            self.ccorpus.execute('INSERT INTO etoiles VALUES (?,?,?);' ,(uci.ident,' '.join(uci.etoiles), ' '.join(uci.paras,)))
            for uce in uci.uces :
                self.ccorpus.execute('INSERT INTO luces VALUES (?,?,?);',(repr(uci.ident),repr(uce.para),repr(uce.ident),))
        for forme in self.corpus.formes :
            self.ccorpus.execute('INSERT INTO formes VALUES (?,?,?,?,?);', (repr(self.corpus.formes[forme].ident), forme, self.corpus.formes[forme].lem, self.corpus.formes[forme].gram, repr(self.corpus.formes[forme].freq),))
        log.info('%f' % (time() - t))

    def dofinish(self) :
        self.corpus.parametres['date'] = datetime.datetime.now().ctime()
        minutes, seconds = divmod(self.time, 60)
        hours, minutes = divmod(minutes, 60)
        self.corpus.parametres['time'] = '%.0fh %.0fm %.0fs' % (hours, minutes, seconds)
        self.corpus.parametres['ucinb'] = self.corpus.getucinb()
        self.corpus.parametres['ucenb'] = self.corpus.getucenb()
        self.corpus.parametres['occurrences'] = self.corpus.gettotocc()
        self.corpus.parametres['formesnb'] = len(self.corpus.formes)
        hapaxnb = self.corpus.gethapaxnb()
        pourhapaxf = (float(hapaxnb) / len(self.corpus.formes)) * 100
        pourhapaxocc = (float(hapaxnb) / self.corpus.parametres['occurrences']) * 100
        self.corpus.parametres['hapax'] = '%i - %.2f %% des formes - %.2f %% des occurrences' % (hapaxnb, pourhapaxf, pourhapaxocc)

class BuildSubCorpus(BuildCorpus):

    def __init__(self, corpus, parametres, dlg = None) :
        log.info('begin subcorpus...')
        self.dlg = dlg
        self.ori = corpus
        self.infile = None
        self.corpus = Corpus(self, {'type' : 'corpus', 'originalpath' : corpus.parametres['originalpath'], 'encoding' : corpus.parametres['encoding']})
        self.last = 0
        self.parametres = parametres
        self.encoding = corpus.parametres['encoding']
        self.corpus.parametres['corpus_name'] = parametres['corpus_name']
        self.corpus.pathout = PathOut(filename = corpus.parametres['originalpath'], dirout = parametres['pathout'])
        self.corpus.pathout.createdir(parametres['pathout'])
        self.corpus.parametres['pathout'] = parametres['pathout']
        self.corpus.parametres['meta'] = parametres.get('meta', False)
        self.corpus.parametres['uuid'] = str(uuid4())
        if parametres.get('frommeta', False) :
            print('make subtexts')
            self.corpus.ucis = [CopyUci(uci) for uci in self.ori.ucis if set(parametres['meta']).intersection(uci.etoiles) != set()]
        elif parametres.get('fromtheme', False) :
            print('make subtexts from theme')
            idpara = 0
            for uci in self.ori.ucis :
                if uci.paras != [] :
                    newuce = []
                    newpara = []
                    for et in uci.paras :
                        if et in parametres['meta'] :
                            newuce += [CopyUce(uce) for uce in uci.uces if uce.para == idpara]
                            newpara.append(et)
                        idpara += 1
                    if newuce != [] :
                        nuci = CopyUci(uci)
                        nuci.uces = newuce
                        nuci.paras = newpara
                        self.corpus.ucis.append(nuci)
                else :
                    idpara += 1
        elif parametres.get('fromclusters', False) :
            self.parametres['uceids'] = [st for i in self.parametres['meta'] for st in self.parametres['lc'][i]]
            self.fromuceids()
        elif parametres.get('fromuceids', False) :
            self.fromuceids()
        #create database
        self.connect()
        self.dobuild()

    def fromuceids(self):
        print('fromuceids')
        dictucekeep = dict(list(zip(self.parametres['uceids'], self.parametres['uceids'])))
        idpara = 0
        for uci in self.ori.ucis :
            if uci.paras == [] :
                keepuces = [CopyUce(uce) for uce in uci.uces if uce.ident in dictucekeep]
                if keepuces != [] :
                    nuci = CopyUci(uci)
                    nuci.uces = keepuces
                    self.corpus.ucis.append(nuci)
                idpara += 1
            else :
                newuces = []
                newpara = []
                for et in uci.paras :
                    keepuces = [CopyUce(uce) for uce in uci.uces if uce.ident in dictucekeepand and uce.para == idpara]
                    idpara += 1
                    if keepuces != [] :
                        newuces += keepuces
                        newpara.append(et)
                if newuces != [] :
                    nuci = CopyUci(uci)
                    nuci.uces = newuces
                    nuci.paras = newpara
                    self.corpus.ucis.append(nuci)

    def read_corpus(self, infile = None):
        self.olduceid = [uce.ident for uci in self.corpus.ucis for uce in uci.uces]
        ident_uci = 0
        ident_uce = 0
        ident_para = -1
        lastpara = -1
        newuceident = {}
        print('redo text, para and st ident')
        for uci in self.corpus.ucis :
            uci.ident = ident_uci
            ident_uci += 1
            for uce in uci.uces :
                uce.uci = uci.ident
                if uce.para != lastpara :
                    ident_para += 1
                    lastpara = uce.para
                    uce.para = ident_para
                else :
                    uce.para = ident_para
                newuceident[uce.ident] = ident_uce
                uce.ident = ident_uce
                ident_uce += 1
        print('backup st text and forms')
        for row in self.ori.getconcorde(self.olduceid) :
            self.c.execute('INSERT INTO uces VALUES(?,?);', (repr(newuceident[row[0]]), row[1]))
            for word in row[1].split() :
                self.corpus.add_word_from_forme(self.ori.formes[word], newuceident[row[0]])
        self.backup_uce()
        print('done')

class BuildFromAlceste(BuildCorpus) :

    def read_corpus(self, infile) :

        if self.dlg is not None :
            self.dlg.Pulse('textes : 0 - segments : 0')
        self.limitshow = 0
        self.count = 1
        if self.corpus.parametres['ucimark'] == 0 :
            self.testuci = testetoile
        elif  self.corpus.parametres['ucimark'] == 1 :
            self.testuci = testint
        txt = []
        iduci = -1
        idpara = -1
        iduce = -1
        try :
            with codecs.open(infile, 'r', self.encoding) as f :
                for linenb, line in enumerate(f) :
                    line = line.rstrip('\n\r')#FIXME .lstrip(codecs.BOM).lstrip(codecs.BOM_UTF8)
                    if self.testuci(line) :
                        iduci += 1
                        if txt != [] :
                            #doc = nlp(' '.join(txt))
                            #print([[word, word.pos_, word.lemma_] for word in doc])
                            iduce, idpara = self.treattxt(txt, iduce, idpara, iduci - 1)
                            txt = []
                            self.corpus.ucis.append(Uci(iduci, line))
                        else :
                            if iduci > 0 :
                                if self.corpus.ucis[-1].uces == [] :
                                    log.info('Empty text : %i' % linenb)
                                    iduci -= 1
                                    self.corpus.ucis.pop()
                            self.corpus.ucis.append(Uci(iduci, line))
                        if self.dlg is not None :
                            if not (iduci + 1) % 10 :
                                self.dlg.Pulse('textes : %i - segments : %i' % (iduci + 1, iduce +1))
                    elif line.startswith('-*') :
                        if iduci != -1 :
                            if txt != [] :
                                iduce, idpara = self.treattxt(txt, iduce, idpara, iduci)
                                txt = []
                            idpara += 1
                            self.corpus.ucis[-1].paras.append(line.split()[0])
                        else :
                            raise Exception('paragrapheOT %i' % linenb)
                    elif line.strip() != '' and iduci != -1 :
                        txt.append(line)
            if txt != [] and iduci != -1 :
                iduce, idpara = self.treattxt(txt, iduce, idpara, iduci)
                del(txt)
            else :
                if iduci != -1 :
                    iduci -= 1
                    self.corpus.ucis.pop()
                    log.info(Exception("Empty text %i" % linenb))
                else :
                    raise Exception('EmptyText %i' % linenb)
            if iduci != -1  and iduce != -1:
                self.backup_uce()
            else :
                log.info(_("No Text in corpus. Are you sure of the formatting ?"))
                raise Exception('TextBeforeTextMark %i' % linenb)
        except UnicodeDecodeError :
            raise Exception("CorpusEncoding")

    def treattxt(self, txt, iduce, idpara, iduci) :
        if self.corpus.parametres.get('ucemethod', 0) == 2 and self.corpus.parametres['douce']:
            txt = 'laphrasepoursplitter'.join(txt)
            txt = self.make_cleans(txt)
            txt = ' '.join([val for val in txt.split() if val not in self.ponctuation_espace])
            ucetxt = txt.split('laphrasepoursplitter')
        else :
            txt = ' '.join(txt)
            txt = self.make_cleans(txt)
            ucetxt = self.make_uces(txt, self.corpus.parametres['douce'])
        if self.corpus.ucis[-1].paras == [] :
            idpara += 1
        for uce in ucetxt :
            iduce += 1
            self.corpus.ucis[-1].uces.append(Uce(iduce, idpara, iduci))
            self.c.execute('INSERT INTO uces VALUES(?,?);', (repr(iduce),uce))
            if not self.tolist :
                uce = uce.split()
            else :
                uce = list(uce)
            for word in uce :
                self.last += 1
                self.corpus.add_word(word)
        log.debug(' '.join([repr(iduci),repr(idpara),repr(iduce)]))
        if self.last > self.lim :
            self.backup_uce()
            self.last = 0
        return iduce, idpara

    def make_uces(self, txt, douce = True, keep_ponct = False) :
        txt = ' '.join(txt.split())
        if douce :
            out = []
            reste, texte_uce, suite = self.decouper(self.prep_txt(txt), self.ucesize + 15, self.ucesize)
            while reste :
                uce = ' '.join([val for val in texte_uce if val not in self.ponctuation_espace])
                if uce != '' :
                    out.append(uce)
                reste, texte_uce, suite = self.decouper(suite, self.ucesize + 15, self.ucesize)
            uce = ' '.join([val for val in texte_uce if val not in self.ponctuation_espace])
            if uce != '' :
                out.append(uce)
            return out
        else :
            return [' '.join([val for val in txt.split() if val not in self.ponctuation_espace])]

#decouper (list_sep)
#make_uces (decouper)
#treat_txt (make_uces)
#read (treat_txt)

class Builder :

    def __init__(self, parent, dlg = None) :
        self.parent = parent
        self.dlg = dlg
        parametres = DoConf(os.path.join(self.parent.UserConfigPath,'corpus.cfg')).getoptions('corpus')
        parametres['pathout'] = PathOut(parent.filename, 'corpus').mkdirout()
        parametres['corpus_name'] = os.path.split(parametres['pathout'])[1]
        parametres['lang'] = self.parent.pref.get('iramuteq','language')
        dial = CorpusPref(parent, parametres)
        dial.CenterOnParent()
        dial.txtpath.SetLabel(parent.filename)
        #dial.repout_choices.SetValue(parametres['pathout'])
        self.res = dial.ShowModal()
        if self.dlg is not None :
            self.dlg = progressbar(self.parent, self.dlg)
        if self.res == 5100 :
            parametres = dial.doparametres()
            parametres['originalpath'] = parent.filename
            PathOut().createdir(parametres['pathout'])
            if parametres.get('dictionary', False) :
                filein = parametres['dictionary']
            else :
                filein = None
            if dial.corpusname.GetValue() != '' :
                parametres['corpus_name'] = dial.corpusname.GetValue()
            dial.Destroy()
            ReadLexique(self.parent, lang = parametres['lang'], filein = filein)
            if parametres['lang'] != 'other' and  os.path.exists(self.parent.DictPath.get(parametres['lang']+'_exp', 'french_exp')):
                self.parent.expressions = ReadDicoAsDico(self.parent.DictPath.get(parametres['lang']+'_exp', 'french_exp'))
            else :
                self.parent.expressions = {}
            self.parametres = parametres
        else :
            dial.Destroy()
            if self.dlg is not None :
                self.dlg.Destroy()

    def doanalyse(self) :
        return BuildFromAlceste(self.parent.filename, self.parametres, self.parent.lexique, self.parent.expressions, dlg = self.dlg).corpus

class SubBuilder :

    def __init__(self, parent, corpus, parametres = None, dlg = None):
        self.parent = parent
        self.ori = corpus
        self.dlg = dlg
        corpus_name = 'Sub' + corpus.parametres['corpus_name']
        if dlg is not None :
            busy = wx.BusyInfo(_("Please wait..."), self)
            wx.SafeYield()
        parametres['corpus_name'] = corpus_name
        if parametres.get('frommeta', False) :
            parametres['meta'] = corpus.make_etoiles()
        elif parametres.get('fromtheme', False) :
            parametres['meta'] = corpus.make_themes()
        elif parametres.get('fromclusters', False) :
            parametres['meta'] = [' '.join(['classe', repr(i)]) for i in range(1,parametres['clnb'] + 1)]
        else :
            parametres['meta'] = []
        if 'fromclusters' not in parametres :
            parametres['meta'].sort()
        if dlg is not None :
            del busy
        dial = SubTextFromMetaDial(parent, parametres)
        self.res = dial.ShowModal()
        if self.res == 5100 :
            if dial.subcorpusname.GetValue() != '' :
                corpus_name = ''.join([l for l in dial.subcorpusname.GetValue() if l.isalnum() or l in ['_']])
            if corpus_name != '' :
                parametres['corpus_name'] = corpus_name
            else :
                parametres['corpus_name'] = 'Sub' + corpus.parametres['corpus_name']
            pathout = os.path.join(corpus.parametres['pathout'], parametres['corpus_name'])
            i = 1
            while os.path.exists(pathout + '_%i' % i) :
                i += 1
            parametres['pathout'] = pathout + '_%i' % i
            meta = dial.m_listBox1.GetSelections()
            if not 'fromclusters' in parametres :
                parametres['meta'] = [parametres['meta'][val] for val in meta]
            else :
                parametres['meta'] = meta
            self.parametres = parametres
            dial.Destroy()
        else :
            dial.Destroy()

    def doanalyse(self):
        return BuildSubCorpus(self.ori, parametres = self.parametres, dlg = self.dlg).corpus

class BuildMergeFromClusters(BuildCorpus):

    def __init__(self, analyses, parametres, dlg = None) :
        log.info('begin subcorpus...')
        self.dlg = dlg
        self.infile = None
        self.corpus = Corpus(self, {'type' : 'corpus', 'originalpath' : 'MergeFromClusters', 'encoding' : 'merge'})
        self.last = 0
        self.analyses = analyses
        self.lcl = []
        self.parametres = parametres
        #self.encoding = corpus.parametres['encoding']
        self.corpus.parametres['corpus_name'] = parametres['corpus_name']
        self.corpus.pathout = PathOut(filename = 'MFC', dirout = parametres['pathout'])
        self.corpus.pathout.createdir(parametres['pathout'])
        self.corpus.parametres['pathout'] = parametres['pathout']
        self.corpus.parametres['meta'] = parametres.get('meta', False)
        self.corpus.parametres['uuid'] = str(uuid4())
        for i, analyse in enumerate(analyses) :
            self.lcl.append([])
            self.analyseid = i
            corpus_uuid = analyse['corpus']
            #if corpus_uuid not in self.parent.history.openedcorpus :
            irapath = parametres['corpusira'][i]
            corpus = Corpus(self, parametres = DoConf(irapath).getoptions('corpus'), read = True)
            ucepath = os.path.join(analyse['pathout'], 'uce.csv')
            corpus.make_ucecl_from_R(ucepath)
            self.ori = corpus
            for j, cl in enumerate(parametres['clusters'][i]) :
               #print cl, self.ori.lc[cl-1]
               self.parametres['uceids'] = self.ori.lc[cl-1]#[st for st in self.ori['lc'][cl-1]]
               self.lcl[i] += self.ori.lc[cl-1]
               self.et = parametres['newet'][i][j]
               self.fromuceids()
        #create database
        self.connect()
        self.dobuild()

    def fromuceids(self):
        print('fromuceids')
        dictucekeep = dict(list(zip(self.parametres['uceids'], self.parametres['uceids'])))
        idpara = 0
        for uci in self.ori.ucis :
            if uci.paras == [] :
                keepuces = [CopyUce(uce) for uce in uci.uces if uce.ident in dictucekeep]
                if keepuces != [] :
                    nuci = CopyUci(uci)
                    nuci.uces = keepuces
                    nuci.etoiles.append(self.et)
                    nuci.analyseid = self.analyseid
                    self.corpus.ucis.append(nuci)
                idpara += 1
            else :
                newuces = []
                newpara = []
                for et in uci.paras :
                    keepuces = [CopyUce(uce) for uce in uci.uces if uce.ident in dictucekeep]
                    idpara += 1
                    if keepuces != [] :
                        newuces += keepuces
                        newpara.append(et)
                if newuces != [] :
                    nuci = CopyUci(uci)
                    nuci.uces = newuces
                    nuci.paras = newpara
                    nuci.etoiles.append(self.et)
                    nuci.analyseid = self.analyseid
                    self.corpus.ucis.append(nuci)
            #print nuci.etoiles, nuci.ident, nuci.uces

    def read_corpus(self, infile = None):
        #self.olduceid = [uce.ident for uci in self.corpus.ucis for uce in uci.uces]
        ident_uci = 0
        ident_uce = 0
        ident_para = -1
        lastpara = -1
        newuceident = {}
        print('redo text, para and st ident')
        for uci in self.corpus.ucis :
            #print uci.ident, ident_uci, [uce.ident for uce in uci.uces], uci.etoiles
            uci.ident = ident_uci
            ident_uci += 1
            for uce in uci.uces :
                uce.uci = uci.ident
                if uce.para != lastpara :
                    ident_para += 1
                    lastpara = uce.para
                    uce.para = ident_para
                else :
                    uce.para = ident_para
                newuceident['%i-%i' %(uci.analyseid, uce.ident)] = ident_uce
                uce.ident = ident_uce
                #print uce.ident
                ident_uce += 1
        print('backup st text and forms')
        rowid = 0
        for i, analyse in enumerate(self.analyses) :
            #print analyse, self.parametres['corpusira']
            irapath = self.parametres['corpusira'][i]
            old = Corpus(self, parametres = DoConf(irapath).getoptions('corpus'), read = True)
            for row in old.getconcorde(self.lcl[i]) :
                self.c.execute('INSERT INTO uces VALUES(?,?);', (newuceident['%i-%i' % (i,row[0])], row[1]))
                for word in row[1].split() :
                    self.corpus.add_word_from_forme(old.formes[word], newuceident['%i-%i' % (i,row[0])])
                rowid += 1
        self.backup_uce()
        print('done')


class MergeClusters :

    def __init__(self, parent, parametres = None, dlg = None):
        self.parent = parent
        #self.ori = corpus
        self.dlg = dlg
        corpus_name = 'MergeFromClusters'
        if dlg is not None :
            busy = wx.BusyInfo(_("Please wait..."), self)
            wx.SafeYield()
        parametres['corpus_name'] = corpus_name
        if dlg is not None :
            del busy
        dial = MergeClusterFrame(parent)
        dial.m_textCtrl4.SetValue(corpus_name)
        self.res = dial.ShowModal()
        if self.res == 5100 :
            self.analyses = {}
            self.clusters = {}
            self.newet = {}
            self.corpusira = {}
            if dial.m_textCtrl4.GetValue() != '' :
                corpus_name = ''.join([l for l in dial.m_textCtrl4.GetValue() if l.isalnum() or l in ['_']])
            if corpus_name != '' :
                parametres['corpus_name'] = corpus_name
            else :
                parametres['corpus_name'] = 'MergeFromClusters'
            for cl in dial.selected :
                corpus_uuid = cl[1]
                #if corpus_uuid not in self.parent.history.openedcorpus :
                irapath = self.parent.history.corpus[corpus_uuid]['ira']
                #corpus = Corpus(self.parent, parametres = DoConf(irapath).getoptions('corpus'), read = True)
                #self.parent.history.openedcorpus[corpus_uuid] = corpus
                if cl[0] not in self.analyses :
                    analyse = DoConf(dial.irapath[cl[0]]).getoptions()
                    #ucepath = os.path.join(os.path.dirname(dial.irapath[cl[0]]), 'uce.csv')
                    #corpus = copycorpus(self.parent.history.openedcorpus[corpus_uuid])
                    #corpus.make_ucecl_from_R(ucepath)
                    self.analyses[cl[0]] = analyse
                    self.clusters[cl[0]] = [cl[2]]
                    self.newet[cl[0]] = [dial.selected[cl]]
                    self.corpusira[cl[0]] = irapath
                else :
                    self.clusters[cl[0]].append(cl[2])
                    self.newet[cl[0]].append(dial.selected[cl])
            analyses = [val for val in self.clusters]
            clusters = [self.clusters[val] for val in analyses]
            self.newet = [self.newet[val] for val in analyses]
            corpusira = [self.corpusira[val] for val in analyses]
            analyses = [self.analyses[val] for val in analyses]
            pathout = os.path.dirname(os.path.dirname(analyses[0]['pathout']))
            self.analyses = analyses
            pathout = os.path.join(pathout, parametres['corpus_name'])
            i = 1
            while os.path.exists(pathout + '_%i' % i) :
                i += 1
            parametres['pathout'] = pathout + '_%i' % i
            self.parametres = parametres
            self.parametres['clusters'] = clusters
            self.parametres['newet'] = self.newet
            self.parametres['corpusira'] = corpusira
            dial.Destroy()
        else :
            dial.Destroy()

    def doanalyse(self):
        return BuildMergeFromClusters(self.analyses, parametres = self.parametres, dlg = self.dlg).corpus

