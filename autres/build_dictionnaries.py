# -*- coding: utf-8 -*-
#Author: Pierre Ratinaud
# usage ?

#------------------------------------
# import des modules python
#------------------------------------
import codecs
import os
from time import time
import re
from subprocess import *
import sys, string
from xml.dom import minidom, Node


txtdir = '/home/pierre/workspace/iramuteq/dev/langues/italian'
encodage = 'macroman'
treetagger = '/home/pierre/prog/treetagger/cmd/tree-tagger-italian-utf8'
fileout = '/home/pierre/workspace/iramuteq/dev/langues/lexique_it_t1.txt'
stopword = '/home/pierre/workspace/iramuteq/dev/langues/IT_NEW_stopwords_utf8.txt'
lexique = '/home/pierre/workspace/iramuteq/dev/langues/lexique_it.txt'
xmlfile = '/home/pierre/workspace/iramuteq/dev/langues/itwiki-latest-pages-articles.xml'


import xml.sax

class WikiPediaHandler(xml.sax.ContentHandler):
    def __init__(self, sparser) :
        self.txt = False
        self.totreat = []
        self.tottitle = 0
        self.diff = 0
        self.last = 0
        self.sparser = sparser 

    def startElement(self, name, attrs):
        if self.diff > 1000 :
            self.sparser.treat_formes()
            self.last = len(self.sparser.formes)
            self.diff = 0
        if name == 'title' :
            self.tottitle += 1
            if len(self.totreat) > 100000 :
                self.diff = len(self.sparser.formes) - self.last
                self.sparser.doparsewiki(' '.join(self.totreat))
                self.totreat = []
                print 'titres :', self.tottitle
        if name == 'text' :
            self.txt = True
        else :
            self.txt = False
        #if name == "title":
        #    for item in attrs.items():
        #        print item
    def characters(self, content) :
        if self.txt :
            self.totreat.append(content)

class Parser :
    def __init__(self, txtdir, encodage, treetagger, fileout) :
        self.txtdir = txtdir
        self.encodage = encodage
        self.tt = treetagger
        self.formes = {}
        self.fileout = fileout
        #self.doparse()
        #self.treat_formes(fileout)

    def clean(self, txt) :
        txt = txt.lower()
        keep_caract = u"a-zA-Z0-9àÀâÂäÄáÁéÉèÈêÊëËìÌîÎïÏòÒôÔöÖùÙûÛüÜçÇß’ñ.:,;!?\n*'_-"
        list_keep = u"[^" + keep_caract + "]+"
        txt = re.sub(list_keep, ' ', txt)
        txt = txt.replace(u'’',u"'")
        txt = txt.replace(u'\'',u' ').replace(u'-', u' ')
        txt = txt.replace(u'?',u' ? ').replace(u'.',u' . ').replace(u'!', u' ! ').replace(u',',u' , ').replace(u';', u' ; ').replace(u':',u' : ')
        txt = ' '.join(txt.split())
        return txt

    def update_dict(self, tmpfile) :
        with codecs.open(tmpfile, 'r', 'utf8') as f :
            content = f.read()
        content = [line.split('\t') for line in content.splitlines()]
        for forme in content :
            if (forme[2] == u'<unknown>') or (forme[1] in [u'PON', u'<unknown>', u'SYM', u'SENT']) or (forme[1]==u'NUM' and forme[2]==u'@card@') :
                pass
            elif (forme[0], forme[1]) in self.formes :
                self.formes[(forme[0], forme[1])][0] += 1
            else :
                self.formes[(forme[0], forme[1])] = [1, forme[2]]
        print len(self.formes)

    def treat_formes(self) :
        print 'treat_formes'
        nformes= {}
        for forme in self.formes :
            if forme[0] in nformes :
                if self.formes[forme][0] > nformes[forme[0]][0] :
                    nformes[forme[0]] = [self.formes[forme][0], forme[1], self.formes[forme][1]]
            else :
                nformes[forme[0]] = [self.formes[forme][0], forme[1], self.formes[forme][1]]
        with open(self.fileout, 'w') as f :
            toprint = [[forme, nformes[forme][1], nformes[forme][2], `nformes[forme][0]`] for forme in nformes]
            toprint = sorted(toprint)
            toprint = '\n'.join(['\t'.join(line) for line in toprint])
            f.write(toprint.encode('utf8'))
        print len(nformes)

    def doparsewiki(self, content) :
        content = self.clean(content)
        with open('/tmp/tmptxt', 'w') as f :
            f.write(content.encode('utf8'))
        p1 = Popen(['cat', '/tmp/tmptxt'], stdout = PIPE)
        with open('/tmp/tttmp', 'w') as f :
            p2 = Popen([treetagger], stdin = p1.stdout, stdout = f)
            out = p2.communicate()
        self.update_dict('/tmp/tttmp')

    def doparse(self):
        files = os.listdir(self.txtdir)
        for fpath in files :
            fpath = os.path.join(self.txtdir, fpath)
            print fpath
            with codecs.open(fpath, 'r', self.encodage) as f : 
                content = f.read()
            content = self.clean(content)
            with open('/tmp/tmptxt', 'w') as f :
                f.write(content.encode('utf8'))
            p1 = Popen(['cat', '/tmp/tmptxt'], stdout = PIPE)
            with open('/tmp/tttmp', 'w') as f :
                p2 = Popen([treetagger], stdin = p1.stdout, stdout = f)
                out = p2.communicate()
            self.update_dict('/tmp/tttmp')


class PostTreat :
    def __init__(self, infile, outfile, stopw = None) :
        self.dictg = {}
        with codecs.open(infile, 'r', 'utf8') as f :
            content = f.read()
        content = [line.split('\t') for line in content.splitlines()]
        content = [self.treatline(line) for line in content if line[3] != '1']
        self.formes = {}
        self.lems = {}
        if stopw is not None :
            with codecs.open(stopw, 'r', 'utf8') as f :
                stw = f.read()
            self.stw = stw.splitlines()
            content = self.dostopword(content)
        self.printcontent(content, outfile)
        self.dictg = {}
        for forme in self.formes :
            self.dictg[self.formes[forme][2]] = self.dictg.get(self.formes[forme][2],0) + 1
        print self.dictg
        print content[0:10]
        print len(content)
    
    def treatline(self, line) :
        gram = line[1].split(u':')[0].lower()
        self.dictg[gram] = self.dictg.get(gram, 0) + 1
        return [line[0], line[2], gram, int(line[3])]

    def dostopword(self, content) :
        for line in content :
            self.formes[line[0]] = line
            self.lems[line[1]] = line
        for word in self.stw :
            if word in self.formes :
                print word, self.formes[word]
                if self.formes[word][2] in ['adj','adv','ver','nom'] :
                    self.formes[word][2] = self.formes[word][2] + '_sup'
                    print self.formes[word]
            else :
                self.formes[word] = [word, word, 'sw', 0]
        return sorted([[forme, self.formes[forme][1], self.formes[forme][2]] for forme in self.formes])

    def printcontent(self, content, outfile) :
        with open(outfile, 'w') as f :
            f.write('\n'.join(['\t'.join(line) for line in content]).encode('utf8'))
            



#sparser = Parser('', encodage, treetagger, fileout)
#parser = xml.sax.make_parser()
#parser.setContentHandler(WikiPediaHandler(sparser))
#parser.parse(open(xmlfile,"r"))
##Parser(txtdir, encodage, treetagger, fileout)
PostTreat(fileout, lexique, stopword)
            


