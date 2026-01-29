try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

class Quantity:
    def __init__(self, value, unit, registry):
        if HAS_NUMPY and isinstance(value, list):
            self.value = np.array(value)
        else:
            self.value = value
        self.registry = registry
        
        if isinstance(unit, str):
            self._units = self._parse_unit_string(unit)
        elif isinstance(unit, dict):
            self._units = unit.copy()
        else:
             raise TypeError("Unit must be a string or dictionary")

        # Validation deferred to usage or init? 
        # For performance with many arrays, maybe validate once?
        # Let's keep validation on init for safety
        for u in self._units:
            if u not in registry._units:
                # Could be a prefixed unit not yet defined? 
                # Be careful. If we use dynamic prefixes, we might fail here if not yet generated.
                # But typically we generate quantity via registry, which should resolve it first.
                 if not registry.resolve_unit(u):
                     raise ValueError(f"Unknown unit: {u}")
    
    
    def _parse_unit_string(self, unit_str):
        """
        Parse unit string like 'm/s^2', 'kg * m', 'm s^-1'.
        Returns dict {unit: exponent}.
        """
        units = {}
        # Simple parser:
        # 1. Normalize: replace / with ' * ' and reverse exponent sign logic is hard in one pass?
        # Better: Recursive descent or simple tokenizing.
        #
        # Let's support:
        # Space or * means multiply
        # / means divide
        # ^ means power
        
        # Split by / to handle numerator / denominator
        parts = unit_str.split('/')
        numerator = parts[0]
        denominators = parts[1:] if len(parts) > 1 else []
        
        def parse_term(term, sign=1):
            # Split by * or space
            term = term.strip()
            if not term: return
            
            # Handle multiplication by * or space
            # Be careful not to split 'km'
            # We can replace * with space and split
            subterms = term.replace('*', ' ').split()
            for sub in subterms:
                if '^' in sub:
                     base, exp = sub.split('^')
                     exp = float(exp) if '.' in exp else int(exp)
                else:
                     base, exp = sub, 1
                
                units[base] = units.get(base, 0) + sign * exp

        parse_term(numerator, 1)
        for d in denominators:
             # If denominator has multiple terms like 's*kg', they are all in denominator?
             # Standard: m/s*kg  -> (m/s)*kg? Or m/(s*kg)?
             # Usually standard precedence: a/b*c -> (a/b)*c. 
             # But a/(b c) is common in parsing.
             # Let's assume / acts on the immediate next term, but usually 'm/s kg' means m * s^-1 * kg.
             # If user writes m/(s kg), we need parens.
             # My split('/') handles 'm / s / kg' -> m, s, kg (all negative).
             # It does NOT handle 'm / (s kg)'.
             # For this simple library, let's assume flat expression:
             # m/s^2 means m * s^-2.
             parse_term(d, -1)
             
        # Filter zeroes
        return {u: e for u, e in units.items() if e != 0}
    
    def is_single_unit(self):
        return len(self._units) == 1 and list(self._units.values())[0] == 1
    
    def __array__(self):
        """Support for converting Quantity to numpy array (strips units)"""
        if HAS_NUMPY:
            return np.array(self.value)
        return list(self.value)
    
    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        """Handle numpy ufuncs (add, multiply, etc.)"""
        if method != '__call__':
            return NotImplemented
            
        # Separate inputs into quantities and numbers
        args = []
        unit_args = []
        for inp in inputs:
            if isinstance(inp, Quantity):
                args.append(inp.value)
                unit_args.append(inp)
            else:
                args.append(inp)
                unit_args.append(None)
        
        # Determine resulting unit based on ufunc
        # This is complex for general ufuncs, handling basic arithmetic only
        if ufunc == np.add or ufunc == np.subtract:
            # Check units match
            u0 = unit_args[0]._units
            u1 = unit_args[1]._units
            if u0 != u1:
                 # Try conversion? For now strict
                 raise ValueError("Units must match for numpy addition/subtraction")
            
            result_val = ufunc(*args, **kwargs)
            return Quantity(result_val, u0, self.registry)
            
        elif ufunc == np.multiply:
            # Add units
            u0 = unit_args[0]._units if unit_args[0] else {}
            u1 = unit_args[1]._units if unit_args[1] else {}
            
            new_units = u0.copy()
            for u, exp in u1.items():
                new_units[u] = new_units.get(u, 0) + exp
                if new_units[u] == 0:
                    del new_units[u]
            
            result_val = ufunc(*args, **kwargs)
            return Quantity(result_val, new_units, self.registry)

        elif ufunc == np.true_divide:
            # Sub units
            u0 = unit_args[0]._units if unit_args[0] else {}
            u1 = unit_args[1]._units if unit_args[1] else {}
            
            new_units = u0.copy()
            for u, exp in u1.items():
                new_units[u] = new_units.get(u, 0) - exp
                if new_units[u] == 0:
                    del new_units[u]
            
            result_val = ufunc(*args, **kwargs)
            return Quantity(result_val, new_units, self.registry)

        return NotImplemented

    def to(self, target_unit_str):
        # 1. Simple Single Unit Check (Affine)
        if self.is_single_unit():
             source_unit = list(self._units.keys())[0]
             self.registry.resolve_unit(target_unit_str) # Ensure target exists/generated
             
             if target_unit_str in self.registry._units:
                 base_src = self.registry.get_base_unit(source_unit)
                 base_dst = self.registry.get_base_unit(target_unit_str)
                 
                 if base_src and base_dst and base_src == base_dst:
                     f_src = self.registry.get_factor(source_unit)
                     o_src = self.registry.get_offset(source_unit)
                     f_dst = self.registry.get_factor(target_unit_str)
                     o_dst = self.registry.get_offset(target_unit_str)
                     
                     # Support array operations
                     # val * f may need special handling if list
                     if isinstance(self.value, list):
                         if HAS_NUMPY:
                             val_arr = np.array(self.value)
                             base_val = val_arr * f_src + o_src
                             new_val = (base_val - o_dst) / f_dst
                             # Return as list if input was list? Or keep as numpy? 
                             # Let's keep consistent: if numpy installed, use it internally, 
                             # but return type?
                             # Regulate: if input list -> output list?
                             new_val = new_val.tolist()
                         else:
                             # Manual list comprehension
                             new_val = [((v * f_src + o_src) - o_dst) / f_dst for v in self.value]
                     elif HAS_NUMPY and isinstance(self.value, np.ndarray):
                         base_val = self.value * f_src + o_src
                         new_val = (base_val - o_dst) / f_dst
                     else:
                        base_val = self.value * f_src + o_src
                        new_val = (base_val - o_dst) / f_dst
                     
                     return Quantity(new_val, target_unit_str, self.registry)

        # 2. General Dimensional Analysis (ignoring offsets)
        
        # Calculate base value (factors only)
        # Handle Array/List
        if isinstance(self.value, list):
             base_value = np.array(self.value) if HAS_NUMPY else self.value[:] 
        elif HAS_NUMPY and isinstance(self.value, np.ndarray):
             base_value = self.value.copy()
        else:
             base_value = self.value
             
        # Source base units
        base_units = {}
        for u, exp in self._units.items():
            factor = self.registry.get_factor(u)
            base = self.registry.get_base_unit(u)
            
            # Apply factor
            if isinstance(base_value, list) and not HAS_NUMPY:
                base_value = [v * (factor ** exp) for v in base_value]
            else:
                base_value *= (factor ** exp)
            
            base_units[base] = base_units.get(base, 0) + exp

        # Parse target units
        # If string, parse it. If dict, use it.
        if isinstance(target_unit_str, str):
             # Try to resolve as atomic unit first?
             if target_unit_str in self.registry._units or self.registry.resolve_unit(target_unit_str):
                 target_units = {target_unit_str: 1}
             else:
                 # Complex string parsing
                 target_units = self._parse_unit_string(target_unit_str)
        elif isinstance(target_unit_str, dict):
             target_units = target_unit_str
        else:
             raise TypeError("Target unit must be string or dict")

        # Target base units
        target_base_units = {}
        target_factor_accum = 1.0
        
        for u, exp in target_units.items():
            # Ensure target units exist
            if u not in self.registry._units and not self.registry.resolve_unit(u):
                 raise ValueError(f"Unknown target unit: {u}")
            
            base = self.registry.get_base_unit(u)
            factor = self.registry.get_factor(u)
            
            target_factor_accum *= (factor ** exp)
            target_base_units[base] = target_base_units.get(base, 0) + exp
            
        # Check dimensionality match
        # Clean up zeroes
        base_units = {k: v for k, v in base_units.items() if v != 0}
        target_base_units = {k: v for k, v in target_base_units.items() if v != 0}
        
        if base_units != target_base_units:
             raise ValueError(f"Incompatible dimensions: {base_units} vs {target_base_units}")
        
        # Convert base_value to target
        # value_dst = value_base / target_factor
        if isinstance(base_value, list) and not HAS_NUMPY:
             new_value = [v / target_factor_accum for v in base_value]
        else:
             new_value = base_value / target_factor_accum
        
        if HAS_NUMPY and isinstance(new_value, np.ndarray) and isinstance(self.value, list):
             new_value = new_value.tolist()

        return Quantity(new_value, target_units, self.registry)

    def __str__(self):
        numerator = []
        denominator = []
        
        for u, exp in sorted(self._units.items()):
            if exp > 0:
                if exp == 1:
                    numerator.append(u)
                else:
                    numerator.append(f"{u}^{exp}")
            else:
                if abs(exp) == 1:
                    denominator.append(u)
                else:
                    denominator.append(f"{u}^{abs(exp)}")
        
        if not numerator:
            num_str = "1"
        else:
            num_str = " ".join(numerator)
            
        if not denominator:
            unit_part = num_str if numerator else ""
            return f"{self.value} {unit_part}".strip()
        
        den_str = " ".join(denominator)
        if len(denominator) > 1:
            den_str = f"({den_str})"
            
        return f"{self.value} {num_str}/{den_str}"

    def __repr__(self):
        return f"<Quantity({self.value}, {self._units})>"
    
    def _add_sub(self, other, op_sign):
        if not isinstance(other, Quantity):
             raise TypeError("Operands must be Quantity instances")

        if self._units == other._units:
             if isinstance(self.value, list) and isinstance(other.value, list) and not HAS_NUMPY:
                  # Manual list add
                  if len(self.value) != len(other.value): raise ValueError("List lengths differ")
                  if op_sign == 1:
                      val = [a + b for a, b in zip(self.value, other.value)]
                  else:
                      val = [a - b for a, b in zip(self.value, other.value)]
                  return Quantity(val, self._units, self.registry)
             
             if isinstance(self.value, list) and not isinstance(other.value, list) and not HAS_NUMPY:
                  # Broadcast scalar other to list self
                  if op_sign == 1:
                      val = [a + other.value for a in self.value]
                  else:
                      val = [a - other.value for a in self.value]
                  return Quantity(val, self._units, self.registry)

             # Numpy or scalar
             val = self.value + other.value if op_sign == 1 else self.value - other.value
             return Quantity(val, self._units, self.registry)
        
        # Conversion path...
        # Simplify: Convert other to base, then to self units (factors only)
        
        # 1. Other -> Base
        other_conv = other.value
        # For lists, this is painful heavily nested.
        # Assume usage of Numpy for ease? Or implement robust list walker.
        # For simplicity MVP: support Scalar mixed units, Vector matching units.
        # If Vector mixed units, require Numpy?
        
        if (isinstance(self.value, list) or (HAS_NUMPY and isinstance(self.value, np.ndarray))) and self._units != other._units:
             # Try to simply call .to() on 'other' to match self unit, then add values
             # But 'to' only works for simple target strings currently.
             # We need a proper 'to_units(dict)'?
             pass 

        # Fallback to scalar logic but applied to array?
        # Let's rely on .to() if possible.
        # Construct target unit string from self._units?
        target_str = " ".join([k for k, v in self._units.items() if v==1]) # Very hacky, only simple unit support
        try:
             # Only works if self is simple single unit for now
             if self.is_single_unit():
                 converted_other = other.to(list(self._units.keys())[0])
                 val = self.value + converted_other.value if op_sign == 1 else self.value - converted_other.value
                 return Quantity(val, self._units, self.registry)
        except:
             pass
        
        raise NotImplementedError("Mixed unit arithmetic for Arrays/Complex units not fully implemented yet in this step.")

    def __add__(self, other):
        return self._add_sub(other, 1)

    def __sub__(self, other):
        return self._add_sub(other, -1)

    def __mul__(self, other):
        if isinstance(other, (int, float, list)) or (HAS_NUMPY and isinstance(other, np.ndarray)):
             if isinstance(self.value, list) and isinstance(other, list):
                 # Element wise mul? Python lists don't do that naturally.
                 # User probably expects scalar mul or numpy-like behavior
                 # [1,2] * 2 = [2,4].
                 # [1,2] * [1,2] -> [1,4]?
                 if not HAS_NUMPY:
                      raise TypeError("Install Numpy for element-wise array operations")
                 val = np.array(self.value) * np.array(other)
                 if isinstance(self.value, list): val = val.tolist()
                 return Quantity(val, self._units, self.registry)
             
             # Scalar mul
             if HAS_NUMPY and isinstance(other, np.ndarray):
                 return Quantity(self.value * other, self._units, self.registry)
                 
             if isinstance(self.value, list) and isinstance(other, (int, float)):
                 # List * scalar -> new list
                 return Quantity([v * other for v in self.value], self._units, self.registry)
                 
             return Quantity(self.value * other, self._units, self.registry)
        
        if isinstance(other, Quantity):
            # Element wise value mul
            if (isinstance(self.value, list) or (HAS_NUMPY and isinstance(self.value, np.ndarray))):
                 if not HAS_NUMPY and isinstance(other.value, list):
                     raise TypeError("Install Numpy for element-wise array operations")
            
            new_val = self.value * other.value # Works if both numpy, or scalar
            new_units = self._units.copy()
            for u, exp in other._units.items():
                new_units[u] = new_units.get(u, 0) + exp
                if new_units[u] == 0:
                    del new_units[u]
            return Quantity(new_val, new_units, self.registry)
            
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)
        
    def __truediv__(self, other):
        if isinstance(other, (int, float, list)) or (HAS_NUMPY and isinstance(other, np.ndarray)):
             if isinstance(self.value, list) and not HAS_NUMPY:
                  if isinstance(other, list): raise TypeError("Install Numpy")
                  return Quantity([v / other for v in self.value], self._units, self.registry)
                  
             return Quantity(self.value / other, self._units, self.registry)
        
        if isinstance(other, Quantity):
            new_val = self.value / other.value
            new_units = self._units.copy()
            for u, exp in other._units.items():
                new_units[u] = new_units.get(u, 0) - exp
                if new_units[u] == 0:
                    del new_units[u]
            return Quantity(new_val, new_units, self.registry)

        return NotImplemented

    def __rtruediv__(self, other):
        if isinstance(other, (int, float, list)) or (HAS_NUMPY and isinstance(other, np.ndarray)):
             if isinstance(self.value, list) and not HAS_NUMPY:
                  return Quantity([other / v for v in self.value], {u: -e for u,e in self._units.items()}, self.registry)
                  
             new_val = other / self.value
             new_units = {}
             for u, exp in self._units.items():
                 new_units[u] = -exp
             return Quantity(new_val, new_units, self.registry)
        return NotImplemented
    
    def __pow__(self, power):
        if not isinstance(power, (int, float)):
             raise TypeError("Power must be a number")
        
        # Support array power?
        if isinstance(self.value, list) and not HAS_NUMPY:
             new_val = [v ** power for v in self.value]
        else:
             new_val = self.value ** power
             
        new_units = {}
        for u, exp in self._units.items():
            new_units[u] = exp * power
        return Quantity(new_val, new_units, self.registry)
