from datetime import datetime

from sqlalchemy import DateTime, Date, Time
from sqlalchemy.orm import sessionmaker
from wshubsapi.Hub import Hub


class RelationalDBHub(Hub):
    __HubName__ = None  # with None, hubInspector will ignore this Hub
    engine = None

    def __init__(self):
        super(RelationalDBHub, self).__init__()
        self._entryTable = None  # defined in plugging creation
        self.__mainPrimaryKey = None

    @property
    def entryTable(self):
        return self._entryTable

    @entryTable.setter
    def entryTable(self, value):
        self.__mainPrimaryKey = self.entryTable.primary_key.columns[0].key
        self._entryTable = value

    @classmethod
    def _getSession(cls):
        session = sessionmaker(bind=cls.engine, expire_on_commit=False)()
        session._model_changes = {}
        return session

    @classmethod
    def __updateValuesFormDict(cls, entry, newEntryDict):
        """
        :type entry: Base
        """
        for newEntryKey in newEntryDict:
            if newEntryKey in entry.__table__.columns and newEntryKey not in entry.__dict__:
                if isinstance(cls.__dict__[newEntryKey].type, (DateTime, Date, Time,)):
                    entry.__dict__[newEntryKey] = datetime.utcfromtimestamp(newEntryDict[newEntryKey]/1e3)
                else:
                    entry.__dict__[newEntryKey] = newEntryDict[newEntryKey]

    def insert(self, entry2Insert):
        session = self._getSession()
        try:
            entry = self.entryTable()
            self.__updateValuesFormDict(entry, entry2Insert)
            session.add(entry)
            session.commit()
            self._get_clients_holder().get_subscribed_clients().inserted(entry)
            return entry.id
        finally:
            session.close()

    def update(self, entry2Update):
        session = self._getSession()
        try:
            ID = entry2Update.pop(self.__mainPrimaryKey)
            entry = session.query(self.entryTable).get(ID)
            self.__updateValuesFormDict(entry, entry2Update)
            session.add(entry)
            session.commit()
            self._get_clients_holder().get_subscribed_clients().updated(entry)
            return True
        finally:
            session.close()
