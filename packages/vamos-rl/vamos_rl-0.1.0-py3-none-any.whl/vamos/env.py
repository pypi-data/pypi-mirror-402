from __future__ import annotations

from typing import Generic, TypeVar, Any

import jax.numpy as jnp
import chex
from flax import struct
from vamos.spaces.space import Space

__all__ = ["EnvParams", "Params", "EnvState", "State", "Timestep", "Env", "Wrapper"]

Params = TypeVar("Params", bound="EnvParams")
"""Type variable for environment parameters, must be a subclass of EnvParams."""

State = TypeVar("State", bound="EnvState")
"""Type variable for environment state, must be a subclass of EnvState."""


@struct.dataclass
class Timestep:
    """Container for environment step outputs.

    A Timestep represents the result of an environment transition, containing
    the observation, reward, and episode termination signals. This is a Flax
    dataclass for JAX compatibility.

    Attributes:
        obs: The observation from the environment. Can be any pytree structure.
        reward: The reward signal from the transition. Defaults to 0.0.
        termination: Whether the episode ended due to a terminal state (e.g.,
            goal reached, failure condition). Defaults to False.
        truncation: Whether the episode ended due to a time limit or other
            external cutoff. Defaults to False.
        info: Additional information from the environment as a dictionary.
    """

    obs: chex.ArrayTree

    reward: chex.Array = 0.0
    termination: chex.Array = False
    truncation: chex.Array = False
    info: dict[str, chex.ArrayTree] = struct.field(default_factory=dict)

    @property
    def episode_over(self) -> chex.Array:
        """Check if the episode has ended.

        Returns:
            Boolean array indicating whether the episode is over, either due
            to termination or truncation.
        """
        return jnp.logical_or(self.termination, self.truncation)


@struct.dataclass
class EnvParams:
    """Base class for environment parameters.

    Environment parameters are static configuration values that define the
    environment's dynamics but do not change during an episode. Examples
    include physical constants (gravity, friction), reward scaling, or
    episode length limits.

    Subclass this to define environment-specific parameters. Uses Flax
    struct.dataclass for JAX compatibility.

    Example:
        >>> @struct.dataclass
        ... class CartpoleParams(EnvParams):
        ...     gravity: float = 9.8
        ...     pole_length: float = 0.5
    """


@struct.dataclass
class EnvState:
    """Base class for environment state.

    Environment state contains all mutable information needed to represent
    the current state of an episode. Unlike Gym/Gymnasium where state is
    stored internally, Vamos environments are stateless and require state
    to be passed explicitly to enable JAX transformations like jit and vmap.

    Subclass this to define environment-specific state. Uses Flax
    struct.dataclass for JAX compatibility.

    Example:
        >>> @struct.dataclass
        ... class CartpoleState(EnvState):
        ...     x: jax.Array
        ...     velocity: jax.Array
    """


class Env(Generic[Params, State]):
    """Base class for JAX-compatible reinforcement learning environments.

    This class provides the interface for RL environments similar to Gym/Gymnasium,
    but designed for JAX's functional programming paradigm. Unlike Gym(nasium) where state
    is stored internally, Vamos environments are stateless - state and parameters
    are passed explicitly to enable JAX transformations like jit and vmap.

    Type Parameters:
        Params: The environment parameters type, must be a subclass of EnvParams.
        State: The environment state type, must be a subclass of EnvState.

    Attributes:
        action_space: Space defining valid actions for the environment.
        observation_space: Space defining the structure of observations.

    Example:
        >>> from vamos.environments.classic_control import CartpoleEnv
        >>> env, params = CartPoleEnv.new()
        >>> rng = jax.random.PRNGKey(0)
        >>> timestep, state = env.reset(params, rng)
        >>> rng, step_rng = jax.random.split(rng)
        >>> action = env.action_space.sample(step_rng)
        >>> timestep, state = env.step(state, action, params, rng)
    """

    action_space: Space
    observation_space: Space

    def reset(self, params: Params, rng: chex.PRNGKey) -> tuple[Timestep, State]:
        """Reset the environment to an initial state.

        Args:
            params: Environment parameters controlling dynamics and configuration.
            rng: JAX random key for stochastic initialization.

        Returns:
            A tuple containing:
                - timestep: The initial Timestep with the starting observation.
                - state: The initial environment state.
        """
        raise NotImplementedError

    def step(
        self,
        state: State,
        action: chex.ArrayTree,
        params: Params,
        rng: chex.PRNGKey,
    ) -> tuple[Timestep, State]:
        """Perform one environment step.

        Takes an action and returns the resulting observation, reward, and
        termination signals. The environment state is passed in and a new
        state is returned, enabling functional composition with JAX.

        Args:
            state: The current environment state.
            action: The action to take, must be valid according to action_space.
            params: Environment parameters controlling dynamics.
            rng: JAX random key for stochastic transitions.

        Returns:
            A tuple containing:
                - timestep: The resulting Timestep with observation, reward,
                    and termination/truncation flags.
                - state: The new environment state after the transition.
        """
        raise NotImplementedError

    @staticmethod
    def get_default_params(**kwargs: Any) -> Params:
        """Get the default parameters for this environment.

        Args:
            **kwargs: Optional keyword arguments to override default values.

        Returns:
            An instance of the environment's parameter class with default
            or overridden values.
        """
        raise NotImplementedError

    @classmethod
    def new(cls, **kwargs: Any) -> tuple["Env", Params]:
        """Create a new environment instance with default parameters.

        Convenience method that instantiates the environment and its
        default parameters in one call.

        Args:
            **kwargs: Optional keyword arguments passed to get_default_params.

        Returns:
            A tuple containing:
                - env: The instantiated environment.
                - params: The default parameters for the environment.
        """
        env = cls()
        params = env.get_default_params(**kwargs)
        return env, params


class Wrapper(Env, Generic[Params, State]):
    """Base class for environment wrappers.

    Wrappers modify the behavior of an underlying environment without changing
    its core implementation. Common uses include reward shaping, observation
    preprocessing, action transformation, or adding time limits.

    Like Env, wrappers are stateless and compatible with JAX transformations.
    The wrapped environment and its spaces are stored as instance attributes.

    Type Parameters:
        Params: The wrapper's parameter type, typically extending the wrapped
            environment's parameters.
        State: The wrapper's state type, typically extending the wrapped
            environment's state.

    Attributes:
        env: The underlying environment being wrapped.
        action_space: The action space (inherited or overridden).
        observation_space: The observation space (inherited or overridden).

    Example:
        >>> env, params = CartPoleEnv.new()
        >>> wrapped_env, wrapped_params = TimeLimitWrapper.wrap(
        ...     env, params, max_steps=500
        ... )
    """

    def __init__(
        self,
        env: Env,
        action_space: Space | None = None,
        observation_space: Space | None = None,
    ):
        """Initialize the wrapper around an environment.

        Args:
            env: The environment to wrap.
            action_space: Optional override for the action space. If None,
                inherits from the wrapped environment.
            observation_space: Optional override for the observation space.
                If None, inherits from the wrapped environment.
        """
        self.env = env
        self.action_space = action_space if action_space else env.action_space
        self.observation_space = (
            observation_space if observation_space else env.observation_space
        )

    def reset(self, params: EnvParams, rng: chex.PRNGKey) -> tuple[Timestep, EnvState]:
        """Reset the wrapped environment.

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
        """Perform one step in the wrapped environment.

        Subclasses should override this to implement custom step behavior,
        typically calling self.env.step() and modifying inputs/outputs.

        Args:
            state: The current environment state (may include wrapper state).
            action: The action to take, possibly transformed by the wrapper.
            params: Environment parameters (may include wrapper-specific params).
            rng: JAX random key for stochastic transitions.

        Returns:
            A tuple containing:
                - timestep: The resulting Timestep, possibly modified by the wrapper.
                - state: The new state, possibly extended with wrapper state.
        """
        raise NotImplementedError

    @classmethod
    def get_default_params(cls, params: EnvParams, **kwargs: Any) -> EnvParams:
        """Get default parameters for the wrapper.

        Unlike Env.get_default_params, wrapper parameters typically extend
        or compose with the underlying environment's parameters.

        Args:
            params: The underlying environment's parameters.
            **kwargs: Optional keyword arguments for wrapper-specific settings.

        Returns:
            Parameters for the wrapped environment, incorporating both the
            original parameters and any wrapper-specific additions.
        """
        raise NotImplementedError

    @classmethod
    def new(cls, *args: Any, **kwargs: Any) -> tuple[Env, Params]:
        """Not supported for wrappers.

        Raises:
            NotImplementedError: Use Wrapper.wrap(env, params) instead.
        """
        raise NotImplementedError("Use Wrapper.wrap(env, params) instead")

    @classmethod
    def wrap(cls, env: Env, params: EnvParams, **kwargs: Any) -> tuple[Env, EnvParams]:
        """Wrap an existing environment with this wrapper.

        Convenience method that creates the wrapper and its parameters in one
        call. This is the preferred way to apply wrappers.

        Args:
            env: The environment to wrap.
            params: The environment's parameters.
            **kwargs: Optional keyword arguments passed to get_default_params.

        Returns:
            A tuple containing:
                - wrapper: The wrapped environment.
                - wrapped_params: Parameters for the wrapped environment.
        """
        wrapper = cls(env)
        wrapped_params = wrapper.get_default_params(params, **kwargs)
        return wrapper, wrapped_params
