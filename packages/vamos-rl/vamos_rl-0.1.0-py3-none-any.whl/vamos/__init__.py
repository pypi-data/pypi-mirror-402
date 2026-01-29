from vamos.env import Env, Wrapper, EnvState, EnvParams
from vamos.registration import make, register, make_vec
from vamos.spaces.space import Space

__version__ = "0.1.0"
__all__ = [
    "Env",
    "Wrapper",
    "EnvState",
    "EnvParams",
    "Space",
    "register",
    "make",
    "make_vec",
]

from vamos.environments import register_environments

register_environments()
