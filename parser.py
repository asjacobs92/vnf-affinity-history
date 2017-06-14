from models import *

def parse_sla(data):
    return data["sla"]

def parse_conflicts(data):
    return data["conflicts"]
    
def parse_weight(data, criterion_name):
    try:
        return data["weights"][criterion_name]
    except:
        return 1

def parse_pms(data):
    pms = []
    for pm_data in data["pms"]:
        pms.append(PhysicalMachine(**pm_data))
    return pms

def parse_fgs(data):
    fgs = []
    for fg_data in data["fgs"]:
        flows = []
        for flow_data in fg_data["flows"]:
            flows.append(Flow(**flow_data))
        fg = ForwardingGraph(**fg_data)
        fg.flows = flows
        fgs.append(fg)
    return fgs

def parse_flavors(data):
    flavors = []
    for flavor_data in data["flavors"]:
        flavors.append(Flavor(**flavor_data))
    return flavors

def parse_vnfs(data, pms, fgs, flavors):
    vnfs = []
    for vnf_data in data["vnfs"]:
        vnf_pm = next((x for x in pms if x.id == int(vnf_data["pm"])), None)
        vnf_flavor = next((x for x in flavors if x.id == int(vnf_data["flavor"])), None)
        vnf_fgs = []
        for vnf_fg in vnf_data["fgs"]:
            vnf_fgs.append(next((x for x in fgs if x.id == int(vnf_fg)), None))
        vnf = VNF(**vnf_data)
        vnf.pm = vnf_pm
        vnf.flavor = vnf_flavor
        vnf.fgs = vnf_fgs
        vnfs.append(vnf)  
    return vnfs
