from __future__ import annotations

from enum import IntEnum, auto
from typing import Any

from vamos.spaces.space import Space
from vamos.env import EnvState, EnvParams, Env, Timestep
import chex

__all__ = ["AutoresetMode", "AutoresetStrategy", "VectorEnv", "VectorWrapper"]


class AutoresetMode(IntEnum):
    """Controls when terminated sub-environments are reset.

    When a sub-environment terminates, the autoreset mode determines whether
    the reset occurs on the same step or the next step.

    Attributes:
        NEXT_STEP: Reset occurs on the next step() call. The terminal observation
            is returned directly, and the following step returns the reset
            observation. Training code must handle episode boundaries carefully.
        SAME_STEP: Reset occurs within the same step() call. The reset observation
            is returned immediately, and the terminal observation is stored in
            timestep.info["final_obs"]. Simplifies training loops since every
            observation is actionable.
    """

    NEXT_STEP = auto()
    SAME_STEP = auto()


class AutoresetStrategy(IntEnum):
    """Controls how reset states are computed for terminated sub-environments.

    JAX's no-branching constraint means reset computations cannot be conditionally
    skipped. The autoreset strategy optimizes what gets computed, trading off
    between computational cost, memory usage, and initial state diversity.

    Attributes:
        COMPLETE: Calls the reset function for every sub-environment at every step.
            Unused reset states are discarded via jax.lax.select. Simplest approach
            with maximum diversity, but wasteful when few environments terminate.
        OPTIMISTIC: Generates M reset states where M << N (number of sub-environments),
            assuming only a fraction terminate each step. Multiple terminating
            environments may share initial states. Good balance of efficiency and
            diversity for large N with expensive resets.
        PRECOMPUTED: Pre-generates a pool of reset states before training, eliminating
            reset computation during rollouts. Zero reset overhead but limited to
            a fixed set of initial states. Best for maximum throughput when initial
            state diversity is not critical.
    """

    COMPLETE = auto()
    OPTIMISTIC = auto()
    PRECOMPUTED = auto()


class VectorEnv:
    """Base class for vectorized environments running multiple instances in parallel.

    Vector environments enable running N instances of the same environment
    simultaneously, which is essential for efficient reinforcement learning
    training. A single call to step() advances all N environments, producing
    N transitions and enabling hardware-efficient batched operations.

    Unlike single environments where state is passed explicitly, vector environments
    manage batched states where the first dimension corresponds to the sub-environment
    index. This class defines the interface; see VMapVectorEnv for the vmap-based
    implementation.

    Attributes:
        env: The underlying single environment being vectorized.
        num_envs: Number of parallel environment instances (N).
        autoreset_mode: Controls when terminated sub-environments are reset.
            See AutoresetMode for options.
        autoreset_strategy: Controls how reset states are computed.
            See AutoresetStrategy for options.
        action_space: Batched action space with shape (num_envs, ...).
        observation_space: Batched observation space with shape (num_envs, ...).
        single_action_space: Action space for a single sub-environment.
        single_observation_space: Observation space for a single sub-environment.

    Example:
        >>> from vamos.vector.vmap_vector_env import VMapVectorEnv
        >>> vec_env = VMapVectorEnv(
        ...     env=CartPoleEnv(),
        ...     num_envs=1024,
        ...     autoreset_mode=AutoresetMode.SAME_STEP,
        ...     autoreset_strategy=AutoresetStrategy.OPTIMISTIC,
        ... )
        >>> rng = jax.random.PRNGKey(0)
        >>> timesteps, states = vec_env.reset(params, rng)
        >>> actions = vec_env.action_space.sample(rng)
        >>> timesteps, states = vec_env.step(states, actions, params, rng)
    """

    env: Env
    num_envs: int
    autoreset_mode: AutoresetMode
    autoreset_strategy: AutoresetStrategy

    action_space: Space
    observation_space: Space
    single_action_space: Space
    single_observation_space: Space

    def reset(self, params: EnvParams, rng: chex.PRNGKey) -> tuple[Timestep, EnvState]:
        """Reset all sub-environments to initial states.

        Args:
            params: Environment parameters controlling dynamics and configuration.
            rng: JAX random key for stochastic initialization. Will be split
                internally to provide unique keys for each sub-environment.

        Returns:
            A tuple containing:
                - timesteps: Batched Timestep with observations of shape (num_envs, ...).
                - states: Batched environment states for all sub-environments.
        """
        raise NotImplementedError

    def step(
        self,
        state: EnvState,
        action: chex.ArrayTree,
        params: EnvParams,
        rng: chex.PRNGKey,
    ) -> tuple[Timestep, EnvState]:
        """Perform one step in all sub-environments simultaneously.

        Advances all N sub-environments with the provided actions. Handles
        autoreset behavior based on the configured autoreset_mode and
        autoreset_strategy when sub-environments terminate.

        Args:
            state: Batched environment state for all sub-environments.
            action: Batched actions with shape (num_envs, ...).
            params: Environment parameters controlling dynamics.
            rng: JAX random key for stochastic transitions. Will be split
                internally for each sub-environment.

        Returns:
            A tuple containing:
                - timesteps: Batched Timestep with observations, rewards, and
                    termination flags, each with first dimension num_envs.
                - states: Updated batched environment states.
        """
        raise NotImplementedError

    @classmethod
    def new(
        cls, env: Env, params: EnvParams, **kwargs: Any
    ) -> tuple["VectorEnv", EnvParams]:
        """Create a new vector environment from a single environment.

        Convenience method that instantiates the vector environment wrapping
        the provided single environment.

        Args:
            env: The single environment to vectorize.
            params: The environment's parameters.
            **kwargs: Optional keyword arguments passed to the constructor
                (e.g., num_envs, autoreset_mode, autoreset_strategy).

        Returns:
            A tuple containing:
                - vec_env: The instantiated vector environment.
                - params: The environment parameters (passed through unchanged).
        """
        vec_env = cls(env, **kwargs)
        return vec_env, params


class VectorWrapper(VectorEnv):
    """Base class for vector environment wrappers.

    Wrappers modify the behavior of an underlying vector environment without
    changing its core implementation. Common uses include reward shaping,
    observation preprocessing, action transformation, or recording statistics.

    Like VectorEnv, wrappers are stateless and compatible with JAX transformations.
    The wrapped environment and its properties are accessible through instance
    attributes.

    Attributes:
        env: The underlying vector environment being wrapped.
        num_envs: Number of parallel environment instances (inherited from wrapped env).
        autoreset_mode: Controls when terminated sub-environments are reset (inherited).
        autoreset_strategy: Controls how reset states are computed (inherited).
        action_space: Batched action space (inherited or overridden).
        observation_space: Batched observation space (inherited or overridden).
        single_action_space: Single environment action space (inherited or overridden).
        single_observation_space: Single environment observation space (inherited or overridden).

    Example:
        >>> vec_env = VMapVectorEnv(env=CartPoleEnv(), num_envs=1024)
        >>> wrapped_env = RecordEpisodeStatistics(vec_env, buffer_size=100)
    """

    def __init__(
        self,
        env: VectorEnv,
        action_space: Space | None = None,
        observation_space: Space | None = None,
        single_action_space: Space | None = None,
        single_observation_space: Space | None = None,
    ):
        """Initialize the wrapper around a vector environment.

        Args:
            env: The vector environment to wrap.
            action_space: Optional override for the batched action space.
                If None, inherits from the wrapped environment.
            observation_space: Optional override for the batched observation space.
                If None, inherits from the wrapped environment.
            single_action_space: Optional override for the single action space.
                If None, inherits from the wrapped environment.
            single_observation_space: Optional override for the single observation space.
                If None, inherits from the wrapped environment.
        """
        self.env = env
        self.num_envs = env.num_envs
        self.autoreset_mode = env.autoreset_mode
        self.autoreset_strategy = env.autoreset_strategy
        self.action_space = action_space if action_space else env.action_space
        self.observation_space = (
            observation_space if observation_space else env.observation_space
        )
        self.single_action_space = (
            single_action_space if single_action_space else env.single_action_space
        )
        self.single_observation_space = (
            single_observation_space
            if single_observation_space
            else env.single_observation_space
        )

    def reset(self, params: EnvParams, rng: chex.PRNGKey) -> tuple[Timestep, EnvState]:
        """Reset the wrapped vector environment.

        Subclasses should override this to implement custom reset behavior,
        typically calling self.env.reset() and modifying the result.

        Args:
            params: Environment parameters (may include wrapper-specific params).
            rng: JAX random key for stochastic initialization.

        Returns:
            A tuple containing:
                - timestep: The initial Timestep, possibly modified by the wrapper.
                - state: The initial state, possibly extended with wrapper state.
        """
        raise NotImplementedError

    def step(
        self,
        state: EnvState,
        action: chex.ArrayTree,
        params: EnvParams,
        rng: chex.PRNGKey,
    ) -> tuple[Timestep, EnvState]:
        """Perform one step in the wrapped vector environment.

        Subclasses should override this to implement custom step behavior,
        typically calling self.env.step() and modifying inputs/outputs.

        Args:
            state: The current environment state (may include wrapper state).
            action: The actions to take, possibly transformed by the wrapper.
            params: Environment parameters (may include wrapper-specific params).
            rng: JAX random key for stochastic transitions.

        Returns:
            A tuple containing:
                - timestep: The resulting Timestep, possibly modified by the wrapper.
                - state: The new state, possibly extended with wrapper state.
        """
        raise NotImplementedError

    @classmethod
    def new(cls, *args: Any, **kwargs: Any) -> tuple["VectorEnv", EnvParams]:
        """Not supported for wrappers.

        Raises:
            NotImplementedError: Use VectorWrapper.wrap(env, params) instead.
        """
        raise NotImplementedError("Use VectorWrapper.wrap(env, params) instead")

    @classmethod
    def wrap(
        cls, env: VectorEnv, params: EnvParams, **kwargs: Any
    ) -> tuple["VectorEnv", EnvParams]:
        """Wrap an existing vector environment with this wrapper.

        Convenience method that creates the wrapper in one call.
        This is the preferred way to apply wrappers.

        Args:
            env: The vector environment to wrap.
            params: The environment's parameters.
            **kwargs: Optional keyword arguments passed to the wrapper constructor.

        Returns:
            A tuple containing:
                - wrapper: The wrapped vector environment.
                - params: The environment parameters (passed through unchanged).
        """
        wrapper = cls(env, **kwargs)
        return wrapper, params
