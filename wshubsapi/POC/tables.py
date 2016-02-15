# coding: utf-8
from datetime import datetime
from jsonpickle import handlers
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Text, text, create_engine, Float
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import AbstractConcreteBase

Base = declarative_base()


def getDateTime(dateStr):
    if dateStr is None: return None
    return datetime.strptime(dateStr, '%Y/%m/%d %H:%M:%S.%f')


class SqlTableEntity(AbstractConcreteBase, Base):
    @classmethod
    def insertOrUpdateFormDict(cls, session, newEntryDict):
        """
        :type session: Session
        :type newEntryDict: dict

        """
        if "id" in newEntryDict:
            return cls.updateFormDict(session, newEntryDict)
        else:
            return cls.insertFormDict(session, newEntryDict)

    @classmethod
    def __updateValuesFormDict(cls, entry, newEntryDict):
        """
        :type entry: Base
        """
        for newEntryKey in newEntryDict:
            if newEntryKey in entry.__table__.columns and not isinstance(entry.__getattribute__(newEntryKey), Base):
                if isinstance(cls.__dict__[newEntryKey].type, DateTime):
                    entry.__dict__[newEntryKey] = getDateTime(newEntryDict[newEntryKey])
                else:
                    entry.__dict__[newEntryKey] = newEntryDict[newEntryKey]

    @classmethod
    def insertFormDict(cls, session, newEntryDict):
        entry = cls()
        # newEntryDict.pop('id', None)
        cls.__updateValuesFormDict(entry, newEntryDict)
        session.add(entry)
        return entry

    @classmethod
    def updateFormDict(cls, session, newEntryDict):
        id = newEntryDict.pop("id")
        entry = session.query(cls).get(id)
        cls.__updateValuesFormDict(entry, newEntryDict)
        session.add(entry)
        return entry


class User(SqlTableEntity):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(Text(collation=u'utf8_unicode_ci'), nullable=False)
    # PhoneNumber = Column(Text(collation=u'utf8_unicode_ci'), nullable=False)
    iconURI = Column(Text(collation=u'utf8_unicode_ci'))
    email = Column(Text(collation=u'utf8_unicode_ci'), nullable=False)
    GCM_ID = Column(Text(collation=u'utf8_unicode_ci'), nullable=True)
    updatedOn = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Event(SqlTableEntity):
    __tablename__ = 'event'

    id = Column(Integer, primary_key=True)
    creatorId = Column(ForeignKey(u'user.id'), nullable=False, index=True)
    createdOn = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    title = Column(Text(collation=u'utf8_unicode_ci', length=30), nullable=False)
    description = Column(Text(collation=u'utf8_unicode_ci'), nullable=False)
    # Type = Column(Enum(u'Public', u'Private'), nullable=False, server_default=text("'Public'"))
    iconURI = Column(Text(collation=u'utf8_unicode_ci'))
    updatedOn = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    # Range = Column(Integer, nullable=False, default=2000)
    closedOn = Column(DateTime, nullable=True, default=None)

    creator = relationship(u'User', primaryjoin='Event.creatorId == User.id')


class Message(SqlTableEntity):
    __tablename__ = 'message'

    id = Column(Integer, primary_key=True)
    creatorId = Column(ForeignKey(u'user.id'), nullable=False, index=True)
    createdOn = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    body = Column(Text(collation=u'utf8_unicode_ci'))
    eventId = Column(ForeignKey(u'event.id'), nullable=False, index=True)
    updatedOn = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    # UsersLimitation = Column(Integer, nullable=True)
    # Schedule = Column(DateTime, nullable=True)
    # State = Column(Integer, nullable=False, server_default=text("1"), index=True)

    creator = relationship(u'User', primaryjoin='Message.creatorId == User.id', lazy='subquery')
    event = relationship(u'Event', primaryjoin='Message.eventId == Event.id', lazy='subquery')


class User_Event(SqlTableEntity):
    __tablename__ = 'user_event'

    id = Column(Integer, primary_key=True)
    userId = Column(ForeignKey(u'user.id'), nullable=False, index=True)
    eventId = Column(ForeignKey(u'event.id'), nullable=False, index=True)

    user = relationship(u'User', primaryjoin='User_Event.userId == User.id')
    event = relationship(u'Event', primaryjoin='User_Event.eventId == Event.id')
    # rLocation = relationship(u'Place', primaryjoin='Task.LocationId == Place.ID')


class UserLocationHistory(SqlTableEntity):
    __tablename__ = 'user_location_history'
    id = Column(Integer, primary_key=True)
    userId = Column(ForeignKey(u'user.id'), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    createdOn = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = relationship(u'User', primaryjoin='UserLocationHistory.userId == User.id')


class ClientLog(SqlTableEntity):
    __tablename__ = 'client_log'
    id = Column(Integer, primary_key=True)
    userId = Column(ForeignKey(u'user.id'), nullable=False, index=True)
    message = Column(Text(collation=u'utf8_unicode_ci'), nullable=True)
    trace = Column(Text(collation=u'utf8_unicode_ci'), nullable=True, default=None)
    mode = Column(Enum(u'DEBUG', u'INFO', u'WARNING', u'ERROR', u'CRITICAL_ERROR'), nullable=False,
                  server_default=text("'DEBUG'"))
    createdOn = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = relationship(u'User', primaryjoin='ClientLog.userId == User.id')


class MyBaseObject(handlers.BaseHandler):
    def flatten(self, obj, data):
        state = obj.__dict__.copy()
        for key in state:
            if isinstance(state[key], Base):
                state[key] = state[key].__dict__.copy()
                del state[key]['_sa_instance_state']

        del state['_sa_instance_state']
        return state


handlers.register(Base, MyBaseObject, base=True)

if __name__ == '__main__':
    pass
    SqlTableEntity.metadata
    # engine = create_engine("mysql://root@localhost/APITest?charset=utf8", echo=True)
    # SqlTableEntity.metadata.create_all(bind=engine)
    # SqlTableEntity.metadata
    # com = engine.connect()
    # s = select([User])
    # com.execute(s)

    # Session = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)
    # session = Session()
    # session._model_changes = {}
    # u = session.query(User).filter(User.id == 13).first()
    # print u.name
