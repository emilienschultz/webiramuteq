de         <- c(464, 165, 194, 392, 398, 235, 509, 96, 58, 662);
peuple     <- c(45,   18,  15,  14,  53,  30,  42, 16,  4, 59 );
republique <- c(35,   10,  16,  29,  29,   9,  21, 14,  2, 42 );
ennemi     <- c(30,   13,  11,  19,  22,  10,  16,  7,  2, 35 );
patrie     <- c(6,     5,  16,   8,  23,  10,  35,  8,  3, 39 );

robespierre <- matrix(c(de, peuple, republique, ennemi, patrie, rep(0, 10)), nrow=6, byrow=TRUE)
tokens <- c("de", "peuple", "republique", "ennemi", "patrie");
rownames(robespierre) <- c(tokens, "others");
colnames(robespierre) <- paste("D", 1:10, sep="");

partSize <- c(8395, 2558, 3920, 6903, 7896, 4555, 10142, 2063, 1084, 13933);
robespierre[6,] <- partSize - colSums(robespierre);

rm(list=c(tokens, "partSize"));
rm("tokens");

