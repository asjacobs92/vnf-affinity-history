import simplejson
from math import *
from time import *
from parser import *
from random import *
from criteria import *
from affinity import *
from csvutils import *
from neuralnet import *
from sklearn.neural_network import MLPClassifier
from sklearn.neural_network import MLPRegressor
from sklearn.naive_bayes import GaussianNB

def reset_vnf(vnf):
    vnf.cpu_usage = 0
    vnf.mem_usage = 0
    vnf.sto_usage = 0
    
    return vnf

def parse_json():
    with open("input/input.json") as data_file:
        data = simplejson.load(data_file)
        data_file.close()
    
    pms = parse_pms(data)
    fgs = parse_fgs(data)
    flavors = parse_flavors(data)
    vnfs = parse_vnfs(data, pms, fgs, flavors)
    
    nsd = NSD()
    nsd.sla = parse_sla(data)
    nsd.conflicts = parse_conflicts(data)
    for criterion in criteria:
        criterion.weight = parse_weight(data, criterion.name)       
        
def init_data():
    global nn_fit_data
    global nn_fit_affinity
    global nn_test_data
    global nn_test_affinity
    global nn_predicted_affinity
    num_tests = 100
    for k in range(num_tests):
        nsd = NSD()
        pms = []
        fgs = []
        vnfs = []
        flavors = []
        
        for i in range(randint(1, 5)):
            flavors.append(Flavor())
        for i in range(randint(1, 10)):
            pms.append(PhysicalMachine())
        for i in range(randint(2, 20)):
            vnfs.append(VNF(choice(pms), choice(flavors)))
        for i in range(randint(1, 10)):
            fgs.append(ForwardingGraph(vnfs))
        for vnf in vnfs:
            vnf.find_fgs(fgs)
    
        count = 0
        fit_threshold = (len(vnfs) * (len(vnfs) - 1)) / 4 
        
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
                        # fit (50% of data)
                        if (count < fit_threshold): 
                            nn_fit_data.append((vnf_a, vnf_b, fg, nsd))
                            nn_fit_affinity.append(affinity)
                        # test (50% of data)
                        else:
                            nn_test_data.append((vnf_a, vnf_b, fg, nsd))
                            nn_test_affinity_dynamic.append(affinity)
                        
                same_pm = vnf_a.pm.id == vnf_b.pm.id
                if (same_fg == False and same_pm == True):
                    affinity = affinity_measurement(vnf_a, vnf_b, None, nsd)["pm"]
                     # fit (50% of data)
                    if (count < fit_threshold): 
                        nn_fit_data.append((vnf_a, vnf_b, None, nsd))
                        nn_fit_affinity.append(affinity)
                    # test (50% of data)
                    else:
                        nn_test_data.append((vnf_a, vnf_b, None, nsd))
                        nn_test_affinity_dynamic.append(affinity)
                count += 1
        
def test_data():
    global criteria
    
    for criterion in criteria:
        if (criterion.type == "dynamic"):
            criterion.weight = 0    
    
    for test in nn_test_data:
        affinity = affinity_measurement(test[0], test[1], test[2], test[3])["result" if test[2] != None else "pm"]
        nn_test_affinity_static.append(affinity)
    
    for criterion in criteria:
        criterion.weight = 1       
    
    for test in nn_test_data:
        affinity = affinity_measurement(test[0], test[1], test[2], test[3])["result" if test[2] != None else "pm"]
        nn_predicted_affinity.append(affinity)

def write_results():
    global nn_test_affinity
    global nn_predicted_affinity
    with open("output/results.csv", "wb") as file:
        csv = CsvUtils(file)
        csv.write_row(csv.get_headers() + ["test_dynamic", "test_static", "predicted", "proximity_rate_1_3", "proximity_rate_2_3"])
       
        for test, test_dynamic, test_static, predicted in zip(nn_test_data, nn_test_affinity_dynamic, nn_test_affinity_static, nn_predicted_affinity):
            proximity_rate_1_3 = float(test_dynamic/predicted)
            proximity_rate_2_3 = float(test_static/predicted)
            data = csv.get_row_data(test[0], test[1], test[2], test[3])
            csv.write_row(data + [test_dynamic, test_static, predicted, proximity_rate_1_3, proximity_rate_2_3])
        
        csv.write_row(["R Squared 1_3: ", str(rsquared(nn_test_affinity_dynamic, nn_predicted_affinity))])
        csv.write_row(["R Squared 2_3: ", str(rsquared(nn_test_affinity_static, nn_predicted_affinity))])

init_data()

start = time()
learn()
test_data()
end = time()

print "Elapsed time: " + str(end - start)
write_results()