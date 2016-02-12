from datetime import datetime

from sqlalchemy import DateTime, Date, Time
from sqlalchemy.orm import sessionmaker

from wshubsapi.Hub import Hub


class RelationalDBHub(Hub):
    __HubName__ = None  # with None, hubInspector will ignore this Hub
    engine = None

    def __init__(self):
        super(RelationalDBHub, self).__init__()
        self.EntryTable = None  # defined in subclass

    @classmethod
    def getSession(cls):
        session = sessionmaker(bind=cls.engine, expire_on_commit=False)()
        session._model_changes = {}
        return session

    @classmethod
    def __updateValuesFormDict(cls, entry, newEntryDict):
        """
        :type entry: Base
        """
        for newEntryKey in newEntryDict:
            if newEntryKey in entry.__table__.columns and not newEntryKey in entry.__dict__:
                if isinstance(cls.__dict__[newEntryKey].type, (DateTime, Date, Time,)):
                    entry.__dict__[newEntryKey] = datetime.utcfromtimestamp(newEntryDict[newEntryKey]/1e3)
                else:
                    entry.__dict__[newEntryKey] = newEntryDict[newEntryKey]

    def insert(self, entry2Insert):
        session = self.getSession()
        try:
            entry = self.EntryTable()
            self.__updateValuesFormDict(entry, entry2Insert)
            session.add(entry)
            session.commit()
            self._getClientsHolder().getSubscribedClients().inserted(entry)
            return entry.id
        finally:
            session.close()

    def update(self, entry2Update):
        session = self.getSession()
        try:
            ID = entry2Update.pop("id")
            entry = session.query(self.EntryTable).get(ID)
            self.__updateValuesFormDict(entry, entry2Update)
            session.add(entry)
            session.commit()
            self._getClientsHolder().getSubscribedClients().updated(entry)
            return True
        finally:
            session.close()
