"""Dict space for composite observations with named subspaces."""

from vamos.spaces.space import Space
import chex
import jax.numpy as jnp
import jax

__all__ = ["Dict"]


class Dict(Space):
    """A composite space containing named subspaces.

    Used for observations or actions that consist of multiple named components,
    such as position, velocity, and sensor readings. Supports arbitrary nesting
    of spaces, including nested ``Dict`` spaces.

    Attributes:
        spaces: Dictionary mapping names to subspaces.
        shape: Always ``None`` for Dict spaces (composite structure).
        dtype: Always ``None`` for Dict spaces (varies by subspace).

    Example:
        Create a simple observation space with position and velocity::

            import jax.numpy as jnp
            space = Dict({
                "position": Array(low=-jnp.ones(3), high=jnp.ones(3)),
                "velocity": Array(low=-jnp.ones(3), high=jnp.ones(3)),
            })

        Create a mixed discrete/continuous space::

            space = Dict({
                "discrete": Scalar(5),
                "continuous": Array(low=jnp.zeros(2), high=jnp.ones(2)),
            })

        Create a nested observation space::

            space = Dict({
                "agent": Dict({
                    "position": Array(low=-jnp.ones(2), high=jnp.ones(2)),
                    "velocity": Array(low=-jnp.ones(2), high=jnp.ones(2)),
                    "action": Scalar(4),
                }),
                "environment": Dict({
                    "obstacles": Array(low=jnp.zeros((10, 2)), high=jnp.ones((10, 2))),
                }),
            })
    """

    def __init__(self, spaces: dict[str, Space]):
        """Initialize a dict space with named subspaces.

        Args:
            spaces: Dictionary mapping string keys to Space objects.
                Must contain at least one subspace.

        Raises:
            AssertionError: If ``spaces`` is empty.
        """
        super().__init__(shape=None, dtype=None)

        assert len(spaces) > 0
        self.spaces: dict[str, Space] = spaces

    def sample(self, rng: chex.PRNGKey) -> chex.ArrayTree:
        """Generate a random sample from each subspace.

        Splits the PRNG key to ensure independent samples from each subspace.

        Args:
            rng: A JAX PRNG key.

        Returns:
            A dictionary with the same keys as ``spaces``, where each value
            is a sample from the corresponding subspace.
        """
        rngs = jax.random.split(rng, len(self.spaces))
        return {
            key: space.sample(rng)
            for rng, (key, space) in zip(rngs, self.spaces.items(), strict=True)
        }

    def contains(self, sample: chex.ArrayTree) -> chex.Array:
        """Check if a sample is contained in all subspaces.

        Args:
            sample: A dictionary with keys matching ``spaces``.

        Returns:
            True if all values in ``sample`` are contained in their
            corresponding subspaces. Returns False if sample is not a dict
            or has mismatched keys.
        """
        # Check that sample is a dict with matching keys
        if not isinstance(sample, dict):
            return jnp.array(False)
        if set(sample.keys()) != set(self.spaces.keys()):
            return jnp.array(False)
        return jnp.all(
            jnp.array([self.spaces[key].contains(sample[key]) for key in self.spaces])
        )

    def vmap(self, n: int) -> "Dict":
        """Create a vectorized version of this dict space.

        Applies ``vmap(n)`` to each subspace.

        Args:
            n: Number of copies to stack.

        Returns:
            A new ``Dict`` space where each subspace has been vectorized.

        Example:
            Vectorize a dict space for batched environments::

                space = Dict({
                    "obs": Array(low=jnp.zeros(4), high=jnp.ones(4)),
                    "action": Scalar(3),
                })
                batched = space.vmap(8)
                # batched["obs"].shape is (8, 4)
                # batched["action"].shape is (8,)
        """
        return Dict(spaces={key: space.vmap(n) for key, space in self.spaces.items()})
