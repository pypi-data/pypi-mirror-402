# pylint: disable=duplicate-code

"""
Module docstring:
"""

import pytest
import numpy as np
from atmosentry.meteoroid import Meteoroid
from atmosentry import Simulation


@pytest.mark.parametrize("param_name", [
    't', 'Cd', 'Ch', 'Mpl', 'Rpl', 'H', 'rho0', 'dt', 'Nfrag', 'fragments_track'
])
def test_simulation(param_name):
    """
    Docstring
    """

    sim = Simulation()
    assert sim

    valid_attrs = {
        't': 0,
        'Cd': 0.7,
        'Ch': 0.02,
        'Mpl': 5.97e24,
        'Rpl': 6371e3,
        'H': 7.2e3,
        'rho0': 1.225,
        'dt': 1e-2,
        'Nfrag': 2,
        'fragments_track': True
    }

    assert getattr(sim, param_name) == valid_attrs[param_name]


def test_simulation_default_imapctor():
    """
    Docstring
    """

    sim = Simulation()

    with pytest.raises(AttributeError):
        assert sim.impactor


def test_simulation_impactor():
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

    sim = Simulation()
    sim.impactor = impactor

    assert sim.impactor == impactor


@pytest.mark.parametrize("param_name", [
    't', 'Cd', 'Ch', 'Mpl', 'Rpl', 'H', 'rho0', 'impactor'
])
@pytest.mark.parametrize("invalid_value", [
    0, [1, 2, 3], 'string', False, np.array([1, 2, 3]), (1, 2)
    ])
def test_simulation_setters(param_name, invalid_value):
    """
    Docstring
    """

    sim = Simulation()

    with pytest.raises(TypeError):
        setattr(sim, param_name, invalid_value)


@pytest.mark.parametrize("invalid_value", [
    0, 0., 'string', [1, 2, 3], (1, 2), np.array([1, 2, 3])
    ])
def test_simulation_setters_bool(invalid_value):
    """
    Docstring
    """

    sim = Simulation()

    with pytest.raises(TypeError):
        sim.fragments_track = invalid_value


@pytest.mark.parametrize("invalid_value", [
    [1, 2, 3],
    np.array([1, 2, 3]),
    'impactor',
    False,
    0,
    0.,
    (1, 2),
    Meteoroid(x=0,
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
])
def test_simulation_setters_fragments(invalid_value):
    """
    Docstring
    """

    sim = Simulation()

    with pytest.raises(TypeError):
        sim.fragments = invalid_value
