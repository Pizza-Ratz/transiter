import pytest

from transiter import models, exceptions
from transiter.data import systemqueries, routequeries
from transiter.services import routeservice, views
from transiter.services.servicemap import servicemapmanager

SYSTEM_ID = "1"
ROUTE_ONE_PK = 2
ROUTE_ONE_ID = "3"
ROUTE_ONE_STATUS = routeservice.Status.GOOD_SERVICE
ROUTE_TWO_PK = 4
ROUTE_TWO_ID = "5"
ROUTE_TWO_STATUS = routeservice.Status.GOOD_SERVICE
RAW_FREQUENCY = 700
SERVICE_MAP_ONE_GROUP_ID = "1000"
SERVICE_MAP_TWO_GROUP_ID = "1001"
STOP_ID = "1002"


def test_list_all_in_system__system_not_found(monkeypatch):
    monkeypatch.setattr(systemqueries, "get_by_id", lambda *args, **kwargs: None)

    with pytest.raises(exceptions.IdNotFoundError):
        routeservice.list_all_in_system(SYSTEM_ID)


def test_list_all_in_system(monkeypatch):
    system = models.System(id=SYSTEM_ID)
    route_one = models.Route(system=system, id=ROUTE_ONE_ID, pk=ROUTE_ONE_PK)
    route_two = models.Route(system=system, id=ROUTE_TWO_ID, pk=ROUTE_TWO_PK)
    monkeypatch.setattr(systemqueries, "get_by_id", lambda *args, **kwargs: system)
    monkeypatch.setattr(
        routequeries, "list_all_in_system", lambda *args: [route_one, route_two]
    )

    expected = [
        views.Route(
            id=ROUTE_ONE_ID, color=None, _system_id=SYSTEM_ID, status=ROUTE_ONE_STATUS
        ),
        views.Route(
            id=ROUTE_TWO_ID, color=None, _system_id=SYSTEM_ID, status=ROUTE_TWO_STATUS
        ),
    ]

    actual = routeservice.list_all_in_system(SYSTEM_ID)

    assert actual == expected


def test_get_in_system_by_id__route_not_found(monkeypatch):
    monkeypatch.setattr(routequeries, "get_in_system_by_id", lambda *args: None)

    with pytest.raises(exceptions.IdNotFoundError):
        routeservice.get_in_system_by_id(SYSTEM_ID, ROUTE_ONE_ID)


def test_get_in_system_by_id(monkeypatch):
    system = models.System(id=SYSTEM_ID)
    route_one = models.Route(system=system, id=ROUTE_ONE_ID)

    monkeypatch.setattr(routequeries, "get_in_system_by_id", lambda *args: route_one)
    monkeypatch.setattr(
        routequeries, "calculate_periodicity", lambda *args: RAW_FREQUENCY
    )
    monkeypatch.setattr(
        servicemapmanager, "build_route_service_maps_response", lambda *args: []
    )

    expected = views.RouteLarge(
        id=ROUTE_ONE_ID,
        periodicity=int(RAW_FREQUENCY / 6) / 10,
        status=ROUTE_ONE_STATUS,
        color=None,
        short_name=None,
        long_name=None,
        description=None,
        url=None,
        type=None,
        _system_id=SYSTEM_ID,
        alerts=[],
        service_maps=[],
    )

    actual = routeservice.get_in_system_by_id(SYSTEM_ID, ROUTE_ONE_ID)

    assert expected == actual
