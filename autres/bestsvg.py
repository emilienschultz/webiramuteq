# -*- coding: utf-8 -*-
# usage ?

#------------------------------------
# import des modules python
#------------------------------------
from optparse import OptionParser


parser = OptionParser()
parser.add_option("-f", "--file", dest="filename",
                  help="open FILE", metavar="FILE", default=False)
parser.add_option("-b", "--whiteblack", dest='b', default=False, action='store_true')

(options, args) = parser.parse_args()

with open(options.filename, 'r') as f :
    content = f.read()

def correct_police(content) :
    return content.replace('Arial Black','Arial')

content = correct_police(content)

def inverse_b_nb(content) :
    return content.replace('#000000','#NOIRNOIRNOIR').replace('#ffffff','#000000').replace('#NOIRNOIRNOIR','#ffffff')

if options.b :
    content = inverse_b_nb(content)


with open(options.filename, 'w') as f :
    f.write(content)