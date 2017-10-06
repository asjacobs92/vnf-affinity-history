import csv
import os
from math import *
from multiprocessing import *
from multiprocessing.pool import ThreadPool
from random import *
from time import *

import numpy
import scipy
import scipy.stats

from affinity import *

vnfs = []
fgs = []
pms = []

num_files = 1

execution_times = {}


def read_fg(job):
    fg = None
    if (int(job[3]) == 1):
        fg_id = int(job[2])
        fg_scheduling = int(job[5])
        max_latency = (4 - fg_scheduling) * 50.0

        flows = []
        fg_vnfs = filter(lambda x: x.fg_id == fg_id, vnfs)
        fg_vnfs.sort(key=lambda x: x.index, reverse=False)
        for i in range(len(fg_vnfs) - 1):
            src = fg_vnfs[i]
            dst = fg_vnfs[i + 1]

            traffic = numpy.random.uniform(0, 1, 1)[0] * 10
            latency = numpy.random.uniform(0, 1, 1)[0] * max_latency
            bnd_usage = numpy.random.uniform(0, 1, 1)[0] * 20
            pkt_loss = numpy.random.uniform(0, 1, 1)[0] * 10
            flows.append(Flow(src.label, dst.label, traffic, latency, bnd_usage, pkt_loss))

            fg = ForwardingGraph(fg_id, fg_scheduling, flows, nsd=NSD(sla=max_latency))
            if (len(fg.flows) == 0):
                fg = None
    return fg


def read_job_events():
    fgs = []
    for i in range(num_files):
        with open("res/dataset/je-part-0000" + str(i) + "-of-00500.csv", "rb") as file_fgs:
            reader_fgs = csv.reader(file_fgs)

            p = ThreadPool()
            fgs = filter(None, p.map(read_fg, list(reader_fgs)))
            p.close()
            p.join()
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
                    cpu_usage = min(100.0, (float(usage[13]) / pm.cpu) * 100)
                    mem_usage = min(100.0, (float(usage[10]) / pm.mem) * 100)
                    sto_usage = min(100.0, (float(usage[14]) / pm.sto) * 100)
                    break

    return cpu_usage, mem_usage, sto_usage


def read_vnf(task):
    vnf = None

    # start event
    if (int(task[5]) == 1):
        timestamp = int(task[0])
        fg_id = int(task[2])
        vnf_index = int(task[3])
        vnf_scheduling = int(task[7])

        pm_id = int(task[4])
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
            possible_types = filter(lambda x: x[3] <= cpu_usage and cpu_usage <= x[4],  VNF.types)
            vnf_type = choice(possible_types)

            flavor = Flavor(min_cpu=vm_cpu * numpy.random.uniform(0, 1, 1)[0] * 2,
                            min_mem=vm_mem * numpy.random.uniform(0, 1, 1)[0] * 2,
                            min_sto=vm_sto * numpy.random.uniform(0, 1, 1)[0] * 2)

            with lock:
                vnf_sequence.value += 1

                vnf = VNF(pm=pm,
                          flavor=flavor,
                          id=vnf_sequence.value,
                          type=vnf_type,
                          vm_cpu=vm_cpu,
                          vm_mem=vm_mem,
                          vm_sto=vm_sto,
                          cpu_usage=cpu_usage,
                          mem_usage=mem_usage,
                          sto_usage=sto_usage,
                          index=vnf_index,
                          scheduling_class=vnf_scheduling,
                          timestamp=timestamp,
                          fg_id=fg_id)

                if ((fg_id, vnf_index) in execution_times):
                    (start_timestamp, stop_timestamp) = execution_times[(fg_id, vnf_index)]
                    execution_times[(fg_id, vnf_index)] = (timestamp, stop_timestamp)
                    print (timestamp, stop_timestamp)
                else:
                    execution_times[(fg_id, vnf_index)] = (timestamp, 0)
                    print (timestamp, 0)

                if (first_tstamp.value == 0):
                    first_tstamp.value = timestamp

                # if (vnf_sequence.value % 10000 == 0):
                print vnf.id

    # stop event
    if (int(task[5]) == 4):
        timestamp = int(task[0])
        fg_id = int(task[2])
        vnf_index = int(task[3])

        with lock:
            if (first_tstamp.value == 0):
                first_tstamp.value = timestamp

            if ((fg_id, vnf_index) in execution_times):
                (start_timestamp, stop_timestamp) = execution_times[(fg_id, vnf_index)]
                if (start_timestamp == 0):
                    start_timestamp = first_tstamp.value

                print (start_timestamp, timestamp)
                execution_times[(fg_id, vnf_index)] = (start_timestamp, timestamp)
            else:
                execution_times[(fg_id, vnf_index)] = (0, timestamp)
                print (0, timestamp)

    return vnf


def init_pool(l, v, ft):
    global lock, vnf_sequence, first_tstamp
    lock = l
    vnf_sequence = v
    first_tstamp = ft


def read_task_events():
    vnfs = []
    for i in range(num_files):
        with open("res/dataset/te-part-0000" + str(i) + "-of-00500.csv", "rb") as file_tasks:
            reader_tasks = csv.reader(file_tasks)
            p = ThreadPool(initializer=init_pool, initargs=(Lock(), Value('i', 0), Value('i', 0)))
            l = list(reader_tasks)[290000:330000]
            vnfs = filter(None, p.map(read_vnf, l))
            p.close()
            p.join()

    for vnf in vnfs:
        print vnf.id
        (start_timestamp, stop_timestamp) = execution_times[(vnf.fg_id, vnf.index)]
        print start_timestamp, stop_timestamp
        vnf.exec_time = stop_timestamp - start_timestamp

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
        p = ThreadPool()
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
    with open("res/input/vnfs.csv", "wb") as file:
        writer = csv.writer(file, delimiter=",")
        for vnf in vnfs:
            row = [
                vnf.id, vnf.type[1], vnf.scheduling_class, vnf.pm.id, vnf.fg_id,
                vnf.flavor.min_cpu, vnf.flavor.min_mem, vnf.flavor.min_sto,
                vnf.vm_cpu, vnf.vm_mem, vnf.vm_sto,
                vnf.cpu_usage, vnf.mem_usage, vnf.sto_usage, vnf.exec_time
            ]
            writer.writerow(row)

    with open("res/input/fgs.csv", "wb") as file:
        writer = csv.writer(file, delimiter=",")
        for fg in fgs:
            fg_row = [fg.id, len(fg.flows), fg.scheduling_class]
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
