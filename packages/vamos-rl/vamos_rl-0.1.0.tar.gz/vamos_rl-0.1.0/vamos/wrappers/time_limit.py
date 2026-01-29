"""Time limit wrapper for truncating episodes after a maximum number of steps."""

import chex
from flax import struct

from vamos import Wrapper, EnvState, EnvParams

from vamos.env import Timestep


@struct.dataclass
class TimeLimitParams(EnvParams):
    """Parameters for the TimeLimit wrapper.

    Attributes:
        env_params: The wrapped environment's parameters.
        max_episode_steps: Maximum steps before truncation.
    """

    env_params: EnvParams = None
    max_episode_steps: int = 0


@struct.dataclass
class TimeLimitState(EnvState):
    """State for the TimeLimit wrapper.

    Attributes:
        env_state: The wrapped environment's state.
        time: Current step count in the episode.
    """

    env_state: EnvState = None
    time: int = 0


class TimeLimit(Wrapper[TimeLimitParams, TimeLimitState]):
    """Wrapper that truncates episodes after a maximum number of steps."""

    @classmethod
    def get_default_params(
        cls, params: EnvParams, max_episode_steps: int
    ) -> TimeLimitParams:
        """Create wrapper parameters with the specified step limit."""
        assert max_episode_steps > 0
        return TimeLimitParams(env_params=params, max_episode_steps=max_episode_steps)

    def reset(
        self, params: TimeLimitParams, rng: chex.PRNGKey
    ) -> tuple[Timestep, TimeLimitState]:
        """Reset the environment and initialize step counter to zero."""
        env_timestep, env_state = self.env.reset(params.env_params, rng)

        state = TimeLimitState(env_state=env_state, time=0)
        return env_timestep, state

    def step(
        self,
        state: TimeLimitState,
        action: chex.ArrayTree,
        params: TimeLimitParams,
        rng: chex.PRNGKey,
    ) -> tuple[Timestep, TimeLimitState]:
        """Step the environment and set truncation if step limit is reached."""
        env_timestep, env_state = self.env.step(
            state.env_state, action, params.env_params, rng
        )

        new_state = TimeLimitState(env_state=env_state, time=state.time + 1)
        truncation = env_timestep.truncation | (
            new_state.time >= params.max_episode_steps
        )
        timestep = env_timestep.replace(truncation=truncation)

        return timestep, new_state
