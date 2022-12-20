import json
import re

import aioredis
import uvicorn
from fastapi import FastAPI, Body, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.params import Query
from fastapi_cache import JsonCoder, FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from pydantic import Required
from fastapi_cache.decorator import cache
from redis import Redis
from sqlalchemy import false

app = FastAPI()
redis = Redis(
    host="127.0.0.1",
    port=6379,
    password="12345",
    decode_responses=True
)


@cache()
async def get_cache():
    return 1


@app.post('/users/')
@cache(expire=60, coder=JsonCoder)
async def create_user(username: str = Query(default=Required),
                      password: str = Query(default=Required, min_length=8, max_length=50),
                      email: str = Query(default=Required)):
    user_id = redis.incr("user_id")
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.fullmatch(regex, email):
        email = email
    else:
        return {"error": "Invalid email address"}
    user = {
        "id": user_id,
        "username": username,
        "password": password,
        "email": email
    }
    redis.hset(name=f"user:{user_id}", mapping=user)
    return user


@app.get('/users/{user_id}')
@cache(expire=60, coder=JsonCoder)
async def get_user(user_id: int):
    user = redis.hgetall(f"user:{user_id}")
    if user:
        return user
    else:
        return {"Error": "User not found"}


@app.put('/users/{user_id}')
async def update_item(user_id: int,
                      username: str,
                      password: str,
                      email: str):
    user = redis.hgetall(f"user:{user_id}")
    new_user = {
        "username": username,
        "password": password,
        "email": email
    }
    redis.hset(name=f"user:{user_id}", mapping=new_user)
    return user


@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://127.0.0.1", encoding="utf8", decode_responses=True, password="12345")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")


# def user_optima(user_id: int):
#     # First it looks for the data in redis cache
#     data = get_user(user_id)
#
#     # If cache is found then serves the data from cache
#     if data is not None:
#         data = json.loads(data)
#         data["cache"] = True
#         return data
#
#     else:
#         # If cache is not found then sends request to the MapBox API
#         data = get_user(user_id)
#
#         # This block sets saves the respose to redis and serves it directly
#         if data.get("code") == "Ok":
#             data["cache"] = False
#             data = json.dumps(data)
#             state = create_user(user_id,data)
#
#             if state is True:
#                 return json.loads(data)
#         return data
#
#
# @app.get("/user_optima/{user_id}")
# def view(user_id: int):
#     """This will wrap our original route optimization API and
#     incorporate Redis Caching. You'll only expose this API to
#     the end user. """
#
#     # coordinates = "90.3866,23.7182;90.3742,23.7461"
#
#     return user_optima(user_id)


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
