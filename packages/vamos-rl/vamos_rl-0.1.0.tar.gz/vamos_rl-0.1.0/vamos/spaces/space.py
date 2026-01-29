"""Abstract base class for all space types."""

from typing import Any

import chex
import jax.numpy as jnp

__all__ = ["Space"]


class Space:
    """Abstract base class defining the interface for all spaces.

    Spaces describe the valid range and structure of values, typically used
    to specify observation and action bounds in RL environments. All concrete
    space implementations must inherit from this class.

    Attributes:
        shape: The shape of samples from this space, or None for composite spaces.
        dtype: The JAX dtype of samples, or None for composite spaces.

    Example:
        Subclasses implement the abstract methods::

            class MySpace(Space):
                def sample(self, rng):
                    return jax.random.uniform(rng, self.shape)

                def contains(self, sample):
                    return sample.shape == self.shape
    """

    shape: tuple[int, ...] | None
    dtype: jnp.dtype | None

    def __init__(
        self, shape: tuple[int, ...] | None, dtype: jnp.dtype | None = None
    ) -> None:
        """Initialize the space.

        Args:
            shape: The shape of samples from this space.
            dtype: The JAX dtype of samples.
        """
        self.shape = shape
        self.dtype = dtype

    def sample(self, rng: chex.PRNGKey) -> chex.ArrayTree:
        """Generate a random sample from this space.

        Args:
            rng: A JAX PRNG key for random number generation.

        Returns:
            A sample conforming to this space's constraints.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError

    def contains(self, sample: chex.ArrayTree) -> chex.Array:
        """Check if a sample is contained within this space.

        Args:
            sample: The value to check.

        Returns:
            A boolean array indicating whether the sample is valid.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError

    def vmap(self, n: int) -> "Space":
        """Create a vectorized version of this space.

        Returns a new space representing ``n`` stacked copies of this space,
        suitable for use with JAX's vmap. The new space will have an additional
        leading dimension of size ``n``.

        Args:
            n: Number of copies to stack.

        Returns:
            A new space with shape ``(n,) + self.shape``.

        Raises:
            NotImplementedError: Must be implemented by subclasses.

        Example:
            Create a batched space for vectorized environments::

                space = Scalar(5)
                batched_space = space.vmap(4)  # Shape: (4,)
        """
        raise NotImplementedError

    def flatten(self) -> "Space":
        """Flatten this space into a 1D representation.

        Returns:
            A flattened version of this space.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError

    def __eq__(self, other: Any) -> bool:
        """Check equality with another space."""
        return (
            isinstance(other, Space)
            and self.shape == other.shape
            and self.dtype == other.dtype
        )

    def __repr__(self) -> str:
        """Return a string representation of the space."""
        return f"{self.__class__.__name__}(shape={self.shape}, dtype={self.dtype})"

    def __contains__(self, sample: chex.ArrayTree) -> bool:
        """Enable ``sample in space`` syntax."""
        return self.contains(sample)
