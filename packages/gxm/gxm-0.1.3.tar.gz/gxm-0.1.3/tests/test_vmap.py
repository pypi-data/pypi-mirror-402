import envpool
import jax
import numpy as np
from ale_py import ALEInterface

import gxm
from gxm.wrappers import RecordEpisodeStatistics

id = "ALE/Breakout-v5"

env = gxm.make("Gymnasium/" + id)
env = RecordEpisodeStatistics(env)
exit()
num_envs = 8

key = jax.random.key(0)
keys = jax.random.split(key, num_envs)

env_states, timesteps = jax.vmap(env.init)(keys)
print(env.action_space)
exit()

for _ in range(100000):
    key, key_action, key_step = jax.random.split(key, 3)
    keys = jax.random.split(key, num_envs)
    actions = env.action_space.sample(key_action, (num_envs,))
    keys_step = jax.random.split(key_step, num_envs)
    env_states, timesteps = jax.vmap(env.step)(keys_step, env_states, actions)
    if jax.numpy.any(timesteps.done):
        print(np.array([1 if d else 0 for d in timesteps.done]))
        print(jax.tree.structure(timesteps.info))
        print(timesteps.info["lives"])

# envs = envpool.make(id, env_type="gymnasium", num_envs=num_envs)
# obs, _ = envs.reset()
# for _ in range(10000):
#     actions = np.random.randint(0, 2, num_envs)
#     print(actions)
#     obs, rewards, dones, truncs, infos = envs.step(actions)
#     if dones.any():
#         print(obs)
#         print(dones)
