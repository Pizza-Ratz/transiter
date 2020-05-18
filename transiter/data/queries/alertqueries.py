import collections
import datetime
import typing

from transiter import models
from transiter.data import dbconnection


def get_route_pk_to_active_alerts(
    route_pks, current_time=None, load_messages=False,
) -> typing.Dict[
    int, typing.List[typing.Tuple[models.AlertActivePeriod, models.Alert]]
]:
    route_pks = list(route_pks)
    if len(route_pks) == 0:
        return {}
    if current_time is None:
        current_time = datetime.datetime.utcnow()
    query = (
        dbconnection.get_session()
        .query(models.Route.pk, models.AlertActivePeriod, models.Alert)
        .filter(models.AlertActivePeriod.alert_pk == models.Alert.pk)
        .filter(models.AlertActivePeriod.starts_at <= current_time)
        .filter(models.AlertActivePeriod.ends_at >= current_time)
        .order_by(models.AlertActivePeriod.starts_at)
        .join(models.Alert.routes)
        .filter(models.Route.pk.in_(route_pks))
    )
    route_pk_to_alert_pks = collections.defaultdict(set)
    route_pk_to_tuple = {route_pk: [] for route_pk in route_pks}
    for route_pk, active_period, alert in query.all():
        if alert.pk in route_pk_to_alert_pks[route_pk]:
            continue
        route_pk_to_alert_pks[route_pk].add(alert.pk)
        route_pk_to_tuple[route_pk].append((active_period, alert))
    return route_pk_to_tuple
