import pytest

from transiter import exceptions
from transiter.db import models
from transiter.db.queries import alertqueries, tripqueries, routequeries
from transiter.services import tripservice, views

SYSTEM_ID = "1"
ROUTE_ID = "2"
TRIP_ONE_ID = "3"
TRIP_ONE_PK = 4
TRIP_TWO_ID = "5"
TRIP_TWO_PK = 6
STOP_ONE_ID = "7"
STOP_ONE_NAME = "7-Name"
STOP_TWO_ID = "8"
STOP_TWO_NAME = "8-Name"


@pytest.fixture
def system():
    return models.System(id=SYSTEM_ID)


@pytest.fixture
def route(system):
    return models.Route(id=ROUTE_ID, system=system)


@pytest.fixture
def trip_1(route):
    return models.Trip(pk=TRIP_ONE_PK, id=TRIP_ONE_ID, route=route)


@pytest.fixture
def trip_2(route):
    return models.Trip(pk=TRIP_TWO_PK, id=TRIP_TWO_ID, route=route)


def test_list_all_in_route__route_not_found(monkeypatch):
    """[Trip service] List all in route - route not found"""
    monkeypatch.setattr(
        routequeries, "get_in_system_by_id", lambda *args, **kwargs: None
    )

    with pytest.raises(exceptions.IdNotFoundError):
        tripservice.list_all_in_route(SYSTEM_ID, ROUTE_ID),


def test_list_all_in_route(
    monkeypatch,
    route,
    trip_1,
    trip_2,
    stop_1_model,
    stop_1_small_view,
    stop_2_model,
    stop_2_small_view,
):
    monkeypatch.setattr(
        routequeries, "get_in_system_by_id", lambda *args, **kwargs: route
    )
    monkeypatch.setattr(
        tripqueries, "list_all_in_route_by_pk", lambda *args, **kwargs: [trip_1, trip_2]
    )
    monkeypatch.setattr(
        tripqueries,
        "get_trip_pk_to_last_stop_map",
        lambda *args, **kwargs: {trip_1.pk: stop_1_model, trip_2.pk: stop_2_model},
    )
    monkeypatch.setattr(
        alertqueries, "get_trip_pk_to_active_alerts", lambda *args, **kwargs: {}
    )

    expected = [
        views.Trip(
            id=TRIP_ONE_ID,
            direction_id=None,
            started_at=None,
            updated_at=None,
            last_stop=stop_1_small_view,
            alerts=[],
            _route_id=ROUTE_ID,
            _system_id=SYSTEM_ID,
        ),
        views.Trip(
            id=TRIP_TWO_ID,
            direction_id=None,
            started_at=None,
            updated_at=None,
            last_stop=stop_2_small_view,
            alerts=[],
            _route_id=ROUTE_ID,
            _system_id=SYSTEM_ID,
        ),
    ]

    actual = tripservice.list_all_in_route(SYSTEM_ID, ROUTE_ID)

    assert expected == actual


def test_get_in_route_by_id__trip_not_found(monkeypatch):
    """[Trip service] Get in route - trip not found"""
    monkeypatch.setattr(tripqueries, "get_in_route_by_id", lambda *args, **kwargs: None)

    with pytest.raises(exceptions.IdNotFoundError):
        tripservice.get_in_route_by_id(SYSTEM_ID, ROUTE_ID, TRIP_ONE_ID),


def test_get_in_route_by_id(
    monkeypatch, route, trip_1, stop_1_model, stop_1_small_view
):
    """[Trip service] Get in in route"""

    monkeypatch.setattr(
        tripqueries, "get_in_route_by_id", lambda *args, **kwargs: trip_1
    )
    monkeypatch.setattr(
        alertqueries, "get_trip_pk_to_active_alerts", lambda *args, **kwargs: {}
    )

    stop_time = models.TripStopTime()
    stop_time.stop = stop_1_model
    trip_1.stop_times = [stop_time]

    expected = views.Trip(
        id=TRIP_ONE_ID,
        direction_id=None,
        started_at=None,
        updated_at=None,
        _route_id=ROUTE_ID,
        _system_id=SYSTEM_ID,
        stop_times=[views.TripStopTime.from_model(stop_time)],
        alerts=[],
        route=views.Route.from_model(route),
    )
    expected.stop_times[0].stop = stop_1_small_view

    actual = tripservice.get_in_route_by_id(SYSTEM_ID, ROUTE_ID, TRIP_ONE_ID)

    assert expected == actual
