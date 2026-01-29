# Vamos

[![Python](https://img.shields.io/pypi/pyversions/vamos-rl.svg)](https://pypi.org/project/vamos-rl/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Vamos is a JAX-native Reinforcement Learning environment API designed for high-performance parallel execution with a Gymnasium-like interface rebuilt from the ground up to leverage JAX's functional programming paradigm and automatic vectorization.

## Key Features

- **Stateless, Functional Design**: Unlike Gymnasium where state is stored internally, Vamos passes state explicitly as function parameters. This enables seamless composition with JAX transformations (`jit`, `vmap`, `grad`).

- **Gymnasium-Familiar API**: If you know Gymnasium, you'll feel at home. Vamos uses similar concepts (spaces, wrappers, step/reset) adapted for JAX's functional style. Builtin is many of the popular Gymnasium environments, wrappers, and make, which is highly extensible. 

## Installation

```bash
pip install vamos-rl
```

## Quick Start

```python
import jax
import vamos

env, params = vamos.make("CartPole-v1")

# Initialize
rng = jax.random.PRNGKey(0)
timestep, state = env.reset(params, rng)
# the timestep is a dataclass containing your step data (observation, reward, etc)

# Take a step
action = env.action_space.sample(rng)
timestep, state = env.step(state, action, params, rng)

print(f"Observation: {timestep.obs}")
print(f"Reward: {timestep.reward}")
print(f"Episode Over: {timestep.episode_over}")  # this is equal to computing `termination or truncation`
```

## Vectorized Environments

Run multiple environments in parallel with `VMapVectorEnv`:

```python
import jax
import vamos

vec_env, params = vamos.make_vec("CartPole-v1", num_envs=1024)

rng = jax.random.PRNGKey(0)
timestep, state = vec_env.reset(params, rng)  # Get the reset observation and state for all 1024 environments

# Step all 1024 environments simultaneously
actions = vec_env.action_space.sample(rng)  # Shape: (1024,)
timestep, state = vec_env.step(state, actions, params, rng)
```

Vamos offers three strategies to optimize automatically reset sub-environments when episodes end:

- **COMPLETE**: Generate N reset states every step (maximum diversity)
- **OPTIMISTIC**: Generate M << N states, reuse when needed (balanced)
- **PRECOMPUTED**: Pre-generate a pool before training (zero overhead)

See the [vector environment documentation](docs/api/autoreset_modes_and_strategies.md) for details on autoreset modes and strategies.

## Gymnasium vs Vamos

| Aspect               | Gymnasium                      | Vamos                         |
|----------------------|--------------------------------|-------------------------------|
| State management     | Internal (mutable)             | Explicit (functional)         |
| Vectorization        | `SyncVectorEnv` (Python loops) | `vmap` (hardware-accelerated) |
| JIT compilation      | Not supported                  | Native support                |
| Autodiff through env | Not possible                   | Supported via JAX             |
| Parallelism          | Process-based                  | Array-based (GPU/TPU)         |
| Randomness           | Modifiable at Episode Resets   | Selectable at every timestep  |

**Gymnasium style** (stateful):
```python
obs, info = env.reset()
obs, reward, term, trunc, info = env.step(action)
```

**Vamos style** (functional):
```python
timestep, state = env.reset(params, rng)
timestep, state = env.step(state, action, params, rng)
```

## Core Concepts

### Timestep

All environment outputs are bundled in a `Timestep` dataclass:

```python
@struct.dataclass
class Timestep:
    obs: ArrayTree          # Current observation
    reward: float           # Reward from last action
    termination: bool       # Episode ended (goal/failure)
    truncation: bool        # Episode cut off (time limit)
    info: dict              # Additional information

    @property
    def episode_over(self):
        return self.termination or self.truncation
```

### Spaces

Define valid actions and observations:
Vamos supports a significantly more limited set of spaces, just three `Scalar` for individual values like a Discrete set of actions, `Array` for a vector or matrix of data like an image and `Dict` for composing multiple spaces together.

```python
from vamos.spaces import Scalar, Array, Dict

# Discrete action (0, 1, 2, 3, 4)
action_space = Scalar(5)

# Continuous bounded values
obs_space = Array(low=[-1.0, -1.0], high=[1.0, 1.0])

# Composite spaces
space = Dict({"position": Array(...), "velocity": Array(...)})
```

### Wrappers

Compose environment modifications:

```python
from vamos.wrappers.time_limit import TimeLimit

env, params = CartPoleEnv.new()
env, params = TimeLimit.wrap(env, params, max_episode_steps=500)
```

## License

MIT License
