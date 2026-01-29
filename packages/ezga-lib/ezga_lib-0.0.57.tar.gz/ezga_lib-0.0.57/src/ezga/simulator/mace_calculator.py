from __future__ import annotations

import os
import urllib.request
from pathlib import Path
from typing import Optional, Union, Dict, Tuple

from .ase_calculator import ase_calculator

from .ase_calculator import ase_calculator
from .mace_utils import (
    resolve_model_spec,
    assert_license_ok,
    download_if_needed,
    get_cache_dir,  # optional if needed explicitly, but mace_utils handles it
)



def mace_calculator(
    calc_path: str = 'MACE_model.model',

    device: str = 'cuda',
    default_dtype: str = 'float32',
    enable_cueq: bool = False,

    # --- Stage 1: MD / relaxation controls ---
    nvt_steps: Union[int, Sequence[float], None] = None,

    # --- Stage 2: relaxation controls ---
    fmax: Union[float, Sequence[float], None] = 0.05,
    steps_max: int = 100,
    hydrostatic_strain: bool = False,
    constant_volume: bool = True,
    optimizer: str = 'FIRE',

    # --- temperature schedules ---
    T: Union[float, Sequence[float]] = 300.0,
    T_ramp: bool = False,  # reserved for future use
    # --- timestep (fs) for the MD integrator ---
    md_timestep_fs: float = 1.0,

    # --- vibrational correction controls ---
    vib_correction: bool = False,
    vib_store_interval: int = 1,
    vib_min_samples: int = 200,
    remove_com_drift: bool = False,
    mass_weighted_com: bool = True,
    vacf_window: str = "hann",

    # --- logging / IO performance knobs ---
    log_interval: int = 0,          # 0 disables printing; otherwise print every k steps
    write_interval: int = 0,        # trajectory write every k steps; set 0 to disable during MD

    # --- constraint controls ---
    constraint_logic: str = "all",
    constraint_action: str = "freeze",
    freeze_components: Optional[Sequence[Union[int, str]]] = None,
    constraints: Optional[Sequence[Callable]] = None,

    # --- Stage 0: pre-MD relaxation controls ---
    pre_relax_fmax: Union[float, Sequence[float], None] = None,
    pre_relax_steps_max: int = 0,
    pre_relax_optimizer: str = 'FIRE',
    pre_relax_constant_volume: bool = True,
    pre_relax_hydrostatic_strain: bool = False,
    pre_relax_with_constraints: bool = True,

    # --- vibrational spectrum controls ---
    vib_spectrum: bool = False,
    vib_spectrum_max_lag: int = None,
    vib_spectrum_cutoff_cm1: float = 3200.0,
    vib_spectrum_mode: str = "total",   # 'total' | 'atom' | 'element' | 'all'

    # --- new optional knobs ---
    allow_asl: bool = False,         # require explicit acceptance for ASL models
    cache_dir: Optional[str] = None, # override cache directory if desired
):
    r"""
    Create an ASE calculator that uses a MACE model specified by *either*:
      - a local file path to a .model,
      - a direct URL (http/https), or
      - a registry model name (e.g., "mpa-0-medium", "mp-0b3-medium", "omat-0-medium").

    If a name/URL is provided, the model is downloaded (once) into a cache and the
    resolved local path is passed to MACECalculator(model_paths=...).

    Parameters (selected)
    ---------------------
    calc_path : str
        Path, URL, or registry key. Default keeps backward compatibility.
        If it is the legacy default ('MACE_model.model') and the file is missing,
        it falls back to 'mpa-0-medium' (MIT).
    allow_asl : bool
        Required to load ASL-licensed models (OMAT/MATPES/OFF/…).
        Alternatively set environment variable MACE_ACCEPT_ASL=1.
    cache_dir : str | None
        Custom cache directory for downloaded models.

    Other parameters are forwarded to your ase_calculator wrapper unchanged.
    """
    # Resolve spec (name/path/url) and enforce license where applicable
    # Resolve spec (name/path/url) and enforce license where applicable
    name, license_tag, url_or_path = resolve_model_spec(calc_path)
    assert_license_ok(license_tag, allow_asl=allow_asl)

    # Ensure we have a local file we can feed to MACECalculator
    model_local_path = download_if_needed(url_or_path, cache_root=cache_dir)

    # Lazy import to keep import time light
    from mace.calculators.mace import MACECalculator

    calculator = MACECalculator(
        model_paths=model_local_path,
        device=device,
        default_dtype=default_dtype,
        enable_cueq=enable_cueq,
    )

    return ase_calculator(
        calculator=calculator,
        device=device,
        default_dtype=default_dtype,

        # --- Stage 1: MD / relaxation controls ---
        nvt_steps=nvt_steps,

        # --- Stage 2: relaxation controls ---
        fmax=fmax,
        steps_max=steps_max,
        hydrostatic_strain=hydrostatic_strain,
        constant_volume=constant_volume,
        optimizer=optimizer,

        # --- temperature schedules ---
        T=T,
        T_ramp=T_ramp,
        # --- timestep (fs) for the MD integrator ---
        md_timestep_fs=md_timestep_fs,
        # --- vibrational correction controls ---
        vib_correction      =   vib_correction,
        vib_store_interval  =   vib_store_interval,     # record every k MD steps -> effective dt = k * md_timestep_fs
        vib_min_samples     =   vib_min_samples,      # need at least this many stored samples to compute spectrum
        remove_com_drift    =   remove_com_drift,   # remove COM velocity before storing
        mass_weighted_com   =   mass_weighted_com,  # COM uses masses if True; else arithmetic mean
        vacf_window         =   vacf_window,

        # --- logging / IO performance knobs ---
        log_interval = log_interval,          # 0 disables printing; otherwise print every k steps
        write_interval = write_interval,        # trajectory write every k steps; set 0 to disable during MD

        # --- constraint controls ---
        constraint_logic=constraint_logic,
        constraint_action=constraint_action,
        freeze_components=freeze_components,
        constraints=constraints,

        # --- Stage 0: pre-MD relaxation controls ---
        pre_relax_fmax = pre_relax_fmax,
        pre_relax_steps_max = pre_relax_steps_max,
        pre_relax_optimizer = pre_relax_optimizer,
        pre_relax_constant_volume = pre_relax_constant_volume,
        pre_relax_hydrostatic_strain = pre_relax_hydrostatic_strain,
        pre_relax_with_constraints = pre_relax_with_constraints,

        # --- vibrational spectrum controls ---
        vib_spectrum=vib_spectrum,
        vib_spectrum_max_lag=vib_spectrum_max_lag,
        vib_spectrum_cutoff_cm1=vib_spectrum_cutoff_cm1,
        vib_spectrum_mode=vib_spectrum_mode,   # 'total' | 'atom' | 'element' | 'all'

    )

