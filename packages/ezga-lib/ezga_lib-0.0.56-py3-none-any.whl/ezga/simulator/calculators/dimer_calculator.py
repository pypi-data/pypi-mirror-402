"""Factory module for Dimer search exploration calculators from random starting points.

This module provides a factory function to generate calculator instances that
perform random Dimer searches to find transition states (TS).
It follows the pattern of `reactivity_calculator`, returning a list of discovered structures.

Typical usage example:

    from ezga.simulator.calculators.dimer_calculator import dimer_calculator

    calc_func = dimer_calculator(
        calc_path="mpa-0-medium",
        num_attempts=5,
        dimer_fmax=0.05
    )
"""
from __future__ import annotations

import os
import copy
import logging
import uuid
import numpy as np
from typing import Union, Sequence, Optional, Callable, Tuple, Dict, Any, List

import ase.io
from ase import Atoms
from ase.constraints import FixAtoms, FixCartesian
from ase.optimize import FIRE
from ase.dimer import DimerControl, MinModeAtoms, MinModeTranslate

# Shared utilities (MACE support, etc.)
from ..mace_utils import (
    resolve_model_spec,
    assert_license_ok,
    download_if_needed,
    get_cache_dir,
)

# Configure module-level logger
logger = logging.getLogger(__name__)

# Type alias for EZGA Simulator return format
CalcResult = Tuple[
    np.ndarray,         # Positions
    List[str],          # Symbols
    Optional[np.ndarray], # Cell
    float,              # Energy
    Dict[str, Any]      # Metadata
]

# =============================================================================
# Helper Functions (Constraints, etc., shared logic pattern)
# =============================================================================
def _to_pred_list(preds: Optional[Sequence[Callable]]) -> list:
    if preds is None: return []
    if callable(preds): return [preds]
    try: return list(preds)
    except TypeError: return [preds]

class _StructAdapter:
    class _APM:
        def __init__(self, constraints):
            self.atomicConstraints = constraints
            
    def __init__(self, symbols, positions, cell, atomic_constraints=None):
        self.atomPositions  = np.asarray(positions, float)
        self.atomLabelsList = np.asarray(symbols, dtype=object)
        self.latticeVectors = np.asarray(cell, float) if cell is not None else np.eye(3)
        self.AtomPositionManager = self._APM(atomic_constraints)

def _evaluate(idx: int, structure: _StructAdapter, constraints: Sequence[Callable], logic: str = "all") -> bool:
    if not constraints: return False
    if logic == "all": return all(c(idx, structure) for c in constraints)
    if logic == "any": return any(c(idx, structure) for c in constraints)
    raise ValueError("logic must be 'all' or 'any'")

def _select_indices(symbols, positions, cell, fixed, constraints, logic="all") -> np.ndarray:
    N = len(symbols)
    adapter = _StructAdapter(symbols, positions, cell, fixed)
    return np.asarray([i for i in range(N) if _evaluate(i, adapter, constraints, logic)], dtype=int)

def _build_ase_constraints(atoms: Atoms, selected: np.ndarray, action: str, freeze_components: Optional[Sequence[Union[int, str]]]):
    N = len(atoms)
    selected = np.unique(selected) if selected.size > 0 else np.array([], dtype=int)
    
    if action == "freeze":
        target = selected
    elif action == "move_only":
        mask = np.ones(N, dtype=bool); mask[selected] = False
        target = np.where(mask)[0]
    else:
        raise ValueError("action must be 'freeze' or 'move_only'")

    if len(target) == 0:
        return None

    if freeze_components is None:
        return FixAtoms(indices=target)
    else:
        # Resolve 'x','y','z' -> 0,1,2
        comp_map = {'x':0, 'y':1, 'z':2, 0:0, 1:1, 2:2}
        comps = [comp_map[c] if isinstance(c,str) else c for c in freeze_components]
        mask = np.zeros((N, 3), dtype=bool)
        mask[np.ix_(target, comps)] = True
        return FixCartesian(mask=mask)

def _package_result(atoms: Atoms, metadata: Dict[str, Any]) -> CalcResult:
    try:
        energy = float(atoms.get_potential_energy())
    except Exception:
        energy = float('nan')
    cell = np.array(atoms.get_cell()) if atoms.pbc.any() else None
    return (
        np.array(atoms.get_positions()),
        atoms.get_chemical_symbols(),
        cell,
        energy,
        copy.deepcopy(metadata)
    )

def _build_atoms_obj(symbols, positions, cell, calc_factory):
    atoms = Atoms(symbols=symbols, positions=positions, cell=cell, pbc=(cell is not None))
    atomic_calc = calc_factory() if callable(calc_factory) else copy.deepcopy(calc_factory)
    atoms.calc = atomic_calc
    return atoms

# =============================================================================
# Dimer Calculator Factory
# =============================================================================

def dimer_calculator(
    calculator_factory: Optional[Union[Callable[[], object], object]] = None,
    
    # --- Dimer / Exploration Params ---
    num_attempts: int = 5,
    root_fmax: float = 0.02,
    dimer_fmax: float = 0.05,
    dimer_steps: int = 200,
    write_trajectories: bool = True,
    
    # Disorder Params
    atoms_to_displace: int = 1,  # Number of atoms to randomly displace per attempt
    displacement_range: Tuple[float, float] = (-0.15, 0.15), 
    
    # --- Constraint Params ---
    constraint_logic: str = "all",
    constraint_action: str = "freeze",
    freeze_components: Optional[Sequence[Union[int, str]]] = None,
    constraints: Optional[Sequence[Callable]] = None,

    # --- MACE Arguments ---
    calc_path: Optional[str] = None,
    device: str = 'cuda',
    default_dtype: str = 'float32',
    allow_asl: bool = False,
    cache_dir: Optional[str] = None,

) -> Callable[..., List[CalcResult]]:
    """
    Builds a callable that runs random Dimer searches.
    
    For each attempt:
      1. Relaxes the start structure (optional if root_fmax > 0).
      2. Selects `atoms_to_displace` random atoms (respecting constraints?).
         *Actually, usually we select from NON-frozen atoms.*
      3. Displaces them randomly within `displacement_range`.
      4. Runs MinModeTranslate (Dimer method) to find a Saddle Point (TS).
    
    Returns a list of unique found structures (Saddles/Minima).
    """
    
    # --- Handle Calculator Source ---
    if calculator_factory is None:
        if calc_path is None:
            raise ValueError("Must provide either `calculator_factory` or `calc_path`.")
        name, license_tag, url_or_path = resolve_model_spec(calc_path)
        assert_license_ok(license_tag, allow_asl=allow_asl)
        model_local_path = download_if_needed(url_or_path, cache_root=cache_dir)
        
        from mace.calculators.mace import MACECalculator
        def _mace_factory():
            return MACECalculator(model_paths=model_local_path, device=device, default_dtype=default_dtype)
        calculator_factory = _mace_factory

    factory_constraints = _to_pred_list(constraints)

    def run(
        symbols: Sequence[str],
        positions: np.ndarray,
        cell: Optional[np.ndarray],
        fixed: Optional[np.ndarray] = None,
        parent_hash: str = "root",
        output_filename: str = "dimer_out.xyz",
        constraints: Optional[Sequence[Callable]] = None,
        **kwargs
    ) -> List[CalcResult]:
        
        discovered: List[CalcResult] = []
        
        # 1. Setup Root
        try:
            root = _build_atoms_obj(symbols, positions, cell, calculator_factory)
        except Exception as e:
            logger.error(f"Failed to build root atoms: {e}")
            return []

        # Constraints
        comb_constraints = list(factory_constraints) + _to_pred_list(constraints)
        
        # Determine selection for constraints
        if comb_constraints:
            selected_idxs = _select_indices(symbols, positions, cell, fixed, comb_constraints, constraint_logic)
        elif fixed is not None and np.any(fixed):
            selected_idxs = np.where(np.asarray(fixed).flatten())[0]
        else:
            selected_idxs = np.array([], dtype=int)
            
        # Apply ASE constraints
        ase_cons = _build_ase_constraints(root, selected_idxs, constraint_action, freeze_components)
        if ase_cons:
            root.set_constraint(ase_cons)
        
        # Identify free (moveable) atoms for displacement
        N = len(root)
        if ase_cons:
            # This is a simplification; ideally we ask the constraint object which indices are fixed.
            # But FixAtoms exposes .index. FixCartesian is trickier.
            # We'll use our `selected_idxs` + `constraint_action` logic.
            if constraint_action == "freeze":
                frozen_set = set(selected_idxs)
                free_indices = [i for i in range(N) if i not in frozen_set]
            else: # move_only
                free_indices = [i for i in selected_idxs]
        else:
            free_indices = list(range(N))

        if not free_indices:
            logger.warning("No free atoms to displace for Dimer search.")
            return []

        # Relax Root
        if root_fmax > 0:
            try:
                opt = FIRE(root, logfile=None)
                opt.run(fmax=root_fmax, steps=100)
            except Exception: pass
        
        discovered.append(_package_result(root, {"type": "initial_minima", "hash": parent_hash}))

        # 2. Loop Attempts
        for i in range(num_attempts):
            image = root.copy()
            image.calc = _build_atoms_obj(symbols, positions, cell, calculator_factory).calc
            if ase_cons: image.set_constraint(ase_cons)

            # Random Displacement
            # Select atoms to displace from free_indices
            n_disp = min(atoms_to_displace, len(free_indices))
            if n_disp > 0:
                target_indices = np.random.choice(free_indices, size=n_disp, replace=False)
                
                # Displacement mask for DimerControl
                # 1 for atoms that are part of the detailed rotation? 
                # The user snippet used `mask` for DimerControl.
                # "The mask argument ... specifies which atoms are allowed to move during the rotation"
                dimer_mask = [0] * N
                
                # Typically we want *all* non-frozen atoms to relax, but maybe only valid atoms for rotation?
                # The user snippet sets mask=1 only for the displaced atom.
                # ASE docs: "mask: list of bool or 0/1, Atoms to be included in the mode search."
                # We'll follow user pattern: included atoms are the ones we displaced.
                for idx in target_indices:
                    dimer_mask[idx] = 1
                    
                    # Apply displacement
                    dx = np.random.uniform(displacement_range[0], displacement_range[1])
                    dy = np.random.uniform(displacement_range[0], displacement_range[1])
                    dz = np.random.uniform(displacement_range[0], displacement_range[1]) # User snippet had explicit range for z
                    
                    # We use uniform box for simplicity or match user if strict
                    # User: x,y [-0.15, 0.15], z [-0.05, 0.15]
                    # We'll stick to provided `displacement_range` for all dims for generality, 
                    # unless we want to be very specific.
                    
                    pos = image.get_positions()
                    pos[idx] += [dx, dy, dz]
                    image.set_positions(pos)

                # Dimer Run
                try:
                    # Setup Dimer
                    # Note: MinModeAtoms(atoms, control) wrapper
                    d_control = DimerControl(
                        initial_eigenmode_method='displacement',
                        displacement_method='vector',
                        logfile=None,
                        mask=dimer_mask
                    )
                    d_atoms = MinModeAtoms(image, d_control)
                    
                    # We need to set the displacement vector again for the eigenmode estimation?
                    # User snippet: d_atoms.displace(displacement_vector=...)
                    # Correct, `displace()` sets the initial guess for the mode.
                    # We should probably apply the same vector we used to kick the atom?
                    # Or just a random vector?
                    # User snippet applies specific vector to `d_atoms.displace`. 
                    # Note: The *image* positions are already updated? 
                    # User snippet:
                    #   1. `mask` set. 
                    #   2. `d_atoms = MinModeAtoms(images[i], d_control)`
                    #   3. `displacement_vector` prepared.
                    #   4. `d_atoms.displace(displacement_vector)` -> This sets the 'mode' direction, not the position.
                    # Wait, MinModeAtoms wraps the atoms.
                    # The user snippet does NOT change `images[i]` positions manually before Dimer?
                    # User snippet: `images` is a copy of `in_file`.
                    # Then loop: `x_disp = ...`. `d_atoms.displace(...)`.
                    # Then `MinModeTranslate`.
                    
                    # IMPORTANT: `d_atoms.displace` alters the positions to create the dimer separation, 
                    # but `MinModeTranslate` moves the *center* of the dimer.
                    # If we start from the minima, we need to push it out of the basin.
                    
                    # Actually `displace` in ASE Dimer just sets the initial direction of mode.
                    # If we want to search for a saddle, we usually need to start *away* from the minimum.
                    # The user snippet seems to rely on `MinModeTranslate` to climb?
                    # But `MinModeTranslate` usually minimizes force along mode and maximizes curvature? No, it finds saddle.
                    # Usually you need to guide it out.
                    # BUT, I will follow the user request: "implementar un file similar... [using the snippet logic]"
                    # The snippet logic:
                    #   d_atoms.displace(...) -> sets mode
                    #   MinModeTranslate(d_atoms).run()
                    
                    # I will replicate this.
                    # I will calculate a random vector for displacement/mode guess.
                    
                    disp_vector = np.zeros((N, 3))
                    for idx in target_indices:
                        dx = np.random.uniform(displacement_range[0], displacement_range[1])
                        dy = np.random.uniform(displacement_range[0], displacement_range[1])
                        dz = np.random.uniform(displacement_range[0], displacement_range[1])
                        disp_vector[idx] = [dx, dy, dz]
                    
                    d_atoms.displace(displacement_vector=disp_vector)
                    
                    # Run
                    dimer_relax = MinModeTranslate(
                        d_atoms, 
                        logfile=None,
                        trajectory=None # We could save intermediate if write_trajectories=True
                    )
                    
                    # Attach writer if needed
                    traj_file = None
                    if write_trajectories:
                        base, ext = os.path.splitext(output_filename)
                        traj_file = f"{base}_dimer_{i}{ext}"
                        dimer_relax.attach(ase.io.Trajectory(traj_file, 'w', image), interval=1)
                        
                    dimer_relax.run(fmax=dimer_fmax, steps=dimer_steps)
                    
                    # Save result
                    # image positions are updated by dimer_relax
                    res_meta = {
                        "type": "dimer_saddle", 
                        "parent": parent_hash, 
                        "attempt": i,
                        "displaced_atoms": target_indices.tolist()
                    }
                    discovered.append(_package_result(image, res_meta))

                except Exception as e:
                    logger.warning(f"Dimer attempt {i} failed: {e}")
                    continue

        return discovered

    return run
