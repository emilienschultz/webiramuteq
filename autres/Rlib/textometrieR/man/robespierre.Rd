\name{robespierre}
\alias{robespierre}
\docType{data}
\title{ Robespierre's discourses }
\description{
  A lexical table containing the frequencies of 5 words in 9 Robespierre public
  discourses (between november 1793 and july 1794).
}
\usage{data(robespierre)}
\format{
  The format is:
 num [1:6, 1:10] 464  45  35  30   6 ...
 - attr(*, "dimnames")=List of 2
  ..$ : chr [1:6] "de" "peuple" "republique" "ennemi" ...
  ..$ : chr [1:10] "D1" "D2" "D3" "D4" ...
}
\details{

  The last line of the table give the total frequency of all the other forms in
  each of these discourses.

}
\source{

  Lafon P. (1980) Sur la variabilit \' e de la fr \' e quence des formes dans un corpus, Mots, 1, pp. 127--165.

}
\references{

  Lafon P. (1980) Sur la variabilit \' e de la fr \' e quence des formes dans un corpus, Mots, 1, pp. 127--165.

}
\examples{
data(robespierre)

## See graphic in Lafon, 1980 : 140

t <- colSums(robespierre)["D9"];     # size of the part
T <- sum(robespierre);             # size of the corpus
f <- rowSums(robespierre)["peuple"]; # total frequency of "peuple"
p <- dhyper(1:15, f, T-f, t)
plot(p, type="h", main="Probabilities of various frequencies of 'peuple' in discourse 'D9'", xlab="Frequency of 'peuple'", ylab="Prob(k)");

}
\keyword{datasets}
