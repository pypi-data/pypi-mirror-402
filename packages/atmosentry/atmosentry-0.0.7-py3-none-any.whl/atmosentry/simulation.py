# pylint: disable=C0103

"""
Add docstring...
"""

import numpy as np
from atmosentry.meteoroid import Meteoroid
from atmosentry.integrator import run
from atmosentry.fragments import generate_fragments


class Simulation():
    """
    This is the atmospheric entry simulation class, which models the entry and (progressive) 
    fragmentation of a meteoroid during atmospheric entry.
    """

    def __init__(self,
                 t=0.,
                 fragments=np.array([]),
                 Cd=0.7,
                 Ch=0.02,
                 Mpl=5.97e24,
                 Rpl=6371e3,
                 rho0=1.225,
                 H=7.2e3,
                 Nfrag=2,
                 fragments_track=True,
                 dt=1e-2
                 ):
        """
        Initializes a new atmospheric entry simulation instance.

        Args:
        -----
            t (float): Initial time of the simulation (default is 0)
            fragments (np.ndarray): Array of fragment objects (default is empty array)
            Cd (float): Drag coefficient [dimensionless] (default is 0.7).
            Ch (float): Heat transfer coefficient [dimensionless] (default is 0.02)
            Mpl (float): Mass of the planet [kg] (default: Earth's mass, 5.97e24)
            Rpl (float): Radius of the planet [m] (default: Earth's radius, 6371e3)
            rho0 (float): Atmospheric surface density [kg/m^3] (default: 1.225)
            H (float): Atmospheric scale height [m] (default: Earth's atmosphere, 7200).
            Nfrag (int): Number of child meteoroids per fragmentation (default: 2).
            fragments_track (bool): Fragment tracking during the simulation (default: True)
            dt (float): Simulation (maximum) timestep [s] (default: 1e-2)
            impactor (Meteoroid, optional): The meteoroid object to simulate. 
                                            (If not provided, the simulation starts empty.)
        """

        self.t = t
        self.fragments = fragments
        self.Cd=Cd
        self.Ch=Ch
        self.Mpl=Mpl
        self.Rpl=Rpl
        self.rho0 = rho0
        self.H=H
        self.Nfrag = Nfrag
        self.fragments_track = fragments_track
        self.dt = dt

    @property
    def t(self):
        """
        Getter for simulation time.
        
        Returns:
        --------
            float: The current simulation time

        """
        return self._t

    @t.setter
    def t(self, t):
        """
        Setter for simulation time.
        
        Args:
        -----
            t (float): The simulation time to set

        Raises:
        -------
            TypeError: If t is not a float.
        """
        if not isinstance(t, float):
            raise TypeError("Simulation time must be a float.")
        if isinstance(t, float):
            self._t = t

    @property
    def fragments(self):
        """
        Getter for the fragments property.
        
        Returns:
        --------
            np.ndarray: The array of Meteoroid fragments.
        """
        return self._fragments

    @fragments.setter
    def fragments(self, fragments):
        """
        Setter for the fragments property.
        
        Args:
        -----
            fragments (np.ndarray): The array of fragments to set.
        
        Raises:
        -------
            TypeError: If fragments is not an array of Meteoroid objects.
        """
        if not isinstance(fragments, np.ndarray):
            raise TypeError("Must store fragments as an array.")
        for fragment in fragments:
            if not isinstance(fragment, Meteoroid):
                raise TypeError("Not a Meteoroid object.")
        if isinstance(fragments, np.ndarray):
            self._fragments = fragments

    @property
    def Cd(self):
        """
        Getter for the drag coefficient.
        
        Returns:
        --------
            float: The drag coefficient.
        """
        return self._Cd

    @Cd.setter
    def Cd(self, Cd):
        """
        Setter for the drag coefficient.
        
        Args:
        -----
            Cd (float): The drag coefficient.
        
        Raises:
        -------
            TypeError: If Cd is not a float.
        """
        if not isinstance(Cd, float):
            raise TypeError("Drag coefficient must be a float.")
        if isinstance(Cd, float):
            self._Cd = Cd

    @property
    def Ch(self):
        """
        Getter for the heat transfer coefficient.
        
        Returns:
        --------
            float: The heat transfer coefficient.
        """
        return self._Ch

    @Ch.setter
    def Ch(self, Ch):
        """
        Setter for the heat transfer coefficient.
        
        Args:
        -----
            Ch (float): The heat transfer coefficient.
        
        Raises:
        -------
            TypeError: If Ch is not a float.
        """
        if not isinstance(Ch, float):
            raise TypeError("Heat transfer coefficient must be a float.")
        if isinstance(Ch, float):
            self._Ch = Ch

    @property
    def Mpl(self):
        """
        Getter for the planet mass.
        
        Returns:
        --------
            float: The mass of the planet.
        """
        return self._Mpl

    @Mpl.setter
    def Mpl(self, Mpl):
        """
        Setter for the planet mass.
        
        Args:
        -----
            Mpl (float): The mass of the planet.
        
        Raises:
        -------
            TypeError: If Mpl is not a float.
        """
        if not isinstance(Mpl, float):
            raise TypeError("Planet mass must be a float.")
        if isinstance(Mpl, float):
            self._Mpl = Mpl

    @property
    def Rpl(self):
        """
        Getter for the planet radius.
        
        Returns:
        --------
            float: The radius of the planet.
        """
        return self._Rpl

    @Rpl.setter
    def Rpl(self, Rpl):
        """
        Setter for the planet radius.
        
        Args:
        -----
            Rpl (float): The radius of the planet.
        
        Raises:
        -------
            TypeError: If Rpl is not a float.
        """
        if not isinstance(Rpl, float):
            raise TypeError("Planet radius must be a float.")
        if isinstance(Rpl, float):
            self._Rpl = Rpl

    @property
    def H(self):
        """
        Getter for the atmospheric scale height.
        
        Returns:
        --------
            float: The atmospheric scale height.
        """
        return self._H

    @H.setter
    def H(self, H):
        """
        Setter for the atmospheric scale height.
        
        Args:
        -----
            H (float): The scale height of the atmosphere.
        
        Raises:
        -------
            TypeError: If H is not a float.
        """
        if not isinstance(H, float):
            raise TypeError("Atmospheric scale height must be a float.")
        if isinstance(H, float):
            self._H = H

    @property
    def fragments_track(self):
        """
        Getter for the fragment tracking status.
        
        Returns:
        --------
            bool: Whether fragment tracking is enabled.
        """
        return self._fragments_track

    @fragments_track.setter
    def fragments_track(self, fragments_track):
        """
        Setter for the fragment tracking status.
        
        Args:
        -----
            fragments_track (bool): Whether to enable or disable fragment tracking.
        
        Raises:
        -------
            TypeError: If fragments_track is not a boolean.
        """
        if not isinstance(fragments_track, bool):
            raise TypeError("Fragment tracking must be a bool.")
        if isinstance(fragments_track, bool):
            self._fragments_track = fragments_track

    @property
    def rho0(self):
        """
        Getter for the atmospheric surface density.
        
        Returns:
        --------
            float: The atmospheric density at surface level.
        """
        return self._rho0

    @rho0.setter
    def rho0(self, rho0):
        """
        Setter for the atmospheric surface density.
        
        Args:
        -----
            rho0 (float): The atmospheric density at surface level.
        
        Raises:
        -------
            TypeError: If rho0 is not a float.
        """
        if not isinstance(rho0, float):
            raise TypeError("Atmospheric surface density must be a float.")
        if isinstance(rho0, float):
            self._rho0 = rho0

    @property
    def dt(self):
        """
        Getter for the simulation (maximum) timstep.
        
        Returns:
        --------
            float: The simulation (maximum) timstep.
        """
        return self._dt

    @dt.setter
    def dt(self, dt):
        """
        Setter for the simulation (maximum) timstep.
        
        Args:
        -----
            dt (float): The simulation (maximum) timstep.
        
        Raises:
        -------
            TypeError: If dt is not a float.
        """
        if not isinstance(dt, float):
            raise TypeError("Simulation timestep must be a float.")
        if isinstance(dt, float):
            self._dt = dt

    @property
    def impactor(self):
        """
        Getter for the impactor object.
        
        Returns:
        --------
            Meteoroid: The Meteoroid object representing the impactor.
        """
        return self._impactor

    @impactor.setter
    def impactor(self, value):
        """
        Setter for the impactor object.
        
        Args:
        -----
            value (Meteoroid): The impactor object to set.
        
        Raises:
        -------
            TypeError: If value is not a Meteoroid object.
        """
        if not isinstance(value, Meteoroid):
            raise TypeError("Impactor must be a Meteoroid object.")
        if isinstance(value, Meteoroid):
            self._impactor = value

    def integrate(self):
        """
        Simulates the atmospheric entry and fragmentation of a meteoroid.

        This method performs the following steps:
        -----------------------------------------
            1. Simulates the entry of the parent body (`self._impactor`) through the atmosphere.
            2. Updates the impactor object (position, velocity, mass, etc.) from simulation results.
            3. If fragment tracking (`self._fragments_track`) is enabled and the meteoroid has not 
            reached the surface the method generates child fragments.
            4. Recursively simulates the entry of all child fragments until all fragments reach the
            surface, or are fully ablated.

        Attributes Updated:
        -------------------
            self._t: The simulation time.
            self._fragments: An array of all fragments generated during the simulation
                            (including their state vectors)
            self._impactor: The final state vector of the main meteoroid.

        Outputs:
        --------
            Prints real-time progress updates to the console, including the meteoroid radius and the
            number of fragments in the Simulation object.
        """

        t, mass, radius, dM, dEkin, x, y, z, vx, vy, vz, _ =\
            run(self._impactor,
                        self._Cd,
                        self._Ch,
                        self._Rpl,
                        self._Mpl,
                        self._rho0,
                        self._H,
                        self._dt,
                        N_c=2.,
            )

        self._t = t
        self._impactor.state.update(x, y, z, vx, vy, vz, radius, mass,
                                    dM, dEkin, t + self._impactor.t_init)

        if self._fragments_track:
            if self._impactor.state.z[-1] > 1:
                self._impactor.children = True

                child_fragments = generate_fragments(self._impactor, self.rho0, self.H, self.Nfrag)

                while len(child_fragments) > 0:
                    fragments_tmp = []

                    for fragment in child_fragments:
                        print(f'R_0={self._impactor.radius}m, N_frags={len(child_fragments)}',\
                              end='\n', flush=True)

                        t_f, mass_f, radius_f, dM_f, dEkin_f, x_f, y_f, z_f, vx_f, vy_f, vz_f, _ =\
                            run(fragment,
                                self._Cd,
                                self._Ch,
                                self._Rpl,
                                self._Mpl,
                                self._rho0,
                                self._H,
                                self._dt,
                                N_c=2.
                            )

                        fragment.state.update(x_f, y_f, z_f, vx_f, vy_f, vz_f, radius_f, mass_f,
                                              dM_f, dEkin_f, t_f + fragment.t_init)

                        if z_f[-1] < 1:
                            self._fragments = np.append(self._fragments, fragment)
                        elif mass_f[-1] < 0.005 * self._impactor.state.mass[0]:
                            mass_f = np.append(mass_f, mass_f[-1])
                            radius_f = np.append(radius_f, radius_f[-1])
                            x_f = np.append(x_f, x_f[-1])
                            y_f = np.append(y_f, y_f[-1])
                            z_f = np.append(z_f, z_f[-1])
                            vx_f = np.append(vx_f, vx_f[-1])
                            vy_f = np.append(vy_f, vy_f[-1])
                            vz_f = np.append(vz_f, vz_f[-1])

                            vel = vx_f[-1] ** 2 + vy_f[-1] ** 2 + vz_f[-1] ** 2

                            dM_f = np.append(dM_f, mass_f[-1])
                            dEkin_f = np.append(dEkin_f, 0.5 * mass_f[-1] * vel)

                            fragment.state.update(x_f, y_f, z_f, vx_f, vy_f, vz_f, radius_f,
                                                  mass_f, dM_f, dEkin_f, t_f + fragment.t_init)
                            self._fragments = np.append(self._fragments, fragment)

                        else:
                            fragment.children = True
                            self._fragments = np.append(self._fragments, fragment)
                            child_frags = generate_fragments(fragment, self.rho0,
                                                             self.H, self.Nfrag)
                            fragments_tmp = np.append(fragments_tmp, child_frags)

                    child_fragments = fragments_tmp
