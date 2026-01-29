"""Stop gradient wrapper to prevent gradient flow through environment outputs."""

import jax.lax
import chex

from vamos import Wrapper, EnvParams, EnvState
from vamos.env import Timestep


class StopGradient(Wrapper):
    """Wrapper that stops gradients from flowing through timesteps and states.

    This prevents gradients from backpropagating through environment dynamics
    during policy optimization, which is standard practice in RL since the
    environment is typically treated as non-differentiable.

    Example:
        >>> env, params = CartPoleEnv.new()
        >>> env, params = StopGradient.wrap(env, params)
    """

    @classmethod
    def get_default_params(cls, params: EnvParams, **kwargs) -> EnvParams:
        """Pass through the underlying params unchanged."""
        return params

    def reset(self, params: EnvParams, rng: chex.PRNGKey) -> tuple[Timestep, EnvState]:
        """Reset and stop gradients on the outputs."""
        timestep, state = self.env.reset(params, rng)
        return jax.lax.stop_gradient(timestep), jax.lax.stop_gradient(state)

    def step(
        self,
        state: EnvState,
        action: chex.ArrayTree,
        params: EnvParams,
        rng: chex.PRNGKey,
    ) -> tuple[Timestep, EnvState]:
        """Step and stop gradients on the outputs."""
        timestep, new_state = self.env.step(state, action, params, rng)
        return jax.lax.stop_gradient(timestep), jax.lax.stop_gradient(new_state)
