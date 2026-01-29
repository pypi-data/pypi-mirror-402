from .quantity import Quantity

class UnitRegistry:
    def __init__(self, autoload=True):
        self._units = {}
        self._base_units = {}
        
        # SI Prefixes
        self._prefixes = {
            'yotta': 1e24, 'zetta': 1e21, 'exa': 1e18, 'peta': 1e15, 'tera': 1e12, 'giga': 1e9, 'mega': 1e6, 'kilo': 1e3, 'hecto': 1e2, 'deca': 10,
            'deci': 1e-1, 'centi': 1e-2, 'milli': 1e-3, 'micro': 1e-6, 'nano': 1e-9, 'pico': 1e-12, 'femto': 1e-15, 'atto': 1e-18, 'zepto': 1e-21, 'yocto': 1e-24,
            # Short forms
            'Y': 1e24, 'Z': 1e21, 'E': 1e18, 'P': 1e15, 'T': 1e12, 'G': 1e9, 'M': 1e6, 'k': 1e3, 'h': 1e2, 'da': 10,
            'd': 1e-1, 'c': 1e-2, 'm': 1e-3, 'u': 1e-6, 'µ': 1e-6, 'n': 1e-9, 'p': 1e-12, 'f': 1e-15, 'a': 1e-18, 'z': 1e-21, 'y': 1e-24
        }
        
        if autoload:
            self.load_defaults()

    def load_defaults(self):
        # Length
        self.define('meter') # Full name for prefix matching
        self.alias('m', 'meter')
        
        # We can still explicitly define common ones if we want short aliases
        self.define('inch', 'meter', 0.0254)
        self.define('ft', 'inch', 12)
        self.define('yd', 'ft', 3)
        self.define('mile', 'yd', 1760)

        # Mass
        self.define('gram') # Base for prefixes usually, though SI base is kg. 
        # Registry handles 'kg' via prefix 'kilo' + 'gram' if 'gram' is base?
        # But 'kg' is the base unit of mass in SI.
        # Let's define 'gram' as base for our system to make 'milli-gram' work nicely.
        self.alias('g', 'gram')
        
        self.define('lb', 'gram', 453.59237)
        self.define('oz', 'lb', 1/16)
        
        # We need to manually alias 'kg' to 'kilogram' if we want short form to work with prefixes?
        # Or just define 'kg' as 1000 g.
        self.define('kg', 'gram', 1000)

        # Time
        self.define('second')
        self.alias('s', 'second')
        self.define('min', 's', 60)
        self.define('hr', 'min', 60)
        self.define('day', 'hr', 24)
        
        # Temperature
        self.define('kelvin')
        self.alias('K', 'kelvin')
        self.define('celsius', 'kelvin', 1.0, 273.15)
        self.alias('degC', 'celsius')
        self.define('rankine', 'kelvin', 5/9, 0)
        self.alias('degR', 'rankine')
        self.define('fahrenheit', 'kelvin', 5/9, 255.37222222222222)
        self.alias('degF', 'fahrenheit')
        # short aliases
        self.alias('C', 'celsius')
        self.alias('F', 'fahrenheit')

        # Power/Energy
        self.define('watt')
        self.alias('W', 'watt')
        self.define('joule')
        self.alias('J', 'joule')
        
        # Force (simulated as base for simplicity in this architecture)
        self.define('newton')
        self.alias('N', 'newton')
        
        # Pressure
        self.define('pascal')
        self.alias('Pa', 'pascal')
        self.define('kPa', 'pascal', 1000)
        self.define('mmHg', 'pascal', 133.3223684) # Standard
        
        # Volume
        self.define('liter')
        self.alias('L', 'liter')
        self.alias('l', 'liter')
        


        
        # Angles
        self.define('radian')
        self.alias('rad', 'radian')
        self.define('degree', 'radian', 0.017453292519943295)
        self.alias('deg', 'degree')

    def define(self, unit_name, base_unit=None, factor=1.0, offset=0.0):
        if base_unit is None:
            self._units[unit_name] = {'base': unit_name, 'factor': 1.0, 'offset': 0.0}
            self._base_units[unit_name] = unit_name
        else:
            if base_unit not in self._units:
                 # Try to resolve base_unit if it's a prefix
                 if not self.resolve_unit(base_unit):
                     raise ValueError(f"Unknown base unit: {base_unit}")
            
            parent_info = self._units[base_unit]
            self._units[unit_name] = {
                'base': parent_info['base'],
                'factor': factor * parent_info['factor'],
                'offset': offset * parent_info['factor'] + parent_info['offset'] 
            }
            
    def alias(self, alias_name, target_name):
        self.define(alias_name, target_name) # Factor 1, offset 0

    def resolve_unit(self, name):
        """Try to resolve dynamic prefixes if unit missing"""
        if name in self._units:
            return True
        
        # Check prefixes
        for prefix, mp in self._prefixes.items():
            if name.startswith(prefix):
                base = name[len(prefix):]
                if base in self._units:
                    # Found it! Define it dynamically
                    self.define(name, base, mp)
                    return True
        return False

    def parse(self, expression):
        """Parse a string expression like '10 km/hr' into a Quantity"""
        import re
        expression = expression.strip()
        match = re.match(r'^([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)\s*(.*)$', expression)
        if match:
            value_str = match.group(1)
            unit_str = match.group(3)
            return self.Quantity(float(value_str), unit_str)
        
        # If no number found, maybe just units? e.g. "m/s" -> 1 m/s
        # Or maybe "kg" -> 1 kg
        # Let's try to assume value 1 if no number at start?
        # But 'm' matches the regex? No, 'm' start with letter.
        return self.Quantity(1, expression)

    def __getattr__(self, name):
        if self.resolve_unit(name):
             return self.Quantity(1, name)
        raise AttributeError(f"'UnitRegistry' object has no attribute '{name}'")
    
    def get_base_unit(self, unit_name):
        return self._units.get(unit_name, {}).get('base')

    def get_factor(self, unit_name):
        return self._units.get(unit_name, {}).get('factor', 1.0)
    
    def get_offset(self, unit_name):
        return self._units.get(unit_name, {}).get('offset', 0.0)
        
    def Quantity(self, value, unit):
        return Quantity(value, unit, self)
