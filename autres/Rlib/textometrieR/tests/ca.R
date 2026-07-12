table <- read.table("clipboard");
myca <- ca(table)

myca$rowmass
myca$rowdist
myca$rowinertia
myca$rowcoord

myca$colmass
myca$coldist
myca$colinertia
myca$colcoord

plot(myca, dim = c(1,2), map = "symmetric", what = c("all", "all"), mass = c(TRUE, TRUE), contrib = c("relative", "relative"), col = c("#0000FF", "#FF0000"))
mtext("side1", side = 1, line = 2);
mtext("side2", side = 2, line = 2)


table[order(table[ ,1]), ];
plot3d.ca(ca(table, nd=3))
