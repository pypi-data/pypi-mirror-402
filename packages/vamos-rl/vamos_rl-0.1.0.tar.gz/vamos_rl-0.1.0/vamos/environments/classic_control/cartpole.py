import chex
import jax
import jax.numpy as jnp
from flax import struct

from vamos.env import Env, Timestep, EnvParams, EnvState
from vamos.spaces import Array, Scalar


@struct.dataclass
class CartpoleParams(EnvParams):
    gravity: float = 9.8
    cart_mass: float = 1.0
    pole_mass: float = 0.1
    length: float = 0.5
    force_mag: float = 10.0
    tau: float = 0.02
    theta_threshold_radians: float = 12 * 2 * jnp.pi / 360
    x_threshold: float = 2.4
    reset_state_limit: float = 0.05

    @property
    def total_mass(self):
        return self.cart_mass + self.pole_mass

    @property
    def pole_mass_length(self):
        return self.pole_mass * self.length


@struct.dataclass
class CartpoleState(EnvState):
    x: jax.Array = None
    x_dot: jax.Array = None
    theta: jax.Array = None
    theta_dot: jax.Array = None


class CartPoleEnv(Env[CartpoleParams, CartpoleState]):
    """Source: https://github.com/Farama-Foundation/Gymnasium/blob/main/gymnasium/envs/classic_control/cartpole.py"""

    def __init__(self):
        default_params = self.get_default_params()
        # Use finfo.max for unbounded velocity dimensions instead of inf
        # since Array space requires finite bounds
        max_float = jnp.finfo(jnp.float32).max
        high = jnp.array(
            [
                default_params.x_threshold * 2,
                max_float,
                default_params.theta_threshold_radians * 2,
                max_float,
            ],
            dtype=jnp.float32,
        )
        self.observation_space = Array(low=-high, high=high)
        self.action_space = Scalar(max_val=2, dtype=jnp.int32)

    def get_default_params(self) -> CartpoleParams:
        # Default environment parameters for CartPole-v1
        return CartpoleParams()

    def reset(
        self, params: CartpoleParams, rng: chex.PRNGKey
    ) -> tuple[Timestep, CartpoleState]:
        obs = jax.random.uniform(
            rng,
            minval=-params.reset_state_limit,
            maxval=params.reset_state_limit,
            shape=(4,),
        )
        state = CartpoleState(
            x=obs[0],
            x_dot=obs[1],
            theta=obs[2],
            theta_dot=obs[3],
        )
        return Timestep(obs=obs), state

    def step(
        self,
        state: CartpoleState,
        action: chex.ArrayTree,
        params: CartpoleParams,
        rng: chex.PRNGKey,
    ) -> tuple[Timestep, CartpoleState]:
        """Performs step transitions in the environment."""
        force = params.force_mag * action - params.force_mag * (1 - action)
        cos_theta = jnp.cos(state.theta)
        sin_theta = jnp.sin(state.theta)

        temp = (
            force + params.pole_mass_length * state.theta_dot**2 * sin_theta
        ) / params.total_mass
        theta_acc = (params.gravity * sin_theta - cos_theta * temp) / (
            params.length
            * (4.0 / 3.0 - params.pole_mass * cos_theta**2 / params.total_mass)
        )
        x_acc = (
            temp - params.pole_mass_length * theta_acc * cos_theta / params.total_mass
        )

        # Only default Euler integration option available here!
        x = state.x + params.tau * state.x_dot
        x_dot = state.x_dot + params.tau * x_acc
        theta = state.theta + params.tau * state.theta_dot
        theta_dot = state.theta_dot + params.tau * theta_acc

        # The gymnasium/gym Cartpole by default had a constant reward even if for terminal states
        reward = jnp.array(1.0)

        # Update state dict and evaluate termination conditions
        state = CartpoleState(
            x=x,
            x_dot=x_dot,
            theta=theta,
            theta_dot=theta_dot,
        )
        timestep = Timestep(
            obs=jnp.array([x, x_dot, theta, theta_dot]),
            reward=reward,
            termination=jnp.logical_or(
                (state.x < -params.x_threshold) | (state.x > params.x_threshold),
                (state.theta < -params.theta_threshold_radians)
                | (state.theta > params.theta_threshold_radians),
            ),
            truncation=False,
            info={},
        )

        return timestep, state
