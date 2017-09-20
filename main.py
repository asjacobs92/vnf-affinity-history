import itertools
import pickle
from math import *
from parser import *
from random import *
from time import *

import numpy
import scipy

from affinity import *
from csvutils import *
from neuralnet import *

vnfs = []
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


def init_affinity((vnf_a, vnf_b)):
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


def init_fit_slice(slice):
    global fit_vnfs

    fit_data = []

    vnfs_per_proc = int(len(fit_vnfs) / 8)

    start_index = slice * vnfs_per_proc
    end_index = (slice + 1) * vnfs_per_proc if slice != 7 else len(fit_vnfs)
    print(start_index, end_index)
    for i in range(start_index, end_index):
        for j in range(i + 1, len(fit_vnfs)):
            vnf_a = fit_vnfs[i]
            vnf_b = fit_vnfs[j]
            result = init_affinity((vnf_a, vnf_b))
            if (result is not None):
                fit_data.append(result)

    return fit_data


def init_fit_db():
    global nn_fit_data, nn_fit_data_array, nn_fit_affinity

    p = Pool(8)
    list_of_slices = p.map(init_fit_slice, range(8))
    nn_fit_data = [y for x in list_of_slices for y in x]
    p.close()
    p.join()
    with open("res/input/nn_fit.csv", "wb") as file:
        writer = csv.writer(file, delimiter=",")
        for (vnf_a, vnf_b, fg, affinity) in nn_fit_data:
            nn_fit_data_array.append(get_nn_features(vnf_a, vnf_b, fg))
            nn_fit_affinity.append(affinity)
            writer.writerow(get_nn_features(vnf_a, vnf_b, fg) + [affinity])

    print len(nn_fit_data)
    print len(nn_fit_affinity)
    print len(nn_fit_data_array)


def init_test_slice(slice):
    global test_vnfs

    test_data = []

    vnfs_per_proc = int(len(test_vnfs) / 8)

    start_index = slice * vnfs_per_proc
    end_index = (slice + 1) * vnfs_per_proc if slice != 7 else len(test_vnfs)
    print(start_index, end_index)
    for i in range(start_index, end_index):
        for j in range(i + 1, len(test_vnfs)):
            vnf_a = test_vnfs[i]
            vnf_b = test_vnfs[j]
            result = init_affinity((vnf_a, vnf_b))
            if (result is not None):
                test_data.append(result)

    return test_data


def init_test_db():
    global test_vnfs, nn_test_data

    p = Pool(8)
    list_of_slices = p.map(init_test_slice, range(8))
    nn_test_data = [y for x in list_of_slices for y in x]
    p.close()
    p.join()

    with open("res/input/nn_test.csv", "wb") as file:
        writer = csv.writer(file, delimiter=",")
        for (vnf_a, vnf_b, fg, affinity) in nn_test_data:
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

    for (vnf_a, vnf_b, fg, affinity) in nn_test_data:
        for criterion in criteria:
            if (criterion.type == "dynamic"):
                criterion.weight = 0

        nn_test_affinity_static.append(affinity_measurement(vnf_a, vnf_b, fg)["result"])

        for criterion in criteria:
            criterion.weight = 1

        nn_test_affinity_dynamic.append(affinity)

        predicted_affinity = neural_net.predict(min_max_scaler.transform([get_nn_features(vnf_a, vnf_b, fg)]))[0]
        nn_predicted_affinity.append(predicted_affinity)

        if (abs((predicted_affinity / affinity) - 1) <= 0.01):
            print abs((predicted_affinity / affinity) - 1)
            # learn(test, predicted_affinity)


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
