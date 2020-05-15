from sqlalchemy import (
    Column,
    TIMESTAMP,
    Table,
    Integer,
    String,
    ForeignKey,
    Enum,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from transiter import parse
from .base import Base
from .updatableentity import updatable_from


@updatable_from(parse.Alert)
class Alert(Base):
    __tablename__ = "alert"

    pk = Column(Integer, primary_key=True)
    id = Column(String)
    source_pk = Column(Integer, ForeignKey("feed_update.pk"), index=True)
    system_pk = Column(Integer, ForeignKey("system.pk"), index=True)

    Cause = parse.Alert.Cause
    Effect = parse.Alert.Effect

    cause = Column(Enum(Cause, native_enum=False))
    effect = Column(Enum(Effect, native_enum=False))
    sort_order = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True))
    updated_at = Column(TIMESTAMP(timezone=True))

    messages = relationship(
        "AlertMessages", back_populates="alert", cascade="all, delete-orphan"
    )
    active_periods = relationship(
        "AlertActivePeriod", back_populates="alert", cascade="all, delete-orphan"
    )
    source = relationship("FeedUpdate", cascade="none")
    agencies = relationship(
        "Agency", secondary="alert_agency", back_populates="alerts", cascade="none",
    )
    routes = relationship(
        "Route", secondary="alert_route", back_populates="alerts", cascade="none",
    )
    stops = relationship(
        "Stop", secondary="alert_stop", back_populates="alerts", cascade="none",
    )
    trips = relationship(
        "Trip", secondary="alert_trip", back_populates="alerts", cascade="none",
    )

    __table_args__ = (UniqueConstraint("system_pk", "id"),)

    @staticmethod
    def from_parsed_alert(alert: parse.Alert) -> "Alert":
        return Alert(id=alert.id, cause=alert.cause, effect=alert.effect,)


alert_agency = Table(
    "alert_agency",
    Base.metadata,
    Column("alert_pk", Integer, ForeignKey("alert.pk"), index=True),
    Column("agency_pk", Integer, ForeignKey("agency.pk"), index=True),
)

alert_route = Table(
    "alert_route",
    Base.metadata,
    Column("alert_pk", Integer, ForeignKey("alert.pk"), index=True),
    Column("route_pk", Integer, ForeignKey("route.pk"), index=True),
)

alert_stop = Table(
    "alert_stop",
    Base.metadata,
    Column("alert_pk", Integer, ForeignKey("alert.pk"), index=True),
    Column("stop_pk", Integer, ForeignKey("stop.pk"), index=True),
)

alert_trip = Table(
    "alert_trip",
    Base.metadata,
    Column("alert_pk", Integer, ForeignKey("alert.pk"), index=True),
    Column("trip_pk", Integer, ForeignKey("trip.pk"), index=True),
)
