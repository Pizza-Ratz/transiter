from sqlalchemy import (
    Column,
    TIMESTAMP,
    Integer,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from .base import Base


class AlertActivePeriod(Base):
    __tablename__ = "alert_active_period"

    pk = Column(Integer, primary_key=True)
    alert_pk = Column(Integer, ForeignKey("alert.pk"), index=True, nullable=False)

    starts_at = Column(TIMESTAMP(timezone=True))
    ends_at = Column(TIMESTAMP(timezone=True))

    alert = relationship("Alert", back_populates="active_periods", cascade="none")
