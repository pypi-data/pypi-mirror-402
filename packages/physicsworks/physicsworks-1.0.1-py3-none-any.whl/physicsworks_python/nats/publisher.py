import json
from abc import ABC
from stan.aio.client import Client as STAN


class Publisher(ABC):

  def __init__(self, client: STAN, subject: str) -> None:
    self._client = client
    self._subject = subject

  async def publish(self, data):
    bytes_data = json.dumps(data).encode('utf-8')
    await self._client.publish(subject=self._subject, payload=bytes_data)
    print(f'[EVENT ->] Event published to subject {self._subject}')
