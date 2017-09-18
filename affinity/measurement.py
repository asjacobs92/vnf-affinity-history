from debug import *
from criteria import *

global debug


def criteria_affinity(vnf_a, vnf_b, fg, type, scope):
    filtered_criteria = filter(
        lambda x: x.type == type and x.scope == scope, criteria)
    weights_sum = 0
    affinities_sum = 0
    for criterion in filtered_criteria:
        weights_sum += criterion.weight
        if (criterion.weight != 0):
            if (debug):
                print "criterion: " + criterion.name + " affinity: " + str(criterion.formula(vnf_a, vnf_b, fg)) + " weight: " + str(criterion.weight)
            affinity = criterion.weight / criterion.formula(vnf_a, vnf_b, fg)
            affinities_sum += affinity

    return (weights_sum / affinities_sum) if (affinities_sum > 0) else 0


def static_pm_affinity(vnf_a, vnf_b, fg):
    return criteria_affinity(vnf_a, vnf_b, fg, "static", "PM")


def static_fg_affinity(vnf_a, vnf_b, fg):
    return criteria_affinity(vnf_a, vnf_b, fg, "static", "FG")


def dynamic_pm_affinity(vnf_a, vnf_b, fg):
    return criteria_affinity(vnf_a, vnf_b, fg, "dynamic", "PM")


def dynamic_fg_affinity(vnf_a, vnf_b, fg):
    return criteria_affinity(vnf_a, vnf_b, fg, "dynamic", "FG")


def static_affinity(vnf_a, vnf_b, fg):
    static_pm_aff = static_pm_affinity(vnf_a, vnf_b, fg)
    static_fg_aff = static_fg_affinity(vnf_a, vnf_b, fg)

    if (debug):
        print "static pm aff: " + str(static_pm_aff)
        print "static fg aff: " + str(static_fg_aff)

    if (static_pm_aff == 0):
        return static_fg_aff

    if (static_fg_aff == 0):
        return static_pm_aff

    return 2.0 / ((1.0 / static_pm_aff) + (1.0 / static_fg_aff))


def trf_affinity(vnf_a, vnf_b, fg):
    if (fg is not None):
        max_fg_trf = 0
        vnfs_trf = 0
        for flow in fg.flows:
            if ((flow.src == vnf_a.label and flow.dst == vnf_b.label) or (flow.src == vnf_b.label and flow.dst == vnf_a.label)):
                vnfs_trf = flow.traffic
            if (flow.traffic > max_fg_trf):
                max_fg_trf = flow.traffic

        if (vnfs_trf != 0):
            return max(0.001, float(vnfs_trf) / max_fg_trf)
    return -1


def network_affinity(vnf_a, vnf_b, fg):
    trf_aff = trf_affinity(vnf_a, vnf_b, fg)
    dynamic_fg_aff = dynamic_fg_affinity(vnf_a, vnf_b, fg)
    if (debug):
        print "trf aff: " + str(trf_aff)
        print "dynamic fg aff: " + str(dynamic_fg_aff)

    if (dynamic_fg_aff == 0):
        return 0

    return max(0.001, 0.5 + ((trf_aff / 2.0) * float(dynamic_fg_aff - (1.0 - dynamic_fg_aff))))


def dynamic_affinity(vnf_a, vnf_b, fg):
    x = 1 if (vnf_a.pm.id == vnf_b.pm.id) else 0
    y = 0
    if (fg is not None):
        flow = next((x for x in fg.flows if ((x.src == vnf_a.label and x.dst == vnf_b.label) or (
            x.src == vnf_b.label and x.dst == vnf_a.label))), None)
        y = 1 if (flow != None) else 0
    if (x == 0 and y == 0):
        return 1.0

    dynamic_pm_aff = dynamic_pm_affinity(vnf_a, vnf_b, fg)
    network_aff = network_affinity(vnf_a, vnf_b, fg)

    if (debug):
        print "dynamic pm affinity: " + str(dynamic_pm_aff)
        print "network aff: " + str(network_aff)

    if (dynamic_pm_aff == 0):
        return network_aff

    if (network_aff == 0):
        return dynamic_pm_aff

    return (x + y) / ((x / dynamic_pm_aff) + (y / network_aff))


def total_affinity(vnf_a, vnf_b, fg):
    static_aff = static_affinity(vnf_a, vnf_b, fg)

    if (debug):
        print "static aff: " + str(static_aff)
    w = 1.0 if (vnf_a.cpu_usage != 0 and vnf_b.cpu_usage != 0) else 0
    if (w == 0):
        return static_aff

    dynamic_aff = dynamic_affinity(vnf_a, vnf_b, fg)
    if (debug):
        print "dynamic aff: " + str(dynamic_aff)
    if (dynamic_aff == 0):
        return static_aff

    if (static_aff == 0):
        return dynamic_aff

    return 2.0 / ((1.0 / static_aff) + (w / dynamic_aff))


def affinity_measurement(vnf_a, vnf_b, fg):
    affinity_result = {}
    if (fg is not None):
        affinity_result['fg'] = fg.label
        affinity_result['vnf_a'] = vnf_a.label
        affinity_result['vnf_b'] = vnf_b.label
        affinity_result['result'] = total_affinity(vnf_a, vnf_b, fg)
    else:
        common_fgs = filter(lambda x: x.id in [
                            y.id for y in vnf_b.fgs], vnf_a.fgs)
        if (len(common_fgs) != 0):
            for fg in common_fgs:
                affinity_result[fg.label] = total_affinity(vnf_a, vnf_b, fg)
        else:
            affinity_result['fg'] = "pm"
            affinity_result['vnf_a'] = vnf_a.label
            affinity_result['vnf_b'] = vnf_b.label
            affinity_result["result"] = total_affinity(vnf_a, vnf_b, None)

    if (debug):
        print affinity_result
    return affinity_result
