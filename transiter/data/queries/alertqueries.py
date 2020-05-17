import time

from transiter.data import dbconnection
from transiter import models
import typing


def list_alerts(
    *,
    system_pk=None,
    route_pks=None,
    stop_ids=None,
    trip_ids=None,
    agency_ids=None,
    current_time=time.time(),
    load_messages=False,
    load_all_active_periods=False,
) -> typing.List[typing.Tuple[models.AlertActivePeriod, models.Alert]]:
    # TODO: overlapping alert active periods? don't want duplicate results!
    query = (
        dbconnection.get_session()
        .query(models.AlertActivePeriod, models.Alert)
        .filter(models.AlertActivePeriod.alert_pk == models.Alert.pk)
        .filter(models.AlertActivePeriod.starts_at <= current_time)
        .filter(models.AlertActivePeriod.ends_at >= current_time)
    )
    if route_pks is not None:
        if len(route_pks) == 0:
            return []
        query = query.join(models.Alert.routes).filter(models.Route.pk.in_(route_pks))

    print(query)
    return query.all()
