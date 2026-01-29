# pylint: disable=C0103
# pylint: disable=W0102
# pylint: disable=R0903

"""
Module: meteoroid

This module defines the Meteoroid class, which contains the physical properties, 
and dynamic state of a meteoroid entering a planetary atmosphere. 
"""
import numpy as np


class MeteoroidState():
    """
    Describes the dynamic state of a meteoroid including its position, velocity, 
    radius, mass, mass loss, and energy loss.

    Attributes:
    -----------
        x (np.ndarray): The x-position of the meteoroid [m]
        y (np.ndarray): The y-position of the meteoroid [m]
        z (np.ndarray): The z-position of the meteoroid [m]
        vx (np.ndarray): The x-component of the meteoroid's velocity [m/s]
        vy (np.ndarray): The y-component of the meteoroid's velocity [m/s]
        vz (np.ndarray): The z-component of the meteoroid's velocity [m/s]
        radius (np.ndarray): Radius of the meteoroid [m]
        mass (np.ndarray): Mass of the meteoroid [kg]
        dM (np.ndarray): Mass loss rate of the meteoroid [kg/s]
        dEkin (np.ndarray): Kinetic energy loss rate of the meteoroid [J/s]
        t (np.ndarray): Time of the meteoroid's state [s]
    """

    def __init__(self,
                 x=None,
                 y=None,
                 z=None,
                 vx=None,
                 vy=None,
                 vz=None,
                 radius=None,
                 mass=None,
                 dM=None,
                 dEkin=None,
                 t=None
                 ):
        """
        Initializes the state of the meteoroid -- this is totally empty, and will
        only be updated during integration. These parameters cannot be set directly 
        by the user.

        Args:
        -----
            x (np.ndarray, optional): The x-position of the meteoroid [m]
            y (np.ndarray, optional): The y-position of the meteoroid [m]
            z (np.ndarray, optional): The z-position of the meteoroid [m]
            vx (np.ndarray, optional): The x-component of the meteoroid's velocity [m/s]
            vy (np.ndarray, optional): The y-component of the meteoroid's velocity [m/s]
            vz (np.ndarray, optional): The z-component of the meteoroid's velocity [m/s]
            radius (np.ndarray, optional): The radius of the meteoroid [m]
            mass (np.ndarray, optional): The mass of the meteoroid [kg]
            dM (np.ndarray, optional): The mass loss rate [kg/s]
            dEkin (np.ndarray, optional): The kinetic energy loss rate [J/s]
            t (np.ndarray, optional): Time of the meteoroid's state [s]
        """

        object.__setattr__(self,'x', x)
        object.__setattr__(self,'y', y)
        object.__setattr__(self,'z', z)
        object.__setattr__(self,'vx', vx)
        object.__setattr__(self,'vy', vy)
        object.__setattr__(self,'vz', vz)
        object.__setattr__(self,'radius', radius)
        object.__setattr__(self,'mass', mass)
        object.__setattr__(self,'dM', dM)
        object.__setattr__(self,'dEkin', dEkin)
        object.__setattr__(self,'t', t)

    def __setattr__(self, key, value):
        """
        Prevent the user from setting attributes directly.

        Args:
        -----
            key (str): The name of the attribute to be set.

        Raises:
        -------
            AttributeError: If an attempt is made to set an attribute directly.
        """

        raise AttributeError(f"Directly setting attribute '{key}' is not allowed!")

    def update(self,
               x,
               y,
               z,
               vx,
               vy,
               vz,
               radius,
               mass,
               dM,
               dEkin,
               t):
        """
        Updates the state of the meteoroid with new values. This method allows 
        updating all dynamic attributes of the meteoroid's state.

        Args:
        -----
            x (np.ndarray): New x-position of the meteoroid [m]
            y (np.ndarray): New y-position of the meteoroid [m]
            z (np.ndarray): New z-position of the meteoroid [m]
            vx (np.ndarray): New x-component of the meteoroid's velocity [m/s]
            vy (np.ndarray): New y-component of the meteoroid's velocity [m/s]
            vz (np.ndarray): New z-component of the meteoroid's velocity [m/s]
            radius (np.ndarray): New radius of the meteoroid [m]
            mass (np.ndarray): New mass of the meteoroid [kg]
            dM (np.ndarray): New mass loss rate of the meteoroid [kg/s]
            dEkin (np.ndarray): New kinetic energy loss rate of the meteoroid [J/s]
            t (np.ndarray): New time of the meteoroid's state [s]

        Raises:
        -------
            TypeError: If any of the input parameters are not of type np.ndarray.

        """

        if not isinstance(x, np.ndarray):
            raise TypeError(f"x must be of type np.ndarray, not {type(x).__name__}")
        if not isinstance(y, np.ndarray):
            raise TypeError(f"y must be of type np.ndarray, not {type(y).__name__}")
        if not isinstance(z, np.ndarray):
            raise TypeError(f"z must be of type np.ndarray, not {type(z).__name__}")
        if not isinstance(vx, np.ndarray):
            raise TypeError(f"vx must be of type np.ndarray, not {type(vx).__name__}")
        if not isinstance(vy, np.ndarray):
            raise TypeError(f"vy must be of type np.ndarray, not {type(vy).__name__}")
        if not isinstance(vz, np.ndarray):
            raise TypeError(f"vz must be of type np.ndarray, not {type(vz).__name__}")
        if not isinstance(radius, np.ndarray):
            raise TypeError(f"radius must be of type np.ndarray, not {type(radius).__name__}")
        if not isinstance(mass, np.ndarray):
            raise TypeError(f"mass must be of type np.ndarray, not {type(mass).__name__}")
        if not isinstance(dM, np.ndarray):
            raise TypeError(f"dM must be of type np.ndarray, not {type(dM).__name__}")
        if not isinstance(dEkin, np.ndarray):
            raise TypeError(f"dEkin must be of type np.ndarray, not {type(dEkin).__name__}")
        if not isinstance(t, np.ndarray):
            raise TypeError(f"t must be of type np.ndarray, not {type(t).__name__}")

        object.__setattr__(self, 'x', x)
        object.__setattr__(self, 'y', y)
        object.__setattr__(self, 'z', z)
        object.__setattr__(self, 'vx', vx)
        object.__setattr__(self, 'vy', vy)
        object.__setattr__(self, 'vz', vz)
        object.__setattr__(self, 'radius', radius)
        object.__setattr__(self, 'mass', mass)
        object.__setattr__(self, 'dM', dM)
        object.__setattr__(self, 'dEkin', dEkin)
        object.__setattr__(self, 't', t)


class Meteoroid():
    """
    Describes the physical properties, and trajectory of a meteoroid during atmospheric
    entry. The object also tracks whether the meteoroid has generated child fragments.

    Attributes:
    -----------
        x (float): The x-position of the meteoroid [m]
        y (float): The y-position of the meteoroid [m]
        z (float): The z-position of the meteoroid [m]
        vx (float): The x-component of the meteoroid's velocity [m/s] 
        vy (float): The y-component of the meteoroid's velocity [m/s] 
        vz (float): The z-component of the meteoroid's velocity [m/s] 
        radius (float): Radius of the meteoroid [m]]
        mass (float): Mass of the meteoroid [kg]]
        sigma (float): Tensile strength of the meteoroid [Pa]
        rho (float): Bulk density of the meteoroid [kg/m^3]
        eta (float): Heat of ablation of the meteoroid [J/kg]
        children (bool, optional): Meteoroid's child fragments (default: False)
        t_init (float, optional): Initial simulation time [s] (default: 0)
        state (MeteroidState): State object to track the bodies trajectory during Simulation

    """

    def __init__(self,
                 x,
                 y,
                 z,
                 vx,
                 vy,
                 vz,
                 radius,
                 mass,
                 sigma,
                 rho,
                 eta,
                 children=False,
                 t_init=0,
                 state=None):
        """
        Initializes a Meteoroid object with the given physical properties and initial state.

        Args:
        -----
            x (float): Initial x-coordinate of the meteoroid [m]
            y (float): Initial y-coordinate of the meteoroid [m]
            z (float): Initial z-coordinate (altitude) of the meteoroid [m]
            vx (float): Initial velocity in the x-direction [m/s]
            vy (float): Initial velocity in the y-direction [m/s]
            vz (float): Initial velocity in the z-direction [m/s]
            radius (float): Radius of the meteoroid [m]]
            mass (float): Mass of the meteoroid in [kg]
            sigma (float): Tensile strength of the meteoroid [Pa]
            rho (float): Bulk density of the meteoroid [kg/m^3]]
            eta (float): Heat of ablation of the meteoroid [J/kg]
            children (bool, optional): Meteoroid's child fragments (default: False)
            t_init (float, optional): Initial simulation time [s] (default: 0)
            state (MeteroidState): State object to track the bodies trajectory during Simulation

        """

        if state is None:
            state = MeteoroidState()

        self.x = x
        self.y = y
        self.z = z
        self.vx = vx
        self.vy = vy
        self.vz = vz
        self.radius = radius
        self.mass = mass
        self.sigma = sigma
        self.rho = rho
        self.eta = eta
        self.children = children
        self.t_init = t_init
        self.state = state

    @property
    def x(self):
        """
        Getter for the meteoroid's x-coordinate.
        """
        return self._x

    @x.setter
    def x(self, value):
        """
        Setter for the meteoroid's x-coordinate.
        """

        if not isinstance(value, (float, int)) or isinstance(value, bool):
            raise TypeError(f"x must be of type [float/int] not {type(value).__name__}")

        self._x = value

    @property
    def y(self):
        """
        Getter for the meteoroid's y-coordinate.
        """
        return self._y

    @y.setter
    def y(self, value):
        """
        Setter for the meteoroid's y-coordinate.
        """

        if not isinstance(value, (float, int)) or isinstance(value, bool):
            raise TypeError(f"y must be of type [float/int] not {type(value).__name__}")

        self._y = value

    @property
    def z(self):
        """
        Getter for the meteoroid's z-coordinate.
        """

        return self._z

    @z.setter
    def z(self, value):
        """
        Setter for the meteoroid's z-coordinate.
        """

        if not isinstance(value, (float, int)) or isinstance(value, bool):
            raise TypeError(f"z must be of type [float/int] not {type(value).__name__}")

        self._z = value

    @property
    def vx(self):
        """
        Getter for the meteoroid's velocity in the x-direction.
        """

        return self._vx

    @vx.setter
    def vx(self, value):
        """
        Setter for the meteoroid's velocity in the x-direction.
        """

        if not isinstance(value, (float, int)) or isinstance(value, bool):
            raise TypeError(f"vx must be of type [float/int] not {type(value).__name__}")

        self._vx = value

    @property
    def vy(self):
        """
        Getter for the meteoroid's velocity in the y-direction.
        """

        return self._vy

    @vy.setter
    def vy(self, value):
        """
        Setter for the meteoroid's velocity in the y-direction.
        """

        if not isinstance(value, (float, int)) or isinstance(value, bool):
            raise TypeError(f"vy must be of type [float/int] not {type(value).__name__}")

        self._vy = value

    @property
    def vz(self):
        """
        Getter for the meteoroid's velocity in the z-direction.
        """

        return self._vz

    @vz.setter
    def vz(self, value):
        """
        Setter for the meteoroid's velocity in the z-direction.
        """

        if not isinstance(value, (float, int)) or isinstance(value, bool):
            raise TypeError(f"vz must be of type [float/int] not {type(value).__name__}")

        self._vz = value

    @property
    def radius(self):
        """
        Getter for the meteoroid's radius.
        """

        return self._radius

    @radius.setter
    def radius(self, value):
        """Setter for the meteoroid's radius."""

        if not isinstance(value, (float, int)) or isinstance(value, bool):
            raise TypeError(f"radius must be of type [float/int], not {type(value).__name__}")

        self._radius = value

    @property
    def mass(self):
        """
        Getter for the meteoroid's mass.
        """

        return self._mass

    @mass.setter
    def mass(self, value):
        """
        Setter for the meteoroid's mass.
        """

        if not isinstance(value, (float, int)) or isinstance(value, bool):
            raise TypeError(f"mass must be of type [float/int] not {type(value).__name__}")

        self._mass = value

    @property
    def sigma(self):
        """
        Getter for the meteoroid's tensile strength.
        """

        return self._sigma

    @sigma.setter
    def sigma(self, value):
        """
        Setter for the meteoroid's tensile strength.
        """

        if not isinstance(value, (float, int)) or isinstance(value, bool):
            raise TypeError(f"sigma must be of type [float/int], not {type(value).__name__}")

        self._sigma = value

    @property
    def rho(self):
        """
        Getter for the meteoroid's bulk density.
        """

        return self._rho

    @rho.setter
    def rho(self, value):
        """
        Setter for the meteoroid's bulk density.
        """

        if not isinstance(value, (float, int)) or isinstance(value, bool):
            raise TypeError(f"rho must be of type [float/int] not {type(value).__name__}")

        self._rho = value

    @property
    def eta(self):
        """
        Getter for the meteoroid's heat of ablation.
        """

        return self._eta

    @eta.setter
    def eta(self, value):
        """
        Setter for the meteoroid's heat of ablation.
        """

        if not isinstance(value, (float, int)) or isinstance(value, bool):
            raise TypeError(f"eta must be of type float[,/int] not {type(value).__name__}")

        self._eta = value

    @property
    def children(self):
        """
        Getter for the meteoroid's children fragments status.
        """

        return self._children

    @children.setter
    def children(self, value):
        """
        Setter for the meteoroid's children fragments status.
        """

        if not isinstance(value, bool):
            raise TypeError(f"children must be of type bool, not {type(value).__name__}")

        self._children = value

    @property
    def t_init(self):
        """
        Getter for the meteoroid's initial time.
        """

        return self._t_init

    @t_init.setter
    def t_init(self, value):
        """
        Setter for the meteoroid's initial time.
        """

        if not isinstance(value, (float, int)) or isinstance(value, bool):
            raise TypeError(f"t_init must be of type [float/int], not {type(value).__name__}")

        self._t_init = value
