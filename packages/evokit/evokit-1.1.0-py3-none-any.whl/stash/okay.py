
from psutil import Process

from evokit.evolvables.prefabs import make_onemax

from viztracer import log_sparse

def accumulate_cpu_time(p: Process) -> float:
    my_cpu_time = p.cpu_times()
    total_time = my_cpu_time.user + my_cpu_time.system
    for pc in p.children():
        total_time += accumulate_cpu_time(pc)
    return total_time


@log_sparse
def test():
    make_algorithm =\
        lambda: make_onemax(1000, 1000, 0.02, max_parents=0)


    algo_2 = make_algorithm()


    for _ in range(6):
        algo_2.step()

if __name__ ==  '__main__':
    test()