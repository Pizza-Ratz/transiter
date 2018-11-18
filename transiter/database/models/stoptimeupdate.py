from sqlalchemy import Column, TIMESTAMP, Index, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from .base import Base


class StopTimeUpdate(Base):
    __tablename__ = 'stop_time_update'

    pk = Column(Integer, primary_key=True)
    stop_pk = Column(Integer, ForeignKey('stop.pk'), nullable=False)
    trip_pk = Column(Integer, ForeignKey('trip.pk'), nullable=False)

    direction = Column(String)
    # TODO rename to status and make a string
    future = Column(Boolean, server_default=text('true'))
    arrival_time = Column(TIMESTAMP(timezone=True))
    departure_time = Column(TIMESTAMP(timezone=True))
    last_update_time = Column(TIMESTAMP(timezone=True))
    stop_sequence = Column(Integer, nullable=False)
    track = Column(String)
    stop_id_alias = Column(String)

    stop = relationship(
        'Stop',
        back_populates='stop_events')
    trip = relationship(
        'Trip',
        back_populates='stop_events')

    _short_repr_list = [
        'arrival_time', 'departure_time', 'track', 'stop_sequence', 'stop_id_alias']


Index('stop_time_update_trip_idx', StopTimeUpdate.trip_pk, StopTimeUpdate.arrival_time)
Index('stop_time_update_stop_idx', StopTimeUpdate.stop_pk, StopTimeUpdate.arrival_time)

