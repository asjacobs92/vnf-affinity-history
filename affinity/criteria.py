from debug import *
from models import *

global debug


def min_cpu_affinity(vnf_a, vnf_b, fg):
    if (debug):
        print "vnf_a vm cpu: " + str(float(vnf_a.vm_cpu)) + " flavor: " + str(float(vnf_a.flavor.min_cpu))
        print "vnf_b vm cpu: " + str(float(vnf_b.vm_cpu)) + " flavor: " + str(float(vnf_b.flavor.min_cpu))

    if (float(vnf_a.vm_cpu) >= float(vnf_a.flavor.min_cpu) and float(vnf_b.vm_cpu) >= float(vnf_b.flavor.min_cpu)):
        return 1.0

    if (float(vnf_a.vm_cpu) >= float(vnf_a.flavor.min_cpu) and float(vnf_b.vm_cpu) < float(vnf_b.flavor.min_cpu)):
        return (1.0 + max(0.001, float(vnf_b.vm_cpu) / float(vnf_b.flavor.min_cpu))) * 0.5

    if (float(vnf_a.vm_cpu) < float(vnf_a.flavor.min_cpu) and float(vnf_b.vm_cpu) >= float(vnf_b.flavor.min_cpu)):
        return (max(0.001, float(vnf_a.vm_cpu) / float(vnf_a.flavor.min_cpu)) + 1.0) * 0.5

    return (max(0.001, float(vnf_a.vm_cpu) / float(vnf_a.flavor.min_cpu)) + max(0.001, float(vnf_b.vm_cpu) / float(vnf_b.flavor.min_cpu))) * 0.5


def min_mem_affinity(vnf_a, vnf_b, fg):
    if (debug):
        print "vnf_a vm mem: " + str(float(vnf_a.vm_mem)) + " flavor: " + str(float(vnf_a.flavor.min_mem))
        print "vnf_b vm mem: " + str(float(vnf_b.vm_mem)) + " flavor: " + str(float(vnf_b.flavor.min_mem))
    if (float(vnf_a.vm_mem) >= float(vnf_a.flavor.min_mem) and float(vnf_b.vm_mem) >= float(vnf_b.flavor.min_mem)):
        return 1.0

    if (float(vnf_a.vm_mem) >= float(vnf_a.flavor.min_mem) and float(vnf_b.vm_mem) < float(vnf_b.flavor.min_mem)):
        return (1.0 + max(0.001, float(vnf_b.vm_mem) / float(vnf_b.flavor.min_mem))) * 0.5

    if (float(vnf_a.vm_mem) < float(vnf_a.flavor.min_mem) and float(vnf_b.vm_mem) >= float(vnf_b.flavor.min_mem)):
        return (max(0.001, float(vnf_a.vm_mem) / float(vnf_a.flavor.min_mem)) + 1.0) * 0.5

    return (max(0.001, float(vnf_a.vm_mem) / float(vnf_a.flavor.min_mem)) + max(0.001, float(vnf_b.vm_mem) / float(vnf_b.flavor.min_mem))) * 0.5


def min_sto_affinity(vnf_a, vnf_b, fg):
    if (debug):
        print "vnf_a vm sto: " + str(float(vnf_a.vm_sto)) + " flavor: " + str(float(vnf_a.flavor.min_sto))
        print "vnf_b vm sto: " + str(float(vnf_b.vm_sto)) + " flavor: " + str(float(vnf_b.flavor.min_sto))
    if (float(vnf_a.vm_sto) >= float(vnf_a.flavor.min_sto) and float(vnf_b.vm_sto) >= float(vnf_b.flavor.min_sto)):
        return 1.0

    if (float(vnf_a.vm_sto) >= float(vnf_a.flavor.min_sto) and float(vnf_b.vm_sto) < float(vnf_b.flavor.min_sto)):
        return (1.0 + max(0.001, float(vnf_b.vm_sto) / float(vnf_b.flavor.min_sto))) * 0.5

    if (float(vnf_a.vm_sto) < float(vnf_a.flavor.min_sto) and float(vnf_b.vm_sto) >= float(vnf_b.flavor.min_sto)):
        return (max(0.001, float(vnf_a.vm_sto) / float(vnf_a.flavor.min_sto)) + 1.0) * 0.5

    return (max(0.001, float(vnf_a.vm_sto) / float(vnf_a.flavor.min_sto)) + max(0.001, float(vnf_b.vm_sto) / float(vnf_b.flavor.min_sto))) * 0.5


def conflicts_affinity(vnf_a, vnf_b, fg):
    if (fg is not None):
        for conflict in fg.nsd.conflicts:
            if (conflict["vnf_a"] == vnf_a.type[1] and conflict["vnf_b"] == vnf_b.type[1]):
                return 0.001
    return 1.0


def cpu_usage_affinity(vnf_a, vnf_b, fg):
    if (debug):
        print "vnf a cpu usage: " + str(vnf_a.cpu_usage)
        print "vnf b cpu usage: " + str(vnf_b.cpu_usage)
    return max(0.001, 1.0 - ((vnf_a.cpu_usage + vnf_b.cpu_usage) / 100.0))


def mem_usage_affinity(vnf_a, vnf_b, fg):
    if (debug):
        print "vnf a mem usage: " + str(vnf_a.mem_usage)
        print "vnf b mem usage: " + str(vnf_b.mem_usage)
    return max(0.001, 1.0 - ((vnf_a.mem_usage + vnf_b.mem_usage) / 100.0))


def sto_usage_affinity(vnf_a, vnf_b, fg):
    if (debug):
        print "vnf a cpu usage: " + str(vnf_a.cpu_usage)
        print "vnf b cpu usage: " + str(vnf_b.cpu_usage)
    return max(0.001, 1.0 - ((vnf_a.sto_usage + vnf_b.sto_usage) / 100.0))


def bnd_usage_affinity(vnf_a, vnf_b, fg):
    if (fg is not None):
        flow = next((x for x in fg.flows if ((x.src == vnf_a.label and x.dst == vnf_b.label) or (
            x.src == vnf_b.label and x.dst == vnf_a.label))), None)
        if (flow != None):
            return max(0.001, 1.0 - (flow.bnd_usage / 100.0))
    return -1.0


def pkt_loss_affinity(vnf_a, vnf_b, fg):
    if (fg is not None):
        flow = next((x for x in fg.flows if ((x.src == vnf_a.label and x.dst == vnf_b.label) or (
            x.src == vnf_b.label and x.dst == vnf_a.label))), None)
        if (flow != None):
            return max(0.001, 1.0 - (flow.pkt_loss / 100.0))
    return -1.0


def lat_affinity(vnf_a, vnf_b, fg):
    if (fg is not None):
        flow = next((x for x in fg.flows if ((x.src == vnf_a.label and x.dst == vnf_b.label) or (
            x.src == vnf_b.label and x.dst == vnf_a.label))), None)
        if (flow != None):
            return 1.0 if (2.0 * flow.latency <= fg.nsd.sla) else max(0.001, 1.0 - ((2.0 * flow.latency - fg.nsd.sla) / fg.nsd.sla))
    return -1.0


criteria = [
    Criterion("min_cpu", "static", "PM", 1, min_cpu_affinity),
    Criterion("min_mem", "static", "PM", 1, min_mem_affinity),
    Criterion("min_sto", "static", "PM", 1, min_sto_affinity),
    Criterion("conflicts", "static", "FG", 1, conflicts_affinity),
    Criterion("cpu_usage", "dynamic", "PM", 1, cpu_usage_affinity),
    Criterion("mem_usage", "dynamic", "PM", 1, mem_usage_affinity),
    Criterion("sto_usage", "dynamic", "PM", 1, sto_usage_affinity),
    Criterion("bnd_usage", "dynamic", "FG", 1, bnd_usage_affinity),
    Criterion("pkt_loss", "dynamic", "FG", 1, pkt_loss_affinity),
    Criterion("lat", "dynamic", "FG", 1, lat_affinity)
]
