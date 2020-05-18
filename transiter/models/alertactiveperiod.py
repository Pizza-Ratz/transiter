from sqlalchemy import (
    Column,
    TIMESTAMP,
    Integer,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from .base import Base
from transiter import parse

import datetime
import time

# TODO: make this the end of the ex
ONE_YEAR_IN_SECONDS = 60 * 60 * 24 * 365


class AlertActivePeriod(Base):
    __tablename__ = "alert_active_period"

    pk = Column(Integer, primary_key=True)
    alert_pk = Column(Integer, ForeignKey("alert.pk"), index=True, nullable=False)

    starts_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.datetime.utcfromtimestamp(0),
    )
    ends_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.datetime.utcfromtimestamp(time.time() + ONE_YEAR_IN_SECONDS),
    )

    alert = relationship("Alert", back_populates="active_periods", cascade="none")

    @staticmethod
    def from_parsed_active_period(
        active_period: parse.AlertActivePeriod,
    ) -> "AlertActivePeriod":
        return AlertActivePeriod(
            starts_at=active_period.starts_at, ends_at=active_period.ends_at
        )
