# -*- coding: utf-8 -*-
#Author: Pierre Ratinaud
#Copyright (c) 2008-2020 Pierre Ratinaud
#License: GNU/GPL

#------------------------------------
# import des modules python
#------------------------------------
import os
import codecs
import sys
import re

#------------------------------------
# import des modules wx
#------------------------------------
import wx
import wx.lib.sized_controls as sc
import wx.lib.filebrowsebutton as filebrowse

#------------------------------------
# import des fichiers du projet
#------------------------------------
from html.parser import HTMLParser


htmldir = 'dev/factiva_html'


class MyHTMLParser(HTMLParser):

    def __init__(self) :
        HTMLParser.__init__(self)
        self.recording = 0
        self.data = []
        self.need = True
        self.author = False
        self.start = False
        self.text = False
        self.count = 0

    def handle_starttag(self, tag, attrs):
        self.need=True
        if tag not in ['div', 'p', 'b'] :
            self.need=False
            self.text = False
            return
        else :
            print(attrs)
            self.need = True
            if tag == 'div' :
                if attrs != [] :
                    tagtype = attrs[0][0]
                    tagname = attrs[0][1].split()
                    if tagtype == 'class' and tagname[0] == 'article' :
                        self.author = False
                        self.start = True
                        self.count = 0
                        self.data.append([])
                    elif tagtype == 'class' and tagname[0] == 'author' :
                        self.author = True
            if tag == 'p' :
                if attrs != [] :
                    tagtype = attrs[0][0]
                    tagname = attrs[0][1].split()
                    if tagtype == 'class' and tagname[0] == 'articleParagraph' :
                        self.text = True
            if tag == 'b' :
                self.text = True
            return

    def handle_data(self, data) :
        #print data.encode('utf-8')
        if self.need :
            #print data.encode('utf-8')
            if self.start :
                pass
                #print 'data', data.encode('utf8')
            if self.author :
                if self.count < 7 :
                    self.data[-1].append(data)
                    self.count += 1
                else :
                    self.author = False
            elif self.text :
                if self.count == 2 and not self.author :
                    self.data[-1].append('PAS DAUTEUR')
                    self.count += 1
                    self.data[-1].append(data)
                else :
                    self.count += 1
                    self.data[-1].append(data)
    #    print "Encountered a start tag:", tag
    #def handle_endtag(self, tag):
    #    print "Encountered an end tag :", tag
    #def handle_data(self, data):
    #    print "Encountered some data  :", data

# execution en direct ???
files = os.listdir(htmldir)
parser = MyHTMLParser()
for f in files :
    f= os.path.join(htmldir, f)
    with codecs.open(f, 'r', 'utf8') as infile :
        content = infile.read()
parser.feed(content)
out = [[' '.join(['****','*date_'+art[4].replace(' ','_'),'*s_'+art[5].replace(' ','_')]), ' '.join(art[10:len(art)-1])] for art in parser.data]
for i in range(0,8):
    print(parser.data[i])
out = [' '.join(art) for art in out]
print('\n\n\n'.join(out))
