library(textometrieR);
sublexicon <- c(1, 2, 1, 3, 2, 1);
names(sublexicon) <- c("A", "D", "G", "J", "B", "C");

lexicon <- c(1, 2, 1, 3, 2, 1, 2, 2, 2, 2, 1, 3, 4);
names(lexicon) <- LETTERS[1:length(lexicon)];

specificites.lexicon.new(lexicon, sublexicon);
