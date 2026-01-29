# pylint: disable=C0103

"""
This module contains the integrator used to simulate the atmospheric trajectory of a meteoroid 
through the atmosphere, including the effects of drag, mass loss due to ablation, deformation, 
and fragmentation.
"""

import numpy as np
from scipy.integrate import solve_ivp
from atmosentry.meteoroid import Meteoroid


def differential_equations(t: float,
                           y: list,
                           sigma_imp: float,
                           rho_imp: float,
                           eta: float,
                           C_d: float,
                           C_h: float,
                           R_pl: float,
                           M_pl: float,
                           rho_atm0: float,
                           H: float):

    """
    Defines the system of differential equations for the meteoroid's atmospheric
    trajectory. This function computes the position, velocity, mass, and size evolution of
    the meteoroid due to atmospheric passage. 

    Parameters:
    ----------
    t : float
        The integration time (unused but required by scipy.integrate.solve_ivp).
    y : list
        A list of state variables [vx, vy, vz, M, x, y, z, R, Rdot, N], where:
        - vx, vy, vz: velocity components [m/s]
        - M: mass [kg]
        - x, y, z: position components [m]
        - R: radius [m]
        - Rdot: rate of change of radius [m/s]
        - N: number of rayleigh-taylor timescales
    sigma_imp : float
        Tensile strength of the meteoroid [Pa]
    rho_imp : float
        Bulk density of the meteoroid [kg/m^3]
    eta : float
        Heat of ablation of the meteoroid [J/kg]
    C_d : float
        Drag coefficient [dimensionless]
    C_h : float
        Heat transfer coefficient [dimensionless]
    R_pl : float
        Radius of the planet [m]
    M_pl : float
        Mass of the planet ([kg]
    rho_atm0 : float
        Atmospheric surface density [kg/m^3]
    H : float
        Atmospheric scale height [m]

    Returns:
    -------
    list
        The time derivatives of the state variables:
        [dvxdt, dvydt, dvzdt, dMdt, dxdt, dydt, dzdt, R_dot, R_ddot, dNdt].

    """

    ### ------ Defining constants ------
    G = 6.67e-11
    sigma = 5.6704e-8
    T = 25000 # assumed temperature of shocked gas at leading edge of the comet
    ### ----------------------- ###

    vx, vy, vz, M, _, _, z, R, Rdot, _ = y
    del t

    v = np.sqrt(vx ** 2 + vy ** 2 + vz ** 2)

    rho_a = rho_atm0 * np.exp(- z / H)
    A = np.pi * R ** 2
    g = G * M_pl / (R_pl + z) ** 2

    dvxdt = - 0.5 *  C_d * rho_a * A * v * vx / M
    dvydt = - 0.5 *  C_d * rho_a * A * v * vy / M
    dvzdt = - 0.5 *  C_d * rho_a * A * v * vz / M - g

    dxdt = vx
    dydt = vy
    dzdt = vz

    dMdt = - np.minimum(sigma * T**4, 0.5 * C_h * rho_a * v**3) * A / eta

    if 0.5 * C_d * rho_a * v ** 2 > sigma_imp:
        R_dot = Rdot
        R_ddot = C_d * rho_a * v ** 2 / (2 * rho_imp * R)

        dNdt = (v / R) * ( (3 * C_d * np.pi * rho_a) / (8 * rho_imp)) ** 0.5
    else:
        R_dot = 0.0
        R_ddot = 0.0

        dNdt = 0

    return [dvxdt, dvydt, dvzdt, dMdt, dxdt, dydt, dzdt, R_dot, R_ddot, dNdt]


def event_Z_crossing(t: float, y: list):
    """
    Event triggered when the altitude crosses zero (i.e., it hits the ground).

    This event is used in the integration process to stop the simulation, signaling 
    that the meteoroid has completed its atmospheric trajectory.

    Parameters:
    ----------
    t : float
        Simulation time (unused but required by scipy.integrate.solve_ivp)
    y : list
        The current state variables

    Returns:
    -------
    float
        The current altitude (z), which will trigger the event when it crosses zero.

    """
    del t

    return y[6]


def event_mass_zero(t: float, y: list):
    """
    Event triggered, stopping the integration, when the meteoroid has lost all of its
    mass due to ablation.

    Parameters:
    ----------
    t : float
        Simulation time (unused but required by scipy.integrate.solve_ivp)
    y : list
        The current state variables

    Returns:
    -------
    float
        The current mass (M), which will trigger the event when it reaches zero.

    """
    del t

    return y[3]


def event_N_crit(t: float, y: list, N_c: float):
    """
    Event triggered once there has been N_RT = N_c Rayleigh-Taylor growth timescales. This 
    defines the onset of fragmentation, given the assumptions used in pancake-models break-
    down.

    Parameters:
    ----------
    t : float
        Simulation time (unused but required by scipy.integrate.solve_ivp)
    y : list
        The current state variables
    N_c : float
        The critical number of Rayleigh-Taylor growth timescale (default: 2)

    Returns:
    -------
    float
        N_RT - N-c, which will trigger the event when it reaches zero.

    """
    del t

    return N_c - y[9]


def run(impactor: Meteoroid,
        C_d: float,
        C_h: float,
        R_pl: float,
        M_pl: float,
        rho_atm0: float,
        H: float,
        dt: float,
        N_c=2.):
    """
    Runs the numerical integration to calculate the meteoroid's atmospheric trajectory,
    stopping the simulation based on predefined events, which include:
    - reaching the ground (altitude = 0)
    - total mass ablation (mass = 0)
    - the onset of fragmentation (following N_rt = N_c Rayleigh-Taylor timescales)

    Parameters:
    ----------
    impactor : Meteoroid
        The meteoroid object
    C_d : float
        Drag coefficient [dimensionless]
    C_h : float
        Heat transfer coefficient [dimensionless]
    R_pl : float
        Radius of the planet [m]]
    M_pl : float
        Mass of the planet [kg]]
    rho_atm0 : float
        Atmospheric surface density [kg/m^3]
    H : float
        Atmospheric scale height [m]
    dt : float
        Simulation (maximum) timestep [s]
    N_c : float, optional
        The critical number of Rayleigh-Taylor growth timescale (default: 2)

    Returns:
    -------
    tuple
        A tuple containing:
        - t : np.ndarray
            Simulation times
        - mass : np.ndarray
            Meteoroid's mass at each timestep
        - radius : np.ndarray
            Meteoroid's radius at each timestep
        - dM : np.ndarray
            Meteoroid's mass loss at each timestep
        - dEkin : np.ndarray
            Meteoroid's energy loss at each timestep
        - x, y, z : np.ndarray
            Meteoroid's position at each timestep
        - vx, vy, vz : np.ndarray
            Meteoroid's velocity at each timestep
        - N_RT : np.ndarray
            Number of elapsed Rayleigh-Taylor timescales at each timestep

    """

    t_span = (0, 5000)

    def event_N_crit_with_Nc(t: float, y: list):
        """
        Event triggered once there has been N_RT = N_c Rayleigh-Taylor growth timescales. This 
        defines the onset of fragmentation, given the assumptions used in pancake-models break-
        down.
        """

        return event_N_crit(t, y, N_c)

    event_Z_crossing.terminal = True
    event_Z_crossing.direction = -1

    event_mass_zero.terminal = True
    event_mass_zero.direction = -1

    event_N_crit_with_Nc.terminal = True
    event_N_crit_with_Nc.direction = -1

    # these events terminate the integration
    events = [event_Z_crossing, event_mass_zero, event_N_crit_with_Nc]

    x0, y0, z0 = impactor.x, impactor.y, impactor.z
    vx0, vy0, vz0 = impactor.vx, impactor.vy, impactor.vz
    R0 = impactor.radius
    M0 = impactor.mass
    Rdot0 = 0

    rho_imp = impactor.rho
    sigma_imp = impactor.sigma
    eta = impactor.eta

    sol_iso = solve_ivp(
        fun=lambda t, y: differential_equations(t, y, sigma_imp, rho_imp, eta, C_d,
                                                C_h, R_pl, M_pl, rho_atm0, H),
        t_span=t_span,
        y0=[vx0, vy0, vz0, M0, x0, y0, z0, R0, Rdot0, 0.],
        method='RK45',
        dense_output=True,
        events=events,
        max_step=dt
    )

    t = sol_iso.t

    vx = sol_iso.sol(t)[0][:len(t)]
    vy = sol_iso.sol(t)[1][:len(t)]
    vz = sol_iso.sol(t)[2][:len(t)]
    mass = sol_iso.sol(t)[3][:len(t)]
    x = sol_iso.sol(t)[4][:len(t)]
    y = sol_iso.sol(t)[5][:len(t)]
    z = sol_iso.sol(t)[6][:len(t)]
    radius = sol_iso.sol(t)[7][:len(t)]
    N_RT = sol_iso.sol(t)[9][:len(t)]

    vel = np.sqrt(vx ** 2 + vy ** 2 + vz ** 2)
    Ekin = 0.5 * mass * (vel ** 2)

    dM = np.abs(np.diff(mass, append=mass[-1]))
    dEkin = np.abs(np.diff(Ekin, append=Ekin[-1]))

    return t, mass, radius, dM, dEkin, x, y, z, vx, vy, vz, N_RT
