import scipy
import numpy

from util import *
from debug import *
from random import *


class Criterion(object):
    def __init__(self, name, type, scope, weight, formula):
        self.name = name
        self.type = type
        self.scope = scope
        self.formula = formula
        self.weight = weight


class VNF(object):
    class_sequence = 1
    types = [
        ('load balancer', 1),
        ('dpi', 2),
        ('firewall', 3),
        ('ips', 4),
        ('ids', 5),
        ('nat', 6),
        ('traffic counter', 7),
        ('cache', 8),
        ('proxy', 9)
    ]

    def __init__(self, pm, flavor, id=0, type=0, vm_cpu=0, vm_mem=0, vm_sto=0, cpu_usage=0, mem_usage=0, sto_usage=0, index=0, timestamp="", fg_id=0):
        self.id = VNF.class_sequence if id == 0 else id
        if (type == 0):
            self.type = choice(VNF.types)
            self.vm_cpu = numpy.random.uniform(0, 1, 1)[0] * 2000  # randrange(100, 2000, 100)
            self.vm_mem = numpy.random.uniform(0, 1, 1)[0] * 2000  # randrange(100, 2000, 100)
            self.vm_sto = numpy.random.uniform(0, 1, 1)[0] * 2000  # randrange(100, 2000, 100)

            self.cpu_usage = numpy.random.uniform(0, 1, 1)[0] * 40  # randint(1,40)
            self.mem_usage = numpy.random.uniform(0, 1, 1)[0] * 40  # randint(1,40)
            self.sto_usage = numpy.random.uniform(0, 1, 1)[0] * 40  # randint(1,40)
        else:
            self.type = type
            self.vm_cpu = vm_cpu
            self.vm_mem = vm_mem
            self.vm_sto = vm_sto

            self.cpu_usage = cpu_usage
            self.mem_usage = mem_usage
            self.sto_usage = sto_usage

        self.label = str(self.type[0]) + "." + str(self.type[1]) + "." + str(self.id)
        self.pm = pm
        self.flavor = flavor
        self.index = index
        self.timestamp = timestamp
        self.fg_id = fg_id

        VNF.class_sequence += 1

    def find_fgs(self, fgs):
        self.fgs = []
        try:
            self.fgs.append(fgs[self.fg_id])
            return True
        except:
            return False


class PhysicalMachine(object):
    class_sequence = 1

    def __init__(self, id=0, cpu=0.5, mem=0.5, sto=0.5):
        self.id = PhysicalMachine.class_sequence if id == 0 else id
        self.cpu = cpu
        self.mem = mem
        self.sto = sto
        PhysicalMachine.class_sequence += 1


class ForwardingGraph(object):
    class_sequence = 1

    def __init__(self, id=0, flows=None, nsd=None):
        self.id = ForwardingGraph.class_sequence if id == 0 else id
        self.label = "fg"
        self.flows = flows
        self.nsd = nsd

        ForwardingGraph.class_sequence += 1


class Flow(object):
    class_sequence = 1

    def __init__(self, src, dst, trf=0, lat=0, bnd_usage=0, pkt_loss=0):
        self.id = Flow.class_sequence
        self.src = src
        self.dst = dst
        if (trf != 0):
            self.traffic = trf
            self.latency = lat
            self.bnd_usage = bnd_usage
            self.pkt_loss = pkt_loss
        else:
            self.traffic = randint(1, 10)
            self.latency = randint(1, 30)
            self.bnd_usage = randint(1, 50)
            self.pkt_loss = randint(1, 5)
        Flow.class_sequence += 1


class Flavor(object):
    class_sequence = 1

    def __init__(self, id=0, min_cpu=0, min_mem=0, min_sto=0):
        self.id = Flavor.class_sequence if id == 0 else id
        if (min_cpu != 0):
            self.min_cpu = min_cpu
            self.min_mem = min_mem
            self.min_sto = min_sto
        else:
            self.min_cpu = numpy.random.uniform(0, 1, 1)[0] * 2000  # randrange(1000, 2000, 100)
            self.min_mem = numpy.random.uniform(0, 1, 1)[0] * 2000  # randrange(1000, 2000, 100)
            self.min_sto = numpy.random.uniform(0, 1, 1)[0] * 2000  # randrange(1000, 2000, 100)
        Flavor.class_sequence += 1


class NSD(object):
    def __init__(self, sla=0.0, conflicts=[]):
        self.sla = numpy.random.uniform(0, 1, 1)[0] * 50 if (sla == 0.0) else sla
        self.conflicts = conflicts
        self.conflicts.append({'vnf_a': 2,  'vnf_b': 3})
