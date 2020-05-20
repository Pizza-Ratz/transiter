"""
The route service is used to retrieve data about routes.
"""
import typing

from transiter import exceptions, models
from transiter.data import dbconnection, systemqueries, routequeries
from transiter.data.queries import alertqueries
from transiter.services import views
from transiter.services.servicemap import servicemapmanager


@dbconnection.unit_of_work
def list_all_in_system(
    system_id, alerts_detail: views.AlertDetail = None
) -> typing.List[views.Route]:
    system = systemqueries.get_by_id(system_id, only_return_active=True)
    if system is None:
        raise exceptions.IdNotFoundError(models.System, system_id=system_id)

    response = []
    routes = list(routequeries.list_in_system(system_id))
    for route in routes:
        route_response = views.Route.from_model(route)
        response.append(route_response)
    _add_alerts(
        response,
        {route.id: route.pk for route in routes},
        alerts_detail or views.AlertDetail.CAUSE_AND_EFFECT,
    )
    return response


@dbconnection.unit_of_work
def get_in_system_by_id(
    system_id, route_id, alerts_detail: views.AlertDetail = None
) -> views.RouteLarge:
    route = routequeries.get_in_system_by_id(system_id, route_id)
    if route is None:
        raise exceptions.IdNotFoundError(
            models.Route, system_id=system_id, route_id=route_id
        )

    periodicity = routequeries.calculate_periodicity(route.pk)
    if periodicity is not None:
        periodicity = int(periodicity / 6) / 10
    result = views.RouteLarge.from_model(route, periodicity)
    if route.agency is not None:
        result.agency = views.Agency.from_model(route.agency)
    _add_alerts(
        [result], {route.id: route.pk}, alerts_detail or views.AlertDetail.MESSAGES,
    )
    result.service_maps = servicemapmanager.build_route_service_maps_response(route.pk)
    return result


def _add_alerts(
    routes: typing.List[views.Route], route_id_to_pk, alert_detail: views.AlertDetail
):
    if alert_detail == views.AlertDetail.NONE:
        return
    route_pk_to_alerts = alertqueries.get_route_pk_to_active_alerts(
        route_id_to_pk.values(), load_messages=alert_detail.value.need_messages
    )
    for route in routes:
        route.alerts = [
            alert_detail.value.clazz.from_models(active_period, alert)
            for active_period, alert in route_pk_to_alerts[route_id_to_pk[route.id]]
        ]
