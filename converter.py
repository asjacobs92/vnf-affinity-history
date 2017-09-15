import csv
import numpy
import scipy
import scipy.stats
import os

from time import *
from math import *
from time import *
from random import *
from affinity import *
from multiprocessing import *

vnfs = []
fgs = []
pms = []

num_files = 1


def read_fg(job):
    fg = None
    if (int(job[3]) == 1):
        fg_id = int(job[2])

        flows = []
        fg_vnfs = filter(lambda x: x.fg_id == fg_id, vnfs)
        fg_vnfs.sort(key=lambda x: x.index, reverse=False)
        for i in range(len(fg_vnfs) - 1):
            src = fg_vnfs[i]
            dst = fg_vnfs[i + 1]

            traffic = numpy.random.uniform(0, 1, 1)[0] * 10
            latency = numpy.random.uniform(0, 1, 1)[0] * 50
            bnd_usage = numpy.random.uniform(0, 1, 1)[0] * 60
            pkt_loss = numpy.random.uniform(0, 1, 1)[0] * 10
            flows.append(Flow(src.label, dst.label, traffic, latency, bnd_usage, pkt_loss))

            fg = ForwardingGraph(fg_id, flows, nsd=NSD())
    return fg


def read_job_events():
    fgs = []
    for i in range(num_files):
        with open("res/dataset/je-part-0000" + str(i) + "-of-00500.csv", "rb") as file_fgs:
            reader_fgs = csv.reader(file_fgs)

            p = Pool()
            fgs = filter(None, p.map(read_fg, list(reader_fgs)))
    return fgs


def read_task_usage(fg_id, vnf_index, pm):
    num_usage_files = 1
    for i in range(num_usage_files):
        with open("res/dataset/tu-part-00000-of-00500.csv", "rb") as file_usage:
            reader_usage = csv.reader(file_usage)
            cpu_usage = 0
            mem_usage = 0
            sto_usage = 0

            for usage in reader_usage:
                if (int(usage[2]) == fg_id and int(usage[3]) == vnf_index and usage[13] != "" and usage[10] != "" and usage[14] != ""):
                    cpu_usage = (float(usage[13]) / pm.cpu) * 100
                    mem_usage = (float(usage[10]) / pm.mem) * 100
                    sto_usage = (float(usage[14]) / pm.sto) * 100
                    break

    return cpu_usage, mem_usage, sto_usage


def read_vnf(task):
    vnf = None
    if (int(task[5]) == 1):
        timestamp = task[0]
        fg_id = int(task[2])
        vnf_index = int(task[3])
        vnf_type = choice(VNF.types)

        pm_id = int(task[4])
        #pm = next((x for x in pms if x.id == pm_id), None)
        pm = None
        for p in pms:
            if (p.id == pm_id):
                pm = p
                break
        if (pm is None):
            pm = PhysicalMachine(pm_id)
            pms.append(pm)

        cpu_usage, mem_usage, sto_usage = read_task_usage(fg_id, vnf_index, pm)

        if (cpu_usage != 0 and mem_usage != 0 and sto_usage != 0):
            vm_cpu = float(task[9])
            vm_mem = float(task[10])
            vm_sto = float(task[11])

            flavor = Flavor(min_cpu=vm_cpu * numpy.random.uniform(0, 1, 1)[0] * 2,
                            min_mem=vm_mem * numpy.random.uniform(0, 1, 1)[0] * 2,
                            min_sto=vm_sto * numpy.random.uniform(0, 1, 1)[0] * 2)

            vnf = VNF(pm=pm,
                      flavor=flavor,
                      type=vnf_type,
                      vm_cpu=vm_cpu,
                      vm_mem=vm_mem,
                      vm_sto=vm_sto,
                      cpu_usage=cpu_usage,
                      mem_usage=mem_usage,
                      sto_usage=sto_usage,
                      index=vnf_index,
                      timestamp=timestamp,
                      fg_id=fg_id)
    return vnf


def read_task_events():
    vnfs = []
    for i in range(num_files):
        with open("res/dataset/te-part-0000" + str(i) + "-of-00500.csv", "rb") as file_tasks:
            reader_tasks = csv.reader(file_tasks)

            p = Pool()
            vnfs = filter(None, p.map(read_vnf, list(reader_tasks)[150000:150050]))
    return vnfs


def read_pm(machine):
    pm = None
    if (int(machine[2]) == 0):
        pm_id = int(machine[1])
        pm_cpu = float(machine[4]) if machine[4] is not "" else 0.5
        pm_mem = float(machine[5]) if machine[5] is not "" else 0.5
        pm_sto = 0.5
        pm = PhysicalMachine(pm_id)
    return pm


def read_machine_events():
    pms = []
    with open("res/dataset/me-part-00000-of-00001.csv", "rb") as file_pms:
        reader_pms = csv.reader(file_pms)
        p = Pool()
        pms = filter(None, p.map(read_pm, list(reader_pms)))
    return pms


def read():
    global pms, vnfs, fgs

    print "reading pms"
    pms = read_machine_events()
    print "pms read: " + str(len(pms))

    print "reading tasks"
    vnfs = read_task_events()
    print "vnfs read: " + str(len(vnfs))

    print "reading jobs"
    fgs = read_job_events()
    print "fgs read: " + str(len(fgs))


def write():
    with open("res/input/vnfs2.csv", "wb") as file:
        writer = csv.writer(file, delimiter=",")
        for vnf in vnfs:
            row = [
                vnf.id, vnf.type[1], vnf.pm.id, vnf.fg_id,
                vnf.flavor.min_cpu, vnf.flavor.min_mem, vnf.flavor.min_sto,
                vnf.vm_cpu, vnf.vm_mem, vnf.vm_sto,
                vnf.cpu_usage, vnf.mem_usage, vnf.sto_usage
            ]
            writer.writerow(row)

    with open("res/input/fgs2.csv", "wb") as file:
        writer = csv.writer(file, delimiter=",")
        for fg in fgs:
            fg_row = [fg.id, len(fg.flows)]
            writer.writerow(fg_row)
            for flow in fg.flows:
                flow_row = [flow.src, flow.dst, flow.traffic, flow.latency, flow.bnd_usage, flow.pkt_loss, fg.nsd.sla]
                writer.writerow(flow_row)


if __name__ == "__main__":
    start = time()
    print "reading vm dataset"
    read()
    end = time()
    print(end - start)

    start = time()
    print "writing vnf dataset"
    write()
    end = time()
    print(end - start)
