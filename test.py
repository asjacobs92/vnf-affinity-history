import scipy.stats
import numpy

p = numpy.random.poisson(1, 100)
m = numpy.mean(p)
print p
print m

probs = []

for i in p:
    probs.append(scipy.stats.poisson.pmf(i, m))

print probs
