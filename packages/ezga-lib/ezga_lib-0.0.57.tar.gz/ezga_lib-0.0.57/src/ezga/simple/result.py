class Result:
    """
    The result object describing the optimization outcome.
    """
    def __init__(self, X=None, F=None, CV=None, G=None, 
                 pop=None, history=None, 
                 algorithm=None, 
                 exec_time=None):
        
        self.X = X  # Best design variable(s) found
        self.F = F  # Objective value(s) of best solution
        self.CV = CV # Constraint violation
        self.G = G  # Constraints of best solution
        
        self.pop = pop   # Final population
        self.history = history # History if track_history was True
        self.algorithm = algorithm
        self.exec_time = exec_time
