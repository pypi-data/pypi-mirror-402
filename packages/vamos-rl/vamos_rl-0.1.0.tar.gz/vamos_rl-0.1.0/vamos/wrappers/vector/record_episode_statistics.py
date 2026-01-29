"""Episode statistics wrapper for tracking rewards and lengths in vector environments."""

from __future__ import annotations

import jax
import jax.numpy as jnp
import chex
from flax import struct

from vamos.env import EnvParams, EnvState, Timestep
from vamos.vector.vector_env import VectorEnv, VectorWrapper

__all__ = ["EpisodeStatisticsState", "RecordEpisodeStatistics"]


@struct.dataclass
class EpisodeStatisticsState(EnvState):
    """State for the EpisodeStatistics wrapper.

    Attributes:
        env_state: The wrapped vector environment's state.
        episode_returns: Rolling buffer of cumulative rewards from last N completed episodes.
        episode_lengths: Rolling buffer of lengths from last N completed episodes.
        current_returns: Accumulated reward for ongoing episode in each environment.
        current_lengths: Step count for ongoing episode in each environment.
        buffer_index: Next write position in the rolling buffers.
        episode_count: Total number of completed episodes.
    """

    env_state: EnvState = None
    episode_returns: chex.Array = None  # Shape: (buffer_size,)
    episode_lengths: chex.Array = None  # Shape: (buffer_size,)
    current_returns: chex.Array = None  # Shape: (num_envs,)
    current_lengths: chex.Array = None  # Shape: (num_envs,)
    buffer_index: chex.Array = None  # Scalar
    episode_count: chex.Array = None  # Scalar


class RecordEpisodeStatistics(VectorWrapper):
    """Wrapper that records episode statistics for vector environments.

    Tracks cumulative rewards and episode lengths in a rolling buffer of the
    last N completed episodes. Statistics are added to the timestep info dict.

    Attributes:
        env: The underlying vector environment.
        buffer_size: Number of episodes to keep in the rolling buffer.
        action_space: The vector action space (inherited from VectorWrapper).
        observation_space: The vector observation space (inherited from VectorWrapper).
        single_action_space: The single environment action space (inherited from VectorWrapper).
        single_observation_space: The single environment observation space (inherited from VectorWrapper).
        num_envs: Number of parallel environments (inherited from VectorWrapper).
    """

    def __init__(self, env: VectorEnv, buffer_size: int = 100):
        """Initialize the wrapper.

        Args:
            env: The vector environment to wrap.
            buffer_size: Number of episodes to store in the rolling buffer.
        """
        super().__init__(env)
        self.buffer_size = buffer_size

    def reset(
        self, params: EnvParams, rng: chex.PRNGKey
    ) -> tuple[Timestep, EpisodeStatisticsState]:
        """Reset the environment and initialize statistics tracking.

        Args:
            params: Environment parameters.
            rng: JAX random key for stochastic initialization.

        Returns:
            A tuple containing:
                - timestep: The initial timestep with episode stats in info.
                - state: The initial state with zeroed statistics.
        """
        timestep, env_state = self.env.reset(params, rng)

        state = EpisodeStatisticsState(
            env_state=env_state,
            episode_returns=jnp.zeros(self.buffer_size, dtype=jnp.float32),
            episode_lengths=jnp.zeros(self.buffer_size, dtype=jnp.int32),
            current_returns=jnp.zeros(self.num_envs, dtype=jnp.float32),
            current_lengths=jnp.zeros(self.num_envs, dtype=jnp.int32),
            buffer_index=jnp.array(0, dtype=jnp.int32),
            episode_count=jnp.array(0, dtype=jnp.int32),
        )

        info = dict(timestep.info)
        info["current_returns"] = state.current_returns
        info["current_lengths"] = state.current_lengths
        timestep = timestep.replace(info=info)

        return timestep, state

    def step(
        self,
        state: EpisodeStatisticsState,
        action: chex.ArrayTree,
        params: EnvParams,
        rng: chex.PRNGKey,
    ) -> tuple[Timestep, EpisodeStatisticsState]:
        """Step the environment and update episode statistics.

        When episodes complete (via termination or truncation), their
        cumulative reward and length are stored in the rolling buffer.

        Args:
            state: The current wrapper state.
            action: Actions for all environments.
            params: Environment parameters.
            rng: JAX random key for stochastic transitions.

        Returns:
            A tuple containing:
                - timestep: The resulting timestep with updated stats in info.
                - state: The new state with updated statistics.
        """
        timestep, env_state = self.env.step(state.env_state, action, params, rng)

        # Update running totals
        new_returns = state.current_returns + timestep.reward
        new_lengths = state.current_lengths + 1

        # Check which episodes ended
        episode_done = timestep.episode_over  # Shape: (num_envs,)

        # Store completed episode stats in rolling buffer
        def store_episode_stats(carry, done_and_stats):
            buffer_returns, buffer_lengths, buffer_idx, count = carry
            done, ep_return, ep_length = done_and_stats

            # Only update if episode is done
            new_buffer_returns = jax.lax.cond(
                done,
                lambda: buffer_returns.at[buffer_idx % self.buffer_size].set(ep_return),
                lambda: buffer_returns,
            )
            new_buffer_lengths = jax.lax.cond(
                done,
                lambda: buffer_lengths.at[buffer_idx % self.buffer_size].set(ep_length),
                lambda: buffer_lengths,
            )
            new_idx = jax.lax.cond(done, lambda: buffer_idx + 1, lambda: buffer_idx)
            new_count = jax.lax.cond(done, lambda: count + 1, lambda: count)

            return (new_buffer_returns, new_buffer_lengths, new_idx, new_count), None

        (episode_returns, episode_lengths, buffer_index, episode_count), _ = (
            jax.lax.scan(
                store_episode_stats,
                (
                    state.episode_returns,
                    state.episode_lengths,
                    state.buffer_index,
                    state.episode_count,
                ),
                (episode_done, new_returns, new_lengths),
            )
        )

        # Reset accumulators for completed episodes
        current_returns = jnp.where(episode_done, 0.0, new_returns)
        current_lengths = jnp.where(episode_done, 0, new_lengths)

        new_state = EpisodeStatisticsState(
            env_state=env_state,
            episode_returns=episode_returns,
            episode_lengths=episode_lengths,
            current_returns=current_returns,
            current_lengths=current_lengths,
            buffer_index=buffer_index,
            episode_count=episode_count,
        )

        info = dict(timestep.info)
        info["current_returns"] = current_returns
        info["current_lengths"] = current_lengths
        timestep = timestep.replace(info=info)

        return timestep, new_state
