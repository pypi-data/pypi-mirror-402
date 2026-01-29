# Examples & Verification Scripts

This directory contains various scripts to verify, benchmark, and demonstrate the capabilities of the Evolutionary Structure Explorer (`ezga`).

## Basic GA (Numeric Optimization)
These scripts test the standard Genetic Algorithm on numerical benchmarks (finding x,y coordinates).

- **`verify_simple_api.py`**: Minimal example of setting up a numeric optimization problem (Sphere).
- **`verify_simple_fast.py`**: A faster, slightly more visual version of the basic verification (plots results).
- **`verify_simple_rastrigin.py`**: Tests the GA on the **Rastrigin Function**, a difficult multimodal benchmark with many local minima. Visualizes convergence.
- **`verify_simple_doe_bo.py`**: Demonstrates the **Hybrid GA**: using Latin Hypercube Sampling (LHS) for initialization and Bayesian Optimization (BO) for candidate injection.
- **`compare_bo.py`**: A side-by-side comparison script (created during debugging) to measure the impact of enabling BO vs pure GA on simple functions.

## Symbolic Regression (Tree Evolution)
These scripts test the Symbolic Regression capabilities (evolving mathematical formulas).

- **`verify_simple_symbolic_regression.py`**: Simple proof-of-concept. Attempts to rediscover a basic curve (e.g., `y = 2.5*x + 5`). Includes Memetic Optimization (constant tuning).
- **`verify_complex_rules.py`**: Advanced example. Attempts to discover complex logical rules (e.g., `(A > 0.5) AND (B < 0.3)`). Includes logic for **Parsimony Pressure** and **Rule Pruning**.
- **`pruning_utils.py`**: Helper library containing the logic for simplifying and pruning symbolic trees (used by `verify_complex_rules.py`).
- **`verify_negative_hypothesis.py`**: Targeted test to check if the system can learn rules involving negations (e.g., `NOT(A)`).

## Grammatical Evolution (GE)
These scripts test the Grammatical Evolution engine (mapping integer vectors to structures via BNF grammars).

- **`verify_ge.py`**: Main verification for GE. Defines a grammar for signal logic and tests the Genotype-to-Phenotype mapping process.
- **`verify_ge_components.py`**: Lower-level unit tests for specific GE components (Mapper, Grammar class).
