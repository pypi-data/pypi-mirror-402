import numpy as np

class ElementwiseProblem:
    """
    Base class for defining optimization problems where evaluation depends
    on individual element vectors (element-wise).
    
    This matches the PyMOO `ElementwiseProblem` signature.
    """
    def __init__(self, n_var: int, n_obj: int = 1, n_constr: int = 0, xl=None, xu=None):
        self.n_var = n_var
        self.n_obj = n_obj
        self.n_constr = n_constr
        
        # Bounds handling
        self.xl = np.array(xl) if xl is not None else -np.inf * np.ones(n_var)
        self.xu = np.array(xu) if xu is not None else np.inf * np.ones(n_var)
        
        # Enforce array shape
        if self.xl.ndim == 0: self.xl = np.full(n_var, self.xl)
        if self.xu.ndim == 0: self.xu = np.full(n_var, self.xu)

    def _evaluate(self, x, out, *args, **kwargs):
        """
        User must override this method.
        
        Args:
            x (np.ndarray): 1D array of design variables.
            out (dict): dictionary to populate with "F" (objectives) and "G" (constraints).
        """
        raise NotImplementedError("You must implement _evaluate(self, x, out).")

    def evaluate(self, x, *args, **kwargs):
        """
        Public evaluation method calling the internal _evaluate.
        """
        out = {}
        self._evaluate(x, out, *args, **kwargs)
        return out
