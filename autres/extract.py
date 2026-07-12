# -*- coding: utf-8 -*-
#Author: Pierre Ratinaud
#Copyright (c) 2008-2020 Pierre Ratinaud
#License: GNU/GPL


import codecs
import os
import sys
reload(sys)
import locale
sys.setdefaultencoding(locale.getpreferredencoding())

#chemin du fichier
corpus_file = '/home/pierre/fac/lerass/debat/debat_ppoira.txt'
#encodage : cp1252 sous windows
enc = 'utf8'
#la variable
variable = u'*loc'

with codecs.open(corpus_file, 'r', enc) as f :
    content = f.read()
content = content.splitlines()


def make_ucis(content) :
    ucis = [[content[i].strip().split(),i] for i in range(0,len(content)) if content[i].startswith(u'****')]
    return ucis, [a[1] for a in ucis]

def make_lines(content,ucinb) :
    return [[ucinb[i]+1,ucinb[i+1]] for i in range(0,len(ucinb)-1)] + [[ucinb[len(ucinb)-1] + 1,len(content)]]
def make_ucis_txt(content, lines):
    return [' '.join(content[l[0]:l[1]]) for l in lines]

def make_etoile(ucis) :
    etoiles = [uci[0][1:] for uci in ucis]
    return etoiles
    
def make_unique_etoiles(etoiles) :
    uetoiles = list(set([etoile for uci in etoiles for etoile in uci]))
    return uetoiles

def treat_var_mod(variables) :
    var_mod = {}
    for variable in variables :
        if u'_' in variable :
            forme = variable.split(u'_')
            var = forme[0]
            mod = forme[1]
            if not var in var_mod :
                var_mod[var] = [variable]
            else :
                if not mod in var_mod[var] :
                    var_mod[var].append(variable)
    return var_mod


def extract_uci(variable, var_mod, ucis_txt, etoiles) :
    for et in var_mod[variable] :
        #et = '_'.join([variable,mod])
        tojoin = ['\n'.join([' '.join([u'****']+etoiles[i]), uci]) for i, uci in enumerate(ucis_txt) if et in etoiles[i]]
        with open(et[1:]+'.txt', 'w') as f :
            f.write('\n\n'.join(tojoin))
        print et[1:]+'.txt'
        
ucis,ucisnb = make_ucis(content)
etoiles = make_etoile(ucis)
uetoiles = make_unique_etoiles(etoiles)
var_mod = treat_var_mod(uetoiles)
lines = make_lines(content, ucisnb)
ucis_txt = make_ucis_txt(content, lines)
extract_uci(variable, var_mod, ucis_txt, etoiles)
print 'ok'
