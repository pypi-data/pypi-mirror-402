import time
import sys
from IPython.display import Video, Image

# import dill
import PIL.Image

# import skrf as rf
from pprint import pprint
import os
import subprocess
import json
import numpy as np
import requests

from .sparams import *
from .utils import *
from .layers import *
from .constants import *
from .log import *
from PIL import Image as PILImage

from subprocess import Popen, PIPE




def solve(path):
    prob=load_prob(path)
    client=prob['client']
    study=prob['study']
    timestamp=prob['timestamp']
    study_type=prob['study_type']
    version=VERSION

    if client=='local':
        0
    else:
        print('')
        client_do(client,'submit',study,path,timestamp,version=version,study_type=study_type)
        # cloud=client['cloud']
        # email=client['email']
        while True:
            status=client_do(client,'query',study=study,version=version)
            if status=='success':
                print("simulation completed successfully!")
                client_do(client,'retrieve',study=study,path=path,version=version)
                break
            elif status=='failed':
                raise Exception("simulation failed!")
                break
            # print(e)
            time.sleep(3+np.random.rand())

        # for i in range(2):
        #     client_ping()
        #     time.sleep(5+np.random.rand())
        #     if  os.path.exists(SERVER):
        #         break
        #     else:
        #         print("servers busy or inactive. starting additional server. this may take up to 2 minutes ...")
        #         r=cloud_start(cloud)
        #         if r=='success':
        #             print("server started successfully. your job is in the jobs. please wait ...")
        #             break
        #         elif r=='busy':
        #             print("all servers are busy. your job is in the jobs. please wait ...")
        #         else:
        #             # raise Exception("can't start server - please try again later - report issue to https://github.com/paulxshen/Luminescent.jl/issues")
        #             0

    # elif client='local':
    #     0
    #     c = run(
    #         [
    #             "luminescent",
    #             path,
    #             prob["gpu_backend"],
    #             # f" --julia-args -t{nthreads}",
    #             f"--julia-args --threads={nthreads}",
    #         ]
    #     )
    #     if c != 0:
    #         print("can't find fdtd binary ")
    #         # exit(1)
    # except:
    #     print("failed")

    # except:
    # run(["julia", "-e", f'println(Base.active_project())'])
    # print("no binaries found - starting julia session to compile - will alternate between execution and JIT compilation - will take 3 mins before simulation starts.\nYou can take a break and come back :) ...")

    # prob = json.loads(open(os.path.join(path, "problem.json"), "rb").read())
    # a = ['julia', '-e', ]
    # gpu_backend = prob["gpu_backend"]
    # _class = prob["class"]
    # if gpu_backend == "CUDA":
    #     array = "cu"
    #     pkgs = ",CUDA"
    # else:
    #     array = "Array"
    #     pkgs = ""

    # run([f'using Luminescent;picrun(raw"{path}")'])
    # b = [f'using Luminescent{pkgs};{_class}run(raw"{path}",{array})']
    # run(a+b)

    # with Popen(cmd,  stdout=PIPE, stderr=PIPE) as p:
    #     if p.stderr is not None:
    #         for line in p.stderr:
    #             print(line, flush=True)
    # exit_code = p.poll()
    # subprocess.run()
    # print(f"julia simulation took {time.time()-timestamp} seconds")
    # print(f"images and results saved in {path}")
    # sol = load(path=path)
    # return sol


def load_sparams(sparams):
    if "re" in list(sparams.values())[0]:
        return {k: v["re"] + 1j * v["im"] for k, v in sparams.items()}
    return {
        wavelength: {k: (v["re"] + 1j * v["im"]) for k, v in d.items()}
        for wavelength, d in sparams.items()
    }


def load(path, show=True):
    path = os.path.abspath(path)
    print(f"loading solution from {path}")
    print(f"may take a minute if simulation folder is remotely mounted")
    return readjsonnp(os.path.join(path, "solution.json"))


def design_from_gds(path, i=1):
    # make_design_gds(path)
    c = gf.import_gds(os.path.join(path, f"design{i}.gds"))
    d = json.load(open(os.path.join(path, "info.json")))
    for p in d[f"designs"][i - 1]["ports"]:
        c.add_port(**p, layer=WG)
    c.info = d
    return c
