"""Environment verification utilities."""

import chex
import jax
import jax.numpy as jnp

from vamos.env import Env, Timestep, EnvState, EnvParams
from vamos.spaces import Space


def check_env(
    env: Env,
    params: EnvParams | None = None,
    num_steps: int = 10,
    check_jit: bool = True,
) -> None:
    """Verify that an environment implementation is correct.

    Checks that:
    - The environment has valid action_space and observation_space
    - reset() returns the correct types (Timestep, EnvState)
    - Observations from reset are contained in observation_space
    - step() returns the correct types (Timestep, EnvState)
    - Observations from step are contained in observation_space
    - Timestep fields have correct types (reward, termination, truncation)
    - reset() and step() can be JIT compiled without recompilation (if check_jit=True)

    Args:
        env: The environment to check.
        params: Optional parameters to pass to the environment, otherwise `get_default_params` is used.
        num_steps: Number of steps to run for verification. Defaults to 10.
        check_jit: Whether to verify JIT compilation of the environment's reset and step
            works without recompilation. Defaults to True.

    Raises:
        AssertionError: If any verification check fails.
    """
    # Check that env has required spaces
    assert isinstance(env.action_space, Space), "action_space must be a Space"
    assert isinstance(env.observation_space, Space), "observation_space must be a Space"

    if params is None:
        params = env.get_default_params()

    # Test reset
    reset_result = env.reset(params, jax.random.PRNGKey(0))
    assert isinstance(reset_result, tuple), "reset must return a tuple"
    assert len(reset_result) == 2, "reset must return (Timestep, EnvState)"
    timestep, state = reset_result

    # Check Timestep and EnvState from reset
    assert isinstance(timestep, Timestep), "First element of reset must be Timestep"
    check_timestep(timestep, env.observation_space)
    assert isinstance(state, EnvState), "Second element of reset must be EnvState"

    # Test step multiple times
    rng = jax.random.PRNGKey(1)
    for _ in range(num_steps):
        rng, action_rng, step_rng = jax.random.split(rng, 3)

        action = env.action_space.sample(action_rng)
        step_result = env.step(state, action, params, step_rng)

        assert isinstance(step_result, tuple), "step must return a tuple"
        assert len(step_result) == 2, "step must return (Timestep, EnvState)"
        timestep, state = step_result

        # Check Timestep and EnvState from step
        assert isinstance(timestep, Timestep), "First element of step must be Timestep"
        check_timestep(timestep, env.observation_space)
        assert isinstance(state, EnvState), "Second element of step must be EnvState"

    # Test JIT compilation
    if check_jit:
        check_jit_compilation(env, params, num_steps=3)


def check_timestep(timestep: Timestep, observation_space: Space) -> None:
    """Check that a Timestep has valid fields and types.

    Args:
        timestep: The timestep to check.
        observation_space: The observation space to validate observations against.

    Raises:
        AssertionError: If any check fails.
    """
    assert observation_space.contains(timestep.obs), (
        f"Observation {timestep.obs} must be contained in observation_space"
    )

    # Check reward is a scalar array
    reward = timestep.reward
    assert isinstance(reward, (jax.Array, jnp.ndarray, float, int)), (
        f"reward must be array-like, got {type(reward)}"
    )
    if isinstance(reward, (jax.Array, jnp.ndarray)):
        assert reward.shape == () or reward.shape == (1,), (
            f"reward must be scalar, got shape {reward.shape}"
        )

    # Check termination is boolean-like
    termination = timestep.termination
    assert isinstance(termination, (jax.Array, jnp.ndarray, bool)), (
        f"termination must be array-like or bool, got {type(termination)}"
    )
    if isinstance(termination, (jax.Array, jnp.ndarray)):
        assert termination.shape == () or termination.shape == (1,), (
            f"termination must be scalar, got shape {termination.shape}"
        )

    # Check truncation is boolean-like
    truncation = timestep.truncation
    assert isinstance(truncation, (jax.Array, jnp.ndarray, bool)), (
        f"truncation must be array-like or bool, got {type(truncation)}"
    )
    if isinstance(truncation, (jax.Array, jnp.ndarray)):
        assert truncation.shape == () or truncation.shape == (1,), (
            f"truncation must be scalar, got shape {truncation.shape}"
        )

    # Check info is a dict
    assert isinstance(timestep.info, dict), (
        f"info must be a dict, got {type(timestep.info)}"
    )


def check_jit_compilation(env: Env, params, num_steps: int = 10) -> None:
    """Check that reset and step can be JIT compiled without recompilation.

    This verifies that the environment functions are properly written for JAX
    tracing and don't cause recompilation on subsequent calls.

    Args:
        env: The environment to check.
        params: Environment parameters.
        num_steps: Number of steps to run to verify no recompilation.

    Raises:
        AssertionError: If recompilation is detected.
    """
    chex.clear_trace_counter()

    @jax.jit
    @chex.assert_max_traces(n=1)
    def reset_fn(reset_params, reset_rng):
        return env.reset(reset_params, reset_rng)

    @jax.jit
    @chex.assert_max_traces(n=1)
    def step_fn(step_state, step_action, step_params, step_rng):
        return env.step(step_state, step_action, step_params, step_rng)

    rng = jax.random.PRNGKey(42)

    # First call triggers compilation, subsequent calls should not recompile
    state = None
    for _ in range(num_steps + 1):
        rng, _reset_rng = jax.random.split(rng)
        timestep, state = reset_fn(params, _reset_rng)

    # Test step compilation
    for _ in range(num_steps + 1):
        rng, action_rng, _step_rng = jax.random.split(rng, 3)
        action = env.action_space.sample(action_rng)
        timestep, state = step_fn(state, action, params, _step_rng)
