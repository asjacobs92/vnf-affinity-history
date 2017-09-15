import scipy
import numpy

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
    for vnf in vnfs:
        vnf.find_fgs(fgs)
        print vnf.__dict__

    fit_vnfs = sample(vnfs, 10)
    print "fit vnfs " + str(len(fit_vnfs))
    test_vnfs = list(set(vnfs) - set(fit_vnfs))
    print "test vnfs " + str(len(test_vnfs))


def init_fit_db():
    global fit_vnfs, nn_fit_data, nn_fit_affinity

    num_good = 0
    num_medium = 0
    num_bad = 0
    num_fit = 3000

    with open("res/input/nn_fit.csv", "wb") as file:
        writer = csv.writer(file, delimiter=",")

        for i in range(0, len(fit_vnfs)):
            for j in range(i + 1, len(fit_vnfs)):
                vnf_a = fit_vnfs[i]
                vnf_b = fit_vnfs[j]

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
                        write = False

                        if (affinity <= 0.30 and num_bad < num_fit):
                            num_bad += 1
                            write = True

                        if (0.30 <= affinity and affinity <= 0.60 and num_medium < num_fit):
                            num_medium += 1
                            write = True

                        if (affinity >= 0.60 and num_good < num_fit):
                            num_good += 1
                            write = True

                        if (write):
                            features = get_nn_features(vnf_a, vnf_b, fg)
                            writer.writerow(features + [affinity])
                            nn_fit_data.append((vnf_a, vnf_b, fg))
                            nn_fit_affinity.append(affinity)

                same_pm = vnf_a.pm.id == vnf_b.pm.id
                if (same_fg == False and same_pm == True):
                    affinity = affinity_measurement(vnf_a, vnf_b, None)["pm"]
                    write = False

                    if (affinity <= 0.30 and num_bad < num_fit):
                        num_bad += 1
                        write = True

                    if (0.30 <= affinity and affinity <= 0.60 and num_medium < num_fit):
                        num_medium += 1
                        write = True

                    if (affinity >= 0.60 and num_good < num_fit):
                        num_good += 1
                        write = True

                    if (write):
                        features = get_nn_features(vnf_a, vnf_b, None)
                        writer.writerow(features + [affinity])
                        nn_fit_data.append((vnf_a, vnf_b, None))
                        nn_fit_affinity.append(affinity)
                        if (vnf_a not in fit_vnfs):
                            fit_vnfs.append(vnf_a)
                        if (vnf_b not in fit_vnfs):
                            fit_vnfs.append(vnf_b)

    print(num_bad, num_medium, num_good)


def init_test_db():
    global test_vnfs

    num_tests = 0
    max_tests = 1000

    with open("res/input/nn_test.csv", "wb") as file:
        writer = csv.writer(file, delimiter=",")
        for i in range(0, len(test_vnfs)):
            for j in range(i + 1, len(test_vnfs)):
                if (num_tests >= max_tests):
                    break

                vnf_a = test_vnfs[i]
                vnf_b = test_vnfs[j]

                same_fg = False
                for fg in filter(lambda x: x.id in [y.id for y in vnf_b.fgs], vnf_a.fgs):
                    same_fg = True
                    flow = next((x for x in fg.flows if ((x.src == vnf_a.label and x.dst == vnf_b.label) or (x.src == vnf_b.label and x.dst == vnf_a.label))), None)
                    if (flow is not None):
                        affinity = affinity_measurement(vnf_a, vnf_b, fg)["result"]
                        if (num_tests < max_tests):
                            features = get_nn_features(vnf_a, vnf_b, fg)
                            writer.writerow(features + [affinity])
                            nn_test_data.append((vnf_a, vnf_b, fg))
                            num_tests += 1

                same_pm = vnf_a.pm.id == vnf_b.pm.id
                if (same_fg == False and same_pm == True):
                    affinity = affinity_measurement(vnf_a, vnf_b, None)["pm"]
                    if (num_tests < max_tests):
                        features = get_nn_features(vnf_a, vnf_b, None)
                        writer.writerow(features + [affinity])
                        nn_test_data.append((vnf_a, vnf_b, None))
                        num_tests += 1
            if (num_tests >= max_tests):
                break


def fit():
    global neural_net
    global nn_fit_data
    global nn_fit_affinity
    global nn_fit_data_array
    global min_max_scaler

    for row in nn_fit_data:
        nn_fit_data_array.append(get_nn_features(row[0], row[1], row[2]))

    # print min_max_scaler.fit_transform(nn_fit_data_array)
    neural_net.fit(min_max_scaler.fit_transform(nn_fit_data_array), nn_fit_affinity)


def test():
    global criteria
    global neural_net
    global nn_test_data
    global nn_test_affinity_static
    global nn_predicted_affinity
    global min_max_scaler

    for criterion in criteria:
        if (criterion.type == "dynamic"):
            criterion.weight = 0

    for test in nn_test_data:
        affinity = affinity_measurement(test[0], test[1], test[2])["result" if test[2] != None else "pm"]
        nn_test_affinity_static.append(affinity)

    for criterion in criteria:
        criterion.weight = 1

    for test in nn_test_data:
        real_affinity = affinity_measurement(test[0], test[1], test[2])["result" if test[2] != None else "pm"]
        nn_test_affinity_dynamic.append(real_affinity)
        data = get_nn_features(test[0], test[1], test[2])
        # print min_max_scaler.transform([data])
        predicted_affinity = neural_net.predict(min_max_scaler.transform([data]))[0]
        nn_predicted_affinity.append(predicted_affinity)
        if (abs((predicted_affinity / real_affinity) - 1) <= 0.1):
            print abs((predicted_affinity / real_affinity) - 1)
            learn(test, predicted_affinity)


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


print "parsing dataset"
parse_dataset()

print "generating fit database"
init_fit_db()
print "generating test database"
init_test_db()

print "starting fit"
# fit()
print "finished fit"
print "starting test"
# test()
print "finished test"
print "writing results"
# write_results()
