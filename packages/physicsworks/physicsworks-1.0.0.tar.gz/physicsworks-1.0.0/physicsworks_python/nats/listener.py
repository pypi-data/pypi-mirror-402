from abc import ABC, abstractmethod

from stan.aio.client import Client as STAN
from stan.aio.client import Msg


class Listener(ABC):

  def __init__(self, stan: STAN, subject: str, queueGroupName: str) -> None:
    self.__client = stan

    self._subject = subject
    self._queueGroupName = queueGroupName

  @abstractmethod
  async def onMessage(self, msg: Msg) -> None:
    print("Received a message (seq={}): {}".format(msg.seq, msg.data))

    await self.__client.ack(msg)

  # async def onError(ex):
  #   print("NATS: An error occured", ex)

  async def listen(self, ack_wait: int = 30) -> None:
    await self.__client.subscribe(
        subject=self._subject,
        queue=self._queueGroupName,
        deliver_all_available=True,
        manual_acks=True,
        ack_wait=ack_wait,
        durable_name=self._queueGroupName,
        cb=self.onMessage,
        # error_cb=self.onError
    )
