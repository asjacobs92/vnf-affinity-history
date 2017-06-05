from app2net.amnesia.models import *
import random

def min_cpu_affinity(vnf_a, vnf_b, fg, nsd):
    if (vnf_a.vm_cpu >= vnf_a.flavor.minimum_cpu and vnf_b.vm_cpu >= vnf_b.flavor.minimum_cpu):
        return 1.0

    if (vnf_a.vm_cpu >= vnf_a.flavor.minimum_cpu and vnf_b.vm_cpu < vnf_b.flavor.minimum_cpu):
        return (1.0 + max(0.001, vnf_b.vm_cpu / vnf_b.flavor.minimum_cpu)) * 0.5

    if (vnf_a.vm_cpu < vnf_a.flavor.minimum_cpu and vnf_b.vm_cpu >= vnf_b.flavor.minimum_cpu):
        return (max(0.001, vnf_a.vm_cpu / vnf_a.flavor.minimum_cpu) + 1.0) * 0.5

    return (max(0.001, vnf_a.vm_cpu / vnf_a.flavor.minimum_cpu) + max(0, vnf_b.vm_cpu / vnf_b.flavor.minimum_cpu)) * 0.5

def min_mem_affinity(vnf_a, vnf_b, fg, nsd):
    if (vnf_a.vm_memory >= vnf_a.flavor.minimum_memory and vnf_b.vm_memory >= vnf_b.flavor.minimum_memory):
        return 1.0

    if (vnf_a.vm_memory >= vnf_a.flavor.minimum_memory and vnf_b.vm_memory < vnf_b.flavor.minimum_memory):
        return (1.0 + max(0.001, vnf_b.vm_memory / vnf_b.flavor.minimum_memory)) * 0.5

    if (vnf_a.vm_memory < vnf_a.flavor.minimum_memory and vnf_b.vm_memory >= vnf_b.flavor.minimum_memory):
        return (max(0.001, vnf_a.vm_memory / vnf_a.flavor.minimum_memory) + 1.0) * 0.5

    return (max(0.001, vnf_a.vm_memory / vnf_a.flavor.minimum_memory) + max(0, vnf_b.vm_memory / vnf_b.flavor.minimum_memory)) * 0.5

def min_sto_affinity(vnf_a, vnf_b, fg, nsd):
    if (vnf_a.vm_storage >= vnf_a.flavor.minimum_storage and vnf_b.vm_storage >= vnf_b.flavor.minimum_storage):
        return 1.0

    if (vnf_a.vm_storage >= vnf_a.flavor.minimum_storage and vnf_b.vm_storage < vnf_b.flavor.minimum_storage):
        return (1.0 + max(0.001, vnf_b.vm_storage / vnf_b.flavor.minimum_storage)) * 0.5

    if (vnf_a.vm_storage < vnf_a.flavor.minimum_storage and vnf_b.vm_storage >= vnf_b.flavor.minimum_storage):
        return (max(0.001, vnf_a.vm_storage / vnf_a.flavor.minimum_storage) + 1.0) * 0.5

    return (max(0.001, vnf_a.vm_storage / vnf_a.flavor.minimum_storage) + max(0, vnf_b.vm_storage / vnf_b.flavor.minimum_storage)) * 0.5

def conflicts_affinity(vnf_a, vnf_b, fg, nsd):
    if (fg is not None):
        for conflict in nsd.conflicts.all():
            if ((conflict.vnf_a.pk == vnf_a.pk and conflict.vnf_b.pk == vnf_b.pk) or
                (conflict.vnf_a.pk == vnf_b.pk and conflict.vnf_b.pk == vnf_a.pk)):
                return 0.001
    return 1.0

def cpu_usage_affinity(vnf_a, vnf_b, fg, nsd):
    return max(0.001, 1.0 - ((vnf_a.cpu_usage + vnf_b.cpu_usage) / 100))

def mem_usage_affinity(vnf_a, vnf_b, fg, nsd):
    return max(0.001, 1.0 - ((vnf_a.memory_usage + vnf_b.memory_usage) / 100))

def sto_usage_affinity(vnf_a, vnf_b, fg, nsd):
    return max(0.001, 1.0 - ((vnf_a.storage_usage + vnf_b.storage_usage) / 100))

def bnd_usage_affinity(vnf_a, vnf_b, fg, nsd):
    if (fg is not None):
        flow = next((x for x in fg.flows.all() if ((x.source.pk == vnf_a.pk and x.destination.pk == vnf_b.pk) or (x.source.pk == vnf_b.pk and x.destination.pk == vnf_a.pk))), None)
        if (flow != None):
            return max(0.001, 1.0 - (flow.bandwidth_usage/100))
    return -1.0

def pkt_loss_affinity(vnf_a, vnf_b, fg, nsd):
    if (fg is not None):
        flow = next((x for x in fg.flows.all() if ((x.source.pk == vnf_a.pk and x.destination.pk == vnf_b.pk) or (x.source.pk == vnf_b.pk and x.destination.pk == vnf_a.pk))), None)
        if (flow != None):
            return max(0.001, 1.0 - (flow.packet_loss/100))
    return -1.0

def lat_affinity(vnf_a, vnf_b, fg, nsd):
    if (fg is not None):
        flow = next((x for x in fg.flows.all() if ((x.source.pk == vnf_a.pk and x.destination.pk == vnf_b.pk) or (x.source.pk == vnf_b.pk and x.destination.pk == vnf_a.pk))), None)
        if (flow != None):
            return 1 if (2 * flow.latency <= nsd.sla) else max(0.001, 1.0 - ((2 * flow.latency - nsd.sla) / nsd.sla))
    return -1.0


def random_affinity(vnf_a, vnf_b, fg, nsd):
    # your code goes here
    return random.uniform(0.001, 1.0)

def random_affinity(vnf_a, vnf_b, fg, nsd):
    return random.uniform(0.001, 1.0)