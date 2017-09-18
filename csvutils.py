import csv
from affinity import *


class CsvUtils(object):
    def __init__(self, file, dialect=csv.excel):
        self.writer = csv.writer(file, dialect=dialect, delimiter=',')

    def write_row(self, row):
        self.writer.writerow(row)

    def get_headers(self):
        headers = [
            "vnf label",
            "vnf min cpu",
            "vnf min mem",
            "vnf min sto",
            "vnf vm cpu",
            "vnf vm mem",
            "vnf vm sto",
            "vnf pm id",
            "vnf cpu usage",
            "vnf mem usage",
            "vnf sto usage",
            "vnf before",
            "vnf after",
            "vnf label",
            "vnf min cpu",
            "vnf min mem",
            "vnf min sto",
            "vnf vm cpu",
            "vnf vm mem",
            "vnf vm sto",
            "vnf pm id",
            "vnf cpu usage",
            "vnf mem usage",
            "vnf sto usage",
            "vnf before",
            "vnf after",
            "sla",
            "fg id",
            "flow traffic",
            "flow latency",
            "flow bnd usage",
            "flow packet loss",
            "min cpu affinity",
            "min mem affinity",
            "min sto affinity",
            "conflicts affinity"
        ]
        return headers

    def get_row_data(self, vnf_a, vnf_b, fg):
        vnf_a_before_id = ""
        vnf_a_after_id = ""
        vnf_b_before_id = ""
        vnf_b_after_id = ""
        flow = None
        if (fg is not None):
            vnf_a_before_id = next((x.src for x in fg.flows if x.dst == vnf_a.label), None) if (
                fg is not None) else "-1.-1"
            vnf_a_after_id = next((x.dst for x in fg.flows if x.src == vnf_a.label), None) if (
                fg is not None) else "-1.-1"
            vnf_b_before_id = next((x.src for x in fg.flows if x.dst == vnf_b.label), None) if (
                fg is not None) else "-1.-1"
            vnf_b_after_id = next((x.dst for x in fg.flows if x.src == vnf_b.label), None) if (
                fg is not None) else "-1.-1"
            flow = next((x for x in fg.flows if (x.dst == vnf_a.label and x.src == vnf_b.label) or (
                x.src == vnf_a.label and x.dst == vnf_b.label)), None)

        values = [
            vnf_a.label,
            vnf_a.flavor.min_cpu,
            vnf_a.flavor.min_mem,
            vnf_a.flavor.min_sto,
            vnf_a.vm_cpu,
            vnf_a.vm_mem,
            vnf_a.vm_sto,
            vnf_a.pm.id,
            vnf_a.cpu_usage,
            vnf_a.mem_usage,
            vnf_a.sto_usage,
            vnf_a_before_id,
            vnf_a_after_id,
            vnf_b.label,
            vnf_b.flavor.min_cpu,
            vnf_b.flavor.min_mem,
            vnf_b.flavor.min_sto,
            vnf_b.vm_cpu,
            vnf_b.vm_mem,
            vnf_b.vm_sto,
            vnf_b.pm.id,
            vnf_b.cpu_usage,
            vnf_b.mem_usage,
            vnf_b.sto_usage,
            vnf_b_before_id,
            vnf_b_after_id,
            fg.nsd.sla if (fg is not None) else 0,
            fg.id if (fg is not None) else "",
            flow.traffic if (flow is not None) else "",
            flow.latency if (flow is not None) else "",
            flow.bnd_usage if (flow is not None) else "",
            flow.pkt_loss if (flow is not None) else "",
            min_cpu_affinity(vnf_a, vnf_b, fg),
            min_mem_affinity(vnf_a, vnf_b, fg),
            min_sto_affinity(vnf_a, vnf_b, fg),
            conflicts_affinity(vnf_a, vnf_b, fg)
        ]
        return values
