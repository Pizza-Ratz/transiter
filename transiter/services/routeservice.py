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
def list_all_in_system(system_id) -> typing.List[views.Route]:
    """
    Get data on all routes in a system.
    """
    system = systemqueries.get_by_id(system_id, only_return_active=True)
    if system is None:
        raise exceptions.IdNotFoundError(models.System, system_id=system_id)
    response = []
    routes = list(routequeries.list_in_system(system_id))
    route_pk_to_active_alert_tuples = alertqueries.get_route_pk_to_active_alerts(
        route.pk for route in routes
    )
    for route in routes:
        route_response = views.Route.from_model(route)
        route_response.alerts = list(
            map(
                views.AlertSmall.from_model,
                (alert for _, alert in route_pk_to_active_alert_tuples[route.pk]),
            )
        )
        response.append(route_response)
    return response


@dbconnection.unit_of_work
def get_in_system_by_id(system_id, route_id) -> views.RouteLarge:
    """
    Get data for a specific route in a specific system.
    """
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
    active_periods_and_alerts = alertqueries.get_route_pk_to_active_alerts([route.pk])[
        route.pk
    ]
    result.alerts = list(
        views.AlertLarge.from_models(active_period, alert)
        for active_period, alert in active_periods_and_alerts
    )
    result.service_maps = servicemapmanager.build_route_service_maps_response(route.pk)
    return result
