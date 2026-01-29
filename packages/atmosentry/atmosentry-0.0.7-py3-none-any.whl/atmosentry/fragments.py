# pylint: disable=C0103

"""
Module: Meteoroid fragmentation methods

This module provides functions to simulate the fragmentation of meteoroids in the atmosphere, 
calculating the mass and velocity of child fragments post-fragmentation.
"""

import numpy as np
from atmosentry.meteoroid import Meteoroid


def gen_fragment_masses(m_init: float, N_frags: int):
    """"
    Generates the mass of child fragments produced, which sum to m_init.

    The mass of child fragments, m_i, are chosen proportional to a random
    variable x, such that
    m_i / m_init = x, where x ~ U[0,1]
    Child fragment masses are then normalised such that
    sum{m_i} = m_init

    Parameters:
    ----------
    m_init : float
        The initial mass of the meteoroid before fragmentation
    N_frags : int
        The number of child fragments generated

    Returns:
    -------
    np.ndarray
        Array of child fragment masses (note: this will sum to m_init)
    """

    masses = np.random.rand(N_frags)
    masses = masses / np.sum(masses) * m_init

    return masses


def calc_fragment_velocities(rho_atm: float, rho_imp: float, vel: float,
                             m_init: float, frag_masses: list):
    """
    Calculates the transverse velocities (v_alpha, v_beta) of child fragments after fragmentation,
    following the procedure described in the article. 

    Fragment velocities are computed along two perpendicular components:
        - v_alpha: Velocity in the horizontal plane.
        - v_beta: Velocity in the vertical plane.

    Random angles (phi) are assigned to each fragment, and the velocities are normalised to conserve
    linear momentum.

    Parameters:
    ----------
    rho_atm : float
        Atmospheric density at the point of fragmentation.
    rho_imp : float
        Density of the meteoroid.
    vel : float
        The velocity of the parent body before fragmentation.
    m_init : float
        The mass of the parent meteoroid before fragmentation.
    frag_masses : list
        The (randomly chosen) fragment masses - from method gen_fragment_masses().

    Returns:
    -------
    tuple
        v_alpha : np.ndarray
            alpha component of fragment's transverse velocity
        v_beta : np.ndarray
            beta component of fragment's transverse velocity
    """

    vs = vel * np.sqrt(rho_atm / rho_imp)

    phi = 2 * np.pi * np.random.rand(len(frag_masses))

    v_alpha = vs * (np.cos(phi) - np.sum(frag_masses * np.cos(phi)) / m_init)
    v_beta = vs * (np.sin(phi) - np.sum(frag_masses * np.sin(phi)) / m_init)

    return v_alpha, v_beta


def generate_fragments(fragment: Meteoroid,
                       rho_atm: float,
                       H: float,
                       N_frag: int):
    """
    Generates child fragments of a a parent body {fragment} following the presc-
    ription described in the article. 

    The mass of the fragments is determined by `gen_fragment_masses`, while their 
    velocities are computed using `calc_fragment_velocities`. The remaining fragment
    properties are inherited from their parent.

    Parameters:
    ----------
    fragment : Meteoroid
        The parent meteoroid object undergoing fragmentation.
    rho_atm : float
        Surface atmospheric density
    H : float
        Scale height of the atmosphere
    N_frag : int
        The number of child fragments generated

    Returns:
    -------
    list of Meteoroid
        A list of `Meteoroid` objects corresponding to the child fragments.
    """

    vx, vy, vz = fragment.state.vx, fragment.state.vy, fragment.state.vz
    x, y, z = fragment.state.x, fragment.state.y, fragment.state.z
    theta = np.arctan(fragment.state.vz / fragment.state.vx)

    rho_m = fragment.rho

    velocity = np.sqrt(vx ** 2 + vy ** 2 + vz ** 2)

    masses = gen_fragment_masses(fragment.state.mass[-1], N_frag)

    v_alpha, v_beta = calc_fragment_velocities(rho_atm * np.exp(-z[-1]/H),
                                               rho_m, velocity[-1], fragment.state.mass[-1],
                                               masses)

    h_final = fragment.state.mass[-1] / (rho_m * np.pi * fragment.state.radius[-1] ** 2)

    fragments = []
    for counter, mass in enumerate(masses):

        r_frag = np.sqrt(mass / (rho_m * np.pi * h_final))

        v_frag_x = vx[-1] + v_beta[counter] * np.cos(theta[-1])
        v_frag_y = vy[-1] + v_alpha[counter]
        v_frag_z = vz[-1] + v_beta[counter] * np.sin(theta[-1])

        frag = Meteoroid(x=x[-1], y=y[-1], z=z[-1],
                         vx=v_frag_x, vy=v_frag_y, vz=v_frag_z,
                         radius=r_frag, mass=mass, rho=rho_m,
                         sigma=fragment.sigma, eta=fragment.eta,
                         t_init=fragment.state.t[-1])

        fragments = np.append(frag, fragments)

    return fragments
