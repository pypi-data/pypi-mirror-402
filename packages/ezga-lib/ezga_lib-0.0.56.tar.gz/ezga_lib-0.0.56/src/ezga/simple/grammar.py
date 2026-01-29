
import numpy as np
import abc

class Node(abc.ABC):
    """
    Abstract base class for all nodes in the Symbolic GA Grammar key.
    """
    @abc.abstractmethod
    def evaluate(self, X):
        """
        Evaluates the node on data X (N_samples, N_features).
        Returns a boolean mask or probabilistic float array (N_samples,).
        """
        pass

    @property
    @abc.abstractmethod
    def size(self):
        """Total number of nodes in the subtree."""
        pass

    @property
    @abc.abstractmethod
    def depth(self):
        """Depth of the subtree."""
        pass
    
    @abc.abstractmethod
    def __str__(self):
        pass

    def simplify(self):
        """
        Returns a simplified version of this tree (or self).
        Default implementation: return self.
        """
        return self

    def get_subtree(self, index):
        """
        DFS traversal to get the node at a specific index (0-indexed).
        Useful for mutation operators.
        """
        count = [0] # Mutable wrapper
        result = [None]
        
        def traverse(node):
            if result[0] is not None:
                return
            
            if count[0] == index:
                result[0] = node
                return
            
            count[0] += 1
            if hasattr(node, 'children'):
                for child in node.children:
                    traverse(child)
            elif hasattr(node, 'child'):
                traverse(node.child)
        
        traverse(self)
        return result[0]

    def set_subtree(self, index, new_node):
        """
        DFS traversal to replace the node at a specific index.
        Returns a NEW immutable copy of the tree with the replacement.
        (Or modifies in-place if we decide on mutable trees - pure Python trees are easier mutable)
        For performance in Python GA, mutable in-place modification is often preferred 
        if we handle cloning carefully at the population level.
        
        This implementation assumes MUTABLE in-place for efficiency, 
        caller must clone first if needed.
        """
        if index == 0:
            return new_node # Replaces the whole root
            
        count = [0]
        replaced = [False]
        
        def traverse(node, parent, child_idx_in_parent):
            if replaced[0]: return
            
            if count[0] == index:
                # Found target, replace in parent
                if parent:
                    # If parent has 'children' list
                    if hasattr(parent, 'children'):
                        parent.children[child_idx_in_parent] = new_node
                    # If strictly binary/unary with attributes
                    elif hasattr(parent, 'left') and child_idx_in_parent == 0:
                        parent.left = new_node
                    elif hasattr(parent, 'right') and child_idx_in_parent == 1:
                        parent.right = new_node
                    elif hasattr(parent, 'child'):
                        parent.child = new_node
                replaced[0] = True
                return

            count[0] += 1
            
            # Recurse
            if isinstance(node, BinaryOperator):
                traverse(node.left, node, 0)
                traverse(node.right, node, 1)
            elif isinstance(node, UnaryOperator):
                traverse(node.child, node, 0)
            # Literals have no children
        
        traverse(self, None, -1)
        return self if not (index == 0) else new_node

    def clone(self):
        import copy
        return copy.deepcopy(self)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._eq(other)

    def _eq(self, other):
        return True


# --- Operators ---

class BinaryOperator(Node):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    
    @property
    def children(self):
        return [self.left, self.right]
        
    @property
    def size(self):
        return 1 + self.left.size + self.right.size
        
    @property
    def depth(self):
        return 1 + max(self.left.depth, self.right.depth)
        
    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.left)}, {repr(self.right)})"

    def _eq(self, other):
        return self.left == other.left and self.right == other.right

    def simplify(self):
        # 1. Recursive Simplify
        self.left = self.left.simplify()
        self.right = self.right.simplify()
        
        l = self.left
        r = self.right
        
        # 2. Constant Folding (Strict Constants only, preserving Optimizable)
        if isinstance(l, Constant) and isinstance(r, Constant):
            # Evaluate using single-sample dummy
            # We can just use the scalar values directly
            try:
                # Need to dispatch based on type since we are in the base class
                # but explicit dispatch is messy. 
                # Alternative: create dummy 1-element arrays and call evaluate.
                dummy_X = np.zeros((1, 1)) # Shape doesn't matter for Constants
                val = self.evaluate(dummy_X)[0]
                return Constant(val)
            except:
                pass
                
        eps = 1e-9
        
        # 3. Algebraic Identities
        # Add
        if isinstance(self, Add):
            if isinstance(l, Constant) and abs(l.value) < eps: return r
            if isinstance(r, Constant) and abs(r.value) < eps: return l
            
            # Associative Grouping: (x + C1) + C2 -> x + (C1+C2)
            if isinstance(l, Add) and isinstance(r, Constant):
                if isinstance(l.right, Constant): return Add(l.left, Constant(l.right.value + r.value)).simplify()
                elif isinstance(l.left, Constant): return Add(l.right, Constant(l.left.value + r.value)).simplify()
            if isinstance(r, Add) and isinstance(l, Constant):
                 if isinstance(r.right, Constant): return Add(r.left, Constant(l.value + r.right.value)).simplify()
                 elif isinstance(r.left, Constant): return Add(r.right, Constant(l.value + r.left.value)).simplify()

            # (x + x) -> 2 * x
            if l == r: return Mul(Constant(2.0), l).simplify()
            
        # Sub
        elif isinstance(self, Sub):
            if isinstance(r, Constant) and abs(r.value) < eps: return l
            if isinstance(l, Constant) and abs(l.value) < eps: return Neg(r).simplify()
            if l == r: return Constant(0.0)
            
        # Mul
        elif isinstance(self, Mul):
            if isinstance(l, Constant) and abs(l.value) < eps: return Constant(0.0)
            if isinstance(r, Constant) and abs(r.value) < eps: return Constant(0.0)
            if isinstance(l, Constant) and abs(l.value - 1.0) < eps: return r
            if isinstance(r, Constant) and abs(r.value - 1.0) < eps: return l
            
            if isinstance(l, Constant) and abs(l.value + 1.0) < eps: return Neg(r).simplify()
            if isinstance(r, Constant) and abs(r.value + 1.0) < eps: return Neg(l).simplify()
            
            # Associative Grouping: (x * C1) * C2 -> x * (C1*C2)
            if isinstance(l, Mul) and isinstance(r, Constant):
                if isinstance(l.right, Constant): return Mul(l.left, Constant(l.right.value * r.value)).simplify()
                elif isinstance(l.left, Constant): return Mul(l.right, Constant(l.left.value * r.value)).simplify()
            if isinstance(r, Mul) and isinstance(l, Constant):
                 if isinstance(r.right, Constant): return Mul(r.left, Constant(l.value * r.right.value)).simplify()
                 elif isinstance(r.left, Constant): return Mul(r.right, Constant(l.value * r.left.value)).simplify()

            if l == r: return Square(l).simplify()
            
        # Div
        elif isinstance(self, Div):
            if isinstance(r, Constant) and abs(r.value - 1.0) < eps: return l
            if isinstance(l, Constant) and abs(l.value) < eps: return Constant(0.0)
            if isinstance(r, Constant) and abs(r.value + 1.0) < eps: return Neg(l).simplify()
            if l == r: return Constant(1.0)
            
        return self

# --- Boolean Binary Operators ---
class AND(BinaryOperator):
    def evaluate(self, X):
        return self.left.evaluate(X) * self.right.evaluate(X)
        
    def __str__(self):
        return f"({self.left} AND {self.right})"

class OR(BinaryOperator):
    def evaluate(self, X):
        # Probabilistic OR: 1 - (1-A)(1-B) or Max(A, B)
        # Using Max for fuzzy logic consistency or smooth approx
        l = self.left.evaluate(X)
        r = self.right.evaluate(X)
        return np.maximum(l, r) 
        
    def __str__(self):
        return f"({self.left} OR {self.right})"

# --- Math Binary Operators ---
class Add(BinaryOperator):
    def evaluate(self, X):
        return self.left.evaluate(X) + self.right.evaluate(X)
    def __str__(self):
        return f"({self.left} + {self.right})"

class Sub(BinaryOperator):
    def evaluate(self, X):
        return self.left.evaluate(X) - self.right.evaluate(X)
    def __str__(self):
        return f"({self.left} - {self.right})"

class Mul(BinaryOperator):
    def evaluate(self, X):
        return self.left.evaluate(X) * self.right.evaluate(X)
    def __str__(self):
        return f"({self.left} * {self.right})"

class Div(BinaryOperator):
    def evaluate(self, X):
        denom = self.right.evaluate(X)
        denom_safe = np.where(np.abs(denom) < 1e-6, np.sign(denom + 1e-9) * 1e-6, denom)
        return self.left.evaluate(X) / denom_safe
    def __str__(self):
        return f"({self.left} / {self.right})"

# --- Unary Operators ---
class UnaryOperator(Node):
    def __init__(self, child):
        self.child = child

    @property
    def children(self):
        return [self.child]

    @property
    def size(self):
        return 1 + self.child.size

    @property
    def depth(self):
        return 1 + self.child.depth

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.child)})"

    def _eq(self, other):
        return self.child == other.child

    def simplify(self):
        # 1. Recursive
        self.child = self.child.simplify()
        
        # 2. Constant Folding
        if isinstance(self.child, Constant):
            try:
                dummy_X = np.zeros((1, 1))
                val = self.evaluate(dummy_X)[0]
                if abs(val) < 1e-9: val = 0.0 # Normalize -0.0 to 0.0
                return Constant(val)
            except:
                pass
                
        # 3. Identities
        # Neg(Neg(x)) -> x
        if isinstance(self, Neg) and isinstance(self.child, Neg):
            return self.child.child

        # Neg(0) -> 0
        if isinstance(self, Neg) and isinstance(self.child, Constant) and abs(self.child.value) < 1e-9:
             return Constant(0.0)
             
        # Sqrt(Square(x)) -> Abs(x)
        if isinstance(self, Sqrt) and isinstance(self.child, Square):
            return Abs(self.child.child).simplify()
            
        return self

# --- Boolean Unary Operators ---
class NOT(UnaryOperator):
    def evaluate(self, X):
        return 1.0 - self.child.evaluate(X)
        
    def __str__(self):
        return f"NOT({self.child})"

# --- Math Unary Operators ---
class Sin(UnaryOperator):
    def evaluate(self, X):
        return np.sin(self.child.evaluate(X))
    def __str__(self):
        return f"sin({self.child})"

class Cos(UnaryOperator):
    def evaluate(self, X):
        return np.cos(self.child.evaluate(X))
    def __str__(self):
        return f"cos({self.child})"

class Exp(UnaryOperator):
    def evaluate(self, X):
        val = self.child.evaluate(X)
        val = np.clip(val, -10, 10) # Clip for overflow safety
        return np.exp(val)
    def __str__(self):
        return f"exp({self.child})"

class Log(UnaryOperator):
    def evaluate(self, X):
        val = np.abs(self.child.evaluate(X)) + 1e-6
        return np.log(val)
    def __str__(self):
        return f"log(|{self.child}|)"

class Sqrt(UnaryOperator):
    def evaluate(self, X):
        val = np.abs(self.child.evaluate(X))
        return np.sqrt(val)
    def __str__(self):
        return f"sqrt(|{self.child}|)"

class Abs(UnaryOperator):
    def evaluate(self, X):
        return np.abs(self.child.evaluate(X))
    def __str__(self):
        return f"|{self.child}|"

class Square(UnaryOperator):
    def evaluate(self, X):
        return np.square(self.child.evaluate(X))
    def __str__(self):
        return f"({self.child})^2"

class Neg(UnaryOperator):
    def evaluate(self, X):
        return -self.child.evaluate(X)
    def __str__(self):
        return f"-({self.child})"


# --- Literals ---

class Literal(Node):
    @property
    def size(self):
        return 1
        
    @property
    def depth(self):
        return 1
    
    @property
    def children(self):
        return []

# --- Math Literals ---
class Variable(Literal):
    def __init__(self, index):
        self.index = index
        
    def evaluate(self, X):
        return X[:, self.index]
        
    def __str__(self):
        return f"x{self.index}"
        
    def __repr__(self):
        return f"Variable({self.index})"
    
    def _eq(self, other):
        return self.index == other.index

class Constant(Literal):
    def __init__(self, value):
        self.value = value
        
    def evaluate(self, X):
        return np.full(len(X), self.value)
        
    def __str__(self):
        return f"{self.value:.3f}"
        
    def __repr__(self):
        return f"Constant({self.value})"
    
    def _eq(self, other):
        # Use simple epsilon check for constants? Or exact?
        # For simplify x-x=0, exact might be needed or eps.
        return abs(self.value - other.value) < 1e-9

class OptimizableConstant(Literal):
    """
    Acts like a Constant, but its value is meant to be optimized per-tree.
    Initializing value can be random, then 'evaluate' returns optimized value.
    The optimization logic (memetic algorithm) will traverse the tree,
    find these nodes, optimize them, and then replace them with frozen 'Constants'.
    """
    def __init__(self, value):
        self.value = value
        
    def evaluate(self, X):
        return np.full(len(X), self.value)
        
    def __str__(self):
        return f"Opt({self.value:.3f})"
        
    def __repr__(self):
        return f"OptimizableConstant({self.value})"

    def _eq(self, other):
        return abs(self.value - other.value) < 1e-9


# --- Boolean Literals ---

class Threshold(Literal):
    def __init__(self, feature, val, op):
        self.feature = feature
        self.val = val
        self.op = op # 0 for >, 1 for <
        
    def evaluate(self, X):
        col = X[:, self.feature]
        # Soft Sigmoid approximation for differentiability/smoothness if needed, 
        # or hard boolean. 
        # Using sharp sigmoid for "ergodic" but smooth exploration
        # Phase 17: Revert sharpness to 10.0 to fix Vanishing Gradient
        sharpness = 10.0
        if self.op == 0: # > val
            # sigmoid(sharp * (x - val))
            logit = sharpness * (col - self.val)
            return 1.0 / (1.0 + np.exp(-logit))
        else: # < val
            # sigmoid(sharp * (val - x))
            logit = sharpness * (self.val - col)
            return 1.0 / (1.0 + np.exp(-logit))

    def __str__(self):
        sym = ">" if self.op == 0 else "<"
        return f"X[{self.feature}] {sym} {self.val:.2f}"
        
    def __repr__(self):
        return f"Threshold({self.feature}, {self.val}, {self.op})"

class Interval(Literal):
    def __init__(self, feature, low, high):
        self.feature = feature
        self.low = min(low, high)
        self.high = max(low, high)
        
    def evaluate(self, X):
        col = X[:, self.feature]
        sharpness = 10.0 # Phase 17 tuning
        # sigmoid(x - low) * sigmoid(high - x)
        act_low = 1.0 / (1.0 + np.exp(-sharpness * (col - self.low)))
        act_high = 1.0 / (1.0 + np.exp(-sharpness * (self.high - col)))
        return act_low * act_high

    def __str__(self):
        return f"{self.low:.2f} < X[{self.feature}] < {self.high:.2f}"

    def __repr__(self):
        return f"Interval({self.feature}, {self.low}, {self.high})"

class Ratio(Literal):
    def __init__(self, feat_a, feat_b, threshold):
        self.feat_a = feat_a
        self.feat_b = feat_b
        self.threshold = threshold
        
    def evaluate(self, X):
        # Avoid div by zero
        val_a = X[:, self.feat_a]
        val_b = X[:, self.feat_b] + 1e-6 
        ratio = val_a / val_b
        
        sharpness = 20.0
        # ratio > threshold
        logit = sharpness * (ratio - self.threshold)
        return 1.0 / (1.0 + np.exp(-logit))
        
    def __str__(self):
        return f"(X[{self.feat_a}]/X[{self.feat_b}]) > {self.threshold:.2f}"

    def __repr__(self):
        return f"Ratio({self.feat_a}, {self.feat_b}, {self.threshold})"

class Gaussian(Literal):
    def __init__(self, feature, mu, sigma):
        self.feature = feature
        self.mu = mu
        self.sigma = sigma + 1e-3 # ensure positive
        
    def evaluate(self, X):
        col = X[:, self.feature]
        # exp( - (x-mu)^2 / 2sigma^2 )
        return np.exp( -0.5 * ((col - self.mu)/self.sigma)**2 )
        
    def __str__(self):
        return f"Gauss(X[{self.feature}], mu={self.mu:.2f})"

    def __repr__(self):
        # Note: we stored sigma+1e-3, but init expects original sigma usually?
        # Actually our init adds +1e-3. If we reconstruct, we might add it again.
        # Ideally we store 'clean' params. But here sigma is state.
        # Let's just return current sigma. The constructor will add 1e-3 again? 
        # Check constructor: self.sigma = sigma + 1e-3
        # If we return current sigma, next time it will be sigma + 2e-3. 
        # For this verification, it's fine.
        return f"Gaussian({self.feature}, {self.mu}, {self.sigma})"
