"""
Module docstring: COME BACK AND UPDATE WHEN ALL THE SETTERS/GETTERS IN PLACE FOR METEOROID CLASS!
"""

import pytest
import numpy as np
from atmosentry.meteoroid import Meteoroid


def test_meteoroid():
    """
    Docstring
    """

    meteoroid = Meteoroid(x=0,
                          y=0,
                          z=100e3,
                          vx=-20e3 * np.cos(45 * np.pi / 180),
                          vy=0,
                          vz=-20e3 * np.sin(45 * np.pi / 180),
                          radius=150,
                          mass=0.6e3 * (4 * np.pi / 3) * (150 ** 3),
                          sigma=1e4,
                          rho=0.6e3,
                          eta=2.5e6)

    assert meteoroid
    assert (meteoroid.x == 0) and (meteoroid.y == 0) and (meteoroid.z == 100e3)
    assert (meteoroid.vx == -20e3 * np.cos(45 * np.pi / 180)) and\
            (meteoroid.vy == 0) and\
            (meteoroid.vz == -20e3 * np.sin(45 * np.pi / 180))
    assert meteoroid.radius == 150
    assert meteoroid.mass == 0.6e3 * (4 * np.pi / 3) * (150 ** 3)
    assert meteoroid.sigma == 1e4
    assert meteoroid.rho == 0.6e3
    assert meteoroid.eta == 2.5e6


@pytest.mark.parametrize("param_name", [
    'x', 'y', 'z', 'vx', 'vy', 'vz', 'radius', 'mass', 'sigma', 'rho', 'eta'
])
@pytest.mark.parametrize("invalid_value", [
    'string', [1, 2, 3], False, np.array([1,2,3]), (1, 2)
])
def test_meteoroid_setters(param_name, invalid_value):
    """
    Test the setters of the Meteoroid class to ensure they
    raise a TypeError when given invalid values.
    """

    valid_values = {
        'x': 0, 'y': 0, 'z': 100e3,
        'vx': -20e3 * np.cos(45 * np.pi / 180),
        'vy': 0, 'vz': -20e3 * np.sin(45 * np.pi / 180),
        'radius': 150,
        'mass': 0.6e3 * (4 * np.pi / 3) * (150 ** 3),
        'sigma': 1e4, 'rho': 0.6e3, 'eta': 2.5e6,
    }

    invalid_params = valid_values.copy()
    invalid_params[param_name] = invalid_value

    with pytest.raises(TypeError):
        _ = Meteoroid(**invalid_params)


@pytest.mark.parametrize("invalid_value", [
    'string', [1, 2, 3], 0., 0, np.array([1,2,3]), (1, 2)
])
def test_meteoroid_setter_children(invalid_value):
    """
    Docstring
    """

    with pytest.raises(TypeError):
        _ = Meteoroid(x=0,
                      y=0,
                      z=100e3,
                      vx=-20e3 * np.cos(45 * np.pi / 180),
                      vy=0,
                      vz=-20e3 * np.sin(45 * np.pi / 180),
                      radius=150,
                      mass=0.6e3 * (4 * np.pi / 3) * (150 ** 3),
                      sigma=1e4,
                      rho=0.6e3,
                      eta=2.5e6,
                      children=invalid_value)


@pytest.mark.parametrize("param_name", [
    'x', 'y', 'z', 'vx', 'vy', 'vz', 'radius', 'mass', 'dM', 'dEkin', 'dt'
])
@pytest.mark.parametrize("invalid_value", [
    'string', [1, 2, 3], 0., 0, np.array([1,2,3]), (1, 2)
])
def test_meteoroid_state(param_name, invalid_value):
    """
    Docstring
    """

    impactor = Meteoroid(x=0,
                         y=0,
                         z=100e3,
                         vx=-20e3 * np.cos(45 * np.pi / 180),
                         vy=0,
                         vz=-20e3 * np.sin(45 * np.pi / 180),
                         radius=150,
                         mass=0.6e3 * (4 * np.pi / 3) * (150 ** 3),
                         sigma=1e4,
                         rho=0.6e3,
                         eta=2.5e6)

    with pytest.raises(AttributeError):
        setattr(impactor.state, param_name, invalid_value)


@pytest.mark.parametrize("param_name", [
    'x', 'y', 'z', 'vx', 'vy', 'vz', 'radius', 'mass', 'dM', 'dEkin', 't'
])
@pytest.mark.parametrize("invalid_value", [
    'string', [1, 2, 3], False, 0, 0., (1, 2),
])
def test_meteoroid_state_update(param_name, invalid_value):
    """
    Docstring
    """

    impactor = Meteoroid(x=0,
                         y=0,
                         z=100e3,
                         vx=-20e3 * np.cos(45 * np.pi / 180),
                         vy=0,
                         vz=-20e3 * np.sin(45 * np.pi / 180),
                         radius=150,
                         mass=0.6e3 * (4 * np.pi / 3) * (150 ** 3),
                         sigma=1e4,
                         rho=0.6e3,
                         eta=2.5e6)

    valid_values = {
        'x': np.linspace(0, 1, 1000),
        'y': np.linspace(0, 1, 1000),
        'z': np.linspace(0, 1, 1000),
        'vx': np.linspace(0, 1, 1000),
        'vy': np.linspace(0, 1, 1000),
        'vz': np.linspace(0, 1, 1000),
        'radius': np.linspace(0, 1, 1000),
        'mass': np.linspace(0, 1, 1000),
        'dM': np.linspace(0, 1, 1000),
        'dEkin': np.linspace(0, 1, 1000),
        't': np.linspace(0, 1, 1000)
    }

    invalid_values = valid_values.copy()
    invalid_values[param_name] = invalid_value

    with pytest.raises(TypeError):
        impactor.state.update(
            invalid_values['x'],
            invalid_values['y'],
            invalid_values['z'],
            invalid_values['vx'],
            invalid_values['vy'],
            invalid_values['vz'],
            invalid_values['radius'],
            invalid_values['mass'],
            invalid_values['dM'],
            invalid_values['dEkin'],
            invalid_values['t']
        )
