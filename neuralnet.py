import numpy
import scipy
from sklearn.neural_network import MLPClassifier
from sklearn.neural_network import MLPRegressor
from sklearn.naive_bayes import GaussianNB

neural_net = MLPRegressor(solver='lbfgs',alpha=1e-5, random_state=1, activation='tanh',hidden_layer_sizes=(100,5), learning_rate = 'adaptive')

nn_fit_data = []
nn_fit_data_array = []
nn_fit_affinity = []
nn_test_data = []
nn_test_affinity_static = []
nn_test_affinity_dynamic = []
nn_predicted_affinity = []

def rsquared(x, y):
    slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(x, y)
    return r_value**2

def get_nn_features(vnf_a, vnf_b, fg, nsd):
    vnf_a_before_id = next((x.src for x in fg.flows if x.dst == vnf_a.label), None) if (fg is not None) else "-1.-1"
    vnf_a_after_id = next((x.dst for x in fg.flows if x.src == vnf_a.label), None) if (fg is not None) else "-1.-1"
    vnf_b_before_id = next((x.src for x in fg.flows if x.dst == vnf_b.label), None) if (fg is not None) else "-1.-1"
    vnf_b_after_id = next((x.dst for x in fg.flows if x.src == vnf_b.label), None) if (fg is not None) else "-1.-1"
    
    values = [
        vnf_a.type[1],
        vnf_a.flavor.min_cpu,
        vnf_a.flavor.min_mem,
        vnf_a.flavor.min_sto,
        vnf_a.vm_cpu,
        vnf_a.vm_mem,
        vnf_a.vm_sto,
        int(vnf_a_before_id.split(".")[1]),
        int(vnf_a_after_id.split(".")[1]),
        vnf_b.type[1],
        vnf_b.flavor.min_cpu,
        vnf_b.flavor.min_mem,
        vnf_b.flavor.min_sto,
        vnf_b.vm_cpu,
        vnf_b.vm_mem,
        vnf_b.vm_sto,
        int(vnf_b_before_id.split(".")[1]),
        int(vnf_b_after_id.split(".")[1]),
        nsd.sla
    ]
    return values

def learn():
    global neural_net
    global nn_fit_data
    global nn_fit_affinity
    global nn_fit_data_array
    
    for row in nn_fit_data:
        nn_fit_data_array.append(get_nn_features(row[0], row[1], row[2], row[3]))
        
    neural_net.fit(nn_fit_data_array, nn_fit_affinity)
