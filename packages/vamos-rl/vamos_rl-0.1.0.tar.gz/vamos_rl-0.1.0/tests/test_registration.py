"""Tests for the environment registration system."""

from __future__ import annotations

import chex
import jax
import jax.numpy as jnp
from absl.testing import absltest, parameterized
from flax import struct

from vamos.env import Env, EnvParams, EnvState, Timestep
from vamos.registration import (
    ENV_ID_RE,
    EnvSpec,
    VectorizeMode,
    _load_env_class,
    make,
    make_vec,
    register,
    registry,
)
from vamos.spaces import Array, Scalar
from vamos.vector import VectorEnv
from vamos.vector.vector_env import AutoresetMode, AutoresetStrategy
from vamos.wrappers.time_limit import TimeLimit, TimeLimitParams


# =============================================================================
# Mock Environment Classes for Testing
# =============================================================================


@struct.dataclass
class MockEnvParams(EnvParams):
    """Parameters for MockEnv."""

    param_value: float = 1.0


@struct.dataclass
class MockEnvState(EnvState):
    """State for MockEnv."""

    value: jax.Array = None


class MockEnv(Env[MockEnvParams, MockEnvState]):
    """A minimal mock environment for testing registration."""

    def __init__(self):
        self.observation_space = Array(
            low=jnp.array([-1.0], dtype=jnp.float32),
            high=jnp.array([1.0], dtype=jnp.float32),
        )
        self.action_space = Scalar(max_val=2, dtype=jnp.int32)

    @staticmethod
    def get_default_params(**kwargs) -> MockEnvParams:
        return MockEnvParams(**kwargs)

    def reset(
        self, params: MockEnvParams, rng: chex.PRNGKey
    ) -> tuple[Timestep, MockEnvState]:
        obs = jax.random.uniform(rng, shape=(1,), minval=-1.0, maxval=1.0)
        state = MockEnvState(value=obs)
        return Timestep(obs=obs), state

    def step(
        self,
        state: MockEnvState,
        action: chex.ArrayTree,
        params: MockEnvParams,
        rng: chex.PRNGKey,
    ) -> tuple[Timestep, MockEnvState]:
        new_value = state.value + action * 0.1
        new_state = MockEnvState(value=new_value)
        return Timestep(obs=new_value, reward=jnp.array(1.0)), new_state


@struct.dataclass
class CustomMockEnvParams(EnvParams):
    """Custom params for testing env_params override."""

    custom_param: float = 99.0


def mock_env_factory(**kwargs) -> tuple[Env, EnvParams]:
    """Factory function that creates a MockEnv."""
    env = MockEnv()
    params = MockEnvParams(**kwargs)
    return env, params


def mock_env_factory_with_custom_param(
    custom_value: float = 5.0, **kwargs
) -> tuple[Env, EnvParams]:
    """Factory function with custom parameter."""
    env = MockEnv()
    params = MockEnvParams(param_value=custom_value, **kwargs)
    return env, params


class MockVectorEnv(VectorEnv):
    """A minimal mock vector environment for testing."""

    def __init__(self, env: Env, num_envs: int = 1):
        self.env = env
        self.num_envs = num_envs
        self.autoreset_mode = AutoresetMode.NEXT_STEP
        self.autoreset_strategy = AutoresetStrategy.COMPLETE
        self.single_action_space = env.action_space
        self.single_observation_space = env.observation_space
        self.action_space = env.action_space.vmap(num_envs)
        self.observation_space = env.observation_space.vmap(num_envs)

    def reset(self, params: EnvParams, rng: chex.PRNGKey) -> tuple[Timestep, EnvState]:
        keys = jax.random.split(rng, self.num_envs)
        timesteps, states = jax.vmap(self.env.reset, in_axes=(None, 0))(params, keys)
        return timesteps, states

    def step(
        self,
        state: EnvState,
        action: chex.ArrayTree,
        params: EnvParams,
        rng: chex.PRNGKey,
    ) -> tuple[Timestep, EnvState]:
        keys = jax.random.split(rng, self.num_envs)
        timesteps, states = jax.vmap(self.env.step, in_axes=(0, 0, None, 0))(
            state, action, params, keys
        )
        return timesteps, states


def mock_vector_env_factory(num_envs: int = 1, **kwargs) -> tuple[VectorEnv, EnvParams]:
    """Factory function that creates a MockVectorEnv."""
    env = MockEnv()
    params = MockEnvParams(**kwargs)
    vec_env = MockVectorEnv(env, num_envs=num_envs)
    return vec_env, params


# =============================================================================
# Test Fixture for Registry Isolation
# =============================================================================


class RegistryTestCase(chex.TestCase):
    """Base test case that isolates the registry for each test."""

    def setUp(self):
        super().setUp()
        # Save the original registry state
        self._original_registry = registry.copy()

    def tearDown(self):
        # Restore the original registry state
        registry.clear()
        registry.update(self._original_registry)
        super().tearDown()


# =============================================================================
# Tests for ENV_ID_RE Regex
# =============================================================================


class TestEnvIdRegex(chex.TestCase):
    """Tests for the environment ID regex pattern."""

    @parameterized.named_parameters(
        ("full_format", "namespace/env-name-v1", "namespace", "env-name", "1"),
        ("no_namespace", "env-name-v1", None, "env-name", "1"),
        ("no_version", "env-name", None, "env-name", None),
        ("namespace_no_version", "namespace/env-name", "namespace", "env-name", None),
        ("simple_name", "CartPole", None, "CartPole", None),
        ("version_only", "CartPole-v0", None, "CartPole", "0"),
        (
            "namespace_version",
            "classic_control/CartPole-v1",
            "classic_control",
            "CartPole",
            "1",
        ),
        ("dots_in_name", "my.env.name-v2", None, "my.env.name", "2"),
        ("colons_in_namespace", "ns:sub/env-v1", "ns:sub", "env", "1"),
        ("underscores", "my_namespace/my_env-v10", "my_namespace", "my_env", "10"),
    )
    def test_env_id_parsing(
        self, env_id, expected_namespace, expected_name, expected_version
    ):
        """Test that ENV_ID_RE correctly parses various environment ID formats."""
        match = ENV_ID_RE.match(env_id)
        self.assertIsNotNone(match, f"Failed to match env_id: {env_id}")
        self.assertEqual(match.group("namespace"), expected_namespace)
        self.assertEqual(match.group("name"), expected_name)
        self.assertEqual(match.group("version"), expected_version)

    @parameterized.named_parameters(
        ("empty_string", ""),
        ("just_slash", "/"),
        ("invalid_chars", "env name with spaces"),
    )
    def test_invalid_env_ids(self, env_id):
        """Test that invalid environment IDs do not match."""
        match = ENV_ID_RE.match(env_id)
        # Empty string and invalid formats should not match the full expected pattern
        if match:
            # If there's a match, ensure it doesn't capture the full intent
            self.assertTrue(
                match.group("name") is None or match.group("name") == "",
                f"Unexpectedly matched invalid env_id: {env_id}",
            )

    def test_version_like_string_matches_as_name(self):
        """Test that '-v1' is parsed as a name (the whole string)."""
        # The non-greedy pattern consumes '-v1' as the full name since
        # there's no other valid parse that matches the version suffix
        match = ENV_ID_RE.match("-v1")
        self.assertIsNotNone(match)
        self.assertEqual(match.group("name"), "-v1")
        self.assertIsNone(match.group("version"))


# =============================================================================
# Tests for VectorizeMode
# =============================================================================


class TestVectorizeMode(chex.TestCase):
    """Tests for the VectorizeMode enum."""

    def test_enum_values_exist(self):
        """Test that VectorizeMode has expected values."""
        self.assertIsNotNone(VectorizeMode.VMAP)
        self.assertIsNotNone(VectorizeMode.VECTOR_ENTRY_POINT)

    def test_enum_values_are_distinct(self):
        """Test that enum values are distinct."""
        self.assertNotEqual(VectorizeMode.VMAP, VectorizeMode.VECTOR_ENTRY_POINT)


# =============================================================================
# Tests for register()
# =============================================================================


class TestRegister(RegistryTestCase):
    """Tests for the register() function."""

    def test_register_with_string_entry_point(self):
        """Test registering an environment with a string entry point."""
        register(
            "test/MockEnv-v1",
            entry_point="tests.test_registration:MockEnv",
        )
        self.assertIn("test/MockEnv-v1", registry)
        spec = registry["test/MockEnv-v1"]
        self.assertEqual(spec.env_id, "test/MockEnv-v1")
        self.assertEqual(spec.entry_point, "tests.test_registration:MockEnv")

    def test_register_with_callable_entry_point(self):
        """Test registering an environment with a callable entry point."""
        register(
            "test/MockEnvCallable-v1",
            entry_point=mock_env_factory,
        )
        self.assertIn("test/MockEnvCallable-v1", registry)
        spec = registry["test/MockEnvCallable-v1"]
        self.assertEqual(spec.entry_point, mock_env_factory)

    def test_register_with_vector_entry_point(self):
        """Test registering an environment with a vector entry point."""
        register(
            "test/MockVecEnv-v1",
            entry_point=mock_env_factory,
            vector_entry_point=mock_vector_env_factory,
        )
        spec = registry["test/MockVecEnv-v1"]
        self.assertEqual(spec.vector_entry_point, mock_vector_env_factory)

    def test_register_with_max_episode_steps(self):
        """Test registering with max_episode_steps."""
        register(
            "test/MockEnvSteps-v1",
            entry_point=mock_env_factory,
            max_episode_steps=500,
        )
        spec = registry["test/MockEnvSteps-v1"]
        self.assertEqual(spec.max_episode_steps, 500)

    def test_register_with_default_kwargs(self):
        """Test registering with default_kwargs."""
        default_kwargs = {"param_value": 2.5}
        register(
            "test/MockEnvKwargs-v1",
            entry_point=mock_env_factory,
            default_kwargs=default_kwargs,
        )
        spec = registry["test/MockEnvKwargs-v1"]
        self.assertEqual(spec.default_kwargs, default_kwargs)

    def test_register_with_env_params(self):
        """Test registering with custom env_params."""
        custom_params = CustomMockEnvParams(custom_param=42.0)
        register(
            "test/MockEnvParams-v1",
            entry_point=mock_env_factory,
            env_params=custom_params,
        )
        spec = registry["test/MockEnvParams-v1"]
        self.assertEqual(spec.env_params, custom_params)

    def test_register_duplicate_raises_error(self):
        """Test that registering a duplicate env_id raises ValueError."""
        register("test/DuplicateEnv-v1", entry_point=mock_env_factory)
        with self.assertRaises(ValueError) as context:
            register("test/DuplicateEnv-v1", entry_point=mock_env_factory)
        self.assertIn("already registered", str(context.exception))

    def test_register_all_options(self):
        """Test registering with all options specified."""
        custom_params = MockEnvParams(param_value=10.0)
        register(
            "test/FullyConfigured-v1",
            entry_point=mock_env_factory,
            vector_entry_point=mock_vector_env_factory,
            max_episode_steps=1000,
            default_kwargs={"param_value": 5.0},
            env_params=custom_params,
        )
        spec = registry["test/FullyConfigured-v1"]
        self.assertEqual(spec.env_id, "test/FullyConfigured-v1")
        self.assertEqual(spec.entry_point, mock_env_factory)
        self.assertEqual(spec.vector_entry_point, mock_vector_env_factory)
        self.assertEqual(spec.max_episode_steps, 1000)
        self.assertEqual(spec.default_kwargs, {"param_value": 5.0})
        self.assertEqual(spec.env_params, custom_params)


# =============================================================================
# Tests for _load_env_class()
# =============================================================================


class TestLoadEnvClass(chex.TestCase):
    """Tests for the _load_env_class() helper function."""

    def test_load_with_colon_separator(self):
        """Test loading a class with colon separator."""
        cls = _load_env_class("tests.test_registration:MockEnv")
        self.assertEqual(cls, MockEnv)

    def test_load_with_dot_separator(self):
        """Test loading a class with dot separator."""
        cls = _load_env_class("tests.test_registration.MockEnv")
        self.assertEqual(cls, MockEnv)

    def test_load_invalid_module_raises_error(self):
        """Test that loading from an invalid module raises an error."""
        with self.assertRaises(ModuleNotFoundError):
            _load_env_class("nonexistent.module:SomeClass")

    def test_load_invalid_attribute_raises_error(self):
        """Test that loading an invalid attribute raises an error."""
        with self.assertRaises(AttributeError):
            _load_env_class("tests.test_registration:NonExistentClass")


# =============================================================================
# Tests for make()
# =============================================================================


class TestMake(RegistryTestCase):
    """Tests for the make() function."""

    def test_make_from_string_entry_point(self):
        """Test creating an environment from a string entry point."""
        register(
            "test/StringEntry-v1",
            entry_point="tests.test_registration:MockEnv",
        )
        env, params = make("test/StringEntry-v1", stop_gradient=False)
        self.assertIsInstance(env, MockEnv)
        self.assertIsInstance(params, MockEnvParams)

    def test_make_from_callable_entry_point(self):
        """Test creating an environment from a callable entry point."""
        register(
            "test/CallableEntry-v1",
            entry_point=mock_env_factory,
        )
        env, params = make("test/CallableEntry-v1", stop_gradient=False)
        self.assertIsInstance(env, MockEnv)
        self.assertIsInstance(params, MockEnvParams)

    def test_make_with_env_kwargs_override_defaults(self):
        """Test that env_kwargs override default_kwargs."""
        register(
            "test/KwargsOverride-v1",
            entry_point=mock_env_factory,
            default_kwargs={"param_value": 1.0},
        )
        env, params = make("test/KwargsOverride-v1", param_value=99.0)
        self.assertEqual(params.param_value, 99.0)

    def test_make_uses_spec_env_params(self):
        """Test that spec.env_params is used when provided."""
        custom_params = MockEnvParams(param_value=42.0)
        register(
            "test/SpecParams-v1",
            entry_point=mock_env_factory,
            env_params=custom_params,
        )
        env, params = make("test/SpecParams-v1")
        self.assertEqual(params, custom_params)
        self.assertEqual(params.param_value, 42.0)

    def test_make_with_max_episode_steps_wraps_with_time_limit(self):
        """Test that max_episode_steps wraps the environment with TimeLimit."""
        register(
            "test/WithTimeLimit-v1",
            entry_point=mock_env_factory,
            max_episode_steps=100,
        )
        env, params = make("test/WithTimeLimit-v1", stop_gradient=False)
        self.assertIsInstance(env, TimeLimit)
        self.assertIsInstance(params, TimeLimitParams)
        self.assertEqual(params.max_episode_steps, 100)

    def test_make_max_episode_steps_arg_overrides_spec(self):
        """Test that max_episode_steps argument overrides spec value."""
        register(
            "test/OverrideTimeLimit-v1",
            entry_point=mock_env_factory,
            max_episode_steps=100,
        )
        env, params = make(
            "test/OverrideTimeLimit-v1", max_episode_steps=200, stop_gradient=False
        )
        self.assertIsInstance(env, TimeLimit)
        self.assertEqual(params.max_episode_steps, 200)

    def test_make_with_env_spec_directly(self):
        """Test make() with an EnvSpec object directly."""
        spec = EnvSpec(
            env_id="direct/Spec-v1",
            entry_point=mock_env_factory,
            vector_entry_point=None,
            default_kwargs={},
            env_params=None,
            max_episode_steps=None,
        )
        env, params = make(spec, stop_gradient=False)
        self.assertIsInstance(env, MockEnv)

    def test_make_unregistered_raises_error(self):
        """Test that making an unregistered env_id raises ValueError."""
        with self.assertRaises(ValueError) as context:
            make("nonexistent/Env-v1")
        self.assertIn("not found", str(context.exception))

    def test_make_no_entry_point_raises_error(self):
        """Test that a spec with no entry_point raises ValueError."""
        spec = EnvSpec(
            env_id="no/EntryPoint-v1",
            entry_point=None,
            vector_entry_point=mock_vector_env_factory,
            default_kwargs={},
            env_params=None,
            max_episode_steps=None,
        )
        with self.assertRaises(ValueError) as context:
            make(spec)
        self.assertIn("no entry_point", str(context.exception))

    def test_make_env_is_functional(self):
        """Test that the created environment is functional."""
        register("test/Functional-v1", entry_point=mock_env_factory)
        env, params = make("test/Functional-v1")

        rng = jax.random.PRNGKey(0)
        timestep, state = env.reset(params, rng)
        self.assertEqual(timestep.obs.shape, (1,))

        action = jnp.array(1)
        rng, step_rng = jax.random.split(rng)
        timestep, state = env.step(state, action, params, step_rng)
        self.assertEqual(timestep.obs.shape, (1,))


# =============================================================================
# Tests for make_vec()
# =============================================================================


class TestMakeVec(RegistryTestCase):
    """Tests for the make_vec() function."""

    def test_make_vec_with_vmap_mode(self):
        """Test creating a vectorized env with VMAP mode."""
        register(
            "test/VmapEnv-v1",
            entry_point=mock_env_factory,
        )
        vec_env, params = make_vec(
            "test/VmapEnv-v1",
            num_envs=4,
            vectorization_mode=VectorizeMode.VMAP,
        )
        self.assertEqual(vec_env.num_envs, 4)

    def test_make_vec_with_vector_entry_point_mode(self):
        """Test creating a vectorized env with VECTOR_ENTRY_POINT mode."""
        register(
            "test/VecEntryEnv-v1",
            entry_point=mock_env_factory,
            vector_entry_point=mock_vector_env_factory,
        )
        vec_env, params = make_vec(
            "test/VecEntryEnv-v1",
            num_envs=8,
            vectorization_mode=VectorizeMode.VECTOR_ENTRY_POINT,
        )
        self.assertIsInstance(vec_env, MockVectorEnv)
        self.assertEqual(vec_env.num_envs, 8)

    def test_make_vec_auto_selects_vector_entry_point(self):
        """Test that make_vec auto-selects VECTOR_ENTRY_POINT when available."""
        register(
            "test/AutoSelectVec-v1",
            entry_point=mock_env_factory,
            vector_entry_point=mock_vector_env_factory,
        )
        vec_env, params = make_vec("test/AutoSelectVec-v1", num_envs=4)
        # Should use MockVectorEnv from vector_entry_point
        self.assertIsInstance(vec_env, MockVectorEnv)

    def test_make_vec_falls_back_to_vmap(self):
        """Test that make_vec falls back to VMAP when no vector_entry_point."""
        register(
            "test/FallbackVmap-v1",
            entry_point=mock_env_factory,
        )
        vec_env, params = make_vec("test/FallbackVmap-v1", num_envs=4)
        # Should use VMapVectorEnv
        from vamos.vector.vmap_vector_env import VMapVectorEnv

        self.assertIsInstance(vec_env, VMapVectorEnv)

    def test_make_vec_num_envs_correct(self):
        """Test that num_envs creates the correct batch size."""
        register("test/NumEnvs-v1", entry_point=mock_env_factory)
        for num_envs in [1, 4, 16]:
            vec_env, params = make_vec(
                "test/NumEnvs-v1",
                num_envs=num_envs,
                vectorization_mode=VectorizeMode.VMAP,
            )
            self.assertEqual(vec_env.num_envs, num_envs)

    def test_make_vec_vector_kwargs_passed(self):
        """Test that vector_kwargs are passed to VMapVectorEnv."""
        register("test/VecKwargs-v1", entry_point=mock_env_factory)
        vec_env, params = make_vec(
            "test/VecKwargs-v1",
            num_envs=4,
            vectorization_mode=VectorizeMode.VMAP,
            vector_kwargs={
                "autoreset_mode": AutoresetMode.SAME_STEP,
            },
        )
        self.assertEqual(vec_env.autoreset_mode, AutoresetMode.SAME_STEP)

    def test_make_vec_env_kwargs_merged(self):
        """Test that env_kwargs are merged with default_kwargs."""
        register(
            "test/MergeKwargs-v1",
            entry_point=mock_env_factory,
            default_kwargs={"param_value": 1.0},
        )
        vec_env, params = make_vec(
            "test/MergeKwargs-v1",
            num_envs=2,
            vectorization_mode=VectorizeMode.VMAP,
            param_value=5.0,
        )
        self.assertEqual(params.param_value, 5.0)

    def test_make_vec_uses_spec_env_params(self):
        """Test that spec.env_params is used when provided."""
        custom_params = MockEnvParams(param_value=77.0)
        register(
            "test/VecSpecParams-v1",
            entry_point=mock_env_factory,
            env_params=custom_params,
        )
        vec_env, params = make_vec(
            "test/VecSpecParams-v1",
            num_envs=2,
            vectorization_mode=VectorizeMode.VMAP,
        )
        self.assertEqual(params, custom_params)

    def test_make_vec_time_limit_in_vmap_mode(self):
        """Test that max_episode_steps applies TimeLimit in VMAP mode."""
        register(
            "test/VecTimeLimit-v1",
            entry_point=mock_env_factory,
            max_episode_steps=50,
        )
        vec_env, params = make_vec(
            "test/VecTimeLimit-v1",
            num_envs=2,
            vectorization_mode=VectorizeMode.VMAP,
            stop_gradient=False,
        )
        # The underlying env should be wrapped with TimeLimit
        self.assertIsInstance(vec_env.env, TimeLimit)
        self.assertIsInstance(params, TimeLimitParams)
        self.assertEqual(params.max_episode_steps, 50)

    def test_make_vec_with_env_spec_directly(self):
        """Test make_vec() with an EnvSpec object directly."""
        spec = EnvSpec(
            env_id="direct/VecSpec-v1",
            entry_point=mock_env_factory,
            vector_entry_point=None,
            default_kwargs={},
            env_params=None,
            max_episode_steps=None,
        )
        vec_env, params = make_vec(spec, num_envs=4)
        self.assertEqual(vec_env.num_envs, 4)

    def test_make_vec_unregistered_raises_error(self):
        """Test that make_vec with unregistered env_id raises ValueError."""
        with self.assertRaises(ValueError) as context:
            make_vec("nonexistent/VecEnv-v1", num_envs=2)
        self.assertIn("not found", str(context.exception))

    def test_make_vec_vector_entry_point_mode_no_entry_raises_error(self):
        """Test that VECTOR_ENTRY_POINT mode without vector_entry_point raises error."""
        register(
            "test/NoVecEntry-v1",
            entry_point=mock_env_factory,
        )
        with self.assertRaises(ValueError) as context:
            make_vec(
                "test/NoVecEntry-v1",
                num_envs=2,
                vectorization_mode=VectorizeMode.VECTOR_ENTRY_POINT,
            )
        self.assertIn("no vector_entry_point", str(context.exception))

    def test_make_vec_vmap_mode_no_entry_point_raises_error(self):
        """Test that VMAP mode without entry_point raises error."""
        spec = EnvSpec(
            env_id="no/EntryVec-v1",
            entry_point=None,
            vector_entry_point=mock_vector_env_factory,
            default_kwargs={},
            env_params=None,
            max_episode_steps=None,
        )
        with self.assertRaises(ValueError) as context:
            make_vec(spec, num_envs=2, vectorization_mode=VectorizeMode.VMAP)
        self.assertIn("no entry_point", str(context.exception))

    def test_make_vec_is_functional(self):
        """Test that the created vector environment is functional."""
        register("test/FunctionalVec-v1", entry_point=mock_env_factory)
        vec_env, params = make_vec(
            "test/FunctionalVec-v1",
            num_envs=4,
            vectorization_mode=VectorizeMode.VMAP,
        )

        rng = jax.random.PRNGKey(0)
        timesteps, states = vec_env.reset(params, rng)
        self.assertEqual(timesteps.obs.shape, (4, 1))

        actions = jnp.array([0, 1, 0, 1])
        rng, step_rng = jax.random.split(rng)
        timesteps, states = vec_env.step(states, actions, params, step_rng)
        self.assertEqual(timesteps.obs.shape, (4, 1))


# =============================================================================
# Tests for JIT Compatibility
# =============================================================================


class TestJITCompatibility(RegistryTestCase):
    """Tests for JIT compatibility of registered environments."""

    def test_make_env_jit_compatible(self):
        """Test that environments created via make() are JIT compatible."""
        register("test/JitEnv-v1", entry_point=mock_env_factory)
        env, params = make("test/JitEnv-v1")

        @jax.jit
        def run_episode(rng):
            timestep, state = env.reset(params, rng)
            action = jnp.array(1)
            rng, step_rng = jax.random.split(rng)
            timestep, state = env.step(state, action, params, step_rng)
            return timestep

        rng = jax.random.PRNGKey(42)
        timestep = run_episode(rng)
        self.assertEqual(timestep.obs.shape, (1,))

    def test_make_vec_jit_compatible(self):
        """Test that vector envs created via make_vec() are JIT compatible."""
        register("test/JitVecEnv-v1", entry_point=mock_env_factory)
        vec_env, params = make_vec(
            "test/JitVecEnv-v1",
            num_envs=4,
            vectorization_mode=VectorizeMode.VMAP,
        )

        @jax.jit
        def run_step(rng):
            timesteps, states = vec_env.reset(params, rng)
            actions = jnp.array([0, 1, 0, 1])
            rng, step_rng = jax.random.split(rng)
            timesteps, states = vec_env.step(states, actions, params, step_rng)
            return timesteps

        rng = jax.random.PRNGKey(42)
        timesteps = run_step(rng)
        self.assertEqual(timesteps.obs.shape, (4, 1))

    @chex.variants(with_jit=True, without_jit=True)
    def test_make_env_with_time_limit_jit_compatible(self):
        """Test TimeLimit wrapped env is JIT compatible."""
        register(
            "test/JitTimeLimit-v1",
            entry_point=mock_env_factory,
            max_episode_steps=10,
        )
        env, params = make("test/JitTimeLimit-v1")

        @self.variant
        def run_steps(rng):
            timestep, state = env.reset(params, rng)
            for _ in range(5):
                rng, step_rng = jax.random.split(rng)
                action = jnp.array(1)
                timestep, state = env.step(state, action, params, step_rng)
            return timestep, state

        rng = jax.random.PRNGKey(0)
        timestep, state = run_steps(rng)
        self.assertEqual(timestep.obs.shape, (1,))


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration(RegistryTestCase):
    """Integration tests for the full registration workflow."""

    def test_full_workflow_make(self):
        """Test complete workflow: register -> make -> use environment."""
        # Register
        register(
            "integration/TestEnv-v1",
            entry_point=mock_env_factory,
            max_episode_steps=10,
            default_kwargs={"param_value": 2.0},
        )

        # Make
        env, params = make("integration/TestEnv-v1")

        # Use
        rng = jax.random.PRNGKey(0)
        timestep, state = env.reset(params, rng)
        self.assertIsNotNone(timestep.obs)

        for _ in range(5):
            rng, step_rng = jax.random.split(rng)
            action = jnp.array(1)
            timestep, state = env.step(state, action, params, step_rng)

        self.assertIsNotNone(timestep.obs)

    def test_full_workflow_make_vec(self):
        """Test complete workflow: register -> make_vec -> use vectorized env."""
        # Register
        register(
            "integration/VecTestEnv-v1",
            entry_point=mock_env_factory,
        )

        # Make vectorized
        vec_env, params = make_vec(
            "integration/VecTestEnv-v1",
            num_envs=8,
            vectorization_mode=VectorizeMode.VMAP,
        )

        # Use
        rng = jax.random.PRNGKey(0)
        timesteps, states = vec_env.reset(params, rng)
        self.assertEqual(timesteps.obs.shape[0], 8)

        for _ in range(5):
            rng, step_rng = jax.random.split(rng)
            actions = jnp.zeros(8, dtype=jnp.int32)
            timesteps, states = vec_env.step(states, actions, params, step_rng)

        self.assertEqual(timesteps.obs.shape[0], 8)

    def test_string_and_callable_entry_points_produce_same_env(self):
        """Test that string and callable entry points produce equivalent envs."""
        register(
            "compare/StringEntry-v1",
            entry_point="tests.test_registration:MockEnv",
        )
        register(
            "compare/CallableEntry-v1",
            entry_point=mock_env_factory,
        )

        env1, params1 = make("compare/StringEntry-v1", stop_gradient=False)
        env2, params2 = make("compare/CallableEntry-v1", stop_gradient=False)

        # Both should be MockEnv instances
        self.assertIsInstance(env1, MockEnv)
        self.assertIsInstance(env2, MockEnv)

        # Both should produce similar behavior
        rng = jax.random.PRNGKey(0)
        ts1, _ = env1.reset(params1, rng)
        ts2, _ = env2.reset(params2, rng)
        chex.assert_trees_all_close(ts1.obs, ts2.obs)


if __name__ == "__main__":
    absltest.main()
