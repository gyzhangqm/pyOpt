#!/usr/bin/env python
# coding: utf-8

"""pyALGENCAN - A Python pyOpt interface to ALGENCAN. 

Copyright (c) 2008-2014 by pyOpt Developers
All rights reserved.
Revision: 1.0   $Date: 10/06/2014 21:00$

Tested on:
---------
Win32 with g77
Linux with g77

Developers:
-----------
- Dr. Ruben E. Perez (RP)

History
-------
    v. 1.0  - Initial Class Creation (RP, 2011)
    V. 1.1  - Updated to Work with ALGENCAN 2.4 (RP, 2014)

"""

from __future__ import print_function

try:
    # import algencan
    from . import algencan
except ImportError:
    raise ImportError('ALGENCAN shared library failed to import')

import os
import copy
import time

import numpy

from pyOpt.optimizer import Optimizer
from pyOpt.gradient import Gradient
from pyOpt.utils import machine_precision

__version__ = '$Revision: $'

# ToDo:
#     - add evals return on source
#     - add unconstrained problems support

inf = 10.E+20  # define a value for infinity

eps = machine_precision()
# eps = math.ldexp(1,-52)


class ALGENCAN(Optimizer):
    """ALGENCAN Optimizer Class - Inherited from Optimizer Abstract Class"""
    def __init__(self, pll_type=None, *args, **kwargs):
        """ALGENCAN Optimizer Class Initialization

        **Keyword arguments:**

        - pll_type -> STR: Parallel Implementation (None,
                            'POA'-Parallel Objective Analysis), *Default* = None

        Documentation last updated:  Feb. 16, 2010 - Peter W. Jansen

        """
        if pll_type is None:
            self.poa = False
        elif pll_type.upper() == 'POA':
            self.poa = True
        else:
            raise ValueError("pll_type must be either None or 'POA'")

        name = 'ALGENCAN'
        category = 'Local Optimizer'
        def_opts = {
            # ALGENCAN Options
            'epsfeas': [float, 1.0e-8],  # Feasibility Convergence Accuracy
            'epsopt': [float, 1.0e-8],  # Optimality Convergence Accuracy
            'efacc': [float, 1.0e-4],  # Feasibility Level for Newton-KKT
                                       # Acceleration
            'eoacc': [float, 1.0e-4],  # Optimality Level for Newton-KKT
                                       # Acceleration
            'checkder': [bool, False],  # Check Derivatives Flag
            'iprint': [int, 10],  # Print Flag (0 - None, )
            'ifile': [str, 'ALGENCAN.out'],  # Output File Name
            'ncomp': [int, 6],  # Print Precision
        }
        informs = {
            0: "Solution was found.",
            1: "Stationary or infeasible point was found.",
            2: "penalty parameter is too large infeasible or "
               "badly scaled problem",
            3: "Maximum of iterations reached.",
        }
        Optimizer.__init__(self,
                           name,
                           category,
                           def_opts,
                           informs,
                           *args,
                           **kwargs)

    def __solve__(self,
                  opt_problem,
                  sens_type='FD',
                  store_sol=True,
                  disp_opts=False,
                  store_hst=False,
                  hot_start=False,
                  sens_mode='',
                  sens_step={},
                  *args,
                  **kwargs):
        """Run Optimizer (Optimize Routine)

        **Keyword arguments:**

        - opt_problem -> INST: Optimization instance
        - sens_type -> STR/FUNC: Gradient type, *Default* = 'FD' 
        - store_sol -> BOOL: Store solution in Optimization class flag,
                       *Default* = True 
        - disp_opts -> BOOL: Flag to display options in solution text,
                       *Default* = False
        - store_hst -> BOOL/STR: Flag/filename to store optimization history,
                       *Default* = False
        - hot_start -> BOOL/STR: Flag/filename to read optimization history,
                       *Default* = False
        - sens_mode -> STR: Flag for parallel gradient calculation,
                       *Default* = ''
        - sens_step -> FLOAT: Sensitivity setp size, *Default* = {}
                       [corresponds to 1e-6 (FD), 1e-20(CS)]

        Additional arguments and keyword arguments are passed to the
        objective function call.

        Documentation last updated:  February. 2, 2011 - Peter W. Jansen

        """
        if self.poa and (sens_mode.lower() == 'pgc'):
            raise NotImplementedError("pyALGENCAN - Current implementation "
                                      "only allows single level "
                                      "parallelization, either 'POA' or 'pgc'")

        if self.poa or (sens_mode.lower() == 'pgc'):
            try:
                import mpi4py
                from mpi4py import MPI
            except ImportError:
                print('pyALGENCAN: Parallel objective Function Analysis '
                      'requires mpi4py')

            comm = MPI.COMM_WORLD
            nproc = comm.Get_size()
            if mpi4py.__version__[0] == '0':
                Bcast = comm.Bcast
            # elif mpi4py.__version__[0] == '1':
            else:  # version can be 1, 2, 3 .... or more
                Bcast = comm.bcast

            self.pll = True
            self.myrank = comm.Get_rank()
        else:
            self.pll = False
            self.myrank = 0

        myrank = self.myrank

        def_fname = self.options['ifile'][1].split('.')[0]
        hos_file, log_file, tmp_file = \
            self._setHistory(opt_problem.name, store_hst, hot_start, def_fname)

        gradient = Gradient(opt_problem, sens_type, sens_mode, sens_step)

        def evalf(n, x, f, flag):
            """
            
            Parameters
            ----------
            n
            x
            f
            flag

            Returns
            -------

            """
            flag = -1
            return f, flag

        def evalg(n, x, g, flag):
            """
            
            Parameters
            ----------
            n
            x
            g
            flag

            Returns
            -------

            """
            flag = -1
            return g, flag

        def evalh(n, x, hlin, hcol, hval, hnnz, flag):
            """
            
            Parameters
            ----------
            n
            x
            hlin
            hcol
            hval
            hnnz
            flag

            Returns
            -------

            """
            flag = -1
            return hlin, hcol, hval, hnnz, flag

        def evalc(n, x, ind, c, flag):
            """
            
            Parameters
            ----------
            n
            x
            ind
            c
            flag

            Returns
            -------

            """
            flag = -1
            return c, flag

        def evaljac(n, x, ind, jcvar, jcval, jcnnz, flag):
            """
            
            Parameters
            ----------
            n
            x
            ind
            jcvar
            jcval
            jcnnz
            flag

            Returns
            -------

            """
            flag = -1
            return jcvar, jcval, jcnnz, flag

        def evalgjacp(n, x, g, m, p, q, work, gotj, flag):
            """
            
            Parameters
            ----------
            n
            x
            g
            m
            p
            q
            work
            gotj
            flag

            Returns
            -------

            """
            flag = -1
            return g, p, q, gotj, flag

        def evalhc(n, x, ind, hclin, hccol, hcval, hcnnz, flag):
            """
            
            Parameters
            ----------
            n
            x
            ind
            hclin
            hccol
            hcval
            hcnnz
            flag

            Returns
            -------

            """
            flag = -1
            return hclin, hccol, hcval, hcnnz, flag

        def evalhl(n,
                   x,
                   m,
                   lmbda,
                   scalef,
                   scalec,
                   hllin,
                   hlcol,
                   hlval,
                   hlnnz,
                   flag):
            """
            
            Parameters
            ----------
            n
            x
            m
            lmbda
            scalef
            scalec
            hllin
            hlcol
            hlval
            hlnnz
            flag

            Returns
            -------

            """
            flag = -1
            return hllin, hlcol, hlval, hlnnz, flag

        def evalhlp(n, x, m, lmbda, sf, sc, p, hp, goth, flag):
            """
            
            Parameters
            ----------
            n
            x
            m
            lmbda
            sf
            sc
            p
            hp
            goth
            flag

            Returns
            -------

            """
            flag = -1
            return hp, goth, flag

        # ======================================================================
        # ALGENCAN - Objective/Constraint Values Function
        # ======================================================================
        def evalfc(n, x, f, m, g, flag):
            """
            
            Parameters
            ----------
            n
            x
            f
            m
            g
            flag

            Returns
            -------

            """
            # Variables Groups Handling
            if opt_problem.use_groups:
                xg = {}
                for group in group_ids.keys():
                    if group_ids[group][1]-group_ids[group][0] == 1:
                        xg[group] = x[group_ids[group][0]]
                    else:
                        xg[group] = x[group_ids[group][0]:group_ids[group][1]]
                xn = xg
            else:
                xn = x

            # Flush Output Files
            self.flushFiles()

            # Evaluate User Function
            flag = 0
            if myrank == 0:
                if self.h_start:
                    [vals, hist_end] = hos_file.read(ident=['obj',
                                                            'con',
                                                            'fail'])
                    if hist_end:
                        self.h_start = False
                        hos_file.close()
                    else:
                        [ff, gg, flag] = \
                            [vals['obj'][0][0],vals['con'][0],
                             int(vals['fail'][0][0])]

            if self.pll:
                self.h_start = Bcast(self.h_start, root=0)

            if self.h_start and self.pll:
                [ff, gg, fail] = Bcast([ff,gg,fail], root=0)
            elif not self.h_start:
                [ff,gg,fail] = opt_problem.obj_fun(xn, *args, **kwargs)

            # Store History
            if myrank == 0:
                if self.sto_hst:
                    log_file.write(x, 'x')
                    log_file.write(ff, 'obj')
                    log_file.write(gg, 'con')
                    log_file.write(fail, 'fail')

            # Objective Assigment
            if isinstance(ff, complex):
                f = ff.astype(float)
            else:
                f = ff

            # Constraints Assigment
            for i in range(len(opt_problem.constraints.keys())):
                if isinstance(gg[i], complex):
                    g[i] = gg[i].astype(float)
                else:
                    g[i] = gg[i]

            return f, g, fail

        # ======================================================================
        # ALGENCAN - Objective/Constraint Gradients Function
        # ======================================================================
        def evalgjac(n, x, jfval, m, jcfun, jcvar, jcval, jcnnz, flag):
            """
            
            Parameters
            ----------
            n
            x
            jfval
            m
            jcfun
            jcvar
            jcval
            jcnnz
            flag

            Returns
            -------

            """
            if self.h_start:
                if myrank == 0:
                    [vals, hist_end] = hos_file.read(ident=['grad_obj',
                                                            'grad_con'])
                    if hist_end:
                        self.h_start = False
                        hos_file.close()
                    else:
                        dff = vals['grad_obj'][0].reshape(
                            (len(opt_problem.objectives.keys()),
                             len(opt_problem.variables.keys())))
                        dgg = vals['grad_con'][0].reshape(
                            (len(opt_problem.constraints.keys()),
                             len(opt_problem.variables.keys())))

                if self.pll:
                    self.h_start = Bcast(self.h_start, root=0)

                if self.h_start and self.pll:
                    [dff, dgg] = Bcast([dff,dgg], root=0)

            if not self.h_start:
                [ff, gg, fail] = opt_problem.obj_fun(x, *args, **kwargs)
                dff, dgg = gradient.getGrad(x,
                                            group_ids,
                                            [ff],
                                            gg,
                                            *args,
                                            **kwargs)

            # Store History
            if self.sto_hst and (myrank == 0):
                log_file.write(dff, 'grad_obj')
                log_file.write(dgg, 'grad_con')

            # Objective Gradient Assignment
            for i in range(len(opt_problem.variables.keys())):
                jfval[i] = dff[0, i]

            # Constraint Gradient Assignment
            jcnnz = 0
            for jj in range(len(opt_problem.constraints.keys())):
                for ii in range(len(opt_problem.variables.keys())):
                    jcfun[jcnnz] = jj + 1
                    jcvar[jcnnz] = ii + 1
                    jcval[jcnnz] = dgg[jj, ii]
                    jcnnz += 1

            return jfval, jcfun, jcvar, jcval, jcnnz, fail

        # Variables Handling
        n = len(opt_problem._variables.keys())
        xl = []
        xu = []
        xx = []
        for key in opt_problem.variables.keys():
            if opt_problem.variables[key].type == 'c':
                xl.append(opt_problem.variables[key].lower)
                xu.append(opt_problem.variables[key].upper)
                xx.append(opt_problem.variables[key].value)
            elif opt_problem.variables[key].type == 'i':
                raise IOError('NLPQL cannot handle integer design variables')
            elif opt_problem.variables[key].type == 'd':
                raise IOError('NLPQL cannot handle discrete design variables')

        xl = numpy.array(xl)
        xu = numpy.array(xu)
        xx = numpy.array(xx)

        # Variables Groups Handling
        group_ids = {}
        if opt_problem.use_groups:
            k = 0
            for key in opt_problem.vargroups.keys():
                group_len = len(opt_problem.vargroups[key]['ids'])
                group_ids[opt_problem.vargroups[key]['name']] = \
                    [k, k+group_len]
                k += group_len

        # Constraints Handling
        m = len(opt_problem.constraints.keys())
        equatn = []
        linear = []
        if m > 0:
            for key in opt_problem.constraints.keys():
                if opt_problem.constraints[key].type == 'e':
                    equatn.append(True)
                elif opt_problem.constraints[key].type == 'i':
                    equatn.append(False)

                linear.append(False)
        else:
            raise IOError('ALGENCAN support for unconstrained problems '
                          'not implemented yet')

        equatn = numpy.array(equatn)
        linear = numpy.array(linear)

        # Objective Handling
        objfunc = opt_problem.obj_fun
        nobj = len(opt_problem.objectives.keys())
        ff = []
        for key in opt_problem.objectives.keys():
            ff.append(opt_problem.objectives[key].value)

        ff = numpy.array(ff)

        # Setup argument list values
        nn = numpy.array([n], numpy.int)
        mm = numpy.array([m], numpy.int)
        lm = numpy.zeros([m], numpy.float)
        coded = numpy.array([False, False, False, False,
                             False, False, True, True, False, False],
                            numpy.bool)
        epsfeas = numpy.array([self.options['epsfeas'][1]], numpy.float)
        epsopt = numpy.array([self.options['epsopt'][1]], numpy.float)
        efacc = numpy.array([self.options['efacc'][1]], numpy.float)
        eoacc = numpy.array([self.options['eoacc'][1]], numpy.float)
        checkder = numpy.array([self.options['checkder'][1]], numpy.bool)
        iprint = numpy.array([self.options['iprint'][1]], numpy.int)
        if myrank != 0:
            iprint = 0
        else:
            iprint = self.options['iprint'][1]

        ncomp = numpy.array([self.options['ncomp'][1]], numpy.int)

        ifile = self.options['ifile'][1]
        if iprint >= 0:
            if os.path.isfile(ifile):
                os.remove(ifile)

        cnormu = numpy.array([0], numpy.float)
        snorm = numpy.array([0], numpy.float)
        nlpsupn = numpy.array([0], numpy.float)
        inform = numpy.array([0], numpy.int)

        # Run ALGENCAN
        t0 = time.time()
        algencan.algencan(epsfeas,
                          epsopt,
                          efacc,
                          eoacc,
                          iprint,
                          ncomp,
                          nn,
                          xx,
                          xl,
                          xu,
                          mm,
                          lm,
                          equatn,
                          linear,
                          coded,
                          checkder,
                          ff,
                          cnormu,
                          snorm,
                          nlpsupn,
                          inform,
                          ifile,
                          evalf,
                          evalg,
                          evalh,
                          evalc,
                          evaljac,
                          evalhc,
                          evalfc,
                          evalgjac,
                          evalgjacp,
                          evalhl,
                          evalhlp)
        sol_time = time.time() - t0

        if myrank == 0:
            if self.sto_hst:
                log_file.close()
                if tmp_file:
                    hos_file.close()
                    name = hos_file.filename
                    os.remove(name+'.cue')
                    os.remove(name+'.bin')
                    os.rename(name+'_tmp.cue', name+'.cue')
                    os.rename(name+'_tmp.bin', name+'.bin')

        if iprint > 0:
            algencan.closeunit(10)

        [fs, gg, fail] = opt_problem.obj_fun(xx, *args, **kwargs)

        # Store Results
        sol_inform = {}
        sol_inform['value'] = inform[0]
        sol_inform['text'] = self.getInform(inform[0])

        if store_sol:
            sol_name = 'ALGENCAN Solution to ' + opt_problem.name

            sol_options = copy.copy(self.options)
            # if sol_options.has_key('defaults'):
            if 'defaults' in sol_options:
                del sol_options['defaults']

            sol_evals = 0

            sol_vars = copy.deepcopy(opt_problem.variables)
            i = 0
            for key in sol_vars.keys():
                sol_vars[key].value = xx[i]
                i += 1

            sol_objs = copy.deepcopy(opt_problem.objectives)
            i = 0
            for key in sol_objs.keys():
                sol_objs[key].value = ff[i]
                i += 1

            if m > 0:
                sol_cons = copy.deepcopy(opt_problem.constraints)
                i = 0
                for key in sol_cons.keys():
                    sol_cons[key].value = gg[i]
                    i += 1
            else:
                sol_cons = {}

            sol_lambda = lm

            opt_problem.addSol(self.__class__.__name__,
                               sol_name,
                               objfunc,
                               sol_time,
                               sol_evals,
                               sol_inform,
                               sol_vars,
                               sol_objs,
                               sol_cons,
                               sol_options,
                               display_opts=disp_opts,
                               Lambda=sol_lambda,
                               Sensitivities=sens_type,
                               myrank=myrank,
                               arguments=args,
                               **kwargs)

        return ff, xx, sol_inform

    def _on_setOption(self, name, value):
        """Set Optimizer Option Value (Optimizer Specific Routine)

        Documentation last updated:  May. 07, 2008 - Ruben E. Perez

        """
        pass

    def _on_getOption(self, name):
        """Get Optimizer Option Value (Optimizer Specific Routine)

        Documentation last updated:  May. 07, 2008 - Ruben E. Perez

        """
        pass

    def _on_getInform(self, infocode):
        """Get Optimizer Result Information (Optimizer Specific Routine)

        Keyword arguments:
        -----------------
        id -> STRING: Option Name

        Documentation last updated:  May. 07, 2008 - Ruben E. Perez

        """
        return self.informs[infocode]

    def _on_flushFiles(self):
        """Flush the Output Files (Optimizer Specific Routine)

        Documentation last updated:  August. 09, 2009 - Ruben E. Perez

        """
        iPrint = self.options['iprint'][1]
        if iPrint >= 0:
            algencan.pyflush(10)


if __name__ == '__main__':
    # Test ALGENCAN
    print('Testing ...')
    algencan = ALGENCAN()
    print(algencan)
