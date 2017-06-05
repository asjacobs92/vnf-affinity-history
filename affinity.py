from app2net.amnesia.models import *
from criteria import formulas

def intersect_fgs(fgs_a, fgs_b):
    common_fgs = []
    for fg_a in fgs_a:
        for fg_b in fgs_b:
            if (fg_a.pk == fg_b.pk):
                common_fgs.append(fg_a)
    return common_fgs

def criteria_affinity(vnf_a, vnf_b, fg, nsd, type, scope):
    filtered_criteria = Criterion.objects.filter(type=type, scope=scope)
    weights_sum = 0
    affinities_sum = 0
    for criterion in filtered_criteria:
        weights_sum += criterion.weight
        formula = getattr(formulas, criterion.formula)
        affinities_sum += criterion.weight/formula(vnf_a, vnf_b, fg, nsd)
    return (weights_sum/affinities_sum) if (affinities_sum > 0) else 0

def static_pm_affinity(vnf_a, vnf_b, fg, nsd):
    return criteria_affinity(vnf_a, vnf_b, fg, nsd, "static", "PM")

def static_fg_affinity(vnf_a, vnf_b, fg, nsd):
    return criteria_affinity(vnf_a, vnf_b, fg, nsd, "static", "FG")

def dynamic_pm_affinity(vnf_a, vnf_b, fg, nsd):
    return criteria_affinity(vnf_a, vnf_b, fg, nsd, "dynamic", "PM")

def dynamic_fg_affinity(vnf_a, vnf_b, fg, nsd):
    return criteria_affinity(vnf_a, vnf_b, fg, nsd, "dynamic", "FG")

def static_affinity(vnf_a, vnf_b, fg, nsd):
    static_pm_aff = static_pm_affinity(vnf_a, vnf_b, fg, nsd)
    static_fg_aff = static_fg_affinity(vnf_a, vnf_b, fg, nsd)

    if (static_pm_aff == 0):
        return static_fg_aff

    if (static_fg_aff == 0):
        return static_pm_aff

    return 2.0 / ((1.0/static_pm_aff) + (1.0/static_fg_aff))

def trf_affinity(vnf_a, vnf_b, fg, nsd):
    if (fg is not None):
        max_fg_trf = 0
        vnfs_trf = 0
        for flow in fg.flows.all():
            if ((flow.source.pk == vnf_a.pk and flow.destination.pk == vnf_b.pk) or
                (flow.source.pk == vnf_b.pk and flow.destination.pk == vnf_a.pk)):
                vnfs_trf = flow.traffic
            if (flow.traffic > max_fg_trf):
                max_fg_trf = flow.traffic

        if (vnfs_trf != 0):
            return max(0.001, float(vnfs_trf)/max_fg_trf)
    return -1.0

def network_affinity(vnf_a, vnf_b, fg, nsd):
    trf_aff = trf_affinity(vnf_a, vnf_b, fg, nsd)
    dynamic_fg_aff = dynamic_fg_affinity(vnf_a, vnf_b, fg, nsd)
    return max(0.001, 0.5 + ((trf_aff/2.0) * float(dynamic_fg_aff - (1.0 - dynamic_fg_aff))))

def dynamic_affinity(vnf_a, vnf_b, fg, nsd):
    x = 1 if (vnf_a.physical_machine.pk == vnf_b.physical_machine.pk) else 0
    y = 0
    if (fg is not None):
        flows = next((x for x in fg.flows.all() if ((x.source.pk == vnf_a.pk and x.destination.pk == vnf_b.pk) or (x.source.pk == vnf_b.pk and x.destination.pk == vnf_a.pk))), None)
        y = 1 if (flows != None) else 0
    if (x == 0 and y == 0):
        return 1.0

    dynamic_pm_aff = dynamic_pm_affinity(vnf_a, vnf_b, fg, nsd)
    network_aff = network_affinity(vnf_a, vnf_b, fg, nsd)

    if (dynamic_pm_aff == 0):
        return network_aff

    if (network_aff == 0):
        return dynamic_pm_aff

    return (x + y) / ((x/dynamic_pm_aff) + (y/network_aff))

def total_affinity(vnf_a, vnf_b, fg, nsd):
    static_aff = static_affinity(vnf_a, vnf_b, fg, nsd)
    w = 1.0 if (vnf_a.cpu_usage != 0 or vnf_b.cpu_usage != 0) else 0
    if (w == 0):
        return static_aff

    dynamic_aff = dynamic_affinity(vnf_a, vnf_b, fg, nsd)
    if (dynamic_aff == 0):
        return static_aff

    if (static_aff == 0):
        return dynamic_aff

    return 2.0 / ((1.0/static_aff) + (w/dynamic_aff))

def affinity_measurement(vnf_a, vnf_b, fg, nsd):
    affinity_result = {}
    if (fg is not None):
        affinity_result['fg'] = fg.label
        affinity_result['vnf_a'] = vnf_a.label
        affinity_result['vnf_b'] = vnf_b.label
        affinity_result['result'] = total_affinity(vnf_a, vnf_b, fg, nsd)
    else:
        common_fgs = intersect_fgs(vnf_a.forwarding_graphs.all(), vnf_b.forwarding_graphs.all())
        if (len(common_fgs) != 0):
            for fg in common_fgs:
                affinity_result[fg.label] = total_affinity(vnf_a, vnf_b, fg, nsd)
        else:
            affinity_result["pm"] = total_affinity(vnf_a, vnf_b, None, nsd)

    return affinity_result
