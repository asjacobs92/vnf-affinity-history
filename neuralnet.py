import numpy
import scipy

from affinity import *
from sklearn.neural_network import MLPClassifier
from sklearn.neural_network import MLPRegressor
from sklearn.naive_bayes import GaussianNB
from sklearn import preprocessing

neural_net = MLPRegressor(solver='lbfgs', activation='tanh', hidden_layer_sizes=(12, 6), alpha=0.001, batch_size='auto',
                          learning_rate='adaptive', learning_rate_init=0.01, power_t=0.5, max_iter=1000, shuffle=True,
                          random_state=9,  tol=0.0001, verbose=False, warm_start=False, momentum=0.9,
                          nesterovs_momentum=True, early_stopping=False, validation_fraction=0.1, beta_1=0.9, beta_2=0.999,
                          epsilon=1e-08)

min_max_scaler = preprocessing.MinMaxScaler()

nn_fit_data = []
nn_validate_data = []
nn_test_data = []

def rsquared(x, y):
    slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(x, y)
    return r_value**2


def get_nn_features(vnf_a, vnf_b, fg):
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
        min_cpu_affinity(vnf_a, vnf_b, fg),
        min_mem_affinity(vnf_a, vnf_b, fg),
        min_sto_affinity(vnf_a, vnf_b, fg),
        conflicts_affinity(vnf_a, vnf_b, fg),
        1 if (vnf_a.pm.id == vnf_b.pm.id) else 0,
        fg.nsd.sla if (fg is not None) else 0,
    ]
    return values
