import argparse
import json
import sys

import numpy as np
from generador import *
from tqdm import *
import time

sys.path.append('../')

parser = argparse.ArgumentParser()

try:
    # Número de trabajos
    parser.add_argument('-J','--jobs', type=json.loads, default='[10]')
    # Número de Máquinas
    parser.add_argument('-M','--machines', type=json.loads, default='[4]')
    # Semilla
    parser.add_argument('-s','--seeds', type= json.loads, default='[0]')

    # Speed Scaling
    parser.add_argument('-S', '--speed-scaling', type=int, default=1)

    # Release and Due date
    # 0 -> Tiempo infinito
    # 1 -> Tiempo por trabajo
    # 2 -> Tiempo por tarea de cada trabajo
    parser.add_argument('-RDDD', '--release-due', type=int, default=0, choices=[0, 1, 2])
    # Time
    # parser.add_argument('-Ti', '--time', type=int, default=0)
    # Path
    parser.add_argument('-P', '--path', type=str, default="./output")
    # Probability
    # parser.add_argument('-prb', '--prb', type=float, default=0.1)
    # Quantity
    parser.add_argument('-Q', '--quantity', type=int, default=1)
    # Distribution
    parser.add_argument('-D','--distribution', type=str, default="normal")

    # JSON save
    parser.add_argument('-j','--json', type=bool, default=False)
    # DZN save
    parser.add_argument('-d','--dzn', type=bool, default=False)
    # Taillard save
    parser.add_argument('-t','--taillard', type=bool, default=False)

    #Instance Type (JSP o FJSP)
    parser.add_argument('-T', '--type', type=int, default=1, choices=[1, 2])

    args = parser.parse_args()

    type_dict = {
        1: "JSP",
        2: "FJSP"
    }

    np.random.seed(args.seeds)

    start = time.time()
    for j in tqdm(args.jobs,desc='Jobs',leave=False):
        for m in tqdm(args.machines,desc='Machines',leave=False):

            generator = Generator(json = args.json, dzn = args.dzn, taillard = args.taillard)
            if len(args.seeds) < args.quantity:
                # args.seeds = args.seeds + list(np.zeros(args.quantity - len(args.seeds),dtype=np.int64))
                p_s = np.linspace(0, 100, num=100,dtype=np.int64)
                for s in args.seeds:
                    p_s = p_s[p_s!=s]
                args.seeds = args.seeds+ list(p_s[:args.quantity-len(args.seeds)])
            for i in trange(args.quantity,desc='Quantity',leave=False):
                generator.savepath = args.path+"/instancesGenerated_"+str(i)
                generator.generate_new_instance(jobs=j, machines=m, ReleaseDateDueDate=np.array(args.release_due), speed = args.speed_scaling,
                                                distribution=args.distribution, seed=args.seeds[i], instance_type=type_dict[args.type])
    
except Exception as e:
    raise