
import numpy as np
import collections

# Import our AST Nodes
from ezga.variation.variation import Variation_Operator
from .grammar import (
    Node, BinaryOperator, UnaryOperator, Literal,
    AND, OR, NOT,
    Threshold, Interval, Ratio, Gaussian
)

class Grammar:
    """
    Represents a customized BNF Grammar.
    Rules are stored as:
    {
        "<NonTerminal>": [
            [ Production_Option_1_Element_1, Production_Option_1_Element_2, ... ],
            [ Production_Option_2_Element_1, ... ]
        ]
    }
    """
    def __init__(self, rules=None, start_symbol="<expr>"):
        self.rules = rules if rules is not None else {}
        self.start_symbol = start_symbol

    def add_rule(self, non_terminal, productions):
        """
        Add a rule.
        productions: list of lists.
        E.g. [ [Class, "<child>"], [Class2, "<child>", "<child>"] ]
        """
        self.rules[non_terminal] = productions

    def get_productions(self, non_terminal):
        return self.rules.get(non_terminal, [])

    def is_non_terminal(self, symbol):
        return isinstance(symbol, str) and symbol.startswith("<") and symbol.endswith(">")

class GEMapper:
    """
    Grammatical Evolution Mapper.
    Maps an integer vector (Genotype) to an AST (Phenotype).
    """
    def __init__(self, grammar: Grammar, max_depth=10, max_wraps=0):
        self.grammar = grammar
        self.max_depth = max_depth
        self.max_wraps = max_wraps # 0 = infinite (or just very large?), usually we error if out of genes
        
    def map(self, genotype):
        """
        genotype: List/Array of integers.
        Returns: Root Node of AST or None if mapping failed.
        """
        self.genotype = np.array(genotype, dtype=int)
        self.gene_idx = 0
        self.wraps = 0
        self.current_depth = 0
        self.nodes_created = 0
        
        try:
            root = self._derive(self.grammar.start_symbol, depth=0)
            return root
        except RecursionError:
            # print("Max Depth Exceeded")
            return None
        except IndexError:
            # Ran out of genes and wrapping limit reached
            return None
        except Exception as e:
            # print(f"Mapping Error: {e}")
            return None

    def _get_gene(self):
        if self.gene_idx >= len(self.genotype):
            if self.wraps < self.max_wraps:
                self.gene_idx = 0
                self.wraps += 1
            else:
                # Simple mode: wrap anyway? Or reuse last gene?
                # Standard GE loops.
                self.gene_idx = 0 # Infinite wrap simplified for now
                pass 
        
        val = self.genotype[self.gene_idx]
        self.gene_idx += 1
        return val

    def _derive(self, symbol, depth):
        if depth > self.max_depth:
            # Force terminal if possible?
            # Creating a default literal if stuck?
            # For now raise
            raise RecursionError("Max depth")

        if not self.grammar.is_non_terminal(symbol):
            # It's a terminal or callable class constructor
            return symbol

        productions = self.grammar.get_productions(symbol)
        if not productions:
            raise ValueError(f"No productions for {symbol}")

        # Selection
        gene = self._get_gene()
        
        # Heuristic for depth limit:
        # If we are deep, prefer productions that are terminals (no strings starting with <)
        # simplistic check:
        # if depth > limit - 2: filter productions?
        
        prod_idx = gene % len(productions)
        chosen_production = productions[prod_idx]
        
        # Instantiate
        # A production is a list: [Constructor, Arg1, Arg2...]
        # The first element is usually the Node Class or None (if it's just a grouping)
        # Actually, let's allow diverse production structures.
        # Structure 1: [Class, Arg, Arg] -> Class(Arg', Arg')
        # Structure 2: ["<op>", Arg] -> recursive
        
        # Strategy:
        # Evaluate all elements in the production list.
        # If element is callable (Class), it waits for subsequent args?
        # Simpler: The production IS the elements. We map them.
        # If the first element is a Class, we instantiate it with the rest.
        
        elements = []
        
        # Special handling for "Parametric" terminals defined in the grammar?
        # e.g. ["Threshold", "feat_idx_gene", "val_gene"]
        # We can handle this by checking if the symbol expects specific gene consumption.
        
        # Let's assume the first item is the factory/class, rest are arguments (which might be NonTerminals)
        constructor = chosen_production[0]
        args_schema = chosen_production[1:]
        
        resolved_args = []
        for arg in args_schema:
            if callable(arg) and not isinstance(arg, type): 
                # e.g. local lambda, strictly shouldn't happen in simple grammar definition
                pass
            
            # If arg is a special marker for consuming a gene (Parametric GE)
            if arg == "__gene__":
                 # Consume a gene and use its raw value (e.g. for features)
                 # Used for Feature Index selection
                 val = self._get_gene()
                 resolved_args.append(val)
            elif arg == "__gene_float__":
                # Consume gene, map to 0-1
                val = self._get_gene()
                # Normalize assuming 8-bit or 32-bit? 
                # Let's assume genotype is arbitrary int.
                # Map large int to 0-1 safely.
                val = (val % 10000) / 10000.0
                resolved_args.append(val)
            else:
                # Recurse
                child = self._derive(arg, depth + 1)
                resolved_args.append(child)
        
        # Instantiate
        
        # 1. Resolve Constructor
        if isinstance(constructor, str) and self.grammar.is_non_terminal(constructor):
             # It's a non-terminal (e.g. "<literal>" -> ["<threshold>"])
             # We must derive it.
             constructor = self._derive(constructor, depth + 1)
             
        # 2. Instantiate if callable
        if isinstance(constructor, type) or callable(constructor):
            # If it's a class or function, call it with args
            try:
                # If valid args, call
                return constructor(*resolved_args)
            except TypeError:
                # If we derived an instance (e.g. via recursive chain), and args are empty, just return it
                if not resolved_args:
                    return constructor
                raise
        else:
            # It's an object instance or primitive
            return constructor


class GEVariation(Variation_Operator):
    """
    Variation Operator optimized for Grammatical Evolution (Integer Vectors).
    """
    def __init__(self, genotype_len, mutation_rate=0.1, crossover_rate=0.9, gene_min=0, gene_max=255):
        # Pass empty lists to super as we override mutate/crossover directly
        super().__init__(mutation_funcs=[], crossover_funcs=[])
        
        self.genotype_len = genotype_len
        self.pm = mutation_rate
        self.pc = crossover_rate
        self.min_val = gene_min
        self.max_val = gene_max

    def mutate(self, containers, **kwargs):
        """
        Integer Mutation (Random Resetting).
        """
        offspring = []
        rng = kwargs.get('rng', np.random.default_rng())
        
        import copy
        for c_original in containers:
            c = copy.deepcopy(c_original)
            
            # Extract Genes (Assume stored in X coord of atoms)
            # Need to be robust: positions might be float, we need to treat them as ints for logic
            # but store back as floats.
            
            apm = c.AtomPositionManager
            pos = np.array(apm.atomPositions)
            
            if len(pos) == 0:
                offspring.append(c)
                continue
                
            genes = np.abs(pos[:, 0]).astype(int)
            
            # Vectorized Mutation
            mask = rng.random(len(genes)) < self.pm
            if np.any(mask):
                # Random Reset
                if self.min_val == 0 and self.max_val == 255:
                     # Fast path
                     new_vals = rng.integers(0, 256, size=np.sum(mask))
                else:
                     new_vals = rng.integers(self.min_val, self.max_val + 1, size=np.sum(mask))
                
                genes[mask] = new_vals
                
                # Update positions
                pos[:, 0] = genes.astype(float)
                apm.set_atomPositions(pos)
                
                # Clear metadata tree if it exists (forcing re-evaluation)
                if hasattr(apm, "metadata") and apm.metadata and "symbolic_tree" in apm.metadata:
                    apm.metadata["symbolic_tree"] = None
            
            offspring.append(c)
            
        return offspring

    def crossover(self, parents, **kwargs):
        """
        One-Point Crossover for Integers.
        """
        rng = kwargs.get('rng', np.random.default_rng())
        offspring = []
        
        # Iterate in pairs
        for i in range(0, len(parents), 2):
            p1 = parents[i]
            # Handle odd number of parents
            if i + 1 >= len(parents):
                offspring.append(p1)
                break
            p2 = parents[i+1]
            
            if rng.random() < self.pc:
                # Perform Crossover
                c1 = copy.deepcopy(p1)
                c2 = copy.deepcopy(p2)
                
                pos1 = np.array(c1.AtomPositionManager.atomPositions)
                pos2 = np.array(c2.AtomPositionManager.atomPositions)
                
                # Ensure they have same length
                l = min(len(pos1), len(pos2))
                if l > 1:
                    cx_point = rng.integers(1, l)
                    
                    # Swap tails (X coords only - genes)
                    tmp = pos1[cx_point:, 0].copy()
                    pos1[cx_point:, 0] = pos2[cx_point:, 0]
                    pos2[cx_point:, 0] = tmp
                    
                    c1.AtomPositionManager.set_atomPositions(pos1)
                    c2.AtomPositionManager.set_atomPositions(pos2)
                    
                    # Clear metadata
                    for c in [c1, c2]:
                         if hasattr(c.AtomPositionManager, "metadata") and c.AtomPositionManager.metadata and "symbolic_tree" in c.AtomPositionManager.metadata:
                             c.AtomPositionManager.metadata["symbolic_tree"] = None
                
                offspring.extend([c1, c2])
            else:
                offspring.extend([p1, p2])
                
        return offspring

