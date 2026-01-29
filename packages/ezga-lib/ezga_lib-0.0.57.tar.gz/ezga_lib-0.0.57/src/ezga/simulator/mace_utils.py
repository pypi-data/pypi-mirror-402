from __future__ import annotations

import os
import urllib.request
from pathlib import Path
from typing import Optional, Union, Dict, Tuple

# --- Optional: use MACE's cache helper if available, else fallback ---
try:
    from mace.tools.utils import get_cache_dir
except Exception:
    def get_cache_dir() -> str:
        cache = os.path.join(os.path.expanduser("~"), ".cache", "mace")
        os.makedirs(cache, exist_ok=True)
        return cache

# -------------------------
# Registry of known models
# -------------------------
# Extend as needed; keep license tags accurate.
_MODEL_REGISTRY: Dict[str, Dict[str, str]] = {
    # MIT (safe to auto-download or vendor)
    "mpa-0-medium": {
        "url": "https://github.com/ACEsuit/mace-mp/releases/download/mace_mpa_0/mace-mpa-0-medium.model",
        "license": "MIT",
    },
    "mp-0b3-medium": {
        "url": "https://github.com/ACEsuit/mace-mp/releases/download/mace_mp_0b3/mace-mp-0b3-medium.model",
        "license": "MIT",
    },
    # ASL (Academic Software License; non-commercial; explicit consent required)
    "omat-0-small": {
        "url": "https://github.com/ACEsuit/mace-mp/releases/download/mace_omat_0/mace-omat-0-small.model",
        "license": "ASL",
    },
    "omat-0-medium": {
        "url": "https://github.com/ACEsuit/mace-mp/releases/download/mace_omat_0/mace-omat-0-medium.model",
        "license": "ASL",
    },
    "matpes-pbe-0": {
        "url": "https://github.com/ACEsuit/mace-foundations/releases/download/mace_matpes_0/MACE-matpes-pbe-omat-ft.model",
        "license": "ASL",
    },
    "matpes-r2scan-0": {
        "url": "https://github.com/ACEsuit/mace-foundations/releases/download/mace_matpes_0/MACE-matpes-r2scan-omat-ft.model",
        "license": "ASL",
    },
    "off23-medium": {
        "url": "https://github.com/ACEsuit/mace-off/raw/main/mace_off23/MACE-OFF23_medium.model?raw=true",
        "license": "ASL",
    },
}

def resolve_model_spec(spec: Optional[Union[str, Path]]) -> Tuple[str, str, str]:
    """
    Resolve user spec into (name_or_path, license, url_or_path).

    Rules:
      - None -> default "mpa-0-medium" (MIT)
      - existing local path -> ("<path>", "LOCAL", "<path>")
      - http(s) URL -> ("<url>", "UNKNOWN", "<url>")
      - registry key -> ("<key>", license, url)
      - else -> error
    """
    if spec is None:
        entry = _MODEL_REGISTRY["mpa-0-medium"]
        return "mpa-0-medium", entry["license"], entry["url"]

    s = str(spec)
    p = Path(s)
    if p.exists() and p.is_file():
        return s, "LOCAL", s

    if s.startswith("http://") or s.startswith("https://"):
        return s, "UNKNOWN", s

    if s in _MODEL_REGISTRY:
        entry = _MODEL_REGISTRY[s]
        return s, entry["license"], entry["url"]

    # If user left the old default 'MACE_model.model' and it doesn't exist,
    # choose a sensible default instead of failing hard.
    if s == "MACE_model.model":
        entry = _MODEL_REGISTRY["mpa-0-medium"]
        return "mpa-0-medium", entry["license"], entry["url"]

    raise ValueError(
        f"Unrecognized model spec '{spec}'. Provide a local file, a URL, or one of: "
        + ", ".join(sorted(_MODEL_REGISTRY.keys()))
    )

def assert_license_ok(license_tag: str, allow_asl: bool) -> None:
    if license_tag != "ASL":
        return
    accepted_env = os.environ.get("MACE_ACCEPT_ASL", "") == "1"
    if not (allow_asl or accepted_env):
        raise RuntimeError(
            "Requested model is under the Academic Software License (ASL). "
            "To proceed, pass allow_asl=True to mace_calculator(...) or set environment "
            "variable MACE_ACCEPT_ASL=1. Ensure your usage complies with ASL (non-commercial)."
        )

def download_if_needed(url_or_path: str, cache_root: Optional[str] = None) -> str:
    """Return a local path; download into cache if given a URL."""
    if url_or_path.startswith("http://") or url_or_path.startswith("https://"):
        cache = cache_root or get_cache_dir()
        os.makedirs(cache, exist_ok=True)
        fname = os.path.basename(url_or_path.split("?")[0]) or "mace.model"
        dest = os.path.join(cache, fname)
        if not os.path.isfile(dest):
            print(f"Downloading MACE checkpoint from: {url_or_path}")
            tmp = dest + ".part"
            urllib.request.urlretrieve(url_or_path, tmp)
            os.replace(tmp, dest)
            print(f"Saved checkpoint to: {dest}")
        return dest
    # local path
    if not Path(url_or_path).exists():
        raise FileNotFoundError(f"Model file not found: {url_or_path}")
    return url_or_path
