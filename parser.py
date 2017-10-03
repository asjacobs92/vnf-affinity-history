import csv
from functools import *
from multiprocessing.pool import ThreadPool

from affinity import *


def parse_vnf(row):
    vnf_id = int(row[0])
    vnf_type = int(row[1])
    vnf_scheduling = int(row[2])
    vnf_pm = int(row[3])
    vnf_fg = int(row[4])
    flavor_data = row[5:8]
    vm_data = row[8:11]
    usage_data = row[11:14]

    pm = PhysicalMachine(vnf_pm)
    flavor = Flavor(min_cpu=float(flavor_data[0]), min_mem=float(flavor_data[1]), min_sto=float(flavor_data[2]))

    return VNF(pm, flavor,
               id=vnf_id,
               fg_id=vnf_fg,
               scheduling_class=vnf_scheduling,
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
        p = ThreadPool()
        vnfs = p.map(parse_vnf, list(reader))
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
            fg_scheduling = int(row[2])
            flows = []
            nsd = None
            for i in range(fg_num_flows):
                flow_data = next(reader)
                flow = Flow(flow_data[0], flow_data[1], float(flow_data[2]), float(flow_data[3]), float(flow_data[4]), float(flow_data[5]))
                flows.append(flow)
                if (nsd is None):
                    nsd = NSD(sla=float(flow_data[6]))

            fgs[fg_id] = ForwardingGraph(fg_id, scheduling_class=fg_scheduling, flows=flows, nsd=nsd)

    return fgs


def find_vnf(vnf_id, vnfs):
    for vnf in vnfs:
        if (vnf.id == vnf_id):
            return vnf
    return None


def parse_affinity_case(vnfs, fgs, case):
    vnf_a_id = int(case[len(case) - 4])
    vnf_b_id = int(case[len(case) - 3])
    fg_id = int(case[len(case) - 2])
    affinity = float(case[len(case) - 1])

    vnf_a = find_vnf(vnf_a_id, vnfs)
    vnf_b = find_vnf(vnf_b_id, vnfs)
    fg = fgs[fg_id] if fg_id != 0 else None
    return (vnf_a, vnf_b, fg, affinity)


def parse_dataset(vnfs, fgs):
    dataset = []

    with open("res/input/nn_dataset.csv", "rb") as file:
        reader = csv.reader(file, delimiter=",")
        p = ThreadPool()
        func = partial(parse_affinity_case, vnfs, fgs)
        dataset = p.map(func, list(reader))
        p.close()
        p.join()

    return dataset
