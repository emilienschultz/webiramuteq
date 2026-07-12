f <- file(description = "cgt75.splitted.txt", open = "r", blocking = TRUE, encoding = "latin1");
cgt75 <- readLines(f, n = -1, ok = TRUE, warn = TRUE);
# i <- grep("\\.", cgt75);
# get.contexts(factor(cgt75, ".");
