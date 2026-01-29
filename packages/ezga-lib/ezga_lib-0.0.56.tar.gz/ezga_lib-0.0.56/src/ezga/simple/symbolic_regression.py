
import numpy as np
from ezga.simple.problem import ElementwiseProblem
from ezga.simple.algorithm import GA
from ezga.simple.minimize import minimize
from ezga.simple.grammar import (
    Variable, Constant, OptimizableConstant,
    Add, Sub, Mul, Div, 
    Sin, Cos, Exp, Log, Sqrt, Abs, Square, Neg,
    AND, OR, Threshold, Interval, Ratio, Gaussian
)
from ezga.simple.ops import SymbolicMutator, generate_random_tree
from ezga.variation.variation import Variation_Operator

import pathlib
from scipy.optimize import minimize as scipy_minimize
import sys

class SymbolicMathMutation:
    """
    Callable Mutation Operator for Symbolic Regression.
    Expected signature: func(container) -> new_container
    """
    def __init__(self, n_features, problem, mutation_rate=0.1, 
                  binary_ops=None, unary_ops=None, literal_types=None):
        self.problem = problem
        self.mutator = SymbolicMutator(n_features, mutation_rate, 
                                      binary_ops, unary_ops, literal_types)
        self.n_features = n_features
        self.literal_types = literal_types
        self.binary_ops = binary_ops
        self.unary_ops = unary_ops

    def __call__(self, container):
        rng = np.random.default_rng()
        import copy
        c = copy.deepcopy(container)
        
        # 1. Get Tree from Registry using Position ID
        apm = c.AtomPositionManager
        pos = apm.atomPositions
        if len(pos) > 0:
            tree_id = float(pos[0][0])
            tree_obj = self.problem.get_tree(tree_id)
        else:
            tree_obj = None

        if tree_obj is None:
            # Generate new random if missing
            tree_obj = generate_random_tree(self.n_features, rng, 
                                            binary_ops=self.binary_ops,
                                            unary_ops=self.unary_ops,
                                            literal_types=self.literal_types)
        
        # 2. Mutate
        new_tree = self.mutator.mutate(tree_obj, rng)
        
        # 3. Register New Tree with New ID
        new_id = self.problem.get_next_id()
        self.problem.register_tree(new_id, new_tree)
        
        # 4. Update Container Position ID
        # HACK: Using dummy atoms. Reset them.
        # Ensure we have 1 dummy atom at least
        new_pos = np.zeros((1, 3))
        new_pos[0, 0] = new_id
        apm.set_atomPositions(new_pos)
        
        # Invalidate Energy
        apm.E = None
        if hasattr(apm, "metadata") and "objectives" in apm.metadata:
            del apm.metadata["objectives"]
            
        return c

class SymbolicMathCrossover:
    """
    Callable Crossover Operator.
    Expected signature: func(c1, c2) -> (new_c1, new_c2)
    """
    def __call__(self, p1, p2):
        import copy
        return copy.deepcopy(p1), copy.deepcopy(p2)


class SymbolicRegressionProblem(ElementwiseProblem):
    def __init__(self, X, y, n_features, binary_ops, unary_ops, literal_types, complexity_penalty=0.0):
        super().__init__(n_var=1, n_obj=1, xl=0, xu=1e6) 
        self.X_data = X
        self.y_data = y
        self.n_features = n_features
        self.binary_ops = binary_ops
        self.unary_ops = unary_ops
        self.literal_types = literal_types
        self.complexity_penalty = complexity_penalty
        
        self.tree_registry = {}
        self.next_id = 10000 # Start high to avoid 0 clashes if 0 valid

    def register_tree(self, id_val, tree):
        self.tree_registry[int(id_val)] = tree
        
    def get_tree(self, id_val):
        return self.tree_registry.get(int(id_val))

    def get_next_id(self):
        self.next_id += 1
        return self.next_id

    def evaluate_tree(self, tree, tree_id=None):
        try:
            # -----------------------------------------------------------
            # Pre-Optimization Simplification
            # -----------------------------------------------------------
            # Apply algebraic simplification (0+x->x, etc) to reduce bloat
            # before we spend time optimizing constants.
            tree = tree.simplify()
            
            # [Fix] Persist simplified tree to registry if we have an ID
            if tree_id is not None:
                self.tree_registry[int(tree_id)] = tree

            # -----------------------------------------------------------
            # Memetic Algorithm Step: Constant Optimization
            # -----------------------------------------------------------
            # 1. Gather all OptimizableConstant nodes
            opt_nodes = []
            
            def collect_opt_nodes(node):
                if isinstance(node, OptimizableConstant):
                    opt_nodes.append(node)
                elif hasattr(node, 'children'):
                    for child in node.children:
                        collect_opt_nodes(child)
                elif hasattr(node, 'child'):
                    collect_opt_nodes(node.child)
            
            collect_opt_nodes(tree)
            
            # 2. If we have ephemeral constants, optimize them!
            if opt_nodes:
                x0 = np.array([n.value for n in opt_nodes])
                
                def objective(params):
                    # Update node values
                    for i, node in enumerate(opt_nodes):
                        node.value = params[i]
                    # Evaluate
                    yp = tree.evaluate(self.X_data)
                    return np.mean((self.y_data - yp)**2)
                
                # Perform local optimization (e.g. BFGS)
                # Cap iterations for speed
                res = scipy_minimize(objective, x0, method='BFGS', options={'maxiter': 50})
                
                # Update with best params
                for i, node in enumerate(opt_nodes):
                    node.value = res.x[i]

                # 3. Freeze them! Replace OptimizableConstant with standard Constant
                # Note: We need parent pointers or a replace traversal.
                # Since our tree structure is simple, a DFS replace is safer.
                
                def freeze_constants(node):
                    # Handling binary ops
                    if isinstance(node, (Add, Sub, Mul, Div)): # BinaryOperator subclasses
                        if isinstance(node.left, OptimizableConstant):
                            node.left = Constant(node.left.value)
                        else:
                            freeze_constants(node.left)
                            
                        if isinstance(node.right, OptimizableConstant):
                            node.right = Constant(node.right.value)
                        else:
                            freeze_constants(node.right)
                            
                    # Handling unary ops
                    elif isinstance(node, (Sin, Cos, Exp, Log, Sqrt, Abs, Square, Neg)): # UnaryOperator subclasses
                         if isinstance(node.child, OptimizableConstant):
                             node.child = Constant(node.child.value)
                         else:
                             freeze_constants(node.child)
                             
                # Handle root case
                if isinstance(tree, OptimizableConstant):
                     # This effectively replaces the root logic outside, but we can't change 'tree' ref passed by value
                     # This edge case (tree = single constant) is rare/useless, so we skip freezing logic for pure root
                     # or handle it if needed. For now, values are updated, so it works.
                     pass
                else:
                    freeze_constants(tree)
                    
            # -----------------------------------------------------------
            # Post-Optimization Simplification (Cleanup)
            # -----------------------------------------------------------
            # Now that Opt constants are real Constants (e.g. 0.000), 
            # we can simplify again to remove +0.0, *1.0, etc.
            tree = tree.simplify()
            if tree_id is not None:
                self.tree_registry[int(tree_id)] = tree

            # -----------------------------------------------------------
            # Standard Evaluation
            # -----------------------------------------------------------
            y_pred = tree.evaluate(self.X_data)
            mse = np.mean((self.y_data - y_pred)**2)
            loss = mse + self.complexity_penalty * tree.size
            if np.isnan(loss) or np.isinf(loss) or loss > 1e9:
                return 1e9
            return loss
        except Exception:
            return 1e9

    def _evaluate(self, x, out, *args, **kwargs):
        try:
            tid = int(x[0])
            tree = self.get_tree(tid)
            if tree is None:
                out["F"] = 1e9
                return
            
            loss = self.evaluate_tree(tree, tree_id=tid)
            out["F"] = loss
        except Exception:
            out["F"] = 1e9


class SymbolicRegressor:
    def __init__(self, 
                 pop_size=100, 
                 pop_size_max=None,
                 generations=50, 
                 n_features=1,
                 binary_ops=None, 
                 unary_ops=None,
                 complexity_penalty=0.001,
                 crossover_probability=0.3,
                 random_state=None):
        
        self.pop_size = pop_size
        self.pop_size_max = pop_size_max
        self.generations = generations
        self.n_features = n_features
        self.complexity_penalty = complexity_penalty
        self.crossover_probability = crossover_probability
        self.random_state = random_state
        
        self.binary_ops = binary_ops if binary_ops else [Add, Sub, Mul, Div, ]#AND, OR 
        self.unary_ops = unary_ops if unary_ops else [Sin, Cos, Exp, Log, Abs, ] # Sqrt, Square
        self.literal_types = [Variable, Constant, ] # Threshold, Interval
        
        self.best_tree = None
        self.best_fitness = float('inf')
        
    def fit(self, X, y):
        # 1. Setup Problem
        problem = SymbolicRegressionProblem(
            X, y, 
            self.n_features, 
            self.binary_ops, 
            self.unary_ops, 
            self.literal_types,
            self.complexity_penalty
        )
        
        # 2. Pre-Register Initial Population
        rng = np.random.default_rng(self.random_state)
        init_ids = np.zeros((self.pop_size, 1))
        
        # Helper to create basic seeds
        seeds = []
        
        # Seed 1: Simple Linear (c0 + c1*x0 + c2*x1...)
        # Construct: Add(Add(..., Mul(Opt, x)), Mul(Opt, x))
        def make_linear_term(feat_idx):
            return Mul(OptimizableConstant(rng.standard_normal()), Variable(feat_idx))
            
        # Linear Sum
        if self.n_features > 0:
            current = OptimizableConstant(rng.standard_normal()) # Bias
            for f in range(self.n_features):
                term = make_linear_term(f)
                current = Add(current, term)
            seeds.append(current)
            
        # Seed 2: Quadratic (x0^2) for each feature
        for f in range(self.n_features):
            # C * x^2 + C
            term = Mul(OptimizableConstant(rng.standard_normal()), 
                       Mul(Variable(f), Variable(f)))
            term = Add(term, OptimizableConstant(rng.standard_normal()))
            seeds.append(term)
        
        # Seed 3: Interaction (x0 * x1) if > 1 feature
        if self.n_features > 1:
            term = Mul(Variable(0), Variable(1))
            term = Mul(term, OptimizableConstant(rng.standard_normal()))
            term = Add(term, OptimizableConstant(rng.standard_normal()))
            seeds.append(term)
            
        # Seed 4: Trigonometric (Linear + C * sin(x))
        # Check if Sin/Cos enabled
        has_sin = any(op.__name__ == 'Sin' for op in self.unary_ops)
        has_cos = any(op.__name__ == 'Cos' for op in self.unary_ops)
        
        for f in range(self.n_features):
            # Base Linear
            lin = make_linear_term(f)
            lin = Add(lin, OptimizableConstant(rng.standard_normal()))
            
            if has_sin:
                # lin + C * sin(x)
                term = Mul(OptimizableConstant(rng.standard_normal()), 
                           Sin(Variable(f)))
                term = Add(lin, term)
                seeds.append(term)
                
            if has_cos:
                # lin + C * cos(x)
                term = Mul(OptimizableConstant(rng.standard_normal()), 
                           Cos(Variable(f)))
                term = Add(lin, term)
                seeds.append(term)
            
        # Fill Population
        for i in range(self.pop_size):
            tid = i + 1
            init_ids[i, 0] = tid
            
            if i < len(seeds):
                # Use seed
                tree = seeds[i]
                # Clone to ensure unique IDs if we reused seeds (we didn't but good practice)
                import copy
                tree = copy.deepcopy(tree)
            else:
                # Random
                tree = generate_random_tree(self.n_features, rng, 
                                            binary_ops=self.binary_ops,
                                            unary_ops=self.unary_ops,
                                            literal_types=self.literal_types)
            
            problem.register_tree(tid, tree)
        
        # 3. Setup Algorithm
        algorithm = GA(
            pop_size=self.pop_size, 
            pop_size_max=self.pop_size_max,
            sampling=init_ids, # Pass explicit IDs as sampling
            enable_bo=False,
            eliminate_duplicates=False, # Explicitly asked by user
            crossover_probability=self.crossover_probability
        )
        
        mutation_op = SymbolicMathMutation(
            self.n_features, 
            problem=problem,
            mutation_rate=4.0, 
            binary_ops=self.binary_ops,
            unary_ops=self.unary_ops,
            literal_types=self.literal_types
        )
        
        crossover_op = SymbolicMathCrossover()
        
        algorithm.mutation = mutation_op
        algorithm.crossover = crossover_op
        
        # 4. Minimize
        res = minimize(
            problem,
            algorithm,
            termination=('n_gen', self.generations),
            seed=self.random_state,
            verbose=False 
        )
        
        # Extract Best
        if res.pop:
            best_ind = None
            min_f = float('inf')
            
            for ind in res.pop:
                # ind is a structure container
                # Extract F
                f_val = np.inf
                try:
                    # Check metadata F or objectives
                    meta = getattr(ind.AtomPositionManager, "metadata", {})
                    if "F" in meta:
                        f_val = meta["F"]
                    elif "objectives" in meta:
                        f_val = meta["objectives"][0]
                    else:
                        f_val = ind.AtomPositionManager.E
                        
                    # Handle single element array
                    if np.ndim(f_val) > 0:
                        f_val = f_val[0]
                    f_val = float(f_val)
                except:
                    pass
                
                if f_val is not None and f_val < min_f:
                    min_f = f_val
                    best_ind = ind
            
            if best_ind:
                # Get Tree ID
                pos = best_ind.AtomPositionManager.atomPositions
                if len(pos) > 0:
                    tid = pos[0][0]
                    self.best_tree = problem.get_tree(tid)
                    self.best_fitness = min_f
                
        return self

    def predict(self, X):
        if self.best_tree:
            return self.best_tree.evaluate(X)
        return np.zeros(len(X))
        
    def score(self, X, y):
        y_pred = self.predict(X)
        return 1 - np.sum((y - y_pred)**2) / np.sum((y - np.mean(y))**2)

    @property
    def expression(self):
        return str(self.best_tree) if self.best_tree else "None"
