"""Array space for multi-dimensional bounded values."""

from vamos.spaces.space import Space
import chex
import jax.numpy as jnp
import jax


__all__ = ["Array"]


class Array(Space):
    """A space for multi-dimensional arrays with element-wise bounds.

    Equivalent to Gymnasium's ``Box``, ``MultiDiscrete``, and ``MultiBinary``
    spaces combined. Each element in the array has its own lower and upper
    bound, allowing for asymmetric bounds across dimensions.

    Attributes:
        low: Array of lower bounds for each element.
        high: Array of upper bounds for each element.
        shape: Shape of the space, derived from the bounds.
        dtype: JAX dtype, derived from the bounds.

    Example:
        Create a 1D continuous observation space::

            import jax.numpy as jnp
            space = Array(low=jnp.zeros(4), high=jnp.ones(4))

        Create a space with asymmetric bounds::

            space = Array(
                low=jnp.array([-1.0, 0.0, 1.0]),
                high=jnp.array([0.0, 1.0, 2.0])
            )

        Create a 2D image-like observation space::

            space = Array(
                low=jnp.zeros((8, 8, 3)),
                high=jnp.ones((8, 8, 3))
            )

        Create an integer array space::

            space = Array(
                low=jnp.zeros(4, dtype=jnp.int32),
                high=jnp.full(4, 10, dtype=jnp.int32)
            )
    """

    def __init__(
        self,
        *,
        low: chex.Array,
        high: chex.Array,
    ):
        """Initialize an array space with element-wise bounds.

        Args:
            low: Lower bounds for each element. Must be a JAX array with
                finite values. The shape and dtype are inferred from this array.
            high: Upper bounds for each element. Must have the same shape
                and dtype as ``low``, with all finite values.

        Raises:
            AssertionError: If ``low`` and ``high`` have different shapes or dtypes.
            AssertionError: If ``low`` or ``high`` contain infinite or NaN values.
        """
        chex.assert_equal_shape([low, high])
        chex.assert_trees_all_equal_dtypes(low, high)
        chex.assert_tree_all_finite(low)
        chex.assert_tree_all_finite(high)

        super().__init__(shape=low.shape, dtype=low.dtype)
        self.low = low
        self.high = high

    def sample(self, rng: chex.PRNGKey) -> chex.ArrayTree:
        """Generate a random sample from the array space.

        Args:
            rng: A JAX PRNG key.

        Returns:
            An array with values uniformly sampled element-wise from
            ``[low, high)``, cast to the space's dtype.
        """
        return jax.random.uniform(
            rng, shape=self.shape, minval=self.low, maxval=self.high
        ).astype(self.dtype)

    def contains(self, sample: chex.Array) -> chex.Array:
        """Check if a sample is within the valid bounds.

        Args:
            sample: The array to check.

        Returns:
            True if the sample has the correct shape and all elements
            are within ``[low, high]``.
        """
        return (
            isinstance(sample, jax.Array)
            and sample.shape == self.shape
            and jnp.all(jnp.logical_and(sample >= self.low, sample <= self.high))
        )

    def vmap(self, n: int) -> "Array":
        """Create a vectorized version of this array space.

        Args:
            n: Number of copies to stack.

        Returns:
            A new ``Array`` space with shape ``(n,) + self.shape``.
            The bounds are broadcast to the new shape.

        Example:
            Vectorize an array space for batched operations::

                space = Array(low=jnp.zeros(4), high=jnp.ones(4))
                batched = space.vmap(3)
                # batched.shape is (3, 4)
        """
        new_shape = (n,) + self.shape
        return Array(
            low=jnp.broadcast_to(self.low, new_shape),
            high=jnp.broadcast_to(self.high, new_shape),
        )
