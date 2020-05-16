"""
The route service is used to retrieve data about routes.
"""
import typing

from transiter import exceptions, models
from transiter.data import dbconnection, systemqueries, routequeries
from transiter.models import Alert
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
    routes = list(routequeries.list_all_in_system(system_id))
    for route in routes:
        route_response = views.Route.from_model(route)
        # TODO: add alerts
        route_response.status = views.Route.Status.GOOD_SERVICE
        response.append(route_response)
    return response


@dbconnection.unit_of_work
def get_in_system_by_id(system_id, route_id) -> views.RouteLarge:
    """
    Get data for a specific route in a specific system.
    """
    route = routequeries.get_in_system_by_id(system_id, route_id)
    # TODO get alerts separately using active time
    if route is None:
        raise exceptions.IdNotFoundError(
            models.Route, system_id=system_id, route_id=route_id
        )
    periodicity = routequeries.calculate_periodicity(route.pk)
    if periodicity is not None:
        periodicity = int(periodicity / 6) / 10
    result = views.RouteLarge.from_model(
        route, views.Route.Status.GOOD_SERVICE, periodicity
    )
    if route.agency is not None:
        result.agency = views.Agency.from_model(route.agency)
    result.alerts = list(map(views.AlertLarge.from_model, route.alerts))
    result.service_maps = servicemapmanager.build_route_service_maps_response(route.pk)
    return result


Status = views.Route.Status
