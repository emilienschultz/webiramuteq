\name{specificites}
\alias{specificites}

\title{ Compute specificites association score }
\description{

 Compute specifities association score, i.e. an indicator of the association
 between tokens and sub-corpus, given a lexical table

}
\usage{
specificites(lexicaltable, types=NULL, parts=NULL)
}

\arguments{

  \item{lexicaltable}{ a complete lexical table, i.e. a numeric matrix where
  each line is a token and each column a part of a corpus. Each cell give the
  frequency of the given token in the corresponding part of the corpus. }

  \item{types}{ Indicate for which rows the specificity index must be computed.
  If \code{NULL}, the specificity index is computed for every form. If
  \code{types} is a character vector, it indicates the name of the row of
  \code{lexicaltable} to be used (an error is thrown if \code{clt} has no row
  names). If it is an integer vector, it indicates the index of the row to be
  used.}

  \item{parts}{ Indicate for which columns the specificity index must be computed.
  If \code{NULL}, the specificity index is computed for every part. If
  \code{parts} is a character vector, it indicates the name of the columns of
  \code{lexicaltable} to be used (an error is thrown if \code{clt} has no
  column names). If it is an integer vector, it indicates the index of the
  column to be used.}

}

\value{
  
The fonction return a matrix of \code{nrow(clt) * ncol(clt)} (the number of
rows and columns may be reduced using \code{types} or \code{parts}), each cell
giving the frequency index.

}

\references{
  Lafon P. (1980) Sur la variabilit \' e de la fr \' e quence des formes dans un corpus,
  Mots, 1, pp. 127--165.
}

\author{Sylvain Loiseau}

\seealso{ \code{\link{specificites.probabilities}}, \code{\link{specificites.lexicon}} }

\examples{
data(robespierre);
specificites(robespierre);
specificites(robespierre, types="peuple", parts=c("D9", "D10"));
}
