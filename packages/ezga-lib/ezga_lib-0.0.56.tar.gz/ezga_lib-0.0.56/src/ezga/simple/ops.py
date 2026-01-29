
import numpy as np
from .grammar import (
    Node, BinaryOperator, UnaryOperator, 
    AND, OR, NOT, 
    Literal, Threshold, Interval, Ratio, Gaussian,
    Add, Sub, Mul, Div,
    Sin, Cos, Exp, Log, Sqrt, Abs, Square, Neg,
    Variable, Constant, OptimizableConstant
)

def generate_random_literal(n_features, rng, literal_types=None):
    """Generates a random literal node."""
    # Default to boolean literals if not specified
    if literal_types is None:
        type_idx = rng.choice(4)
        feat = rng.integers(0, n_features)
        
        if type_idx == 0: # Threshold
            val = rng.uniform(0.0, 1.0)
            op = rng.choice([0, 1])
            return Threshold(feat, val, op)
            
        elif type_idx == 1: # Interval
            v1 = rng.uniform(0.0, 1.0)
            v2 = rng.uniform(0.0, 1.0)
            return Interval(feat, v1, v2)
            
        elif type_idx == 2: # Ratio
            feat2 = rng.integers(0, n_features)
            thresh = rng.uniform(0.5, 2.0)
            return Ratio(feat, feat2, thresh)
            
        elif type_idx == 3: # Gaussian
            mu = rng.uniform(0.0, 1.0)
            sigma = rng.uniform(0.05, 0.3)
            return Gaussian(feat, mu, sigma)
            
    else:
        # Generic literal generation
        Choice = rng.choice(literal_types)
        
        if Choice == Variable:
            return Variable(rng.integers(0, n_features))
        elif Choice == Constant:
            # Mixture: 50% small (randn), 50% large (uniform -1000 to 1000)
            # AND: 50% chance to be OptimizableConstant (Ephemeral Constant)
            val = rng.standard_normal() if rng.random() < 0.5 else rng.uniform(-1000, 1000)
            
            if rng.random() < 0.5:
                return OptimizableConstant(val)
            else:
                return Constant(val)
        elif Choice in [Threshold, Interval, Ratio, Gaussian]:
             # Fallback to boolean logic above if mixed, but for now simple recursion
             return generate_random_literal(n_features, rng, literal_types=None)
        else:
            # Fallback or error
            return Constant(0.0)

def generate_random_tree(n_features, rng, max_depth=4, current_depth=0, 
                        binary_ops=None, unary_ops=None, literal_types=None):
    """Recursively generates a random tree."""
    
    # Defaults for backward compatibility (Boolean Logic)
    if binary_ops is None: binary_ops = [AND, OR]
    if unary_ops is None: unary_ops = [NOT]
    
    # Terminal condition
    if current_depth >= max_depth:
        return generate_random_literal(n_features, rng, literal_types)
    
    # 30% chance to stop at this level (if not root) and pick literal
    if current_depth > 0 and rng.random() < 0.3:
        return generate_random_literal(n_features, rng, literal_types)
        
    # Operator
    # Decide between Unary and Binary
    # Let's say 50/50 split if both exist
    is_binary = True
    if binary_ops and unary_ops:
        is_binary = rng.random() < 0.6
    elif unary_ops:
        is_binary = False
    elif binary_ops:
        is_binary = True
    else:
        # No operators, just literal
        return generate_random_literal(n_features, rng, literal_types)

    if not is_binary:
        op_cls = rng.choice(unary_ops)
        child = generate_random_tree(n_features, rng, max_depth, current_depth + 1,
                                    binary_ops, unary_ops, literal_types)
        return op_cls(child)
    else:
        op_cls = rng.choice(binary_ops)
        left = generate_random_tree(n_features, rng, max_depth, current_depth + 1,
                                   binary_ops, unary_ops, literal_types)
        right = generate_random_tree(n_features, rng, max_depth, current_depth + 1,
                                    binary_ops, unary_ops, literal_types)
        return op_cls(left, right)


class SymbolicMutator:
    def __init__(self, n_features, mutation_rate=0.1, 
                 binary_ops=None, unary_ops=None, literal_types=None):
        self.n_features = n_features
        self.mutation_rate = mutation_rate
        
        # Defaults
        self.binary_ops = binary_ops if binary_ops else [AND, OR]
        self.unary_ops = unary_ops if unary_ops else [NOT]
        self.literal_types = literal_types # None means default Boolean literals
        
    def mutate(self, root: Node, rng):
        """
        Applies one of the ergodic mutations to the root.
        Returns a NEW root (or same if no mutation happened).
        """
        if rng.random() > 1.0: 
            pass
            
        root = root.clone()
        
        # Pick strategy
        strategies = ['M1', 'M2', 'M3', 'M4']
        weights = [0.4, 0.2, 0.2, 0.2] # 40% param change, others structural
        choice = rng.choice(strategies, p=weights)
        
        if choice == 'M1':
            return self.mutate_literal(root, rng)
        elif choice == 'M2':
            return self.mutate_insert(root, rng)
        elif choice == 'M3':
            return self.mutate_delete(root, rng)
        elif choice == 'M4':
            return self.mutate_reorder(root, rng)
            
        return root

    def mutate_literal(self, root, rng):
        """M1: Atomic Replacement OR Perturbation of a random Literal."""
        size = root.size
        
        literal_indices = []
        for i in range(root.size):
            node = root.get_subtree(i)
            if isinstance(node, Literal):
                literal_indices.append(i)
        
        if not literal_indices:
            return root
            
        chosen_idx = rng.choice(literal_indices)
        node_to_mod = root.get_subtree(chosen_idx)
        
        # Check if it is a Constant -> Perturb!
        if isinstance(node_to_mod, Constant):
            if rng.random() < 0.7:
                 # Perturb
                 val = node_to_mod.value
                 # Perturbation scale: proportional + absolute noise
                 noise = rng.standard_normal() * (0.1 * abs(val) + 0.1)
                 new_literal = Constant(val + noise)
                 return root.set_subtree(chosen_idx, new_literal)
                 
        # Default: Full Replacement
        new_lit = generate_random_literal(self.n_features, rng, self.literal_types)
        return root.set_subtree(chosen_idx, new_lit)

    def mutate_insert(self, root, rng):
        """M2: Structural Insertion (Growth)."""
        size = root.size
        target_idx = rng.integers(0, size)
        target_node = root.get_subtree(target_idx)
        
        if target_node.depth > 6: # Depth limit
            return root
            
        new_literal = generate_random_literal(self.n_features, rng, self.literal_types)
        
        # Pick Operator
        is_binary = True
        if self.binary_ops and self.unary_ops:
            is_binary = rng.random() < 0.7
        elif self.unary_ops: is_binary = False
        
        if is_binary:
            op_cls = rng.choice(self.binary_ops)
            # Randomly decide if N is left or right child
            if rng.random() < 0.5:
                new_subtree = op_cls(target_node, new_literal)
            else:
                new_subtree = op_cls(new_literal, target_node)
        else:
            op_cls = rng.choice(self.unary_ops)
            new_subtree = op_cls(target_node) # Wrap current node
            
        return root.set_subtree(target_idx, new_subtree)

    def mutate_delete(self, root, rng):
        """M3: Structural Deletion (Pruning)."""
        op_indices = []
        for i in range(root.size):
            node = root.get_subtree(i)
            if isinstance(node, (BinaryOperator, UnaryOperator)):
                op_indices.append(i)
                
        if not op_indices:
            return root 
            
        chosen_idx = rng.choice(op_indices)
        op_node = root.get_subtree(chosen_idx)
        
        # Pick child to keep
        if isinstance(op_node, UnaryOperator):
            child_to_keep = op_node.child
        else:
            # Binary
            if rng.random() < 0.5:
                child_to_keep = op_node.left
            else:
                child_to_keep = op_node.right
                
        return root.set_subtree(chosen_idx, child_to_keep)

    def mutate_reorder(self, root, rng):
        """M4: Reordering (Commutativity)."""
        # Pick Binary operator (assuming commutative or just swapping args)
        # Even for non-commutative (Sub, Div), swapping is a valid mutation (sign flip / inverse).
        
        comm_indices = []
        for i in range(root.size):
            node = root.get_subtree(i)
            if isinstance(node, BinaryOperator):
                comm_indices.append(i)
                
        if not comm_indices:
            return root
            
        chosen_idx = rng.choice(comm_indices)
        node = root.get_subtree(chosen_idx)
        
        # Swap children in place (referencing the node in the CLONED tree)
        temp = node.left
        node.left = node.right
        node.right = temp
        
        return root
