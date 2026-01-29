from .registry import UnitRegistry

# Create a shared registry for constants? 
# Or should constants be attached to a specific registry instance?
# Usually constants are universal. 
# But our Quantity needs a 'registry' instance to work.
# If we instantiate a new UnitRegistry here, it's fine.
_reg = UnitRegistry(autoload=True)

# Define constants
c = 299792458 * _reg.m / _reg.s
G = 6.67430e-11 * _reg.m**3 / (_reg.kg * _reg.s**2)
g_0 = 9.80665 * _reg.m / _reg.s**2
h = 6.62607015e-34 * _reg.J * _reg.s
angle_degree = _reg.parse("0.017453292519943295 rad") # If rad was defined...
# We haven't defined radians.
# Let's stick to core mechanical/EM constants.

# Boltzmann
k_B = 1.380649e-23 * _reg.J / _reg.K

# Electron charge?
# need coulomb
