from __future__ import annotations

import gymnasium as gym

from ray.tune.registry import _global_registry, ENV_CREATOR
from ray.rllib.env import MultiAgentEnv
from typing import Callable

from ..multigrid_env import MultiGridEnv



def get_env_creator(env_specifier: str | type[gym.Env]) -> Callable[[], gym.Env]:
    """
    Get the environment creator callable for the specified environment.

    Parameters
    ----------
    env_specifier : str or type[gym.Env]
        Environment specifier (e.g. 'CartPole-v1' or gym.CartPoleEnv)
    """
    if isinstance(env_specifier, str):
        return _global_registry.get(ENV_CREATOR, env_specifier)
    elif callable(env_specifier):
        return env_specifier
    else:
        raise ValueError(f'Invalid environment specifier: {env_specifier}')

def to_rllib_env(
    env_cls: type[MultiGridEnv],
    *wrappers: gym.Wrapper,
    default_config: dict = {}) -> type[MultiAgentEnv]:
    """
    Convert a ``MultiGridEnv`` environment class to an RLLib ``MultiAgentEnv`` class.

    Note that this is a wrapper around the environment **class**,
    not environment instances.

    Parameters
    ----------
    env_cls : type[MultiGridEnv]
        ``MultiGridEnv`` environment class
    wrappers : gym.Wrapper
        Gym wrappers to apply to the environment
    default_config : dict
        Default configuration for the environment

    Returns
    -------
    rllib_env_cls : type[MultiAgentEnv]
        RLlib ``MultiAgentEnv`` environment class
    """
    class RLlibMultiAgentEnv(gym.Wrapper, MultiAgentEnv):

        def __init__(self, config: dict = {}):
            self._obs_space_in_preferred_format = True
            self._action_space_in_preferred_format = True
            config = {**default_config, **config}
            env = env_cls(**config)
            for wrapper in wrappers:
                env = wrapper(env)

            gym.Wrapper.__init__(self, env)
            MultiAgentEnv.__init__(self)

        def get_agent_ids(self):
            return {agent.index for agent in self.agents}

        def step(self, *args, **kwargs):
            obs, reward, terminated, truncated, info = super().step(*args, **kwargs)
            terminated['__all__'] = all(terminated.values())
            truncated['__all__'] = all(truncated.values())
            return obs, reward, terminated, truncated, info

    RLlibMultiAgentEnv.__name__ = f"RLlib_{env_cls.__name__}"
    return RLlibMultiAgentEnv
