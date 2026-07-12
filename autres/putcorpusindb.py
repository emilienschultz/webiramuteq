# -*- coding: utf-8 -*-

#------------------------------------
# import des modules python
#------------------------------------
import sqlite3
import codecs
import os
import shelve
from time import time


#------------------------------------
# execution directe,
#definition de fonction,
#encore execution directe
# ???
#------------------------------------

corpus_out = 'corpus.txt'

with codecs.open(corpus_out ,'r', 'utf8') as f:
    content = f.read()
    sep = '\n\n'
    ucis_paras_uces = [[[uce for uce in para.splitlines()] for para in uci.split('$$$')] for uci in content.split(sep)]
print(ucis_paras_uces[0])
#db = 'corpus.db'
#conn = sqlite3.connect(db)
#c = conn.cursor()
#conn.text_factory = str
#c = conn.cursor()
#c.execute('''CREATE TABLE if not exists uce (id INTEGER PRIMARY KEY, iduci INTEGER, idpara INTEGER, content TEXT)''')
#c = conn.cursor()
idpara = -1
iduce = -1
uce_uci_para = {}
para_uci = {}
formes = {}

def addforme(word, formes, iduce) :
    if word in formes :
        formes[word][0] += 1
        if iduce in formes[word][1] :
            formes[word][1][iduce] += 1
        else :
            formes[word][1][iduce] = 1
    else :
        formes[word] = [1, {iduce:1}]

for i, uci in enumerate(ucis_paras_uces) :
    for para in uci :
        idpara += 1
        para_uci[idpara] = i
        for uce in para :
            iduce += 1
            uce_uci_para[iduce] = [i, idpara]
            fileout = os.path.join('uce', '%i.txt' % iduce)
            with open(fileout, 'w') as f :
                f.write(uce)
            uce = uce.split()
            for word in uce :
                addforme(word, formes, iduce)
t1 = time() #chronométrage
d = shelve.open('shelves.db')
d['formes']=formes
d.close()
print(time() - t1) #chronométrage
t2 = time() #chronométrage
d = shelve.open('shelves.db')
formes = d['formes']
d.close()
print(time() - t2) #chronométrage
t3 = time() #chronométrage
word = formes['les']
ucis = [uce_uci_para[iduce][0] for iduce in word[1]]
word[0]
print(time() - t3) #chronométrage

#c.execute('INSERT INTO uce values (?, ?, ?, ?)', (iduce, i, idpara, uce))
#conn.commit()
