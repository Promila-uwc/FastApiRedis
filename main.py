import os

import aioredis
from fastapi import FastAPI, Body, Depends
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import Redis
from redis_om import get_redis_connection, EmbeddedJsonModel

# from models import User
from fastapi import FastAPI, Request, Response
from fastapi_redis_cache import FastApiRedisCache, cache, cache_one_day
from sqlalchemy.orm import Session
from redis_om.model import NotFoundError

app = FastAPI()

redis = get_redis_connection(
    host="127.0.0.1",
    port=6379,
    password="12345",
    decode_responses=True,
)


@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost", encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")


class User(EmbeddedJsonModel):
    name: str
    email: str

    class Meta:
        database = redis


@app.get("/")
async def root():
    return {"message": "Hello world"}


# create an author
@app.post("/user")
def create_user(user: User):
    return user.save()


# Will be cached for one year
@app.get("/all-users")
@cache_one_day()
async def get_users():
    return User.all_pks()
