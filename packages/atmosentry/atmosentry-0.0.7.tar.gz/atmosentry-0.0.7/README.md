[![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/PyCQA/pylint)
![Tests](https://github.com/richard17a/atmosentry/actions/workflows/python-package.yml/badge.svg)
[![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-360/) 
[![Python 3.9](https://img.shields.io/badge/python-3.9-red.svg)](https://www.python.org/downloads/release/python-360/) 
[![Python 3.10](https://img.shields.io/badge/python-3.10-green.svg)](https://www.python.org/downloads/release/python-360/)
![Version](https://img.shields.io/badge/version-v0.0.2-blue)

# atmosentry

atmosentry is a numerical integrator that simulates the atmospheric entry of comets. For full description of the numerical model see [this article](https://academic.oup.com/mnras/advance-article/doi/10.1093/mnras/staf507/8098221).
Key details are described below, focussing primarily on free model parameters. 

## Setup

- Clone the Github repository
- Navigate to the project directory (/atmosentry)
- Important: Ensure you are using a Python version between 3.8-3.10
- Install required packages
    - pip3 install -r requirements.txt
- Install the package
    - pip3 install .

## How to use atmosentry

The [examples/](./examples/) sub-directory contains several ipython notebooks that demonstrate the basic functionality of atmosentry.


## Model description

atmosentry includes specific semi-analytical prescriptions for the ablation, deformation, and fragmentation of comets as they travel through the atmosphere.


### Atmospheric deceleration

Assuming the comet arrives at the top of the atmosphere at an initial angle $\theta$ wrt. the local horizontal, and velocity $\mathbf{v}=(v_x,v_y,v_z)$, 
its deceleration is given by
```math
m\dfrac{d\mathbf{v}}{dt} = -\dfrac{1}{2}C_D\rho_{\rm atm}(z)A|\mathbf{v}|\mathbf{v} -g(z)\mathbf{\hat{e}}_z,
```
where $C_D$ is the comet's drag coefficient, which is left as a free parameter. The comet's position is tracked through the atmosphere, and evolves as
```math
\dfrac{d\mathbf{x}}{dt} = \mathbf{v}.
```

As isothermal atmospheric profile is assumed with scale height $H$,
```math
\rho_{\rm atm} = \rho_{\rm atm,0}\exp{\left(-\dfrac{z}{H}\right)},
```
where the surface atmospheric density $\rho_{\rm atm, 0}$ is also left as a free parameter.

### Mass ablation

Mass loss due to ablation is described by the classical Bronshten (1983) parameterisation,
```math
\xi\dfrac{dm}{dt} = -A\,\text{min}\left(\dfrac{1}{2}C_H\rho_{\rm atm}v^3,\sigma_{\rm SB}T^4\right),
```
where $T \simeq 25000\,{\rm K}$ is the temperature of the shocked gas at the leading edge of the comet. The heat transfer coefficient 
($C_H$) is left as a free parameter.


### Deformation

Given the friable, highly porous nature of cometary impactors, we adopt the progressive fragmentation described in Chyba et al., (1993), 
in which the comet deforms into a cylinder of height $h=m/(\pi\rho_mr^2)$. Its radius increases according to
```math
r\dfrac{d^2r}{dt^2} = \dfrac{C_D}{2}\left(\dfrac{\rho_{\rm atm}}{\rho_{\rm m}}\right)v^2.
```

### Fragmentation

This deformation will not continue indefinitely, with 3D simulations demonstrating that Rayleigh-Taylor instabilities drive the fragmentation of the comet.
Comets break-up after $N_{\rm RT}$ Rayleigh-Taylor growth timescales, which is left as a free parameter in the model. The number of fragments ($n$) produced
during fragmentation remains poorly constrained, and is also left as a free parameter. The masses of child fragments are chosen proportional to a random variable
```math
\dfrac{m_i}{m_{\rm parent}} = x, \hspace{1em} \text{where}~x\sim\mathcal{U}[0,1],
```
and normalised such that 
```math
\sum_{i=1}^n{m_i} = m_{\rm parent}.
```
