import chex

from vamos import Env


def benchmark_env(env):
    # TODO
    pass


def benchmark_vector_env(vec_env):
    # TODO
    pass


def evaluate_env_policy(env: Env, policy: callable, num_episodes: int, rng: chex.PRNGKey) -> tuple[float, chex.Array, chex.Array]:
    # TODO
    pass

