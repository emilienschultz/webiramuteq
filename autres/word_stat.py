# -*- coding: utf-8 -*-
#Author: Pierre Ratinaud
#Copyright (c) 2008-2020 Pierre Ratinaud
#Lisense: GNU/GPL



def make_word_stat(corpus, listin) :
    ducis = {}
    duces={}
    huces = []
    for lem in listin :
        guces = []
        for word in corpus.lems[lem] :
            print(word, 'nb d\'uce avec:', len(corpus.formes[word][1]), 'eff tot:',sum([corpus.formes[word][1][val] for val in corpus.formes[word][1]]))
            uces = [val for val in corpus.formes[word][1]]
            print(word, len(uces), 'uces')
            print(word, len(list(set([val[0] for val in uces]))), 'ucis')
            guces += uces
        huces.append(set(guces))
        print('lem', lem, len(set(guces)), 'uces')
        print('lem', lem, len(set([val[0] for val in set(guces)])), 'ucis')
    inter = set(huces[0]).intersection(huces[1])#.intersection(huces[2])
    print('intersection:', len(list(set(inter))), 'uces')
    inter2 = set([val[0] for val in huces[0]]).intersection([val[0] for val in huces[1]])#.intersection([val[0] for val in huces[2]]) 
    print('intersection:', len(list(set(inter2))), 'ucis')
