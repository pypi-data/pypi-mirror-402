from __future__ import annotations

from typing import Any

import chex
import jax
import jax.numpy as jnp
from flax import struct

from vamos.env import Timestep, EnvParams, EnvState
from vamos.vector import VectorEnv, AutoresetMode, AutoresetStrategy
from vamos import Env


@struct.dataclass
class VectorEnvState:
    """Wrapper state for vectorized environments.

    This wraps the underlying sub-environment states and adds metadata
    needed for autoreset handling.

    Attributes:
        env_state: The batched sub-environment states.
        episode_over: Boolean array indicating which environments just ended
            (terminated or truncated). For NEXT_STEP mode, this signals that
            the next step should return reset obs/state instead of stepping.
    """

    env_state: EnvState
    episode_over: chex.Array


class VMapVectorEnv(VectorEnv):
    """Vectorized environment using JAX vmap for parallel execution.

    This class wraps a single environment and uses jax.vmap to execute multiple
    instances in parallel. It handles autoreset behavior when episodes terminate,
    with configurable modes and strategies.

    Attributes:
        env: The underlying single environment.
        num_envs: Number of parallel environment instances.
        autoreset_mode: When resets occur (NEXT_STEP or SAME_STEP).
        autoreset_strategy: How reset states are computed (COMPLETE, OPTIMISTIC,
            or PRECOMPUTED).
        optimistic_num_resets: For OPTIMISTIC strategy, number of reset states
            to generate per step. Must be <= num_envs.
        precomputed_states: For PRECOMPUTED strategy, pre-generated reset states.
    """

    def __init__(
        self,
        env: Env,
        *,
        num_envs: int,
        autoreset_mode: AutoresetMode = AutoresetMode.NEXT_STEP,
        autoreset_strategy: AutoresetStrategy = AutoresetStrategy.COMPLETE,
        optimistic_num_resets: int | None = None,
        precomputed_states: tuple[Timestep, EnvState] | None = None,
    ):
        """Initialize the vectorized environment.

        Args:
            env: The single environment to vectorize.
            num_envs: Number of parallel environment instances.
            autoreset_mode: When resets occur relative to termination.
            autoreset_strategy: How reset states are computed.
            optimistic_num_resets: For OPTIMISTIC strategy, number of reset
                states per step. Required if autoreset_strategy is OPTIMISTIC.
            precomputed_states: For PRECOMPUTED strategy, a pre-generated
                (timestep, state) tuple with shape (num_precomputed_states, ...).
                Use `VMapVectorEnv.precomputed_states(env, num_precomputed_states)`
                for easily generating this.
        """
        self.env = env
        self.num_envs = num_envs

        self.single_action_space = env.action_space
        self.single_observation_space = env.observation_space
        self.action_space = env.action_space.vmap(num_envs)
        self.observation_space = env.observation_space.vmap(num_envs)

        self.autoreset_mode = autoreset_mode
        self.autoreset_strategy = autoreset_strategy
        self.optimistic_num_resets = optimistic_num_resets

        # Validate strategy-specific requirements
        if autoreset_strategy == AutoresetStrategy.OPTIMISTIC:
            if optimistic_num_resets is None:
                raise ValueError(
                    "optimistic_num_resets must be provided for autoreset_strategy=OPTIMISTIC"
                )
            if optimistic_num_resets > num_envs:
                raise ValueError(
                    f"optimistic_num_resets ({optimistic_num_resets}) cannot exceed num_envs ({num_envs})"
                )

        if autoreset_strategy == AutoresetStrategy.PRECOMPUTED:
            if precomputed_states is None:
                raise ValueError(
                    "precomputed_states must be provided for autoreset_strategy=PRECOMPUTED"
                )

            # Get number of precomputed states from first leaf
            self.precomputed_states = precomputed_states
            first_leaf = jax.tree.leaves(precomputed_states[1])[0]
            self.num_precomputed_states = first_leaf.shape[0]
        else:
            if precomputed_states is not None:
                raise ValueError(
                    f"The autoreset_strategy is {autoreset_strategy} not precomputed_state is not None ({precomputed_states})"
                )

            self.precomputed_states = None
            self.num_precomputed_states = 0

        # Create vmapped functions (assumes that the environment params are static)
        self._vmapped_reset = jax.vmap(env.reset, in_axes=(None, 0))
        self._vmapped_step = jax.vmap(env.step, in_axes=(0, 0, None, 0))

    def reset(
        self, params: EnvParams, rng: chex.PRNGKey
    ) -> tuple[Timestep, VectorEnvState]:
        """Reset all environment instances.

        For PRECOMPUTED strategy, this selects from precomputed states using
        modulo indexing. For other strategies, new states are generated.

        Args:
            params: Environment parameters (shared across all instances).
            rng: JAX random key for stochastic initialization.

        Returns:
            A tuple containing:
                - timestep: Batched Timestep with shape (num_envs, ...).
                - state: VectorEnvState wrapping the batched environment states.
        """
        if self.autoreset_strategy == AutoresetStrategy.PRECOMPUTED:
            # Randomly select from the precomputed timesteps and states
            precomputed_timesteps, precomputed_states = self.precomputed_states
            indices = jax.random.randint(
                rng, (self.num_envs,), 0, self.num_precomputed_states
            )
            timesteps = jax.tree.map(lambda x: x[indices], precomputed_timesteps)
            env_states = jax.tree.map(lambda x: x[indices], precomputed_states)
        else:
            # Generate fresh states for all environments (even for OPTIMISTIC autoreset strategy)
            rngs = jax.random.split(rng, self.num_envs)
            timesteps, env_states = self._vmapped_reset(params, rngs)

        # Wrap in VectorEnvState with episode_over=False (no episode has ended yet)
        state = VectorEnvState(
            env_state=env_states,
            episode_over=jnp.zeros(self.num_envs, dtype=jnp.bool_),
        )

        return timesteps, state

    def step(
        self,
        state: VectorEnvState,
        action: chex.ArrayTree,
        params: EnvParams,
        rng: chex.PRNGKey,
    ) -> tuple[Timestep, VectorEnvState]:
        """Perform one step in all environment instances.

        Handles autoreset based on the configured mode and strategy:
        - NEXT_STEP mode: When episodes end, terminal obs/state is returned. On the
            following step, reset obs/state is returned (the action is ignored).
        - SAME_STEP mode: When episodes end, the environment immediately resets and
            returns initial obs. The final observations are in info["final_obs"].
            The terminal state is never returned.

        Strategies control how reset states are generated:
        - COMPLETE: Generate N unique reset states (one per sub-environment)
        - OPTIMISTIC: Generate M << N reset states, reuse via modulo indexing
        - PRECOMPUTED: Use pre-generated pool of reset states

        Args:
            state: VectorEnvState containing batched environment states.
            action: Batched actions of shape (num_envs, ...).
            params: Environment parameters (shared across all instances).
            rng: JAX random key for stochastic transitions.

        Returns:
            A tuple containing:
                - timestep: Batched Timestep with observations, rewards, etc.
                - state: Updated VectorEnvState.
        """
        # Split RNG for step and potential reset operations
        rng, step_rng, reset_rng = jax.random.split(rng, 3)
        step_rngs = jax.random.split(step_rng, self.num_envs)

        # Vectorized step over all environments
        step_timesteps, new_env_states = self._vmapped_step(
            state.env_state, action, params, step_rngs
        )

        episode_over = step_timesteps.episode_over

        # Helper to select values based on a mask
        def make_select_fn(mask: chex.Array):
            def select_fn(falsy_val: chex.Array, truthy_val: chex.Array) -> chex.Array:
                broadcast_mask = jnp.reshape(mask, (-1,) + (1,) * (falsy_val.ndim - 1))
                return jax.lax.select(broadcast_mask, truthy_val, falsy_val)

            return select_fn

        select_episode_over = make_select_fn(episode_over)

        # Helper to index into a pytree
        def index_pytree(pytree: Any, indices: chex.Array) -> Any:
            return jax.tree.map(lambda x: x[indices], pytree)

        # Generate reset states based on strategy
        if self.autoreset_strategy == AutoresetStrategy.COMPLETE:
            reset_rngs = jax.random.split(reset_rng, self.num_envs)
            reset_timesteps, reset_states = self._vmapped_reset(params, reset_rngs)

        elif self.autoreset_strategy == AutoresetStrategy.OPTIMISTIC:
            reset_rngs = jax.random.split(reset_rng, self.optimistic_num_resets)
            reset_timesteps_m, reset_states_m = self._vmapped_reset(params, reset_rngs)
            indices = jnp.arange(self.num_envs) % self.optimistic_num_resets
            reset_timesteps = index_pytree(reset_timesteps_m, indices)
            reset_states = index_pytree(reset_states_m, indices)

        elif self.autoreset_strategy == AutoresetStrategy.PRECOMPUTED:
            precomputed_timesteps, precomputed_states = self.precomputed_states
            indices = jnp.arange(self.num_envs) % self.num_precomputed_states
            reset_timesteps = index_pytree(precomputed_timesteps, indices)
            reset_states = index_pytree(precomputed_states, indices)

        else:
            raise ValueError(f"Unknown autoreset strategy: {self.autoreset_strategy}")

        # Handle autoreset based on mode
        if self.autoreset_mode == AutoresetMode.SAME_STEP:
            # Store terminal observations before replacing with reset obs
            final_obs = step_timesteps.obs

            # Use reset obs/states for environments where episode ended
            new_obs = jax.tree.map(
                select_episode_over, step_timesteps.obs, reset_timesteps.obs
            )
            new_env_states = jax.tree.map(
                select_episode_over, new_env_states, reset_states
            )

            # Store final_obs in info
            new_info = step_timesteps.info
            new_info["final_obs"] = final_obs
            step_timesteps = step_timesteps.replace(obs=new_obs, info=new_info)

            # episode_over tracks which environments just ended this step
            new_episode_over = episode_over

        else:
            # NEXT_STEP mode: handle envs that ended on the previous step
            # For those envs, return reset obs/state instead of step results
            prev_episode_over = state.episode_over
            select_prev_over = make_select_fn(prev_episode_over)

            # Replace step results with reset results for envs that need reset
            new_obs = jax.tree.map(
                select_prev_over, step_timesteps.obs, reset_timesteps.obs
            )
            new_env_states = jax.tree.map(
                select_prev_over, new_env_states, reset_states
            )

            # For envs that just reset, clear termination/truncation and set zero reward
            new_termination = jax.tree.map(
                select_prev_over,
                step_timesteps.termination,
                jnp.zeros(self.num_envs, dtype=jnp.bool_),
            )
            new_truncation = jax.tree.map(
                select_prev_over,
                step_timesteps.truncation,
                jnp.zeros(self.num_envs, dtype=jnp.bool_),
            )
            new_reward = jax.tree.map(
                select_prev_over,
                step_timesteps.reward,
                jnp.zeros(self.num_envs, dtype=step_timesteps.reward.dtype),
            )

            step_timesteps = step_timesteps.replace(
                obs=new_obs,
                termination=new_termination,
                truncation=new_truncation,
                reward=new_reward,
            )

            # episode_over is True only for envs that ended THIS step (not ones that just reset)
            new_episode_over = ~prev_episode_over & episode_over

        new_state = VectorEnvState(
            env_state=new_env_states,
            episode_over=new_episode_over,
        )

        return step_timesteps, new_state

    @classmethod
    def precompute_reset_states(
        cls,
        env: Env,
        params: EnvParams,
        rng: chex.PRNGKey,
        num_states: int,
    ) -> tuple[Timestep, EnvState]:
        """Pre-generate reset states for PRECOMPUTED strategy.

        This helper generates a pool of reset states that can be passed
        to the constructor for PRECOMPUTED autoreset strategy.

        Args:
            env: The environment to generate reset states from.
            params: Environment parameters.
            rng: Random key for generating states.
            num_states: Number of unique reset states to generate.

        Returns:
            Tuple of (timesteps, states) with shape (num_states, ...).
        """
        rngs = jax.random.split(rng, num_states)
        vmapped_reset = jax.vmap(env.reset, in_axes=(None, 0))
        return vmapped_reset(params, rngs)
