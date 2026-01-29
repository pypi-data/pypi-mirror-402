class GA:
    """
    Configuration holder for the Genetic Algorithm.
    """
    def __init__(self, 
                 pop_size: int = 100,
                 pop_size_max: int = None,
                 sampling = None,
                 selection = None,
                 crossover = None,
                 mutation = None,
                 eliminate_duplicates: bool = False,
                 n_offsprings: int = None,
                 enable_bo: bool = False,
                 bo_size: int = 30,
                 crossover_probability: float = 0.2):
        
        self.pop_size = pop_size
        self.pop_size_max = pop_size_max
        self.sampling = sampling
        self.selection = selection
        self.crossover = crossover
        self.mutation = mutation
        self.eliminate_duplicates = eliminate_duplicates
        self.n_offsprings = n_offsprings
        self.enable_bo = enable_bo
        self.bo_size = bo_size
        self.crossover_probability = crossover_probability
