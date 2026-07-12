from corpus import *
from functions import DoConf

corpus_encodage = 'cp1252'
corpus_in = '/home/pierre/fac/identite/identite_sans_doublons_ok_corpus_6/Corpus/corpus.cira'

corpus_parametres = DoConf('/home/pierre/.iramuteq/corpus.cfg').getoptions('corpus')
corpus_parametres['filename'] = self.filename
corpus_parametres['encoding'] = corpus_encodage
corpus_parametres['syscoding'] = 'utf8'
#corpus = BuildFromAlceste(self.filename, corpus_parametres, self.lexique, self.expressions).corpus
                #with codecs.open(self.filename, 'r', self.corpus_encodage) as f:
corpus = Corpus(self, parametres = {'filename': corpus_in, 'syscoding': 'utf8'}, read = corpus_in)

corpus.conn_all()

etoiles = ['*date_0211','*date_0311', '*date_0411', '*date_0511', '*date_0611', '*date_0711']
corpus.read_corpus()
corpus.make_lems()
actives = corpus.make_actives(450)
corpus.make_and_write_sparse_matrix_from_uces(actives, 'mm.mm')
ucesize = corpus.getucesize()
float(sum(ucesize)/len(ucesize)
actives = corpus.make_actives(10)
#ucesize = corpus.make_uceactsize(actives)
#uc1, uc2 = corpus.make_uc(actives, 25, 27)
corpus.make_and_write_sparse_matrix_from_uc(actives, 25, 27, 'uc1.mm', 'uc2.mm')
tab = corpus.make_lexitable(100, etoiles)
