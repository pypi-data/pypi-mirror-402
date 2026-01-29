"""Scalar space for single discrete or continuous values."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vamos.spaces.space import Space
import chex
import jax.numpy as jnp
import jax

if TYPE_CHECKING:
    from vamos.spaces.array import Array

__all__ = ["Scalar"]


INTEGER_DTYPES = (
    jnp.uint2,
    jnp.uint4,
    jnp.uint8,
    jnp.uint16,
    jnp.uint32,
    jnp.uint64,
    jnp.int2,
    jnp.int4,
    jnp.int8,
    jnp.int16,
    jnp.int32,
    jnp.int64,
)
FLOATING_DTYPES = (
    jnp.float4_e2m1fn,
    jnp.float8_e3m4,
    jnp.float8_e4m3,
    jnp.float8_e8m0fnu,
    jnp.float8_e4m3fn,
    jnp.float8_e4m3fnuz,
    jnp.float8_e5m2,
    jnp.float8_e5m2fnuz,
    jnp.float8_e4m3b11fnuz,
    jnp.bfloat16,
    jnp.float16,
    jnp.float32,
    jnp.float64,
)


class Scalar(Space):
    """A space for single scalar values within a bounded range.

    Similar to Gymnasium's ``Discrete`` space but with support for both
    discrete (integer) and continuous (floating-point) values. Useful for
    defining action spaces with a fixed number of discrete actions or
    single continuous values.

    Attributes:
        max_val: Upper bound of the valid range (exclusive for integers).
        min_val: Lower bound of the valid range (inclusive).
        shape: Always ``()`` for scalar spaces.
        dtype: The JAX dtype for samples.
        n: The number of categories

    Example:
        Create a discrete action space with 4 actions (0, 1, 2, 3)::

            action_space = Scalar(4)
            rng = jax.random.PRNGKey(0)
            action = action_space.sample(rng)  # Returns int32 in [0, 4)

        Create a discrete space with custom range::

            space = Scalar(min_val=1, max_val=10)  # Values in [1, 10]

        Create a continuous scalar space::

            space = Scalar(min_val=-1.0, max_val=1.0, dtype=jnp.float32)
    """

    def __init__(
        self,
        max_val: int | float,
        *,
        min_val: int | float = 0,
        dtype: jnp.dtype = jnp.int32,
    ):
        """Initialize a scalar space.

        Args:
            max_val: Upper bound of the range. For integer dtypes, samples are
                in ``[min_val, max_val)``. Must be a Python scalar (not a JAX array).
            min_val: Lower bound of the range (inclusive). Defaults to 0.
                Must be a Python scalar (not a JAX array).
            dtype: JAX dtype for samples. Use integer types (e.g., ``jnp.int32``)
                for discrete spaces or float types (e.g., ``jnp.float32``) for
                continuous spaces. Defaults to ``jnp.int32``.

        Raises:
            AssertionError: If ``max_val`` or ``min_val`` is not a scalar.
        """
        assert dtype in INTEGER_DTYPES + FLOATING_DTYPES
        super().__init__(shape=(), dtype=dtype)

        chex.assert_scalar(max_val)
        chex.assert_scalar(min_val)

        self.max_val = max_val
        self.min_val = min_val

        if any(self.dtype == dtype for dtype in INTEGER_DTYPES):
            self.n = self.max_val - self.min_val
        else:
            self.n = None

    def sample(self, rng: chex.PRNGKey) -> chex.Scalar:
        """Generate a random sample from the scalar space.

        Args:
            rng: A JAX PRNG key.

        Returns:
            A scalar value uniformly sampled from ``[min_val, max_val)``,
            cast to the space's dtype.
        """
        return jax.random.uniform(
            rng, shape=self.shape, minval=self.min_val, maxval=self.max_val
        ).astype(self.dtype)

    def contains(self, sample: chex.Array) -> chex.Array:
        """Check if a sample is within the valid range.

        Args:
            sample: The value to check.

        Returns:
            True if the sample is a scalar within ``[min_val, max_val]``.
        """
        return (
            isinstance(sample, jax.Array)
            and sample.shape == self.shape
            and jnp.all(jnp.logical_and(sample >= self.min_val, sample <= self.max_val))
        )

    def vmap(self, n: int) -> Array:
        """Create a vectorized version of this scalar space.

        Args:
            n: Number of copies to stack.

        Returns:
            An ``Array`` space with shape ``(n,)`` and the same bounds.

        Example:
            Vectorize a scalar space for batched operations::

                space = Scalar(5)
                batched = space.vmap(4)
                # batched is Array(low=[0,0,0,0], high=[5,5,5,5])
        """
        from vamos.spaces.array import Array

        return Array(
            low=jnp.full((n,) + self.shape, self.min_val, dtype=self.dtype),
            high=jnp.full((n,) + self.shape, self.max_val, dtype=self.dtype),
        )
