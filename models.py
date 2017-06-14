from random import *
from debug import *

class Criterion(object):
    def __init__(self, name, type, scope, weight, formula):
        self.name = name
        self.type = type
        self.scope = scope
        self.formula = formula
        self.weight = weight
    
class VNF(object):
    class_sequence = 0
    def __init__(self, pm, flavor):
        self.id = VNF.class_sequence
        self.type = choice([
            ('load balancer', 1), 
            ('dpi', 2), 
            ('firewall', 3), 
            ('ips', 4), 
            ('ids', 5), 
            ('nat', 6), 
            ('traffic counter', 7), 
            ('cache', 8), 
            ('proxy', 9)])
        self.label = str(self.type[0]) + "." + str(self.type[1]) + "." + str(self.id)
        self.pm = pm
        self.flavor = flavor
        
        self.vm_cpu = randrange(1000, pm.cpu, 100)
        self.vm_mem = randrange(768, pm.mem, 256)
        self.vm_sto = randrange(800, pm.sto, 100)

        self.cpu_usage = randrange(5, 30, 1)
        self.mem_usage = randrange(5, 30, 1)
        self.sto_usage = randrange(5, 30, 1)
        
        VNF.class_sequence += 1
      
    def find_fgs(self, fgs):
        vnf_fgs = []
        for fg in fgs:
            flow = next((x for x in fg.flows if (x.src == self.label or x.dst == self.label)), None)
            if (flow is not None):
                vnf_fgs.append(fg)
        self.fgs = vnf_fgs

class PhysicalMachine(object):
    class_sequence = 0
    def __init__(self):
        self.id = PhysicalMachine.class_sequence
        self.cpu = randrange(1500, 4000, 100)
        self.mem = randrange(1024, 8196, 512)
        self.sto = randrange(1000, 8000, 100)
        PhysicalMachine.class_sequence += 1
    
class ForwardingGraph(object):
    class_sequence = 0
    def __init__(self, vnfs):
        self.id = ForwardingGraph.class_sequence
        self.label = "fg" + str(self.id)
        self.flows = []
        vnfs_ids = [x.label for x in vnfs]
        last_id = "0.0"
        num_flows = randrange(1, len(vnfs), 1)
        for i in range(num_flows):
            if (i + 1 == num_flows):
                dst = "0.0"
                self.flows.append(Flow(last_id, dst))
            else:
                dst = choice(vnfs_ids)
                vnfs_ids.remove(dst)
                self.flows.append(Flow(last_id, dst))
                last_id = dst
                
        ForwardingGraph.class_sequence += 1

class Flow(object):
    class_sequence = 0
    def __init__(self, src, dst):
        self.id = Flow.class_sequence
        self.src = src
        self.dst = dst
        self.traffic = randrange(10, 1000, 10)
        self.latency = randrange(1, 100, 1)
        self.bnd_usage = randrange(5, 80, 1)
        self.pkt_loss = randrange(1, 80, 1)
        Flow.class_sequence += 1

class Flavor(object):
    class_sequence = 0
    def __init__(self):
        self.id = Flavor.class_sequence
        self.min_cpu = randrange(1000, 1500, 100)
        self.min_mem = randrange(512, 2048, 256)
        self.min_sto = randrange(500, 1000, 100)
        Flavor.class_sequence += 1

class NSD(object):
    def __init__(self, sla = 0.0, conflicts = []):
        self.sla = randrange(10, 1000, 5) if (sla == 0.0) else sla
        self.conflicts = conflicts
