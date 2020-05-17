setwd("C:/Users/equipo/Documents/Bittor/Infor/BH/Script-ak eta baliabideak-20200515/bayesian_analysis")

results_sa<-read.csv(file="results_SA.csv",header=TRUE,sep=";",stringsAsFactor=FALSE)
results_ga<-read.csv(file="results_GA.csv",header=TRUE,sep=";",stringsAsFactor=FALSE)

library("scmamp")
library("ggplot2")
library(latex2exp)
test.results <- bSignedRankTest(x=-results_sa$Modularitatea, y=-results_ga$Modularitatea, rope=c(-0.001, 0.001))
test.results$posterior.probabilities

p1<-plotSimplex(test.results, plot.density=TRUE, A="GA",B="SA", plot.points=TRUE, posterior.label=FALSE, alpha=0.5, point.size=1,font.size = 5)
ggsave("Simplex_gurea.png",p1, width = 125, height = 125, dpi = 300, units = "mm", device='png')
colMeans(test.results$posterior)