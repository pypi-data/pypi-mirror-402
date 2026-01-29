# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  redis-helper
# FileName:     lock.py
# Description:  支持自动续期的互斥任务锁
# Author:       ASUS
# CreateDate:   2026/01/12
# Copyright ©2011-2026. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import asyncio
import uuid
import socket
import os
import time
import json
import redis.asyncio as redis
from typing import Optional

_RENEW_LUA = """
local v = redis.call("get", KEYS[1])
if not v then return 0 end

local data = cjson.decode(v)
if data["token"] ~= ARGV[1] then
  return 0
end

data["ttl"] = tonumber(ARGV[2])
data["last_renew"] = tonumber(ARGV[3])

redis.call("set", KEYS[1], cjson.encode(data), "ex", ARGV[2])
return 1
"""

_RELEASE_LUA = """
local v = redis.call("get", KEYS[1])
if not v then return 0 end

local data = cjson.decode(v)
if data["token"] ~= ARGV[1] then
  return 0
end

return redis.call("del", KEYS[1])
"""


class RedisWatchdogMutex:
    def __init__(self, redis_client: redis.Redis, key: str, ttl: int = 120):
        self.redis = redis_client
        self.key = key
        self.ttl = ttl

        self.token = uuid.uuid4().hex
        self.owner = f"{socket.gethostname()}-{os.getpid()}"
        self.start = time.time()

        self._stop = asyncio.Event()
        self._renew_task: Optional[asyncio.Task] = None

    def _payload(self):
        return json.dumps({
            "token": self.token,
            "owner": self.owner,
            "pid": os.getpid(),
            "start": self.start,
            "last_renew": time.time(),
            "ttl": self.ttl
        })

    async def acquire(self) -> bool:
        return await self.redis.set(
            self.key,
            self._payload(),
            nx=True,
            ex=self.ttl
        )

    async def _renew_loop(self):
        try:
            while not self._stop.is_set():
                await asyncio.wait_for(self._stop.wait(), timeout=self.ttl / 3)

                if self._stop.is_set():
                    break

                ok = await self.redis.eval(
                    _RENEW_LUA,
                    1,
                    self.key,
                    self.token,
                    self.ttl,
                    time.time()
                )

                if ok != 1:
                    print(f"[LOCK LOST] {self.key} owned by {self.owner}")
                    break

        except asyncio.TimeoutError:
            pass
        except Exception as e:
            print("Renew error:", e)

    async def release(self):
        await self.redis.eval(
            _RELEASE_LUA,
            1,
            self.key,
            self.token
        )

    async def inspect(self):
        v = await self.redis.get(self.key)
        return json.loads(v) if v else None

    async def __aenter__(self):
        ok = await self.acquire()
        if not ok:
            return False

        self._stop.clear()
        self._renew_task = asyncio.create_task(self._renew_loop())
        return True

    async def __aexit__(self, exc_type, exc, tb):
        self._stop.set()
        if self._renew_task:
            try:
                await self._renew_task
            except (Exception,):
                pass

        await self.release()
