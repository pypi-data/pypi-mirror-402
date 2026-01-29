# Synth-Fuse ⚡ ALCHEM-J

 *“Every algorithm is a plugin; every fusion is a pipeline; every pipeline is a JAX transform.”*

[![PyPI](https://img.shields.io/pypi/v/synthfuse)](https://pypi.org/project/synthfuse/)
[![Python](https://img.shields.io/pypi/pyversions/synthfuse)](https://pypi.org/project/synthfuse/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue) 
[![DOI](https://zenodo.org/badge/1136013621.svg)](https://doi.org/10.5281/zenodo.18289083)

Synth-Fuse is a **JAX-native fusion engine** that composes **swarm intelligence**, **reinforcement learning**, and **numerical algorithms** into a **single, differentiable, hardware-scalable execution graph**—written as **one-line spells**.

---

## ⚡ 30-Second Demo

``` bash
pip install synthfuse
alj
>>> (𝕀 ⊗ 𝕃(alpha=1.5) ⊗ ℂ(r=3.8))
>>> run 100
```

| Stage | Primitive | Meaning               |
| ----- | --------- | --------------------- |
| `𝕀`  | ISO/RIME  | Swarm exploration     |
| `𝕃`  | Lévy      | Heavy-tailed jumps    |
| `ℂ`   | Chaos     | Adaptive perturbation |
### One-liner Benchmarks

``` bash
# Continuous optimisation
uv run sfbench "(𝕀 ⊗ 𝕃(alpha=1.5))" --bench rastrigin --dims 1000 --steps 5000

# Combinatorial
uv run sfbench "𝕎 ⊗ ℍ" --bench tsp-200 --pop 256

# Live telemetry
uv run sfmonitor --recipe fql_rime --steps 500

```

## 🧪 Pre-Built Recipes (import → JIT)

``` python
from synthfuse.recipes import fql_rime, mrbmo_ppo, ns2uo, ntep, stcl

step, state = fql_rime.make(dims=1000, pop=512)
```

| Recipe        | Spell               | Use-Case                         |
| ------------- | ------------------- | -------------------------------- |
| **FQL-RIME**  | `(𝔽𝕃 ⊗ 𝕃 ⊗ ℝ𝔽)` | Flow-guided Lévy + PPO           |
| **MRBMO-PPO** | `(𝕊𝕄 ∘ 𝜑 ⊗ ℝ𝕄)` | Siege-elite PPO                  |
| **NS²UO**     | `(𝕊𝕨 ⊗ 𝕆𝕊)`     | Neuro-Swarm-to-Universal-Opt     |
| **NTEP**      | `(𝕎 ⊗ 𝕀𝕋)`       | Neural Tool-Embedding Protocol   |
| **STCL**      | `(𝕊𝕋 ⊗ 𝕎)`       | Semantic-Thermo Compression Loop |
## 📦 Install

``` bash
# stable
pip install synthfuse

# dev speed-run
curl -LsSf https://astral.sh/uv/install.sh | sh
uv pip install synthfuse[dev]
```

## 🪄 Spell Language (ALCHEM-J)

| Symbol | Primitive     | Meaning                     |
| ------ | ------------- | --------------------------- |
| `𝕀`   | ISO/RIME      | Swarm update                |
| `ℝ`    | PPO/A2C/DQN   | RL policy                   |
| `𝕃`   | Lévy          | Heavy-tailed noise          |
| `𝕊`   | SVD-UKF       | Low-rank stabiliser         |
| `𝕎`   | Weierstrass   | Semantic gravity field      |
| `ℂ`    | Chaos         | Adaptive perturbation       |
| `𝜑`   | Meta-gradient | Natural-gradient correction |
Compose via **pure combinators**:

- `⊗` – sequential fusion
    
- `⊕` – parallel fusion
    
- `∘` – conditional fusion

Example spell:
``` python
"(𝕎 ⊗ 𝕊𝕋 ⊗ ℍ)(sigma=0.7, halt=cos<0.01)"
```

## 🧰 CLI Tools

| Tool          | Command                     | Purpose                   |
| ------------- | --------------------------- | ------------------------- |
| **REPL**      | `alj`                       | Interactive spell casting |
| **Benchmark** | `sfbench <spell>`           | Standardised perf tests   |
| **Monitor**   | `sfmonitor --recipe <name>` | Live telemetry dashboard  |
| **Visualise** | `sfviz "<spell>" -f svg`    | Spell → SVG / HTML        |
## 🏗️ Adding Your Own Primitive


``` python
# alchemj/plugins/my_step.py
from synthfuse.alchemj.registry import register
import jax
import jax.numpy as jnp

@register("𝕏")
def my_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """One-sentence purpose. Failure: alpha<0 → divergence; caught by CI."""
    alpha = params.get("alpha", 1.0)
    return state.replace(x=state.x + alpha * jax.random.normal(key, state.x.shape))
```

Micro-bench in `tests/test_my_step.py` → open PR → **fast-merge**.

------------
## 🧪 Emergent Behaviours (observed & bounded)

| Behaviour                    | Mechanism             | Control Signal          |
| ---------------------------- | --------------------- | ----------------------- |
| Spontaneous decentralisation | consensus dominance   | modularity Q ≥ 0.3      |
| Crosstalk-free routing       | zeta pole separation  | σ\_zeta gradient        |
| Thermal self-balancing       | Hamiltonian heat term | κ ≤ max-current-density |
| Topology-safe compression    | semantic load Λ ≥ τ   | rollback if Λ < τ       |
| Single-shot convergence      | Weierstrass smoothing | σ\_min clamp            |

## 🔐 Security & Safety

- **Pure functions only** – no side-effects inside step.
    
- **Sandboxed execution** – external I/O outside JIT.
    
- **Checkpoint every 15 min** – rollback < 30 s.
    
- **Formal verification hooks** exported for external provers.

## 📜 Citation

``` bibitex
@software{synthfuse2026,
  author = {Jimenez, J. Roberto and K2, Kimi},
  title = {Synth-Fuse: A Modular Fusion Library for Hybrid Swarm–RL–Numerical Intelligence},
  url = {https://github.com/deskiziarecords/synthfuse},
  version = {0.1.0-alpha},
  date = {2026-01-17},
  license = {Apache-2.0}
}
```

--------
## Support Me

 If you would like to support the development of these resources, consider contributing towards helping me get some gear for continued improvement or simply treating me to a coffee. Your support means a lot!" 
 [buy me a coffee](buymeacoffee.com/hipotermiah)
 
-----------
## 🤝 Contributing

We treat PRs like **spells**: **pure**, **composable**, **JIT-ready**.  
Read [CONTRIBUTING.md](https://www.kimi.com/chat/CONTRIBUTING.md) → open issue/PR → **fast-merge**.

-----
## 💬 Community

- **Matrix**: `#synthfuse:matrix.org`
    
- **Discussions**: GitHub Discussions tab
    
- **Email**: [tijuanapaint@gmail.com](mailto:tijuanapaint@gmail.com) | [kimi@moonshot.cn](mailto:kimi@moonshot.cn)

**Welcome to the fusion – cast your spell.**

