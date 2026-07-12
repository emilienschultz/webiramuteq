#!/bin/env python
# -*- coding: utf-8 -*-
#Author: Pierre Ratinaud

#a simple treetagger parser
import codecs
import time
import re
from functions import ReadDicoAsDico
from itertools import izip, chain

t1 = time.time()
#infile = '/home/pierre/prog/treetagger/cmd/allenglish.txt'

infile = '/home/pierre/fac/cablegate/cablestagger.txt'
word_list = '/home/pierre/fac/cablegate/liste_de_mots.csv'
actives_list = '/home/pierre/fac/cablegate/actives.csv'
supps_list = '/home/pierre/fac/cablegate/supplementaires.csv'


def prepare_for_treetagger(corpus, parent) :
    fileout = '/home/pierre/workspace/iramuteq/corpus/corpus_pour_tt.txt'
    corpus.quick_clean1()
    lang = corpus.parametre['lang']
    dico_path = parent.DictPath.get(lang + '_exp', 'french_exp')
    expressions = ReadDicoAsDico(dico_path)
    corpus.find_expression(expressions)
    #corpus.content = re.sub(u'[-]+', ' ', corpus.content)
    corpus.content = re.sub(u'[ ]+', ' ', corpus.content)
    #FIXME : remplacer . par ' . '
    #corpus.quick_clean2()
    with open(fileout, 'w') as f :
        f.write(corpus.content)

def partition(alist, indices):
    pairs = izip(chain([0], indices), chain(indices, [None]))
    return (alist[i:j] for i, j in pairs)

def partition_uci(uci) :
    if uci == [] :
        pass
    else :
        indices = [i for i, forme in enumerate(uci) if forme[0].startswith(u'*')]
        pairs = izip(chain([0], indices), chain(indices, [None]))
        return (uci[i,j] for i, j in pairs)

def dodict(inlist, indict) :
    for i, forme in enumerate(inlist) :
        if tuple(forme) in tot :
            tot[tuple(forme)].append(i)
        else :
            tot[tuple(forme)] = [i]

def treat_forme(forme, tformes) :
    ponct =[u',', u'', u'``', u"''", u':', u'#', u')', '(', u'!', u'?', u';', u'-', u'.', u'...']
    if forme[0] in ponct :
        return forme[0]
    tforme = (forme[0], forme[1].split(':')[0])
    return tformes[tforme]

def make_formes_and_lems(inlist) :
    formes = {}
    tformes = {}
    formes_lems = {}
    lems = {}
    for forme in inlist :
        word = forme[0]
        gram = forme[1].split(':')[0]
        lem = forme[2]
        tforme = (word,gram)
        if tforme in tformes :
            if formes_lems[tformes[tforme]] == u'<unknown>' and lem != u'<unknown>' :
                formes_lems[tformes[tforme]] = lem
        else :
            if word in formes :
                nword = u'@'.join([word,''])
                while nword in formes and formes[nword] != gram :
                    nword = u'@'.join([nword,''])
                formes[nword] = [0, {}, gram, len(formes)]
                tformes[tforme] = nword
                formes_lems[nword] = lem
            else :
                formes[word] = [0, {}, gram, len(formes)]
                tformes[tforme] = word
                formes_lems[word] = lem
    for forme in formes :
        if formes_lems[forme] == u'<unknown>' :
            formes_lems[forme] = forme
        if formes_lems[forme] in lems :
            lems[formes_lems[forme]].append(forme)
        else :
            lems[formes_lems[forme]] = [forme]
    del formes_lems
    return formes, lems, tformes 

def make_ucis_txt_formes_from_tt(corpus, tformes) :
    ucis_txt = [[treat_forme(forme, tformes) for forme in uci] for uci in corpus.ucis_txt]
    del tformes
    return [' '.join(uci) for uci in ucis_txt]
    
def get_ucis_from_tt(corpus) :
    content_split = [tuple(line.split('\t')) for line in corpus.content.splitlines()]
    #print [i for i, line in enumerate(content_split) if line[0] == u'****']
    ponct =[u',', u'', u'``', u"''", u':', u'#', u')', '(', u'!', u'?', u';', u'-', u'.', u'...']
    lformes = [forme for forme in list(set(content_split)) if not forme[0].startswith(u'*') and forme[0] not in ponct] 
    formes, lems, tformes = make_formes_and_lems(lformes)
    ucis = partition(content_split, [i for i, line in enumerate(content_split) if line[0] == u'****'])
    del content_split
    ucis = [uci for uci in ucis]
    ucis.pop(0)
    indices_max_et = [max([i for i, forme in enumerate(uci) if forme[0].startswith(u'*')]) for uci in ucis]
    corpus.ucis = [uci[:indices_max_et[i] + 1] for i, uci in enumerate(ucis)]
    corpus.ucis = [[[et[0] for et in uci],''] for uci in corpus.ucis]
    corpus.ucis_txt = [uci[indices_max_et[i] + 1:] for i, uci in enumerate(ucis)]
    del ucis
    corpus.formes = formes
    corpus.lems = lems
    return make_ucis_txt_formes_from_tt(corpus, tformes)

#with codecs.open(infile, 'r', 'latin1') as f :
#    #content = [line.split('\t') for line in f]
#    content = f.read()
#print time.time() - t1
#print(u'#1')
#c1 = content.splitlines()
#print(u'#1b')
#c1s = [val.split('\t') for val in c1]
#print('#2')
#sc1 = list(set(c1))
#print('#3')
#sc1 = [val.split('\t') for val in sc1]
#print len(sc1)
#print('#4')
#formes = [val for val in sc1 if not val[0].isdigit()]
#print len(formes)
#print('#5')
#sformes = [val[0] for val in formes]
#print len(sformes)
#print('#6')
#
#t4 = time.time()
#def make_dicts(inlist) :
#    tot = {}
#    totgram = {}
#    for i, forme in enumerate(inlist) :
#        if tuple(forme) in tot :
#            tot[tuple(forme)].append(i)
#        else :
#            tot[tuple(forme)] = [i]
#        if forme[1] in totgram :
#            totgram[forme[1]] += 1
#        else :
#            totgram[forme[1]] = 1
#    return tot, totgram
#tot, totgram = make_dicts(c1s)
#print 'dico', time.time() - t4
#
#def load_keys() :
#    key_file = '/home/pierre/fac/cablegate/keys_english.txt'
#    with open(key_file, 'r') as f :
#        keys = f.read()
#    keys = keys.splitlines()
#    keys = [line.split('\t') for line in keys]
#    return keys
#
#keys = load_keys()
#print keys
#kact = [key[0] for key in keys if key[2] == '1']
#ksup = [key[0] for key in keys if key[2] == '2']
#
#actives = [[len(tot[forme]), forme[0], forme[1], forme[2]] for forme in tot if forme[1] in kact and len(tot[forme]) > 3]
#actives.sort()
#supps = [[len(tot[forme]), forme[0], forme[1], forme[2]] for forme in tot if forme[1] in ksup and len(tot[forme]) > 3]
#supps.sort()
#
#words = [[len(tot[word]), word[0], word[1], word[2]] for word in tot]
#words.sort()
##hapax = [word for word in words if word[3] == 1]
##print len(hapax)
#def print_list(thelist, fileout) :
#    with open(fileout, 'w') as f :
#        f.write('\n'.join(['\t'.join(['\t'.join(list(line[1:])), `line[0]`]) for line in thelist]).encode('latin1'))
#print_list(words, word_list)
#print_list(actives, actives_list)
#print_list(supps, supps_list)
#print time.time() - t4
#t5 = time.time()
#print('#7')
#def make_uci(c1s) :
#    return [val.tolist() for val in numpy.split(numpy.array(c1s),[i for i, line in enumerate(c1s) if line[0] == u'****'])] 
#
##def make_ucil(c1s) :
#from itertools import izip, chain
#def partition(alist, indices):
#    pairs = izip(chain([0], indices), chain(indices, [None]))
#    return (alist[i:j] for i, j in pairs)
#
#def partition_uci(uci) :
#    if uci == [] :
#        pass
#    else :
#        indices = [i for i, forme in enumerate(uci) if forme[0].startswith(u'*')]
#        pairs = izip(chain([0], indices), chain(indices, [None]))
#        return (uci[i,j] for i, j in pairs)
#
##ucis = make_uci(c1s)
#t2 = time.time()
#ucis = partition(c1s, [i for i, line in enumerate(c1s) if line[0] == u'****'])
#print time.time() - t2
#print('#8')
#print ucis
##for uci in ucis :
##    if uci != []:
##        print max([i for i, forme in enumerate(uci) if forme[0].startswith(u'*')])
#
#ucis = [uci for uci in ucis]
#ucis.pop(0)
#indices_max_et = [max([i for i, forme in enumerate(uci) if forme[0].startswith(u'*')]) for uci in ucis]
##ucis2 = [partition_uci(uci) for uci in ucis]
##print len(ucis2)
#print len(indices_max_et)
#print'#9'
##print ucis2[0:2]
#etoiles = [uci[:indices_max_et[i] + 1] for i, uci in enumerate(ucis)]
#ucis = [uci[indices_max_et[i] + 1:] for i, uci in enumerate(ucis)]
#print len(etoiles)
#print etoiles[0]
#print('#10')
#t3 = time.time()
##ucis = [[val for val in uci if val[1] != 'PUN'] for uci in ucis]
#ind_sent = [[i for i, forme in enumerate(uci) if forme[1] == 'SENT'] for uci in ucis]
#print time.time() - t3
#print ind_sent[0]
#print len(ucis), len(ind_sent)
##inuformes = [i for i,forme in enumerate(sformes) if sformes.count(forme) > 1]
##inuformes = [formes[i] for i, forme in enumerate(sformes) if forme in sformes[i+1:]]
##nonunique = [forme for forme in formes if formes.count(forme) > 1]
#print('#10')
#split_sents = [[partition(uci, ind_sent[i])] for i, uci in enumerate(ucis)]
#PUNCT = [u',', u'', u'``', u"''", u':', u'#', u')', '(', u'!', u'?', u';', u'-', u'.']
#split_sents = [[val for sent in uci for val in sent] for uci in split_sents]
#split_sents = [[val for sent in uci for val in sent if val[0] not in PUNCT and not val[0].isdigit()] for uci in split_sents]
##for i in range(0,1) :
##    for sent in split_sents[i] :
##        for val in sent :
##            print val
##nuformes = [formes[i] for i in inuformes]
##print('#8')
#
##print double
#print totgram
