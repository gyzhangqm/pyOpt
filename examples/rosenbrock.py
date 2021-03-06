#!/usr/bin/env python
# coding: utf-8

"""Solves Rosenbrock's Unconstrained Problem.

    min     100*(x2-x1^2)**2 + (1-x1)^2
    s.t.:   -10 <= xi <= 10,  i = 1,2
    
    f* = 0 , x* = [1, 1]

"""

from __future__ import print_function

# from pyOpt import *
from pyOpt.optimization import Optimization
from pyOpt.pyPSQP.pyPSQP import PSQP
from pyOpt.pySLSQP.pySLSQP import SLSQP
from pyOpt.pyCONMIN.pyCONMIN import CONMIN
from pyOpt.pyCOBYLA.pyCOBYLA import COBYLA
from pyOpt.pySOLVOPT.pySOLVOPT import SOLVOPT
from pyOpt.pyKSOPT.pyKSOPT import KSOPT
from pyOpt.pyNSGA2.pyNSGA2 import NSGA2
from pyOpt.pySDPEN.pySDPEN import SDPEN


def objfunc(x):
    r"""Objective function

    Parameters
    ----------
    x : iterable

    Returns
    -------
    tuple

    """
    f = 100 * (x[1] - x[0]**2)**2 + (1 - x[0])**2
    g = []

    fail = 0
    return f, g, fail


opt_prob = Optimization('Rosenbrock Unconstraint Problem', objfunc)
opt_prob.addVar('x1', 'c', lower=-10.0, upper=10.0, value=-3.0)
opt_prob.addVar('x2', 'c', lower=-10.0, upper=10.0, value=-4.0)
opt_prob.addObj('f')
print(opt_prob)

# Instantiate Optimizer (PSQP) & Solve Problem
psqp = PSQP()
psqp.setOption('IPRINT', 0)
psqp(opt_prob, sens_type='FD')
print(opt_prob.solution(0))

# Instantiate Optimizer (SLSQP) & Solve Problem
slsqp = SLSQP()
slsqp.setOption('IPRINT', -1)
slsqp(opt_prob, sens_type='FD')
print(opt_prob.solution(1))

# Instantiate Optimizer (CONMIN) & Solve Problem
conmin = CONMIN()
conmin.setOption('IPRINT', 0)
conmin(opt_prob, sens_type='CS')
print(opt_prob.solution(2))

# Instantiate Optimizer (COBYLA) & Solve Problem
cobyla = COBYLA()
cobyla.setOption('IPRINT', 0)
cobyla(opt_prob)
print(opt_prob.solution(3))

# Instantiate Optimizer (SOLVOPT) & Solve Problem
solvopt = SOLVOPT()
solvopt.setOption('iprint', -1)
solvopt(opt_prob, sens_type='FD')
print(opt_prob.solution(4))

# Instantiate Optimizer (KSOPT) & Solve Problem
ksopt = KSOPT()
ksopt.setOption('IPRINT', 0)
ksopt(opt_prob, sens_type='FD')
print(opt_prob.solution(5))

# Instantiate Optimizer (NSGA2) & Solve Problem
nsga2 = NSGA2()
nsga2.setOption('PrintOut', 0)
nsga2(opt_prob)
print(opt_prob.solution(6))

# Instantiate Optimizer (SDPEN) & Solve Problem
sdpen = SDPEN()
sdpen.setOption('iprint', -1)
sdpen(opt_prob)
print(opt_prob.solution(7))
