from __future__ import annotations

import importlib
import re
from enum import IntEnum, auto
from typing import Callable, Any

from flax import struct

from vamos.env import Env, EnvParams
from vamos.vector import VectorEnv
from vamos.vector.vmap_vector_env import VMapVectorEnv
from vamos.wrappers.stop_gradient import StopGradient
from vamos.wrappers.time_limit import TimeLimit


ENV_ID_RE = re.compile(
    r"^(?:(?P<namespace>[\w:-]+)/)?(?P<name>[\w:.-]+?)(?:-v(?P<version>\d+))?$"
)


class VectorizeMode(IntEnum):
    VMAP = auto()
    # Todo: PMAP / SHARDED option
    VECTOR_ENTRY_POINT = auto()


# Type alias for factory functions that create environments
EnvFactory = Callable[..., tuple[Env, EnvParams]]


@struct.dataclass
class EnvSpec:
    env_id: str
    entry_point: str | EnvFactory | None
    vector_entry_point: str | Callable[..., tuple[VectorEnv, EnvParams]] | None
    default_kwargs: dict[str, Any]
    env_params: EnvParams | None

    max_episode_steps: int | None


registry: dict[str, EnvSpec] = dict()


def register(
    env_id: str,
    entry_point: str | EnvFactory | None = None,
    vector_entry_point: str | Callable[..., tuple[VectorEnv, EnvParams]] | None = None,
    max_episode_steps: int | None = None,
    default_kwargs: dict | None = None,
    env_params: EnvParams | None = None,
):
    """Register an environment with the global registry.

    Args:
        env_id: The environment ID in format [namespace/](env-name)[-v(version)].
        entry_point: Either a string path to an Env class (e.g.,
            "vamos.environments.classic_control.cartpole:CartPoleEnv") which will
            have .new() called on it, or a factory callable that returns (Env, EnvParams).
        vector_entry_point: Optional string path or callable for creating vectorized
            environments directly, bypassing vmap.
        max_episode_steps: Optional maximum episode length. If provided, the
            environment will be wrapped with TimeLimit.
        default_kwargs: Default keyword arguments passed to the entry point.
        env_params: The environment parameters to use rather than the default_env_params.

    Raises:
        ValueError: If env_id is already registered.
    """
    if env_id in registry:
        raise ValueError(f"Environment {env_id} is already registered.")

    spec = EnvSpec(
        env_id=env_id,
        entry_point=entry_point,
        vector_entry_point=vector_entry_point,
        default_kwargs=default_kwargs if default_kwargs else {},
        env_params=env_params,
        max_episode_steps=max_episode_steps,
    )

    registry[env_id] = spec


def _load_env_class(entry_point: str) -> type[Env]:
    """Load an Env class from a string path.

    Args:
        entry_point: Module path in format "module.path:ClassName" or "module.path.ClassName".

    Returns:
        The Env class.
    """
    if ":" in entry_point:
        module_path, attr_name = entry_point.rsplit(":", 1)
    else:
        module_path, attr_name = entry_point.rsplit(".", 1)

    module = importlib.import_module(module_path)
    return getattr(module, attr_name)


def make(
    env_id: str | EnvSpec,
    max_episode_steps: int | None = None,
    stop_gradient: bool = True,
    **env_kwargs: Any,
) -> tuple[Env, EnvParams]:
    """Create an environment from a registered ID or EnvSpec.

    Args:
        env_id: Either an environment ID string or an EnvSpec object.
        max_episode_steps: Optional override for maximum episode length. If provided,
            wraps the environment with TimeLimit. If None, uses the spec's value.
        stop_gradient: If True (default), wraps the environment with StopGradient
            to prevent gradients from flowing through observations and states.
        **env_kwargs: Additional keyword arguments passed to the environment's
            entry point, merged with the spec's default_kwargs.

    Returns:
        A tuple of (env, params) ready for use.

    Raises:
        ValueError: If env_id is not found in the registry.
        ValueError: If the spec has no entry_point defined.
    """
    # Get the spec
    if isinstance(env_id, EnvSpec):
        spec = env_id
    else:
        if env_id not in registry:
            raise ValueError(f"Environment {env_id} not found in registry.")
        spec = registry[env_id]

    if spec.entry_point is None:
        raise ValueError(f"Environment {spec.env_id} has no entry_point defined.")

    # Merge default kwargs with provided kwargs (provided takes precedence)
    kwargs = {**spec.default_kwargs, **env_kwargs}

    # Create the environment
    # String entry points are Env classes (call .new()), callables are factories (call directly)
    if isinstance(spec.entry_point, str):
        env_cls = _load_env_class(spec.entry_point)
        env, params = env_cls.new(**kwargs)
    else:
        env, params = spec.entry_point(**kwargs)

    # Use spec's env_params if provided
    if spec.env_params is not None:
        params = spec.env_params

    # Apply TimeLimit wrapper if max_episode_steps is specified
    effective_max_steps = (
        max_episode_steps if max_episode_steps is not None else spec.max_episode_steps
    )
    if effective_max_steps is not None:
        env, params = TimeLimit.wrap(env, params, max_episode_steps=effective_max_steps)

    # Apply StopGradient wrapper to prevent gradients through env dynamics
    if stop_gradient:
        env, params = StopGradient.wrap(env, params)

    return env, params


def make_vec(
    env_id: str | EnvSpec,
    num_envs: int = 1,
    vectorization_mode: VectorizeMode | str | None = None,
    vector_kwargs: dict[str, Any] | None = None,
    max_episode_steps: int | None = None,
    stop_gradient: bool = True,
    **env_kwargs,
) -> tuple[VectorEnv, EnvParams]:
    """Create a vectorized environment from a registered ID or EnvSpec.

    Args:
        env_id: Either an environment ID string or an EnvSpec object.
        num_envs: Number of parallel environment instances.
        vectorization_mode: How to create the vectorized environment:
            - VectorizeMode.VMAP (default): Wrap base env with VMapVectorEnv
            - VectorizeMode.VECTOR_ENTRY_POINT: Use the spec's vector_entry_point
        vector_kwargs: Additional keyword arguments passed to VMapVectorEnv
            (e.g., autoreset_mode, autoreset_strategy).
        max_episode_steps: Optional override for maximum episode length. If provided,
            wraps the environment with TimeLimit. If None, uses the spec's value.
        stop_gradient: If True (default), wraps the environment with StopGradient
            to prevent gradients from flowing through observations and states.
        **env_kwargs: Additional keyword arguments passed to the environment's
            entry point, merged with the spec's default_kwargs.

    Returns:
        A tuple of (vector_env, params) ready for use.

    Raises:
        ValueError: If env_id is not found in the registry.
        ValueError: If vectorization_mode is VECTOR_ENTRY_POINT but spec has none.
    """
    # Get the spec
    if isinstance(env_id, EnvSpec):
        spec = env_id
    else:
        if env_id not in registry:
            raise ValueError(f"Environment {env_id} not found in registry.")
        spec = registry[env_id]

    # Normalize vectorization_mode
    if vectorization_mode is None:
        # Default to VECTOR_ENTRY_POINT if available, otherwise VMAP
        if spec.vector_entry_point is not None:
            mode = VectorizeMode.VECTOR_ENTRY_POINT
        else:
            mode = VectorizeMode.VMAP
    elif isinstance(vectorization_mode, str):
        mode = VectorizeMode(vectorization_mode)
    else:
        mode = vectorization_mode

    vector_kwargs = vector_kwargs or {}

    if mode == VectorizeMode.VECTOR_ENTRY_POINT:
        if spec.vector_entry_point is None:
            raise ValueError(
                f"Environment {spec.env_id} has no vector_entry_point defined. "
                "Use vectorization_mode=VectorizeMode.VMAP instead."
            )

        # vector_entry_point is always a callable (string loads a factory, not a class)
        kwargs = {**spec.default_kwargs, **env_kwargs}
        assert len(vector_kwargs) == 0
        if isinstance(spec.vector_entry_point, str):
            vector_factory = _load_env_class(spec.vector_entry_point)
            vec_env, params = vector_factory(num_envs=num_envs, **kwargs)
        else:
            vec_env, params = spec.vector_entry_point(num_envs=num_envs, **kwargs)

        # Use spec's env_params if provided
        if spec.env_params is not None:
            params = spec.env_params

        return vec_env, params

    else:  # VectorizeMode.VMAP
        # Create base environment
        if spec.entry_point is None:
            raise ValueError(f"Environment {spec.env_id} has no entry_point defined.")

        kwargs = {**spec.default_kwargs, **env_kwargs}
        # String entry points are Env classes (call .new()), callables are factories (call directly)
        if isinstance(spec.entry_point, str):
            env_cls = _load_env_class(spec.entry_point)
            env, params = env_cls.new(**kwargs)
        else:
            env, params = spec.entry_point(**kwargs)

        # Use spec's env_params if provided
        if spec.env_params is not None:
            params = spec.env_params

        # Apply TimeLimit wrapper if max_episode_steps is specified
        effective_max_steps = (
            max_episode_steps
            if max_episode_steps is not None
            else spec.max_episode_steps
        )
        if effective_max_steps is not None:
            env, params = TimeLimit.wrap(
                env, params, max_episode_steps=effective_max_steps
            )

        # Apply StopGradient wrapper to prevent gradients through env dynamics
        if stop_gradient:
            env, params = StopGradient.wrap(env, params)

        # Wrap with VMapVectorEnv
        vec_env = VMapVectorEnv(env, num_envs=num_envs, **vector_kwargs)

        return vec_env, params
