from typing import Any

import redis
from pydantic import BaseModel, UUID4
from uuid import uuid4
from ul_api_utils.utils.memory_db.repository import BaseMemoryDbRepository

redis_client: Any = redis.StrictRedis.from_url("redis://172.19.0.2:6379")
redis_db = BaseMemoryDbRepository(redis_client=redis_client)


class Person(BaseModel):
    id: UUID4
    name: str = 'Slava'


slava = Person(id=uuid4())


redis_db['slava'] = 35
value = redis_db['slava', Person]
value2 = redis_db.get('slava', default=1)
