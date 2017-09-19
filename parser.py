import csv
from multiprocessing import *

from affinity import *


def parse_vnf(row):
    vnf_id = int(row[0])
    vnf_type = int(row[1])
    vnf_pm = int(row[2])
    vnf_fg = int(row[3])
    flavor_data = row[4:7]
    vm_data = row[7:10]
    usage_data = row[10:13]

    pm = PhysicalMachine(vnf_pm)
    flavor = Flavor(min_cpu=float(flavor_data[0]), min_mem=float(flavor_data[1]), min_sto=float(flavor_data[2]))

    return VNF(pm, flavor,
               id=vnf_id,
               fg_id=vnf_fg,
               type=next((x for x in VNF.types if vnf_type == x[1]), choice(VNF.types)),
               vm_cpu=float(vm_data[0]),
               vm_mem=float(vm_data[1]),
               vm_sto=float(vm_data[2]),
               cpu_usage=float(usage_data[0]),
               mem_usage=float(usage_data[1]),
               sto_usage=float(usage_data[2]))


def parse_vnfs():
    vnfs = []
    with open("res/input/vnfs.csv", "rb") as file:
        reader = csv.reader(file, delimiter=",")
        p = Pool()
        vnfs = p.map(parse_vnf, list(reader)[0:10000])
        p.close()
        p.join()

    return vnfs


def parse_fgs():
    fgs = {}
    with open("res/input/fgs.csv", "rb") as file:
        reader = csv.reader(file, delimiter=",")
        for row in reader:
            fg_id = int(row[0])
            fg_num_flows = int(row[1])
            flows = []
            nsd = None
            for i in range(fg_num_flows):
                flow_data = next(reader)
                flow = Flow(flow_data[0], flow_data[1], float(flow_data[2]), float(flow_data[3]), float(flow_data[4]), float(flow_data[5]))
                flows.append(flow)
                if (nsd is None):
                    nsd = NSD(sla=float(flow_data[6]))

            fgs[fg_id] = ForwardingGraph(fg_id, flows=flows, nsd=nsd)

    return fgs
