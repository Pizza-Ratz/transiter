from sqlalchemy import (
    Column,
    Enum,
    TIMESTAMP,
    Integer,
    String,
    Float,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from transiter import parse
from .base import Base
from .updatableentity import updatable_from


@updatable_from(parse.Vehicle)
class Vehicle(Base):
    __tablename__ = "vehicle"

    pk = Column(Integer, primary_key=True)
    id = Column(String)
    source_pk = Column(Integer, ForeignKey("feed_update.pk"), index=True)
    system_pk = Column(Integer, ForeignKey("system.pk"), nullable=False, index=True)

    Status = parse.Vehicle.Status
    CongestionLevel = parse.Vehicle.CongestionLevel

    label = Column(String)
    license_plate = Column(String)
    current_status = Column(
        Enum(Status, native_enum=False), nullable=False, default=Status.IN_TRANSIT_TO
    )
    latitude = Column(Float)
    longitude = Column(Float)
    bearing = Column(Float)
    odometer = Column(Float)
    speed = Column(Float)
    congestion_level = Column(
        Enum(CongestionLevel, native_enum=False),
        nullable=False,
        default=CongestionLevel.UNKNOWN_CONGESTION_LEVEL,
    )
    updated_at = Column(TIMESTAMP(timezone=True))

    source = relationship("FeedUpdate", cascade="none")
    system = relationship("System", back_populates="vehicles", cascade="none")
    trip = relationship("Trip", back_populates="vehicle", cascade="none")

    __table_args__ = (UniqueConstraint(system_pk, id),)
