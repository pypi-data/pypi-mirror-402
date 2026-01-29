import numpy as np
import copy
import random

class ProblemCalculatorWrapper:
    """
    Wraps an ElementwiseProblem to function as an EZGA Calculator.
    """
    def __init__(self, problem):
        self.problem = problem

    def __call__(self, positions, symbols, cell, fixed, constraints, sampling_temperature, output_filename, parent_hash, **kwargs):
        """
        Executes the problem evaluation.
        
        Maps atomPositions[:, 0] -> x
        Maps out["F"] -> Energy
        """
        # Extract decision variables from x-coordinates
        x = positions[:, 0]
        
        out = {}
        try:
            # Check for Symbolic Regression Registry Lookup
            if hasattr(self.problem, 'get_tree'):
                # Assuming single variable index stored in x[0]
                tree_id = x[0]
                tree = self.problem.get_tree(tree_id)
                if tree is not None:
                    # Evaluate using problem's helper
                    loss = self.problem.evaluate_tree(tree)
                    objs = [loss]
                    energy = loss
                    F = np.array([loss])
                    G = None
                else:
                    # Missing tree? Maybe standard eval or error
                    # Fallback to standard if no tree found (should not happen if registered)
                    self.problem._evaluate(x, out)
                    F = out.get("F")
                    G = out.get("G")
                    energy = float(F) if np.ndim(F)==0 else float(F[0])
                    objs = [energy]
            else:
                self.problem._evaluate(x, out)
                
                # Handling single objective for now. Multi-objective expansion:
                # If F is a list/array, we might need to store it in metadata 
                # and use a scalar (e.g., sum or first obj) as 'Energy' for the engine's scalar logic,
                # while the Selector uses the full vector from metadata.
                F = out.get("F")
                G = out.get("G")
                
                if np.ndim(F) == 0:
                    energy = float(F)
                    objs = [energy]
                else:
                    # Multi-objective
                    # Engine 'Energy' mostly used for simple logging or scalar stats.
                    # We use the first objective as the 'Energy' proxy or sum.
                    # But crucial data goes to metadata["objectives"]
                    objs = list(F)
                    energy = float(objs[0]) 

        except Exception as e:
            # Return NaN energy on failure?
            print(f"Evaluation failed: {e}")
            energy = np.nan
            objs = []
            G = None
        
        #   Metadata to pass back
        metadata = {
            "objectives": objs,
            "F": F,
            "G": G,
            "hash": str(hash(tuple(x))) # Simple hash for graph tracking
        }
        
        # We return the SAME positions (no relaxation)
        # FORCE cell to None to prevent accidental periodicity/wrapping
        return positions, symbols, None, energy, metadata

class PolynomialMutationVector:
    """
    Adapts Polynomial Mutation to EZGA's structure mutation interface.
    """
    def __init__(self, eta, prob, xl, xu):
        self.eta = eta
        self.prob = prob
        self.xl = xl
        self.xu = xu
    
    def __call__(self, structure):
        # 1. Deep copy to avoid mutating parent in place
        new_struct = copy.deepcopy(structure)
        
        # 2. Extract x
        apm = new_struct.AtomPositionManager
        # FORCE remove lattice to prevent wrapping of coordinates
        try:
            apm.set_latticeVectors(None)
        except:
            pass

        pos = np.array(apm.atomPositions, dtype=float)
        x = pos[:, 0]
        
        n_var = len(x)
        
        # 3. Apply PM (element-wise)
        # Vectorized implementation of PM
        
        # Mask for variables to mutate
        do_mutation = np.random.random(n_var) < self.prob
        
        if not np.any(do_mutation):
            return new_struct
            
        idx = np.where(do_mutation)[0]
        
        # Helpers
        y = x[idx]
        yl = self.xl[idx]
        yu = self.xu[idx]
        
        # Delta calculation
        delta_1 = (y - yl) / (yu - yl)
        delta_2 = (yu - y) / (yu - yl)
        
        val = np.random.random(len(idx))
        mut_pow = 1.0 / (self.eta + 1.0)
        
        delta_q = np.zeros_like(y)
        
        # Case 1: val <= 0.5
        mask1 = val <= 0.5
        xy1 = 1.0 - delta_1[mask1]
        val1 = 2.0 * val[mask1] + (1.0 - 2.0 * val[mask1]) * (xy1 ** (self.eta + 1.0))
        delta_q[mask1] = (val1 ** mut_pow) - 1.0
        
        # Case 2: val > 0.5
        mask2 = ~mask1
        xy2 = 1.0 - delta_2[mask2]
        val2 = 2.0 * (1.0 - val[mask2]) + 2.0 * (val[mask2] - 0.5) * (xy2 ** (self.eta + 1.0))
        delta_q[mask2] = 1.0 - (val2 ** mut_pow)
        
        # Update
        y_new = y + delta_q * (yu - yl)
        
        # Clip
        y_new = np.clip(y_new, yl, yu)
        
        # 4. Write back
        x[idx] = y_new
        pos[:, 0] = x
        apm.set_atomPositions(pos)
        
        return new_struct

class SimulatedBinaryCrossoverVector:
    """
    Adapts Simulated Binary Crossover (SBX) to EZGA's structure crossover interface.
    """
    def __init__(self, eta, prob, xl, xu):
        self.eta = eta
        self.prob = prob
        self.xl = xl
        self.xu = xu
    
    def __call__(self, struct_a, struct_b):
        # 1. Deep copy parents
        child_a = copy.deepcopy(struct_a)
        child_b = copy.deepcopy(struct_b)
        
        # 2. Extract x from parents (using temp copy to ensure valid lattice handling)
        # Force remove lattice first to avoid confusion
        for s in [child_a, child_b]:
            try:
                s.AtomPositionManager.set_latticeVectors(None)
            except:
                pass

        pos_a = np.array(child_a.AtomPositionManager.atomPositions, dtype=float)
        x_a = pos_a[:, 0]
        
        pos_b = np.array(child_b.AtomPositionManager.atomPositions, dtype=float)
        x_b = pos_b[:, 0]
        
        n_var = len(x_a)
        
        # 3. Apply SBX
        if np.random.random() <= self.prob:
            for i in range(n_var):
                if np.random.random() <= 0.5:
                    if np.abs(x_a[i] - x_b[i]) > 1e-14:
                        y1 = min(x_a[i], x_b[i])
                        y2 = max(x_a[i], x_b[i])
                        
                        yl = self.xl[i]
                        yu = self.xu[i]
                        
                        rand = np.random.random()
                        beta = 1.0 + (2.0 * (y1 - yl) / (y2 - y1))
                        alpha = 2.0 - beta ** -(self.eta + 1.0)
                        
                        if rand <= (1.0 / alpha):
                            betaq = (rand * alpha) ** (1.0 / (self.eta + 1.0))
                        else:
                            betaq = (1.0 / (2.0 - rand * alpha)) ** (1.0 / (self.eta + 1.0))
                            
                        c1 = 0.5 * ((y1 + y2) - betaq * (y2 - y1))
                        
                        beta = 1.0 + (2.0 * (yu - y2) / (y2 - y1))
                        alpha = 2.0 - beta ** -(self.eta + 1.0)
                        
                        if rand <= (1.0 / alpha):
                            betaq = (rand * alpha) ** (1.0 / (self.eta + 1.0))
                        else:
                            betaq = (1.0 / (2.0 - rand * alpha)) ** (1.0 / (self.eta + 1.0))
                            
                        c2 = 0.5 * ((y1 + y2) + betaq * (y2 - y1))
                        
                        c1 = min(max(c1, yl), yu)
                        c2 = min(max(c2, yl), yu)
                        
                        if np.random.random() <= 0.5:
                            x_a[i] = c2
                            x_b[i] = c1
                        else:
                            x_a[i] = c1
                            x_b[i] = c2

        # 4. Write back
        pos_a[:, 0] = x_a
        child_a.AtomPositionManager.set_atomPositions(pos_a)
        
        pos_b[:, 0] = x_b
        child_b.AtomPositionManager.set_atomPositions(pos_b)
        
        return child_a, child_b

class ShiftMutationVector:
    """
    Directional shift mutation to aid Guided Variation (Generative Models).
    Shifts a random subset of variables by a fixed fraction of the domain.
    """
    def __init__(self, shift_fraction, prob, xl, xu):
        self.shift_fraction = shift_fraction
        self.prob = prob
        self.xl = xl
        self.xu = xu
    
    def __call__(self, structure):
        # 1. Deep copy
        new_struct = copy.deepcopy(structure)
        
        # 2. Extract x
        apm = new_struct.AtomPositionManager
        try:
            apm.set_latticeVectors(None)
        except:
            pass

        pos = np.array(apm.atomPositions, dtype=float)
        x = pos[:, 0]
        n_var = len(x)
        
        # 3. Apply Shift
        do_mutation = np.random.random(n_var) < self.prob
        
        if not np.any(do_mutation):
            return new_struct
            
        idx = np.where(do_mutation)[0]
        
        # Apply shift
        y = x[idx]
        yl = self.xl[idx]
        yu = self.xu[idx]
        
        range_val = yu - yl
        shift = self.shift_fraction * range_val
        
        y_new = y + shift
        
        # Clip
        y_new = np.clip(y_new, yl, yu)
        
        # 4. Write back
        x[idx] = y_new
        pos[:, 0] = x
        apm.set_atomPositions(pos)
        
        return new_struct

    @property
    def __name__(self):
        sign = "+" if self.shift_fraction > 0 else ""
        return f"Shift{sign}{self.shift_fraction:.2f}"

class ShiftMutationVariable:
    """
    Directional shift mutation for a SPECIFIC variable index.
    Essential for Guided Variation to span the feature space orthogonally.
    """
    def __init__(self, index, shift_fraction, xl, xu):
        self.index = index
        self.shift_fraction = shift_fraction
        self.xl = xl
        self.xu = xu
    
    def __call__(self, structure):
        # 1. Deep copy
        new_struct = copy.deepcopy(structure)
        
        # 2. Extract x
        apm = new_struct.AtomPositionManager
        try:
            apm.set_latticeVectors(None)
        except:
            pass

        pos = np.array(apm.atomPositions, dtype=float)
        x = pos[:, 0]
        
        if self.index >= len(x):
            return new_struct

        # 3. Apply Shift to specific variable
        y = x[self.index]
        yl = self.xl[self.index]
        yu = self.xu[self.index]
        
        range_val = yu - yl
        shift = self.shift_fraction * range_val
        
        y_new = y + shift
        
        # Clip
        y_new = np.clip(y_new, yl, yu)
        
        # 4. Write back
        x[self.index] = y_new
        pos[:, 0] = x
        apm.set_atomPositions(pos)
        
        return new_struct

    @property
    def __name__(self):
        sign = "+" if self.shift_fraction > 0 else ""
        return f"ShiftVar{self.index}{sign}{self.shift_fraction:.2f}"
