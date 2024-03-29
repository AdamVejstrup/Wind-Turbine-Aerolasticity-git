# -*- coding: utf-8 -*-
"""
Created on Sun Mar 26 11:15:31 2023

@author: Toke Schäffer

Script that calculates the motion of an airfoil suspended by a spring using
odeint from scipy.integrate. The airfoil has a certain geometric angle of attack
alpha_g which can be changed. The code runs with and without dynamic stall
(boolean variable use_stall). 

Notes on theory (page 114, Aerodynamics of Wind Turbines, Hansen):
If the airfoil moves downwards, the angle of attack increases and the lift
changes according to the airfoil data. If the airfoil moves upwards, the angle
of attack decreases. If the airfoil is moving downwards and the slope of the
lift dcl/dalpha is positive, the lift coefficient will increase. Accordingly,
the aerodynamic force will increase. The aerodynamic force is in the opposite
direction of the motion of the airfoil. This means that the airfoil will be
slowed down (positive damping). The same argument is true if the airfoil moves
upwards and the slope of the lift dcl/dalpha is negative, see (alpha, cl)-plot. 

Based on the above argument, it is very important to have correct estimates of
the lift. This is why the dynamic stall model is clever to use here.
For example, the code is unstable for alpha_g = 20 deg without dynamic stall,
but stable with dynamic stall. Computers may overestimate ocscillations
if static lift data is used.
"""

import numpy as np
from scipy.integrate import odeint
import matplotlib.pyplot as plt

# Use dynamic stall
use_stall = False

# Geometric angle of attack [rad]
alpha_g = np.deg2rad(0)

# Simulation time [s]
t_sim = 40

# Number of time steps
nots = 1000

# Time vector
t = np.linspace(0, t_sim, nots)

# Airfoil name
a_name = 'FFA-W3-241'

# Airfoil file name
a_file_name = f'{a_name}.txt'

# Airfoil data
# Columns: alpha, cl, cd, cm, f_stat, cl_inv, cl_fs
a_data = np.loadtxt(a_file_name)

# Extractig force coefficients
(alpha_tab, cl_tab, cd_tab, cm_tab,
f_stat_tab, cl_inv_tab, cl_fs_tab) = a_data.T

# Given system parameters
m = 1       # Mass of the airfoil [kg]
k = 61.7    # Spring constant [N/m]
c = 0.2     # Chord length [m]
V_0 = 2     # Mean wind speed [m/s]
rho = 1.225 # Air density [kg/m^3]
s = 1       # Some value [m] ?

def pend(y, t, m, k, c, V_0, alpha_g, rho, s, use_stall):
    """calculates the motion of an airfoil suspended by a spring using
    odeint from scipy.integrate.
    
    # odeint solves a system of first order differential equations i.e.
    # dx/dt = f(x, t)
    # To solve a second order differential equation we need to transform
    # the equation to a system of first order differential equations.
    
    # How to do this depends on whether we use dynamic stall or not.
    
    # Without dynamic stall we define (slide 12 NII_1):
    # z1 = x
    # z2 = dx/dt = dz1/dt
    # From EOM we have:
    # dz2/dt = ddz1/dt = (-k*z1 - input_force) / m
    
    # With dynamic stall we use the same definition of z1 and z2 as above.
    # Additionally we define
    # dz3/dt = (f_stat - z3)/tau
    
    """
    
    # Defining z1, z2 and z3 from y in this manner (below) is just a "copy"
    # of the example from
    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.odeint.html
    
    if use_stall:
        z1, z2, z3 = y
    
    else:
        z1, z2 = y
    
    # Follwing the algorithm from NII_1 slide 12
    
    # Flow angle
    phi = np.arctan(z2/V_0)
    
    # Angle of attack
    alpha = alpha_g + phi
    
    # Relative velocity
    V_rel = np.sqrt(z2**2 + V_0**2)
    
    # Lift coefficient with dynamic stall
    if use_stall:
        
        # Follwing the algorithm from NII_1 slide 13
        f_stat = np.interp(np.rad2deg(alpha), alpha_tab, f_stat_tab)
        cl_inv = np.interp(np.rad2deg(alpha), alpha_tab, cl_inv_tab)
        cl_fs = np.interp(np.rad2deg(alpha), alpha_tab, cl_fs_tab)
        
        # Time constant
        tau = 4*c/V_rel
        
        cl = z3 * cl_inv + (1-z3) * cl_fs
    
    # Lift coefficient without dynamic stall
    else:
        cl = np.interp(np.rad2deg(alpha), alpha_tab, cl_tab)
    
    # Input force from NII_1 slide 12
    input_force = 0.5*rho * V_rel**2 * c*s*cl * np.cos(phi)
    
    # Calculating the derivatives dz1/dt, dz2/dt (and dz3/dt for dynamic stall)
    if use_stall:
        dydt = [z2, (-k*z1 - input_force) / m, (f_stat-z3)/tau]
    else:
        dydt = [z2, (-k*z1 - input_force) / m]
        
    return dydt

# Given initial conditions
if use_stall:
    y0 = [0.02, 0, 0]
else:
    y0 = [0.02, 0]

# Solving the problem
sol = odeint(pend, y0, t, args=(m, k, c, V_0, alpha_g, rho, s, use_stall))

# Plotting the results
plt.rcParams.update({'font.size':12})

plt.figure()

# String telling whether dynamic stall is used or not
if use_stall:
    stall_str = 'with dynamic stall'
else:
    stall_str = 'without dynamic stall'

# String telling the geometric angle of attack
alpha_g_str = f'$\\alpha_g$ = {np.rad2deg(alpha_g):.1f} $\degree$'

plt.title('Airfoil x-position')

# First column of the solution corresponds to the x position
plt.plot(t, sol[:, 0], label=f'{alpha_g_str} ({stall_str})')

plt.xlim(t[0], t[-1])
plt.xlabel('Time [s]')
plt.ylabel('x [m]')
plt.grid()
plt.legend()
plt.show()

# Plotting the static lift coefficient
# It should be avoided to be in the stall region 
cl_max_idx = np.argmax(cl_tab)

x_lim_lower, x_lim_upper = -10, 30

plt.figure()
plt.title('Static lift coefficient')
plt.plot(alpha_tab, cl_tab)
plt.xlabel('Angle of attack [deg]')
plt.ylabel('Lift coefficient')
plt.axvline(alpha_tab[cl_max_idx], color='r', linestyle='--', label='Stall angle')
label_1 = 'Positive slope for increasing angle of attack'
label_2 = 'Negative slope for increasing angle of attack'
plt.axvspan(x_lim_lower, alpha_tab[cl_max_idx], alpha=0.2, color='g', label=label_1)
plt.axvspan(alpha_tab[cl_max_idx], x_lim_upper, alpha=0.2, color='r', label=label_2)
plt.xlim(x_lim_lower, x_lim_upper)
plt.legend()
plt.show()

