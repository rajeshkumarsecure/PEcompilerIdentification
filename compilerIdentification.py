#!/usr/bin/python3

# Dependencies:
# Detect It Easy(DIE): https://github.com/horsicq/DIE-engine/releases


import json
import multiprocessing as mp
from multiprocessing import pool
import os
import subprocess
import sys

def listener(queue, inp_dir):    
    '''listens for incomming messages on queue and writes them to the file. '''

    # Removing trailing slash (if present) in the input folder name
    if inp_dir.endswith("/"):
        inp_dir = inp_dir[:-1]

    with open("result_{0}.txt".format(inp_dir), 'w') as out_file:

        out_file.write("File\tCompiler\n")

        while 1:
            message = queue.get()
            if message == 'kill':
                break
            out_file.write(str(message) + '\n')
            out_file.flush()

def find_compiler(inp_file, file_name, queue):
    '''finds the compiler type using DIE and writes the output to queue'''
    
    DIE_Ouptut = subprocess.check_output(["diec", "-j", inp_file], stderr=subprocess.DEVNULL)
    try:
        for item in json.loads(DIE_Ouptut)["detects"][0]["values"]:
            if item["type"] == "Compiler" or item["type"] == "Library":
                queue.put("{0}\t{1}".format(file_name, item["name"]))
    except:
        queue.put("{0}\t{1}".format(file_name, "NA"))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Please provide the folder name which contains the input samples...")
        sys.exit(0)

    inp_dir = sys.argv[1].strip()

    manager = mp.Manager()
    queue = manager.Queue()
    pool = mp.Pool(mp.cpu_count())

    #put listener to work first
    watcher = pool.apply_async(listener, (queue, inp_dir))

    jobs = []

    for each_file in os.listdir(inp_dir):
        file_path = os.path.join(inp_dir, each_file)
        job = pool.apply_async(find_compiler, (file_path, each_file, queue))
        jobs.append(job)

    # collect results from the workers throught the pool result queue
    for job in jobs:
        job.get()

    
    # Kill the listener
    queue.put('kill')
    pool.close()
    pool.join()
    