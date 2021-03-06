# -*- coding: utf-8 -*-
"""
Created on Sun Mar  6 15:09:12 2016

@author: alex
"""

from AlexRobotics.control import linear        as RCL
from AlexRobotics.dynamic import DynamicSystem as DS
from AlexRobotics.signal  import filters

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

'''
################################################################################
'''


class RRT:
    """ Rapid Random Trees search algorithm """
    
    ############################
    def __init__(self, sys , x_start ):
        
        self.DS = sys          # Dynamic system class
        
        self.x_start = x_start  # origin of the graph
        
        self.start_node = Node( self.x_start , None , 0  , None )
        
        self.Nodes = []
        self.Nodes.append( self.start_node )
        
        
        # Params
        self.dt  = 0.05
        self.INF = 10000
        self.eps = 0.001
        
        self.goal_radius          = 0.2        
        self.alpha                = 0.9    # prob of random exploration
        self.max_nodes            = 25000  # maximum number of nodes
        self.max_distance_compute = 500    # maximum number of nodes to check distance
        self.max_solution_time    = 10     # won"t look for solution taking longuer than that
        
        self.test_u_domain        = False  # run a check on validity of u input at each state
        
        
        # Smoothing params
        self.low_pass_filter      = filters.low_pass( fc = 3 , dt = self.dt )        
        
        # Traj controller
        self.traj_ctl_kp          = 25
        self.traj_ctl_kd          = 10
        
        # Ploting
        self.dyna_plot            = False
        self.dyna_node_no_update  = 50
        self.fontsize             = 4
        self.y1axis               = 0  # State to plot on y1 axis
        self.y2axis               = 1  # State to plot on y2 axis
        
        self.discretizeactions()
        
        # Init
        self.solution              = None
        self.randomized_input      = False
        
        
    #############################
    def discretizeactions(self, Nu0 = 3 ):
        
        self.U = np.linspace( self.DS.u_lb[0]  , self.DS.u_ub[0]  , Nu0  )
        
        
    ############################
    def rand_state(self):    
        """ Sample a random state """
        
        ranges = self.DS.x_ub - self.DS.x_lb
        
        x_random = np.random.rand( self.DS.n ) * ranges + self.DS.x_lb
        
        return x_random
        
    ############################
    def rand_input(self, x = 0 ):    
        """ Sample a random state """
        
        n_options = len( self.U )
        j         = np.random.randint(0,n_options)
        
        u         = self.U[j]
        
        # correct for m=1 --> make it a numpy array
        if self.DS.m == 1:
                u = np.array([u])
        
        # if u domain check is active
        if self.test_u_domain :
            # I new sample is not a valid option
            if not( self.DS.isavalidinput( x , u ) ):
                # Sample again (recursivity)
                u = self.rand_input( x )
        
        return u
        
        
    ############################
    def nearest_neighbor(self, x_target ):    
        """ Sample a random state """
        
        closest_node = None
        min_distance = self.INF
        
        if len(self.Nodes) < self.max_distance_compute + 1 :
            # Brute force        
            for node in self.Nodes:
                d = node.distanceTo( x_target )
                if d < min_distance:
                    if node.t < self.max_solution_time:
                        min_distance = d
                        closest_node = node
        
        else:
            # Check only last X nodes
            for i in range(self.max_distance_compute):
                node = self.Nodes[ len(self.Nodes) - i - 1 ]
                d = node.distanceTo( x_target )
                if d < min_distance:
                    if node.t < self.max_solution_time:
                        min_distance = d
                        closest_node = node
            
                
        return closest_node
        
        
    ############################
    def select_control_input(self, x_target , closest_node ):    
        """ Sample a random state """
        
        
        # Select a random control input
        if self.randomized_input :
            
            u          = self.rand_input( closest_node.x )
            x_next     = closest_node.x + self.DS.fc( closest_node.x , u ) * self.dt
            t_next     = closest_node.t + self.dt
            new_node   = Node( x_next , u , t_next  , closest_node )
        
        # Pick control input that bring the sys close to random point
        else:
            
            new_node     = None
            min_distance = self.INF
            
            for u in self.U:
                
                # Fix for m=1
                if self.DS.m == 1:
                        u = np.array([u])
                
                # if u domain check is active
                if self.test_u_domain:
                    # if input is not valid
                    if not( self.DS.isavalidinput( closest_node.x , u ) ):
                        # Skip this u
                        continue
                
                x_next     = closest_node.x + self.DS.fc( closest_node.x , u ) * self.dt
                t_next     = closest_node.t + self.dt
                node       = Node( x_next , u , t_next  , closest_node )
                
                d = node.distanceTo( x_target )
                
                if d < min_distance:
                    min_distance = d
                    new_node     = node
                    
                
        return new_node
        
    
    ############################
    def one_step(self):    
        """ """
        x_random  = self.rand_state()
        
        # If random point is a valid state
        if True:
            node_near = self.nearest_neighbor( x_random )
            
            # if a valid neighbor was found
            if not node_near == None:
                new_node  = self.select_control_input( x_random , node_near )
                
                # if there is a valid control input
                if not new_node == None:
                    self.Nodes.append( new_node )
        
        
    ############################
    def compute_steps(self , n , plot = False ):    
        """ """
        for i in range( n ):
            self.one_step()
            
        if plot:
            self.plot_2D_Tree()
    
           
        
    ############################
    def find_path_to_goal(self, x_goal ):
        """ """
        
        self.x_goal = x_goal
        
        succes   = False
        
        no_nodes = 0
        
         # Plot
        if self.dyna_plot:
            self.dyna_plot_init()
        
        while not succes:
            
            # Exploration:
            if np.random.rand() > self.alpha :
                # Try to converge to goal
                x_random = x_goal
                self.randomized_input = False
            else:
                # Random exploration
                x_random  = self.rand_state()
                self.randomized_input = True

            # If random point is a valid state
            if True:
                node_near = self.nearest_neighbor( x_random )
                
                # if a valid neighbor was found
                if not node_near == None:
                    new_node  = self.select_control_input( x_random , node_near )
                    
                    # if there is a valid control input
                    if not new_node == None:
                        self.Nodes.append( new_node )
            
            # Distance to goal
            d = new_node.distanceTo( x_goal )
            
            # Print
            no_nodes = no_nodes + 1
            #print '\nNumber of Nodes = ', no_nodes
            
            # Plot
            if self.dyna_plot:
                self.dyna_plot_add_node( new_node , no_nodes )
            
            # Succes?
            if d < self.goal_radius:
                succes = True
                self.goal_node = new_node
                
            # Tree reset
            if no_nodes == self.max_nodes:
                print('\nSearch Fail: Reseting Tree')
                #self.plot_2D_Tree()
                no_nodes = 0
                self.Nodes = []
                self.Nodes.append( self.start_node )
                
                if self.dyna_plot :
                    
                    self.dyna_plot_clear()
                    
                
        
        print('\nSucces!!!!: Path to goal found')
        
        
        # Compute Path
        self.compute_path_to_goal()
        
        # Plot
        if self.dyna_plot:
            self.dyna_plot_solution()
        
                
    ############################
    def compute_path_to_goal(self):
        """ """
        
        node = self.goal_node
        
        t      = 0
        
        x_list  = []
        u_list  = []
        t_list  = []
        dx_list = []
        
        self.path_node_list = []
        
        # Until node = start_node
        while node.distanceTo( self.x_start ) > self.eps:
            
            self.path_node_list.append( node )
            
            x_list.append( node.P.x   )
            u_list.append( node.u     )
            t_list.append( node.P.t   )
            
            dx_list.append( self.DS.fc( node.P.x , node.u )  ) # state derivative
            
            
            # Previous Node
            node  = node.P 
            
        
        # Arrange Time array
        t = np.array( t_list )
        t = np.flipud( t )
        
        # Arrange Input array
        u = np.array( u_list ).T
        u = np.fliplr( u )
        
        # Arrange State array
        x = np.array( x_list ).T
        x = np.fliplr( x )
        
        # Arrange State Derivative array
        dx = np.array( dx_list ).T
        dx = np.fliplr( dx )
            
        # Save solution
        self.time_to_goal    = t.max()
        self.solution        = [ x , u , t , dx ]
        self.solution_length = len( self.path_node_list )
        
    
    ############################
    def solution_smoothing( self ):
        
        [ x , u , t , dx ]  = self.solution
        
        x_new  = x.copy
        dx_new = dx.copy()
        
        #dx_new[1] = self.low_pass_filter.filter_array( dx[1] )
        
        x_new  = self.low_pass_filter.filter_array( x  )
        dx_new = self.low_pass_filter.filter_array( dx )
        
        # Filer acceleration only
        self.solution   = [ x , u , t , dx_new ]
        
        #self.solution   = [ x_new , u , t , dx_new ]
        
    
    
    ############################
    def save_solution(self, name = 'RRT_Solution.npy' ):
        
        arr = np.array( self.solution )
        
        np.save( name , arr )
        
        
    ############################
    def load_solution(self, name = 'RRT_Solution.npy' ):
        
        arr = np.load( name )
        
        self.solution        = arr.tolist()
        self.time_to_goal    = self.solution[2].max()
        self.solution_length = self.solution[2].size
        

    ############################
    def plot_open_loop_solution(self):
        """ """
        
        self.OL_SIM = DS.Simulation( self.DS , self.time_to_goal , self.solution_length )
        
        self.OL_SIM.t        = self.solution[2].T
        self.OL_SIM.x_sol_CL = self.solution[0].T
        self.OL_SIM.u_sol_CL = self.solution[1].T
        
        self.OL_SIM.plot_CL('x') 
        self.OL_SIM.plot_CL('u')
        
    
    ############################
    def plot_open_loop_solution_acc(self, index = 0 ):
        """ """
        
        t       = self.solution[2].T
        dx      = self.solution[3].T
        
        fig , plots = plt.subplots( 1, sharex=True,figsize=(4, 3),dpi=300, frameon=True)
        
        plots.plot( t , dx )
        
        
    ############################
    def animate3D_solution(self, time_scale = 1 ):
        """ 
        animate robots with open loop solution
        --------------------------------------
        only works if self.DS is a 3D mainpulator class
        
        """
        
        self.OL_SIM = DS.Simulation( self.DS , self.time_to_goal , self.solution_length )
        
        self.OL_SIM.t        = self.solution[2].T
        self.OL_SIM.x_sol_CL = self.solution[0].T
        self.OL_SIM.u_sol_CL = self.solution[1].T
        
        self.DS.Sim = self.OL_SIM 
        
        self.DS.animate3DSim( time_scale )
        
        
    ############################
    def open_loop_controller(self, x , t ):
        """ feedback law """
        
        if self.solution == None:
            
            u = self.DS.ubar
            
            return u
        
        else:
            
            # Find time index
            times = self.solution[2]
            i = (np.abs(times - t)).argmin()
            
            # Find associated control input
            if self.DS.m == 1:
                inputs = self.solution[1][0]
                u_bar  = np.array( [ inputs[i] ] )
            else:
                u_bar = self.solution[1][:,i]
            
            # No action pass trajectory time
            if t > self.time_to_goal:
                u_bar    = self.DS.ubar
    
            return u_bar
            
            
    ############################
    def trajectory_controller(self, x , t ):
        """ feedback law """
        
        if self.solution == None:
            
            u = self.DS.ubar
            
            return u
        
        else:
            
            # Find time index
            times = self.solution[2]
            i = (np.abs(times - t)).argmin()
            
            # Find associated control input
            if self.DS.m == 1:
                inputs = self.solution[1][0]
                u_bar  = np.array( [ inputs[i] ] )
            else:
                u_bar = self.solution[1][:,i]
            
            # Find associated state and compute error
            states   = self.solution[0]
            x_target = states[:,i]
            
            # No action pass trajectory time
            if t > self.time_to_goal:
                u_bar    = self.DS.ubar
                x_target = self.x_goal
            
            error    = x_target - x
            
            # Error feedback
            if self.DS.n == 2:
                """ 1 DOF manipulator """
                K     = np.array([ self.traj_ctl_kp , self.traj_ctl_kd ])
                u_fdb = np.dot( K , error )
                
                if self.DS.m == 1:
                    u_ctl    = u_bar + u_fdb
                else:
                    u_ctl    = u_bar + np.array([0,0])
                    u_ctl[0] = u_ctl[0] + u_fdb
                
            elif self.DS.n == 4:
                """ 2 DOF manipulator """
                u1     = np.dot( np.array([ self.traj_ctl_kp , 0  , self.traj_ctl_kd ,  0 ]) , error ) 
                u2     = np.dot( np.array([ 0  , self.traj_ctl_kp ,  0 , self.traj_ctl_kd ]) , error ) 
                u_fdb  = np.array([ u1 , u2 ])
                
                if self.DS.m == 2:
                    u_ctl    = u_bar + u_fdb
                else:
                    u_ctl    = u_bar + np.zeros(self.DS.m)
                    u_ctl[0] = u_ctl[0] + u1
                    u_ctl[1] = u_ctl[1] + u2
                
            else:
                u_ctl = 0
                
            #print u_bar, u_fdb, u_ctl
            
            return u_ctl
            
    
    
    
    ##################################################################
    ### Ploting functions
    ##################################################################            
                
    ############################
    def plot_2D_Tree(self):
        """ """
        
        self.y1min = self.DS.x_lb[ self.y1axis ]
        self.y1max = self.DS.x_ub[ self.y1axis ]
        self.y2min = self.DS.x_lb[ self.y2axis ]
        self.y2max = self.DS.x_ub[ self.y2axis ]
        
        self.phasefig = plt.figure(figsize=(3, 2),dpi=300, frameon=True)
        self.ax       = self.phasefig.add_subplot(111)
        
        for node in self.Nodes:
            if not(node.P==None):
                line = self.ax.plot( [node.x[ self.y1axis ],node.P.x[ self.y1axis ]] , [node.x[ self.y2axis ],node.P.x[ self.y2axis ]] , 'o-')
                
        if not self.solution == None:
            for node in self.path_node_list:
                if not(node.P==None):
                    line = self.ax.plot( [node.x[ self.y1axis ],node.P.x[ self.y1axis ]] , [node.x[ self.y2axis ],node.P.x[ self.y2axis ]] , 'r')
        
        
        plt.xlabel(self.DS.state_label[ self.y1axis ] + ' ' + self.DS.state_units[ self.y1axis ] , fontsize=6)
        plt.ylabel(self.DS.state_label[ self.y2axis ] + ' ' + self.DS.state_units[ self.y2axis ] , fontsize=6)
        plt.xlim([ self.y1min , self.y1max ])
        plt.ylim([ self.y2min , self.y2max ])
        plt.grid(True)
        plt.tight_layout()
        plt.show()
        
    
    ############################
    def dyna_plot_init(self):
        
        self.y1min = self.DS.x_lb[ self.y1axis ]
        self.y1max = self.DS.x_ub[ self.y1axis ]
        self.y2min = self.DS.x_lb[ self.y2axis ]
        self.y2max = self.DS.x_ub[ self.y2axis ]
        
        matplotlib.rc('xtick', labelsize=self.fontsize )
        matplotlib.rc('ytick', labelsize=self.fontsize )
        
        self.phasefig  = plt.figure(figsize=(3, 2),dpi=600, frameon=True)
        self.ax        = self.phasefig.add_subplot(111)
        
        self.time_template = 'Number of nodes = %i'
        self.time_text     = self.ax.text(0.05, 0.05, '', transform=self.ax.transAxes, fontsize=self.fontsize )
        
        plt.xlabel(self.DS.state_label[ self.y1axis ] + ' ' + self.DS.state_units[ self.y1axis ] , fontsize=self.fontsize )
        plt.ylabel(self.DS.state_label[ self.y2axis ] + ' ' + self.DS.state_units[ self.y2axis ] , fontsize=self.fontsize )
        plt.xlim([ self.y1min , self.y1max ])
        plt.ylim([ self.y2min , self.y2max ])
        plt.grid(True)
        plt.tight_layout()
        
        plt.ion()
        
        self.node_wait_list = 0
        
        
     ############################
    def dyna_plot_add_node(self, node , no_nodes ):
        
        if not(node.P==None):
                line = self.ax.plot( [node.x[ self.y1axis ],node.P.x[ self.y1axis ]] , [node.x[ self.y2axis ],node.P.x[ self.y2axis ]] , 'o-')
                self.time_text.set_text(self.time_template % ( no_nodes ))
                self.node_wait_list = self.node_wait_list + 1
                
                
                if self.node_wait_list == self.dyna_node_no_update:
                    plt.pause( 0.01 )
                    self.node_wait_list = 0
                    
                    
    ############################
    def dyna_plot_clear(self ):
        
        self.ax.clear()
        plt.close( self.phasefig )
        self.dyna_plot_init()
                    
                    
    ############################
    def dyna_plot_solution(self ):
        
        if not self.solution == None:
            for node in self.path_node_list:
                if not(node.P==None):
                    line = self.ax.plot( [node.x[ self.y1axis ],node.P.x[ self.y1axis ]] , [node.x[ self.y2axis ],node.P.x[ self.y2axis ]] , 'r')
                    
            #plt.ioff()
            plt.show()
    
        
        
class Node:
    """ node of the graph """
    
    ############################
    def __init__(self, x , u , t , parent ):
        
        self.x = x  # Node coordinates in the state space
        self.u = u  # Control inputs used to get there
        self.t = t  # Time when arriving at x
        self.P = parent # Previous node
        
    
    ############################
    def distanceTo(self, x_other ):
        """ Compute distance to otherNode """
        
        return np.linalg.norm( self.x - x_other )
        
        
        
        
'''
#################################################################
##################          Main                         ########
#################################################################
'''


if __name__ == "__main__":     
    """ MAIN TEST """
    pass
        
        
