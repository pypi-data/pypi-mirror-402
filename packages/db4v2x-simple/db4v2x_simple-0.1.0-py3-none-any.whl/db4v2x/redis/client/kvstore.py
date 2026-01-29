"""database config and data access functions using redis.asyncio.cluster."""

from typing import Any, List
from collections import defaultdict

from redis.asyncio.cluster import RedisCluster

from .scripts import (
    batch_set_script,
    batch_get_script,
    batch_hset_script,
    batch_hget_script,
)


class KVStore:
    """redis cluster config and data access functions."""

    def __init__(self, redis: RedisCluster) -> None:
        """Class initialization."""
        self._redis = redis

        self._batch_set_script = self._redis.register_script(batch_set_script)
        self._batch_get_script = self._redis.register_script(batch_get_script)

        self._batch_hset_script = self._redis.register_script(batch_hset_script)
        self._batch_hget_script = self._redis.register_script(batch_hget_script)

    async def batch_set(self, key2value: dict, lua_enable: bool = False, ex: int = 5):
        if lua_enable:
            await self._batch_set_script(
                keys=list(key2value.keys()), args=list(key2value.values()) + [str(ex)]
            )
        else:
            for k, v in key2value.items():
                await self._redis.set(k, v, ex=ex)

    async def batch_get(self, key_list: List[str], lua_enable: bool = False):
        if lua_enable:
            value_list = await self._batch_get_script(keys=key_list)
            results = {k: v for k, v in zip(key_list, value_list)}
        else:
            results = {k: await self._redis.get(k) for k in key_list}

        return results

    async def batch_hset(
        self, key2field2value: dict, lua_enable: bool = False, ex: int = 5
    ):
        if lua_enable:
            keys, argv = [], []
            for key, field2value in key2field2value.items():
                keys.append(key)
                argv.append(str(len(field2value)))
                for field, val in field2value.items():
                    argv.append(str(field))
                    argv.append(str(val))
            argv.append(str(ex))
            await self._batch_hset_script(keys=keys, args=argv)

        else:
            for key, field2value in key2field2value.items():
                await self._redis.hset(key, mapping=field2value)
                await self._redis.expire(key, ex)

    async def batch_hget(self, key2field_list: dict, lua_enable: bool = False) -> Any:
        res_dict = defaultdict(dict)
        if lua_enable:
            keys = []
            argv = []
            for key, field_list in key2field_list.items():
                keys.append(key)
                argv.append(str(len(field_list)))
                for f in field_list:
                    argv.append(f)

            raw = await self._batch_hget_script(keys=keys, args=argv)

            for i in range(0, len(raw), 3):
                key = raw[i]
                fields = raw[i + 1]
                values = raw[i + 2]
                res_dict[key] = dict(zip(fields, values))
        else:
            for key, field_list in key2field_list.items():
                values = await self._redis.hmget(key, field_list)
                res_dict[key] = dict(zip(field_list, values))

        return res_dict

    def lock(self, key: str):
        return self._redis.lock(key, timeout=10, blocking_timeout=12)

    @property
    def redis(self):
        return self._redis
