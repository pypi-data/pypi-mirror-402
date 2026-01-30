import pymongo


class MongoClientWrapper:

  def __init__(self):
    self.db = None
    self._client = None

  @property
  def client(self):
    if self._client is None:
      raise Exception('Cannot access MongoDB client before connecting!')
    return self._client

  def connect(self, url, dbName):
    try:
      self._client = pymongo.MongoClient(url, serverSelectionTimeoutMS=5000)

      db = self._client[dbName]

      self.db = db

      return db
    except Exception as ex:
      print(ex)


mongoClientWrapper = MongoClientWrapper()
