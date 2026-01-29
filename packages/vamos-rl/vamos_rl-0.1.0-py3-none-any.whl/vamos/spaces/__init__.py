"""Spaces module for defining observation and action bounds.

This module provides space classes that describe the valid range and structure
of observations and actions in reinforcement learning environments, similar to
Gym/Gymnasium spaces but designed for JAX.

Classes:
    Space: Abstract base class for all spaces.
    Scalar: Single scalar values (discrete or continuous).
    Array: Multi-dimensional arrays with element-wise bounds.
    Dict: Composite spaces with named subspaces.

Example:
    Define an action space with 4 discrete actions::

        from vamos.spaces import Scalar
        action_space = Scalar(4)  # Actions: 0, 1, 2, 3

    Define a continuous observation space::

        import jax.numpy as jnp
        from vamos.spaces import Array
        observation_space = Array(
            low=jnp.zeros(4),
            high=jnp.ones(4)
        )

    Define a composite observation space::

        from vamos.spaces import Dict, Scalar, Array
        import jax.numpy as jnp
        observation_space = Dict({
            "position": Array(low=-jnp.ones(3), high=jnp.ones(3)),
            "velocity": Array(low=-jnp.ones(3), high=jnp.ones(3)),
            "action": Scalar(4),
        })
"""

from vamos.spaces.space import Space
from vamos.spaces.array import Array
from vamos.spaces.scalar import Scalar
from vamos.spaces.dict import Dict

__all__ = ["Space", "Scalar", "Array", "Dict"]
