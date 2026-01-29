import asyncio

from nats.aio.client import Client as NATS
from stan.aio.client import Client as STAN


class NatsClientWrapper:

  def __init__(self):
    self._nc = None
    self._client = None

  @property
  def client(self):
    if self._client is None:
      raise Exception('Cannot access NATS client before connecting!')
    return self._client

  async def disconnected_cb():
    print('Got disconnected!')

  async def reconnected_cb(self):
    print(f'Got reconnected to {self._nc.connected_url.netloc}')

  # async def error_cb(e):
  #   print(f'There was an error: {e}')

  async def closed_cb():
    print('Connection is closed')

  async def connect(self, url: str, clusterId: str, clientId: str, io_loop=None):
    while True:
      try:
        nc = NATS()
        await nc.connect(
            servers=[url],
            io_loop=io_loop,
            disconnected_cb=self.disconnected_cb,
            reconnected_cb=self.reconnected_cb,
            ping_interval=60,
            #  error_cb=self.error_cb,
            closed_cb=self.closed_cb)

        self._nc = nc

        # Start session with NATS Streaming cluster.
        sc = STAN()
        await sc.connect(clusterId, clientId, nats=nc)

        self._client = sc

        break
      except Exception as ex:
        # Could not connect to any server in the cluster.
        print(ex)

        await asyncio.sleep(5)

        continue


natsClientWrapper = NatsClientWrapper()
