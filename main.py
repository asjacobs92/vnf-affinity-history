import simplejson
import scipy
import numpy
import sys
from math import *
from time import *
from random import *
from criteria import *
from affinity import *
from csvutils import *
from neuralnet import *
from sklearn.neural_network import MLPClassifier
from sklearn.neural_network import MLPRegressor
from sklearn.naive_bayes import GaussianNB

fit_pms = []
fit_flavors = []
fit_vnfs = []
fit_fgs = []
fit_nsd = NSD()

test_pms = []
test_flavors = []
test_vnfs = []
test_fgs = []
test_nsd = None

init = True
real = True

def init_fit_data():
    pms = []
    vnfs = []
    flavors = []
    fgs = []
    nsd = []

    for i in range(5):
        flavors.append(Flavor())
    for i in range(20):
        pms.append(PhysicalMachine())
    for i in range(100):
        vnfs.append(VNF(choice(pms), choice(flavors)))

    flows = []
    vnfs_ids = [x.label for x in vnfs]
    shuffle(vnfs_ids)
    last_id = "0.0"
    num_flows = randint(4, 12)
    while (True):
        if (len(vnfs_ids) == 0):
            dst = "0.0"
            flows.append(Flow(last_id, dst))
            break

        if (len(flows) == num_flows):
            dst = "0.0"
            flows.append(Flow(last_id, dst))
            fgs.append(ForwardingGraph(flows = flows))
            flows = []
        else:
            dst = vnfs_ids.pop()
            flows.append(Flow(last_id, dst))
            last_id = dst

    for vnf in vnfs:
        vnf.find_fgs(fgs)

    nsd = NSD()
    return pms, flavors, vnfs, fgs, nsd

def init_fake_test_data():
    global fit_vnfs
    global fit_flavors
    global fit_fgs
    global fit_nsd

    global test_vnfs
    global test_flavors
    global test_fgs
    global test_nsd

    p = numpy.random.poisson(lam=0.5, size=1000)
    m = numpy.mean(p)

    for flavor in fit_flavors:
        test_flavors.append(Flavor(flavor.id,
                                    scipy.stats.poisson.pmf(choice(p), m) * 2100,
                                    scipy.stats.poisson.pmf(choice(p), m) * 2100,
                                    scipy.stats.poisson.pmf(choice(p), m) * 2100))

    for vnf in fit_vnfs:
        flavor = next((x for x in test_flavors if x.id == vnf.flavor.id), test_flavors[0])
        test_vnfs.append(VNF(vnf.pm, flavor,
                                id = vnf.id,
                                type = vnf.type,
                                vm_cpu = scipy.stats.poisson.pmf(choice(p), m) * 2100,
                                vm_mem = scipy.stats.poisson.pmf(choice(p), m) * 2100,
                                vm_sto = scipy.stats.poisson.pmf(choice(p), m) * 2100,
                                cpu_usage = scipy.stats.poisson.pmf(choice(p), m) * 50,
                                mem_usage = scipy.stats.poisson.pmf(choice(p), m) * 50,
                                sto_usage = scipy.stats.poisson.pmf(choice(p), m) * 50))

    for fg in fit_fgs:
        flows = []
        for flow in fg.flows:
            flows.append(Flow(flow.src, flow.dst,
                                scipy.stats.poisson.pmf(choice(p), m) * 10,
                                scipy.stats.poisson.pmf(choice(p), m) * 15,
                                scipy.stats.poisson.pmf(choice(p), m) * 30,
                                scipy.stats.poisson.pmf(choice(p), m) * 5))
        test_fgs.append(ForwardingGraph(id = fg.id, flows = flows))

    for vnf in test_vnfs:
        vnf.find_fgs(test_fgs)
    test_nsd = NSD(sla = scipy.stats.poisson.pmf(choice(p), m) * fit_nsd.sla)

def init_real_test_data():
    global test_pms
    global test_vnfs
    global test_flavors
    global test_fgs
    global test_nsd

    p = numpy.random.poisson(lam=0.5, size=1000)
    m = numpy.mean(p)

    with open("data/me-part-00000-of-00001.csv", "rb") as file_pms:
        reader_pms = csv.reader(file_pms)
        for pm in reader_pms:
            if (int(pm[2]) == 0):
                pm_id = pm[1]
                pm_cpu = float(pm[4]) if pm[4] is not "" else 0.5
                pm_mem = float(pm[5]) if pm[5] is not "" else 0.5
                pm_sto = 0.5

                test_pms.append(PhysicalMachine(pm_id))

    num_files = 1
    for i in range(num_files):
        with open("data/te-part-0000" + str(i) + "-of-00500.csv", "rb") as file_tasks:
            with open("data/tu-part-0000" + str(i) + "-of-00500.csv", "rb") as file_usage:
                print file_tasks
                print file_usage
                reader_tasks = csv.reader(file_tasks)
                reader_usage = csv.reader(file_usage)

                for task in reader_tasks:
                    file_usage.seek(0)
                    if (len(test_vnfs) >= 1000):
                        break

                    if (int(task[5]) == 1):
                        timestamp = task[0]
                        fg_id = int(task[2])
                        vnf_index = int(task[3])
                        pm_id = int(task[4])
                        vnf_type = choice(VNF.types)

                        pm = next((x for x in fit_pms if x.id == pm_id), None)
                        if (pm is None):
                            pm = PhysicalMachine(pm_id)
                            test_pms.append(pm)

                        vm_cpu = float(task[9])
                        vm_mem = float(task[10])
                        vm_sto = float(task[11])
                        cpu_usage = 0
                        mem_usage = 0
                        sto_usage = 0

                        for usage in reader_usage:
                            if (int(usage[2]) == fg_id and int(usage[3]) == vnf_index and usage[13] != "" and usage[10] != "" and usage[14] != ""):
                                cpu_usage = (float(usage[13]) / pm.cpu) * 100
                                mem_usage = (float(usage[10]) / pm.mem) * 100
                                sto_usage = (float(usage[14]) / pm.sto) * 100
                                break

                        if (cpu_usage == 0 or mem_usage == 0 or sto_usage == 0):
                            continue

                        flavor = next((x for x in test_flavors if x.min_cpu == vm_cpu and x.min_mem == vm_mem and x.min_sto == vm_sto), None)
                        if (flavor is None):
                            flavor = Flavor(min_cpu = vm_cpu * numpy.random.uniform(0,1,1)[0] * 2,
                                            min_mem = vm_mem * numpy.random.uniform(0,1,1)[0] * 2,
                                            min_sto = vm_sto * numpy.random.uniform(0,1,1)[0] * 2)
                            fit_flavors.append(flavor)

                        vnf = VNF(pm, flavor,
                                    type = vnf_type,
                                    vm_cpu = vm_cpu,
                                    vm_mem = vm_mem,
                                    vm_sto = vm_sto,
                                    cpu_usage = cpu_usage,
                                    mem_usage = mem_usage,
                                    sto_usage = sto_usage,
                                    index = vnf_index,
                                    timestamp = timestamp,
                                    fg_id = fg_id)
                        # print vnf.__dict__
                        # sys.stdin.read(1)
                        test_vnfs.append(vnf)

    print len(test_vnfs)
    for i in range(num_files):
        with open("data/je-part-0000" + str(i) + "-of-00500.csv", "rb") as file_fgs:
            reader_fgs = csv.reader(file_fgs)

            for fg in reader_fgs:
                if (int(fg[3]) == 1):
                    fg_id = int(fg[2])

                    flows = []
                    fg_vnfs = filter(lambda x: x.fg_id == fg_id, test_vnfs)
                    fg_vnfs.sort(key= lambda x: x.index, reverse=False)
                    for i in range(len(fg_vnfs) - 1):
                        src = fg_vnfs[i]
                        dst = fg_vnfs[i + 1]

                        traffic = scipy.stats.poisson.pmf(choice(p), m) * 10
                        latency = scipy.stats.poisson.pmf(choice(p), m) * 15
                        bnd_usage = scipy.stats.poisson.pmf(choice(p), m) * 30
                        pkt_loss = scipy.stats.poisson.pmf(choice(p), m) * 5

                        flows.append(Flow(src.label, dst.label, traffic, latency, bnd_usage, pkt_loss))

                    test_fgs.append(ForwardingGraph(fg_id, flows))

    for vnf in test_vnfs:
        vnf.find_fgs(test_fgs)
    test_nsd = NSD(sla = scipy.stats.poisson.pmf(choice(p), m) * fit_nsd.sla)

def parse_fit_csvs():
    global fit_pms
    global fit_vnfs
    global fit_flavors
    global fit_fgs
    global fit_nsd

    with open("input/vnfs-fit.csv", "rb") as file:
        reader = csv.reader(file, delimiter = ";")
        for row in reader:
            vnf_id = int(row[0])
            vnf_type = int(row[1])
            vnf_pm = int(row[2])
            flavor_data = row[3:6]
            vm_data = row[6:9]
            usage_data = row[9:12]

            pm = next((x for x in fit_pms if x.id == vnf_pm), None)
            if (pm is None):
                pm = PhysicalMachine(vnf_pm)
                fit_pms.append(pm)

            flavor = next((x for x in fit_flavors if x.min_cpu == float(flavor_data[0]) and x.min_mem == float(flavor_data[1]) and x.min_sto == float(flavor_data[2])), None)
            if (flavor is None):
                flavor = Flavor(min_cpu = float(flavor_data[0]), min_mem = float(flavor_data[1]), min_sto = float(flavor_data[2]))
                fit_flavors.append(flavor)

            vnf = VNF(pm, flavor,
                        id = vnf_id,
                        type = vnf_type,
                        vm_cpu = float(vm_data[0]),
                        vm_mem = float(vm_data[1]),
                        vm_sto = float(vm_data[2]),
                        cpu_usage = float(usage_data[0]),
                        mem_usage = float(usage_data[1]),
                        sto_usage = float(usage_data[2]))
            fit_vnfs.append(vnf)

    with open("input/fgs-fit.csv", "rb") as file:
        reader = csv.reader(file, delimiter = ";")
        for row in reader:
            fg_id = int(row[0])
            fg_num_flows = int(row[1])
            flows = []
            for i in range(fg_num_flows):
                flow_data = next(reader)
                flow = Flow(flow_data[0], flow_data[1], float(flow_data[2]), float(flow_data[3]), float(flow_data[4]), float(flow_data[5]))
                flows.append(flow)
                if (fit_nsd is None):
                    fit_nsd = NSD(sla = float(flow_data[6]))
            fit_fgs.append(ForwardingGraph(fg_id, flows = flows))

    for vnf in fit_vnfs:
        vnf.find_fgs(fit_fgs)

def parse_test_csvs():
    global fit_pms
    global test_vnfs
    global test_flavors
    global test_fgs
    global test_nsd

    with open("input/vnfs-test.csv", "rb") as file:
        reader = csv.reader(file, delimiter = ";")
        for row in reader:
            vnf_id = int(row[0])
            vnf_type = int(row[1])
            vnf_pm = int(row[2])
            flavor_data = row[3:6]
            vm_data = row[6:9]
            usage_data = row[9:12]

            pm = next((x for x in fit_pms if x.id == vnf_id), None)
            if (pm is None):
                pm = PhysicalMachine(vnf_pm)
                fit_pms.append(pm)

            flavor = next((x for x in test_flavors if x.min_cpu == float(flavor_data[0]) and x.min_mem == float(flavor_data[1]) and x.min_sto == float(flavor_data[2])), None)
            if (flavor is None):
                flavor = Flavor(min_cpu = float(flavor_data[0]), min_mem = float(flavor_data[1]), min_sto = float(flavor_data[2]))
                test_flavors.append(flavor)

            vnf = VNF(pm, flavor,
                        id = vnf_id,
                        type = vnf_type,
                        vm_cpu = float(vm_data[0]),
                        vm_mem = float(vm_data[1]),
                        vm_sto = float(vm_data[2]),
                        cpu_usage = float(usage_data[0]),
                        mem_usage = float(usage_data[1]),
                        sto_usage = float(usage_data[2]))
            test_vnfs.append(vnf)

    with open("input/fgs-test.csv", "rb") as file:
        reader = csv.reader(file, delimiter = ";")
        for row in reader:
            fg_id = int(row[0])
            fg_num_flows = int(row[1])
            flows = []
            for i in range(fg_num_flows):
                flow_data = next(reader)
                flow = Flow(flow_data[0], flow_data[1], float(flow_data[2]), float(flow_data[3]), float(flow_data[4]), float(flow_data[5]))
                flows.append(flow)
                if (test_nsd is None):
                    test_nsd = NSD(sla = float(flow_data[6]))
            test_fgs.append(ForwardingGraph(fg_id, flows = flows))

    for vnf in test_vnfs:
        vnf.find_fgs(test_fgs)

def write_data_csvs(scope, vnfs, fgs, nsd):
    with open("input/vnfs-" + scope + ".csv", "wb") as file:
        writer = csv.writer(file, delimiter = ";")
        for vnf in vnfs:
            row = [
                vnf.id, vnf.type[1], vnf.pm.id,
                vnf.flavor.min_cpu, vnf.flavor.min_mem, vnf.flavor.min_sto,
                vnf.vm_cpu, vnf.vm_mem, vnf.vm_sto,
                vnf.cpu_usage, vnf.mem_usage, vnf.sto_usage
            ]
            writer.writerow(row)

    with open("input/fgs-" + scope + ".csv", "wb") as file:
        writer = csv.writer(file, delimiter = ";")
        for fg in fgs:
            fg_row = [fg.id, len(fg.flows)]
            writer.writerow(fg_row)
            for flow in fg.flows:
                flow_row = [flow.src, flow.dst, flow.traffic, flow.latency, flow.bnd_usage, flow.pkt_loss, nsd.sla]
                writer.writerow(flow_row)

def init_fit_db():
    global fit_pms
    global fit_vnfs
    global fit_flavors
    global fit_fgs
    global fit_nsd

    global nn_fit_data
    global nn_fit_affinity

    nsd = fit_nsd
    pms = list(fit_pms)
    vnfs = list(fit_vnfs)
    flavors = list(fit_flavors)
    fgs = list(fit_fgs)

    num_good = 0
    num_medium = 0
    num_bad = 0
    num_fit = 1000

    with open("input/nn_fit.csv", "wb") as file:
        writer = csv.writer(file, delimiter = ";")
        while (True):
            if (num_bad < num_fit or num_medium < num_fit or num_good < num_fit):
                if (init):
                    pms, flavors, vnfs, fgs, nsd = init_fit_data()
                    fit_pms += pms
                    fit_flavors += flavors
                    fit_nsd = nsd
                print(num_bad, num_medium, num_good)
            else:
                break

            for i in range(0, len(vnfs)):
                for j in range(i + 1, len(vnfs)):
                    vnf_a = vnfs[i]
                    vnf_b = vnfs[j]

                    same_fg = False
                    for fg in filter(lambda x: x.id in [y.id for y in vnf_b.fgs], vnf_a.fgs):
                        same_fg = True
                        flow = next((x for x in fg.flows if ((x.src == vnf_a.label and x.dst == vnf_b.label) or (x.src == vnf_b.label and x.dst == vnf_a.label))), None)
                        if (flow is not None):
                            affinity = affinity_measurement(vnf_a, vnf_b, fg, nsd)["result"]
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
                                features = get_nn_features(vnf_a, vnf_b, fg, nsd)
                                writer.writerow(features + [affinity])
                                nn_fit_data.append((vnf_a, vnf_b, fg, fit_nsd))
                                nn_fit_affinity.append(affinity)
                                if (fg not in fit_fgs):
                                    fit_fgs.append(fg)
                                if (vnf_a not in fit_vnfs):
                                    fit_vnfs.append(vnf_a)
                                if (vnf_b not in fit_vnfs):
                                    fit_vnfs.append(vnf_b)

                    same_pm = vnf_a.pm.id == vnf_b.pm.id
                    if (same_fg == False and same_pm == True):
                        affinity = affinity_measurement(vnf_a, vnf_b, None, nsd)["pm"]
                        write = False

                        if (affinity <= 0.15 and num_bad < num_fit):
                            num_bad += 1
                            write = True

                        if (0.425 <= affinity and affinity <= 0.575 and num_medium < num_fit):
                            num_medium += 1
                            write = True

                        if (affinity >= 0.85 and num_good < num_fit):
                            num_good += 1
                            write = True

                        if (write):
                            features = get_nn_features(vnf_a, vnf_b, None, nsd)
                            writer.writerow(features + [affinity])
                            nn_fit_data.append((vnf_a, vnf_b, None, fit_nsd))
                            nn_fit_affinity.append(affinity)
                            if (vnf_a not in fit_vnfs):
                                fit_vnfs.append(vnf_a)
                            if (vnf_b not in fit_vnfs):
                                fit_vnfs.append(vnf_b)

    if (init):
        write_data_csvs("fit", fit_vnfs, fit_fgs, nsd)

def init_test_db():
    global fit_pms
    global test_vnfs
    global test_flavors
    global test_fgs
    global test_nsd

    if (init):
        if (real):
            init_real_test_data()
        else:
            init_fake_test_data()

    num_tests = 0
    max_tests = 1000

    with open("input/nn_test.csv", "wb") as file:
        writer = csv.writer(file, delimiter = ";")
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
                        affinity = affinity_measurement(vnf_a, vnf_b, fg, test_nsd)["result"]
                        if (num_tests < max_tests):
                            features = get_nn_features(vnf_a, vnf_b, fg, test_nsd)
                            writer.writerow(features + [affinity])
                            nn_test_data.append((vnf_a, vnf_b, fg, test_nsd))
                            num_tests += 1

                same_pm = vnf_a.pm.id == vnf_b.pm.id
                if (same_fg == False and same_pm == True):
                    affinity = affinity_measurement(vnf_a, vnf_b, None, test_nsd)["pm"]
                    if (num_tests < max_tests):
                        features = get_nn_features(vnf_a, vnf_b, None, test_nsd)
                        writer.writerow(features + [affinity])
                        nn_test_data.append((vnf_a, vnf_b, None, test_nsd))
                        num_tests += 1
            if (num_tests >= max_tests):
                break

    if (init):
        write_data_csvs("test", test_vnfs, test_fgs, test_nsd)


def fit():
    global neural_net
    global nn_fit_data
    global nn_fit_affinity
    global nn_fit_data_array

    for row in nn_fit_data:
        nn_fit_data_array.append(get_nn_features(row[0], row[1], row[2], row[3]))

    neural_net.fit(nn_fit_data_array, nn_fit_affinity)

def test():
    global criteria
    global neural_net
    global nn_test_data
    global nn_test_affinity_static
    global nn_predicted_affinity

    for criterion in criteria:
        if (criterion.type == "dynamic"):
            criterion.weight = 0

    for test in nn_test_data:
        affinity = affinity_measurement(test[0], test[1], test[2], test[3])["result" if test[2] != None else "pm"]
        nn_test_affinity_static.append(affinity)

    for criterion in criteria:
        criterion.weight = 1

    for test in nn_test_data:
        real_affinity = affinity_measurement(test[0], test[1], test[2], test[3])["result" if test[2] != None else "pm"]
        nn_test_affinity_dynamic.append(real_affinity)
        data = get_nn_features(test[0], test[1], test[2], test[3])
        predicted_affinity = neural_net.predict([data])[0]
        nn_predicted_affinity.append(predicted_affinity)
        #if (abs((predicted_affinity/real_affinity) - 1) <= 0.04):
            #learn(test, predicted_affinity)

def write_results():
    global nn_test_affinity
    global nn_predicted_affinity

    print(len(nn_test_data))
    print(len(nn_fit_data))
    print(len(nn_test_affinity_dynamic))
    print(len(nn_test_affinity_static))
    print(len(nn_predicted_affinity))
    with open("output/results.csv", "wb") as file:
        csv = CsvUtils(file)
        csv.write_row(csv.get_headers() + ["test_dynamic", "test_static", "test_predicted"])

        for test, test_dynamic, test_static, test_predicted in zip(nn_test_data, nn_test_affinity_dynamic, nn_test_affinity_static, nn_predicted_affinity):

            data = csv.get_row_data(test[0], test[1], test[2], test[3])
            csv.write_row(data + [test_dynamic, test_static, test_predicted])

        print("R Squared 1_3: ", str(rsquared(nn_test_affinity_dynamic, nn_predicted_affinity)))
        print("R Squared 2_3: ", str(rsquared(nn_test_affinity_static, nn_predicted_affinity)))

print "init: " + str(init)
if (not init):
    print "parsing fit database"
    parse_fit_csvs()
    print "parsing test database"
    parse_test_csvs()

print "generating fit database"
init_fit_db()
print "generating test database"
init_test_db()

print "starting fit"
fit()
print "finished fit"
print "starting test"
test()
print "finished test"
print "writing results"
write_results()
