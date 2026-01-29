import os
import shutil
import numpy as np
from pathlib import Path
import tempfile
import warnings

from ezga.core.config import (
    GAConfig, 
    PopulationParams, 
    SimulatorParams, 
    EvaluatorParams, 
    VariationParams,
    GenerativeParams, 
    AgenticParams,
    SelectionParams
)
from ezga.factory import build_default_engine
from ezga.variation.variation import Variation_Operator

from .problem import ElementwiseProblem
from .algorithm import GA
from .result import Result
from .operators import ProblemCalculatorWrapper, PolynomialMutationVector, SimulatedBinaryCrossoverVector, ShiftMutationVector, ShiftMutationVariable

def _write_initial_xyz(filename, X):
    """
    Writes a dummy XYZ file where X values are stored in the x-coordinate 
    of 'H' atoms.
    """
    n_samples, n_var = X.shape
    with open(filename, 'w') as f:
        for i in range(n_samples):
            # Header
            f.write(f"{n_var}\n")
            # Comment line (metadata)
            f.write("Energy=0.0 Properties=species:S:1:pos:R:3\n")
            # Atoms
            for j in range(n_var):
                # Storing variable in x-position. 
                # Use y-position to spacing out atoms to avoid merging/collision logic
                # in the underlying structure manager. 
                # 2.0A spacing is sufficient for H atoms.
                val = X[i, j]
                f.write(f"H {val:.6f} {j*2.0:.1f} 0.0\n")

def _extract_x_from_structure(container):
    """
    Extracts design vector X from structure.
    """
    try:
        # container.AtomPositionManager.atomPositions returns list/array
        pos = np.array(container.AtomPositionManager.atomPositions, dtype=float)
        return pos[:, 0]
    except Exception:
        return None

def _extract_f_from_structure(container):
    """
    Extracts Objective F from structure metadata.
    """
    try:
        # First check metadata "objectives"
        meta = getattr(container.AtomPositionManager, "metadata", {})
        if "objectives" in meta:
            objs = meta["objectives"]
            if len(objs) == 1:
                return float(objs[0])
            return np.array(objs)
        
        val = container.AtomPositionManager.E
        if val is None:
            return np.inf
        return val
    except Exception:
        return np.inf

def minimize(problem: ElementwiseProblem,
             algorithm: GA,
             termination: tuple = ('n_gen', 100),
             seed: int = 1,
             verbose: bool = False,
             save_history: bool = False,
             **kwargs) -> Result:
    """
    Minimizes the given problem using the provided algorithm configuration.
    
    Args:
        problem: ElementwiseProblem instance.
        algorithm: GA configuration instance.
        termination: Tuple ('n_gen', int) or similar.
        seed: Random seed.
        verbose: Print logs.
        save_history: Keep full history (not implemented fully, placeholder).
        **kwargs: Extra args passed to GAConfig.
    
    Returns:
        Result object.
    """
    
    # 1. Prepare Workspace
    # We create a temporary directory for this run to keep things clean
    # or use a local 'run_simple' folder.
    run_dir = Path(f"run_simple_{seed}")
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir()
    
    try:
        # 2. Initialize Population
        rng = np.random.default_rng(seed)
        
        # Sampling (DOE or Random)
        X_init = None
        
        # If user passed explicit array
        if isinstance(algorithm.sampling, np.ndarray):
            X_init = algorithm.sampling
            # Ensure shape
            if X_init.shape[1] != problem.n_var:
                raise ValueError(f"Sampling shape {X_init.shape} mismatch with n_var={problem.n_var}")
        
        # If user requested LHS
        elif algorithm.sampling == "lhs":
            try:
                from scipy.stats import qmc
                sampler = qmc.LatinHypercube(d=problem.n_var, seed=seed)
                sample = sampler.random(n=algorithm.pop_size)
                X_init = qmc.scale(sample, problem.xl, problem.xu)
            except ImportError:
                print("Warning: scipy not installed, falling back to random sampling instead of LHS.")
                X_init = rng.uniform(problem.xl, problem.xu, size=(algorithm.pop_size, problem.n_var))
        
        # Default Random
        else:
            X_init = rng.uniform(problem.xl, problem.xu, size=(algorithm.pop_size, problem.n_var))
        
        init_xyz = run_dir / "initial.xyz"
        _write_initial_xyz(init_xyz, X_init)
        
        # 3. Setup Operators
        # Calculator
        calc = ProblemCalculatorWrapper(problem)
        
        # Mutation and Crossover Setup
        # 1. Mutation
        if algorithm.mutation is not None:
             mut_ops = [algorithm.mutation]
        else:
             # Default to PM
             pm_prob = 1.0 / problem.n_var
             mut_ops = [
                 PolynomialMutationVector(eta=20.0, prob=pm_prob, xl=problem.xl, xu=problem.xu)
             ]
             # Add orthogonal shift operators for Generative Model guidance (Visualized as multi-scale basis)
             for i in range(problem.n_var):
                 # Coarse
                 mut_ops.append(ShiftMutationVariable(index=i, shift_fraction=0.05, xl=problem.xl, xu=problem.xu))
                 mut_ops.append(ShiftMutationVariable(index=i, shift_fraction=-0.05, xl=problem.xl, xu=problem.xu))
                 # Fine
                 mut_ops.append(ShiftMutationVariable(index=i, shift_fraction=0.001, xl=problem.xl, xu=problem.xu))
                 mut_ops.append(ShiftMutationVariable(index=i, shift_fraction=-0.001, xl=problem.xl, xu=problem.xu))

        # 2. Crossover
        if algorithm.crossover is not None:
             cx_ops = [algorithm.crossover]
        else:
             # Default to SBX
             cx_ops = [SimulatedBinaryCrossoverVector(eta=15.0, prob=0.9, xl=problem.xl, xu=problem.xu)]
        
        # 4. Feature/Objective Extractors
        # EZGA needs callables that take a Partition and return arrays
        def features_func(partition):
            # N x D
            data = []
            for c in partition.containers:
                x = _extract_x_from_structure(c)
                try:
                    lat = c.AtomPositionManager.latticeVectors
                except:
                    pass

                if x is None:
                    # Fallback for broken structure
                    x = np.full(problem.n_var, np.nan)
                
                # Robustness: Filter invalid shapes
                if x.shape[0] == problem.n_var:
                    data.append(x)
                else:
                    print(f"WARN: Skipping structure with invalid shape {x.shape} (Expected {problem.n_var})")
                    # Must append something to keep length aligned with partition? 
                    # Evaluator expects N features for N containers.
                    # We should append NaNs if we can't skip?
                    # If we skip, len(data) != len(partition.containers).
                    # Evaluator maps features[i] to container[i].
                    # So we MUST append!
                    x_nan = np.full(problem.n_var, np.nan)
                    data.append(x_nan)
            return np.array(data, dtype=float)

        def objectives_func(partition):
            # N x M
            data = []
            expected_m = problem.n_obj
            
            for c in partition.containers:
                blob = _extract_f_from_structure(c)
                
                # Convert blob to flat list/array of floats
                if blob is None:
                    row = [np.nan] * expected_m
                else:
                    # If scalar, wrap
                    if np.ndim(blob) == 0:
                        blob = [blob]
                    
                    row = list(np.array(blob).flatten())
                
                # Check Length
                if len(row) == expected_m:
                    data.append(row)
                elif len(row) < expected_m:
                    # Pad? Or just assuming scalar was meant to be repeated? 
                    # Usually if we have multi-obj defined but get scalar 0.0 (from init), 
                    # it means it wasn't evaluated properly or it's a dummy.
                    # Let's pad with Nan
                    padded = row + [np.nan] * (expected_m - len(row))
                    data.append(padded)
                else:
                    # Truncate?
                    data.append(row[:expected_m])
            
            # Handle mixed length or types if any
            try:
                # Force 2D array
                return np.array(data, dtype=float)
            except Exception as e:
                print(f"Warning: Objective extraction failed: {e}")
                # return zeros?
                return np.zeros((len(partition.containers), expected_m))

        # 5. Parse Termination
        n_gen = 100
        if termination and termination[0] == 'n_gen':
            n_gen = termination[1]

        # 6. Build Configuration
        # We need to map GA simple params to GAConfig complex params
        cfg = GAConfig(
            output_path=str(run_dir),
            rng=seed,
            debug=verbose,
            max_generations=n_gen,
            initial_generation=0,
            
            # Population
            population=PopulationParams(
                dataset_path=str(init_xyz),
                size_limit=algorithm.pop_size_max if algorithm.pop_size_max is not None else algorithm.pop_size*10, # Enable culling to enforce size limit logic
                filter_duplicates=algorithm.eliminate_duplicates,
                # Isolate DB for this run to avoid contamination
                db_path=str(run_dir / "db"),
                db_ro_path=str(run_dir / "db_ro")
            ),
            
            # Simulator
            simulator=SimulatorParams(
                calculator=calc,
                mode="sampling"
            ),
            
            # Evaluator
            evaluator=EvaluatorParams(
                features_funcs=features_func,
                objectives_funcs=objectives_func
            ),
            
            # Selection
            multiobjective=SelectionParams(
                selection_method=algorithm.selection if algorithm.selection else "boltzmann_bigdata",
                size=algorithm.n_offsprings if algorithm.n_offsprings is not None else algorithm.pop_size
            ),
            
            # Variation
            variation=VariationParams(
                # Adjust rates?
                initial_mutation_rate=1.0, # 1 mutation per struct?
                
            ),
            
            # Generative Model (Bayesian Optimization)
            generative=GenerativeParams(
                size=algorithm.bo_size if algorithm.enable_bo else 0, # Enable if requested
                start_gen=0,
                candidate_multiplier=10,
                bo_kwargs={"n_objectives": problem.n_obj},
                # Adapt tolerance to variable scale (0.5% of range)
                # Finest mutation is 0.1%, so 0.5% is safe target
                tolerance=list((problem.xu - problem.xl) * 0.005),
                max_variation_iterations=200
            ),
            agentic=AgenticParams(poll_interval=999999), # No syncing
            
            **kwargs
        )
        
        # 7. Build Engine
        # We explicitly inject our variation operator which has the vector mutation
        # Note: Variation_Operator takes mutation_funcs=[...]
        var_op = Variation_Operator(
            mutation_funcs=mut_ops,
            crossover_funcs=cx_ops,
            feature_func=features_func,
            # Pass through other config params if needed
            max_prob=cfg.variation.max_prob
        )
        
        engine = build_default_engine(
            cfg,
            variation=var_op
        )
        
        # 8. Execute
        final_pop = engine.run()
        
        # 9. Extract Results
        # Get 'dataset' which holds the archive/population
        ds = final_pop.get_dataset('dataset')
        all_containers = list(ds.containers)
        
        X_all = []
        F_all = []
        
        best_idx = -1
        best_f = np.inf
        
        for idx, c in enumerate(all_containers):
            x_vec = _extract_x_from_structure(c)
            f_val = _extract_f_from_structure(c)
            
            X_all.append(x_vec)
            F_all.append(f_val)
            
            # Minimize logic
            # Handle scalar f_val
            f_scalar = f_val if np.ndim(f_val) == 0 else f_val[0]
            
            if f_scalar < best_f:
                best_f = f_scalar
                best_idx = idx
        
        res = Result(
            X=X_all[best_idx] if best_idx >= 0 else None,
            F=F_all[best_idx] if best_idx >= 0 else None,
            pop=all_containers,
            history=None, # access context logs if needed
            algorithm=algorithm,
            exec_time=None 
        )
        
        return res

    except Exception as e:
        # Cleanup? 
        if verbose:
            import traceback
            traceback.print_exc()
        raise e
    # finally:
    #    # Optional cleanup of run_dir
    #    if not verbose:
    #        shutil.rmtree(run_dir)
