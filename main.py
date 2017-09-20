from math import *
from random import *
from time import *

import numpy
import scipy

from util import *
from parser import *
from affinity import *
from neuralnet import *
from multiprocessing import *

vnfs = []
fgs = {}

dataset = []

num_iter = 0
iter_limit = 20

best_rsquared = 0
best_fit_data = []
best_test_data = []

def parse():
    global fgs, vnfs

    vnfs = parse_vnfs()
    print len(vnfs)
    fgs = parse_fgs()
    print len(fgs)

    vnfs = filter(lambda x: x.find_fgs(fgs), vnfs)
    print len(vnfs)


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


def init_dataset_slice(slice):
    global vnfs

    dataset_slice = []

    vnfs_per_proc = int(len(vnfs) / cpu_count())
    start_index = slice * vnfs_per_proc
    end_index = (slice + 1) * vnfs_per_proc if slice != 7 else len(vnfs)
    print(start_index, end_index)
    for i in range(start_index, end_index):
        for j in range(i + 1, len(vnfs)):
            vnf_a = vnfs[i]
            vnf_b = vnfs[j]
            result = init_affinity((vnf_a, vnf_b))
            if (result is not None):
                dataset_slice.append(result)

    return dataset_slice


def init_dataset():
    global dataset

    p = Pool(cpu_count())
    list_of_slices = p.map(init_dataset_slice, range(cpu_count()))
    dataset = [y for x in list_of_slices for y in x]
    p.close()
    p.join()

    with open("res/input/nn_dataset.csv", "wb") as file:
        writer = csv.writer(file, delimiter=",")
        for (vnf_a, vnf_b, fg, affinity) in dataset:
            writer.writerow(get_nn_features(vnf_a, vnf_b, fg) + [affinity])


def split_dataset():
    global dataset, nn_fit_data, nn_validate_data, nn_test_data

    print "Dataset size: " + str(len(dataset))

    nn_fit_data = sample(dataset, int(len(dataset) * 0.8))
    print "Fit cases " + str(len(nn_fit_data))

    dataset_remain = list(set(dataset) - set(nn_fit_data))
    print "Remaining dataset: " + str(len(dataset_remain))

    nn_validate_data = sample(dataset_remain, int(len(dataset_remain) * 0.5))
    print "Validate cases " + str(len(nn_validate_data))

    nn_test_data = list(set(dataset_remain) - set(nn_validate_data))
    print "Test cases " + str(len(nn_test_data))


def fit():
    global neural_net, min_max_scaler, nn_fit_data

    fit_array = []
    fit_affinity = []

    for (vnf_a, vnf_b, fg, affinity) in nn_fit_data:
        fit_array.append(get_nn_features(vnf_a, vnf_b, fg))
        fit_affinity.append(affinity)

    neural_net.fit(min_max_scaler.fit_transform(fit_array), fit_affinity)


def validate():
    global neural_net, min_max_scaler, nn_fit_data, nn_validate_data, nn_test_data

    real_affinity = []
    predicted_affinity = []

    for (vnf_a, vnf_b, fg, affinity) in nn_validate_data:
        real_affinity.append(affinity)
        predicted_affinity.append(neural_net.predict(min_max_scaler.transform([get_nn_features(vnf_a, vnf_b, fg)]))[0])

    rsquared = rsquared(real_affinity, predicted_affinity)
    print "Validation R-squared value: " + str(rsquared)
    if (rsquared > best_fit_data):
        best_fit_data = nn_fit_data
        best_test_data = nn_test_data

    return (rsquared(real_affinity, predicted_affinity) > 0.6) or (num_iter >= iter_limit)


def test():
    global criteria, neural_net, min_max_scaler, nn_test_data

    real_affinity = []
    static_affinity = []
    predicted_affinity = []

    for (vnf_a, vnf_b, fg, affinity) in nn_test_data:
        for criterion in criteria:
            if (criterion.type == "dynamic"):
                criterion.weight = 0

        real_affinity.append(affinity)
        static_affinity.append(affinity_measurement(vnf_a, vnf_b, fg)["result"])
        predicted_affinity.append(neural_net.predict(min_max_scaler.transform([get_nn_features(vnf_a, vnf_b, fg)]))[0])

    print "Writing results"
    with open("res/output/results.csv", "wb") as file:
        writer = csv.writer(file, delimiter=",")
        writer.writerow(get_headers())

        for (vnf_a, vnf_b, fg, affinity), static, predicted in zip(nn_test_data, static_affinity, predicted_affinity):
            writer.writerow(get_row_data(vnf_a, vnf_b, fg) + [affinity, static, predicted])

    print("R Squared Real-Predicted: ", str(rsquared(real_affinity, predicted_affinity)))
    print("R Squared Real-Static: ", str(rsquared(real_affinity, static_affinity)))


if __name__ == "__main__":
    process_start = time()

    start = time()
    print "Parsing vnfs and fgs"
    parse()
    end = time()
    print "Parsing time (s): " + str(end - start)

    print "Initializing affinity dataset"
    start = time()
    init_dataset()
    end = time()
    print "Initializing time (s): " + str(end - start)

    start = time()
    while True:
        num_iter += 1

        print "Splitting dataset"
        split_dataset()

        print "Starting fit"
        fit()

        print "Starting validation"
        if (validate()):
            break

    if (num_iter >= iter_limit):
        nn_fit_data = best_fit_data
        nn_test_data = best_test_data
        fit()

    print "Starting test"
    test()
    end = time()
    print "Fit-validate-test time (s): " + str(end - start)

    process_stop = time()
    print "Total time (s): " + str(process_stop - process_start)
