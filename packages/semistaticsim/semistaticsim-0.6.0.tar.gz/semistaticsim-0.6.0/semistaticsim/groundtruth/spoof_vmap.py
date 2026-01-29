import os

import jax.numpy as jnp

os.environ["JAX_PLATFORM_NAME"] = "cpu"
import jax
jax.config.update('jax_platform_name', "cpu")


def spoof_vmap(list_of_dataclasses):
    leaves_proto, tree_def = jax.tree.flatten(list_of_dataclasses[0])
    leaves_acc = []
    for leaf in leaves_proto:
        if isinstance(leaf, jnp.ndarray):
            pass
        else:
            leaf = jnp.array([leaf])
        leaves_acc.append(leaf[None])

    for i, o in enumerate(list_of_dataclasses[1:]):
        leaves, tree_def = jax.tree.flatten(o)
        if leaves_acc is None:
            leaves_acc = leaves
        else:
            tmp = []
            for leaf_acc, leaf in zip(leaves_acc, leaves):
                if isinstance(leaf, jnp.ndarray):
                    pass
                else:
                    leaf = jnp.array([leaf])
                tmp.append(jnp.concatenate([leaf_acc, leaf[None]]))
            leaves_acc = tmp
    ret = jax.tree.unflatten(tree_def, leaves_acc)
    return ret