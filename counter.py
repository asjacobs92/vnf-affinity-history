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

num_jobs = 0
num_pms = 0
num_tasks = 0

num_files = 1


def count_jobs():
    global num_jobs
    for i in range(num_files):
        with open("res/dataset/je-part-0000" + str(i) + "-of-00500.csv", "rb") as file_fgs:
            reader_fgs = csv.reader(file_fgs)
            for line in reader_fgs:
                if (int(line[3]) == 1):
                    num_jobs += 1


def count_tasks():
    global num_tasks
    for i in range(num_files):
        with open("res/dataset/te-part-0000" + str(i) + "-of-00500.csv", "rb") as file_tasks:
            reader_tasks = csv.reader(file_tasks)
            for line in reader_tasks:
                if (int(line[5]) == 1):
                    num_tasks += 1


def count_machines():
    global num_pms
    with open("res/dataset/me-part-00000-of-00001.csv", "rb") as file_pms:
        reader_pms = csv.reader(file_pms)
        for line in reader_pms:
            if (int(line[2]) == 0):
                num_pms += 1


def count():
    print "counting pms"
    count_machines()
    print "pms read: " + str(num_pms)

    print "counting tasks"
    count_tasks()
    print "vnfs read: " + str(num_tasks)

    print "counting jobs"
    count_jobs()
    print "fgs read: " + str(num_jobs)


if __name__ == "__main__":
    count()
