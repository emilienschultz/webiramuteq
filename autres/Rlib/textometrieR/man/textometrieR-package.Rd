\name{textometrieR-package}
\alias{textometrieR-package}
\alias{textometrieR}
\docType{package}
\title{
Statistical exploration of textual corpora
}
\description{
Statistical exploration of textual corpora using several methods
from french 'lexiometrie' and french 'Data Analysis' schools. It includes
methods for exploring irregularity of distribution of lexicon (or other
features) accross parts of texts; multidimensionnal exploration ('Analyse
des correspondances'), etc.
}
\details{
\tabular{ll}{
Package: \tab textometrieR\cr
Type: \tab Package\cr
Version: \tab 1.0\cr
Date: \tab 2009-01-18\cr
License: \tab GPLv3\cr
Depends: \tab R (>= 2.5.0)\cr
Packaged: \tab Thu Mar 12 17:00:01 2009; sloiseau\cr
Built: \tab R 2.7.1; ; 2009-03-12 17:00:03; unix\cr
}

Index:
\preformatted{
pareto                  Draw pareto graphic
specificites            Compute specificites indices of association between words and subcorpus
repartition            compute repartition graph
}
% ~~ An overview of how to use the package, including the most important ~~
% ~~ functions ~~
}
\author{
Sylvain Loiseau, Lise Vaudor, Matthieu Decorde
% ~~ The author and/or maintainer of the package ~~
}
\references{
%~~ Literature or other references for background information ~~
}
%~~ Optionally other standard keywords, one per line, from file KEYWORDS in ~~
%~~ the R documentation directory ~~
\keyword{ package }
\seealso{
%~~ Optional links to other man pages, e.g. ~~
%~~ \code{\link[<pkg>:<pkg>-package]{<pkg>}} ~~
}
\examples{
data(robespierre);
specificites(robespierre);
}
