
import numpy as np
from ezga.variation.variation import Variation_Operator
from .ops import SymbolicMutator, generate_random_tree

class SymbolicVariation(Variation_Operator):
    """
    Custom Variation Operator for Symbolic Regression.
    Adapts the standard EZGA variation loop to work on Trees stored in metadata
    instead of atomPositions.
    """
    def __init__(self, n_features, mutation_rate=0.1):
        # We don't use standard mutation_funcs like PolynomialMutation
        # so we pass empty lists to super, or minimal defaults.
        super().__init__(mutation_funcs=[], crossover_funcs=[])
        
        self.mutator = SymbolicMutator(n_features, mutation_rate)
        # We might need access to n_features for random generation if needed
        self.n_features = n_features

    def mutate(self, containers, **kwargs):
        """
        Overrides the standard mutate method.
        Iterates over containers, retrieves the Tree from metadata,
        applies SymbolicMutator, and updates the container.
        """
        # Get RNG from kwargs or use default
        rng = kwargs.get('rng', np.random.default_rng())
        
        offspring = []
        
        import copy
        for c_original in containers:
            c = copy.deepcopy(c_original)
            
            # DEBUG: Check atom count
            try:
                apm = c.AtomPositionManager
                # print(f"DEBUG: Mutating Container {id(c)} - AtomCount: {apm.atomCount}")
                if apm.atomCount == 0:
                    print(f"WARNING: Container {id(c)} has 0 atoms! Positions: {apm.atomPositions}")
            except Exception as e:
                print(f"DEBUG: Error checking APM: {e}")

            # 1. Retrieve Tree
            # We assume the Individual (Container) has 'tree' in metadata
            
            meta = getattr(c.AtomPositionManager, "metadata", {})
            tree_obj = meta.get("symbolic_tree", None)
            
            # Handle String -> Object
            if isinstance(tree_obj, str):
                try:
                    # Provide context for eval
                    from ezga.simple.grammar import AND, OR, NOT, Threshold, Interval, Ratio, Gaussian
                    ctx = {
                        "AND": AND, "OR": OR, "NOT": NOT,
                        "Threshold": Threshold, "Interval": Interval, 
                        "Ratio": Ratio, "Gaussian": Gaussian
                    }
                    tree_obj = eval(tree_obj, ctx)
                except Exception as e:
                    print(f"ERROR parsing tree from string: {e}")
                    tree_obj = None

            if tree_obj is None:
                tree_obj = generate_random_tree(self.n_features, rng)
            
            # 2. Mutate
            new_tree = self.mutator.mutate(tree_obj, rng)
            
            # 3. Store back as String for JSON safety
            meta["symbolic_tree"] = repr(new_tree)
            
            # Also update atomPositions purely for visualization/hashing (optional)?
            # Or just leave them as dummy.
            # We can maybe store a hash or simple representation in positions.
            
            offspring.append(c)
            
        return offspring

    def crossover(self, parents, **kwargs):
        # For now, simplistic cloning (no crossover) or 
        # we can implement Subtree Crossover later.
        # Just return parents as-is (they will be mutated next steps).
        
        # If the Engine calls crossover, it expects offspring.
        # If we pass empty crossover_funcs to super, 
        # the default implementation might do nothing or fail.
        
        # We can implement a pass-through.
        return parents

