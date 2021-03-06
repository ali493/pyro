# -*- coding: utf-8 -*-
"""
Created on Mon Nov 12 20:28:17 2018

@author: Alexandre
"""

import numpy as np

from pyro.dynamic  import pendulum
from pyro.planning import discretizer
from pyro.analysis import costfunction
from pyro.planning import valueiteration
from pyro.control  import controller

sys  = pendulum.SinglePendulum()

# Discrete world 
grid_sys = discretizer.GridDynamicSystem( sys )

# Cost Function
cf = costfunction.QuadraticCostFunction( sys )

cf.xbar = np.array([ -3.14 , 0 ]) # target
cf.INF  = 10000

# VI algo
vi = valueiteration.ValueIteration_2D( grid_sys , cf )

vi.initialize()
vi.load_data('simple_pendulum_vi')
#vi.compute_steps(200)
#vi.load_data()
vi.assign_interpol_controller()
vi.plot_policy(0)
vi.plot_cost2go()
vi.save_data('simple_pendulum_vi')

#asign controller
cl_sys = controller.ClosedLoopSystem( sys , vi.ctl )

# Simulation and animation
x0   = [0,0]
tf   = 10
cl_sys.plot_trajectory( x0 , tf )
cl_sys.sim.plot('xu')
cl_sys.animate_simulation()

# Compute and plot cost
cl_sys.sim.cf = cf
cl_sys.sim.compute_cost()
cl_sys.sim.plot('j')