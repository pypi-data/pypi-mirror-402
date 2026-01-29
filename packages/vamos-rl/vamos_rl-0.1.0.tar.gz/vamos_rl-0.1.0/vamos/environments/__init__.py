from vamos.registration import register


def register_environments():
    # CartPole
    register(
        "CartPole-v0",
        entry_point="vamos.environments.classic_control.cartpole:CartPoleEnv",
        vector_entry_point=None,
        max_episode_steps=200,
    )

    register(
        "CartPole-v1",
        entry_point="vamos.environments.classic_control.cartpole:CartPoleEnv",
        vector_entry_point=None,
        max_episode_steps=500,
    )
