import scipy
import numpy
import itertools
import pickle

from math import *
from time import *
from random import *

from parser import *
from csvutils import *
from affinity import *
from neuralnet import *


fit_vnfs = []
test_vnfs = []
fgs = {}


def parse_dataset():
    global fgs, fit_vnfs, test_vnfs

    vnfs = parse_vnfs()
    print len(vnfs)
    fgs = parse_fgs()
    print len(fgs)

    vnfs = filter(lambda x: x.find_fgs(fgs), vnfs)
    print len(vnfs)
    # print vnf.__dict__

    fit_vnfs = sample(vnfs, int(len(vnfs) * 0.4))
    print "fit vnfs " + str(len(fit_vnfs))
    test_vnfs = list(set(vnfs) - set(fit_vnfs))
    print "test vnfs " + str(len(test_vnfs))


def init_fit_affinity((vnf_a, vnf_b)):
    same_fg = False
    for fg in filter(lambda x: x.id in [y.id for y in vnf_b.fgs], vnf_a.fgs):
        same_fg = True
        flow = None

        for f in fg.flows:
            if ((f.src == vnf_a.label and f.dst == vnf_b.label) or (f.src == vnf_b.label and f.dst == vnf_a.label)):
                flow = f
                break
        if (flow is not None):
            affinity = affinity_measurement(vnf_a, vnf_b, fg)["result"]
            return (vnf_a, vnf_b, fg, affinity)

    same_pm = vnf_a.pm.id == vnf_b.pm.id
    if (same_fg == False and same_pm == True):
        affinity = affinity_measurement(vnf_a, vnf_b, None)["result"]
        return (vnf_a, vnf_b, None, affinity)

    return None


def init_fit_db():
    global fit_vnfs, nn_fit_data, nn_fit_affinity

    combinations = list(itertools.combinations(fit_vnfs, r=2))
    print "#combs: " + str(len(combinations))
    with open("res/input/nn_fit.csv", "wb") as file:
        writer = csv.writer(file, delimiter=",")

        #p = Pool(4)
        # results = p.map(, )
        print "combinations calculated, creating fit db"
        for (vnf_a, vnf_b) in combinations:
            result = init_fit_affinity((vnf_a, vnf_b))
            if (result is not None):
                (vnf_a, vnf_b, fg, affinity) = result
                features = get_nn_features(vnf_a, vnf_b, fg)
                nn_fit_affinity.append(affinity)
                nn_fit_data.append((vnf_a, vnf_b, fg))
                nn_fit_data_array.append(features)
                writer.writerow(features + [affinity])
        # p.close()
        # p.join()

    print len(nn_fit_data)
    print len(nn_fit_affinity)


def init_test_affinity((vnf_a, vnf_b)):
    same_fg = False
    for fg in filter(lambda x: x.id in [y.id for y in vnf_b.fgs], vnf_a.fgs):
        same_fg = True
        flow = None
        for f in fg.flows:
            if ((f.src == vnf_a.label and f.dst == vnf_b.label) or (f.src == vnf_b.label and f.dst == vnf_a.label)):
                flow = f
                break
        if (flow is not None):
            affinity = affinity_measurement(vnf_a, vnf_b, fg)["result"]
            return (vnf_a, vnf_b, fg, affinity)

    same_pm = vnf_a.pm.id == vnf_b.pm.id
    if (same_fg == False and same_pm == True):
        affinity = affinity_measurement(vnf_a, vnf_b, None)["result"]
        return (vnf_a, vnf_b, None, affinity)

    return None


def init_test_db():
    global test_vnfs, nn_test_data

    combinations = list(itertools.combinations(test_vnfs, r=2))
    print "#combs: " + str(len(combinations))
    with open("res/input/nn_test.csv", "wb") as file:
        writer = csv.writer(file, delimiter=",")
        print "combinations calculated, creating test db"
        for (vnf_a, vnf_b) in combinations:
            result = init_test_affinity((vnf_a, vnf_b))
            if (result is not None):
                (vnf_a, vnf_b, fg, affinity) = result
                nn_test_data.append((vnf_a, vnf_b, fg))
                writer.writerow(get_nn_features(vnf_a, vnf_b, fg) + [affinity])
    print len(nn_test_data)


def fit():
    global neural_net
    global nn_fit_affinity
    global nn_fit_data_array
    global min_max_scaler

    neural_net.fit(min_max_scaler.fit_transform(nn_fit_data_array), nn_fit_affinity)


def test():
    global criteria
    global neural_net
    global nn_test_data
    global nn_test_affinity_static
    global nn_predicted_affinity
    global min_max_scaler

    for (vnf_a, vnf_b, fg) in nn_test_data:
        for criterion in criteria:
            if (criterion.type == "dynamic"):
                criterion.weight = 0

        nn_test_affinity_static.append(affinity_measurement(vnf_a, vnf_b, fg)["result"])

        for criterion in criteria:
            criterion.weight = 1

        real_affinity = affinity_measurement(vnf_a, vnf_b, fg)["result"]
        nn_test_affinity_dynamic.append(real_affinity)

        predicted_affinity = neural_net.predict(min_max_scaler.transform([get_nn_features(vnf_a, vnf_b, fg)]))[0]
        nn_predicted_affinity.append(predicted_affinity)

        if (abs((predicted_affinity / real_affinity) - 1) <= 0.01):
            print abs((predicted_affinity / real_affinity) - 1)
            #learn(test, predicted_affinity)


def write_results():
    global nn_test_affinity
    global nn_predicted_affinity

    print(len(nn_test_data))
    print(len(nn_fit_data))
    print(len(nn_test_affinity_dynamic))
    print(len(nn_test_affinity_static))
    print(len(nn_predicted_affinity))
    with open("res/output/results.csv", "wb") as file:
        csv = CsvUtils(file)
        csv.write_row(csv.get_headers() + ["test_dynamic", "test_static", "test_predicted"])

        for test, test_dynamic, test_static, test_predicted in zip(nn_test_data, nn_test_affinity_dynamic, nn_test_affinity_static, nn_predicted_affinity):
            data = csv.get_row_data(test[0], test[1], test[2])
            csv.write_row(data + [test_dynamic, test_static, test_predicted])

        print("R Squared 1_3: ", str(rsquared(nn_test_affinity_dynamic, nn_predicted_affinity)))
        print("R Squared 1_2: ", str(rsquared(nn_test_affinity_dynamic, nn_test_affinity_static)))
        print("R Squared 2_3: ", str(rsquared(nn_test_affinity_static, nn_predicted_affinity)))


start = time()
print "parsing dataset"
parse_dataset()
end = time()
print(end - start)

start = time()
print "generating fit database"
init_fit_db()
print "generating test database"
init_test_db()
end = time()
print(end - start)

start = time()
print "starting fit"
fit()
print "finished fit"
print "starting test"
test()
print "finished test"
print "writing results"
write_results()
end = time()
print(end - start)
