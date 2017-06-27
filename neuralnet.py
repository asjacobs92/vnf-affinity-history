import numpy
import scipy
from criteria import *
from sklearn.neural_network import MLPClassifier
from sklearn.neural_network import MLPRegressor
from sklearn.naive_bayes import GaussianNB

neural_net = MLPRegressor(solver='adam', activation='tanh', hidden_layer_sizes=(100, 50, 25, 10, 5, 1), learning_rate = 'adaptive')

nn_fit_data = []
nn_fit_data_array = []
nn_fit_affinity = []
nn_test_data = []
nn_test_affinity_static = []
nn_test_affinity_dynamic = []
nn_predicted_affinity = []
nn_predicted_affinity_clean = []

def rsquared(x, y):
    slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(x, y)
    return r_value**2
    

def get_nn_features(vnf_a, vnf_b, fg, nsd):
    vnf_a_before_id = next((x.src for x in fg.flows if x.dst == vnf_a.label), "-1.-1") if (fg is not None) else "-1.-1"
    vnf_a_after_id = next((x.dst for x in fg.flows if x.src == vnf_a.label), "-1.-1") if (fg is not None) else "-1.-1"
    vnf_b_before_id = next((x.src for x in fg.flows if x.dst == vnf_b.label), "-1.-1") if (fg is not None) else "-1.-1"
    vnf_b_after_id = next((x.dst for x in fg.flows if x.src == vnf_b.label), "-1.-1") if (fg is not None) else "-1.-1"
    
    values = [
        vnf_a.type[1],
        vnf_b.type[1],
        int(vnf_a_before_id.split(".")[1]),
        int(vnf_a_after_id.split(".")[1]),
        int(vnf_b_before_id.split(".")[1]),
        int(vnf_b_after_id.split(".")[1]),
        min_cpu_affinity(vnf_a, vnf_b, fg, nsd),
        min_mem_affinity(vnf_a, vnf_b, fg, nsd), 
        min_sto_affinity(vnf_a, vnf_b, fg, nsd),
        1 if (vnf_a.pm.id == vnf_b.pm.id) else 0,
        nsd.sla
    ]
    return values

def learn(data, affinity):
    global neural_net
    global nn_fit_data
    global nn_fit_affinity
    global nn_fit_data_array
    
    nn_fit_data.append(data)
    nn_fit_affinity.append(affinity)
    nn_fit_data_array.append(get_nn_features(data[0], data[1], data[2], data[3]))
    
    neural_net.fit(nn_fit_data_array, nn_fit_affinity)
