#chd.R
source('%s')
source('%s')
source('%s')
source('%s')
classif.mode <- %i
file.data1 <- '%s'
file.data2 <- '%s'
file.listuce1 <- '%s'
file.listuce2 <- '%s'
file.uce <- '%s'
mincl <- %i
graph.arbre1 <- '%s'
graph.arbre2 <- '%s'
graph.dendro1 <- '%s'
graph.dendro2 <- '%s'
data.out <- %s

data1<-read.csv2(file.data1, header = FALSE)
    
if (classif.mode == 0) {
    data2<-read.csv2(file.data2, header = FALSE)
}        
chd1<-CHD(data1)
    
if (classif.mode == 0) {
    chd2<-CHD(data2)
} else {
    chd2<-chd1
}
    
#lecture des uce
listuce1<-read.csv2(file.listuce1)

if (classif.mode == 0) {
    listuce2<-read.csv2(file.listuce2)
}

rm(data1)

if (classif.mode == 0) rm(data2)

chd.result <- Rchdtxt(file.uce,mincl=mincl,classif_mode=classif.mode)
n1 <- chd.result$n1
classeuce1 <- chd.result$cuce1
classeuce2 <- chd.result$cuce2

tree.tot1 <- make_tree_tot(chd1)
open_file_graph(graph.arbre1, widt = 600, height=400)
plot(tree.tot1$tree.cl)
dev.off()

if (classif.mode == 0) {
    tree.tot2 <- make_tree_tot(chd2)
    open_file_graph(graph.arbre2, width = 600, height=400)
    plot(tree.tot2$tree.cl)
    dev.off()
}          
tree.cut1 <- make_dendro_cut_tuple(tree.tot1$dendro_tuple, chd.result$coord_ok, classeuce1, 1)
classes<-n1[,9]
open_file_graph(graph.dendro1, width = 600, height=400)
plot.dendropr(tree.cut1$tree.cl,classes)
dev.off()

if (classif.mode == 0) {
    tree.cut2 <- make_dendro_cut_tuple(tree.tot2$dendro_tuple, chd.result$coord_ok, classeuce2, 2)
    open_file_graph(graph.dendro2, width = 600, height=400)
    plot(tree.cut2$tree.cl)
    dev.off()
} 
save.image(file=data.out)  
  
  
(RscriptPath['CHD'], RscriptPath['chdtxt'], RscriptPath['anacor'], RscriptPath['Rgraph'])
  
    """ % DicoPath['TableUc1']
  
        """ % DicoPath['TableUc2']
""" % DicoPath['listeuce1']

    """ % DicoPath['listeuce2']
""" % (DicoPath['uce'], mincl, classif_mode)
"""%DicoPath['arbre1']
    """ %DicoPath['arbre2']  
""" % DicoPath['dendro1']
    """ % DicoPath['dendro2']
% DicoPath['RData']
