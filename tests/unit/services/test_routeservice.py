import pytest
import datetime
from transiter import models, exceptions
from transiter.data import systemqueries, routequeries
from transiter.data.queries import alertqueries
from transiter.services import routeservice, views
from transiter.services.servicemap import servicemapmanager

SYSTEM_ID = "1"
ROUTE_ONE_PK = 2
ROUTE_ONE_ID = "3"
ROUTE_TWO_PK = 4
ROUTE_TWO_ID = "5"
ALERT_ID = "6"
ALERT_HEADER = "Header"
ALERT_DESCRIPTION = "Description"
RAW_FREQUENCY = 700
SERVICE_MAP_ONE_GROUP_ID = "1000"
SERVICE_MAP_TWO_GROUP_ID = "1001"
STOP_ID = "1002"
TIME_1 = datetime.datetime.utcfromtimestamp(1000)
TIME_2 = datetime.datetime.utcfromtimestamp(2000)


@pytest.fixture
def alert_1_model():
    return models.Alert(
        id=ALERT_ID,
        cause=models.Alert.Cause.UNKNOWN_CAUSE,
        effect=models.Alert.Effect.UNKNOWN_EFFECT,
        active_periods=[models.AlertActivePeriod(starts_at=TIME_1, ends_at=TIME_2)],
        messages=[
            models.AlertMessage(header=ALERT_HEADER, description=ALERT_DESCRIPTION)
        ],
    )


@pytest.fixture
def alert_1_small_view():
    return views.AlertSmall(
        id=ALERT_ID,
        cause=models.Alert.Cause.UNKNOWN_CAUSE,
        effect=models.Alert.Effect.UNKNOWN_EFFECT,
    )


@pytest.fixture
def alert_1_large_view():
    return views.AlertLarge(
        id=ALERT_ID,
        cause=models.Alert.Cause.UNKNOWN_CAUSE,
        effect=models.Alert.Effect.UNKNOWN_EFFECT,
        active_period=views.AlertActivePeriod(starts_at=TIME_1, ends_at=TIME_2),
        messages=[
            views.AlertMessage(header=ALERT_HEADER, description=ALERT_DESCRIPTION)
        ],
    )


def test_list_all_in_system__system_not_found(monkeypatch):
    monkeypatch.setattr(systemqueries, "get_by_id", lambda *args, **kwargs: None)

    with pytest.raises(exceptions.IdNotFoundError):
        routeservice.list_all_in_system(SYSTEM_ID)


def test_list_all_in_system(monkeypatch, alert_1_model, alert_1_small_view):
    system = models.System(id=SYSTEM_ID)
    route_one = models.Route(system=system, id=ROUTE_ONE_ID, pk=ROUTE_ONE_PK)
    route_two = models.Route(system=system, id=ROUTE_TWO_ID, pk=ROUTE_TWO_PK)

    monkeypatch.setattr(systemqueries, "get_by_id", lambda *args, **kwargs: system)
    monkeypatch.setattr(
        routequeries, "list_in_system", lambda *args: [route_one, route_two]
    )
    monkeypatch.setattr(
        alertqueries,
        "get_route_pk_to_active_alerts",
        lambda *args: {
            ROUTE_ONE_PK: [(alert_1_model.active_periods[0], alert_1_model)],
            ROUTE_TWO_PK: [],
        },
    )

    expected = [
        views.Route(
            id=ROUTE_ONE_ID,
            color=None,
            _system_id=SYSTEM_ID,
            alerts=[alert_1_small_view],
        ),
        views.Route(id=ROUTE_TWO_ID, color=None, _system_id=SYSTEM_ID, alerts=[]),
    ]

    actual = routeservice.list_all_in_system(SYSTEM_ID)

    assert actual == expected


def test_get_in_system_by_id__route_not_found(monkeypatch):
    monkeypatch.setattr(routequeries, "get_in_system_by_id", lambda *args: None)

    with pytest.raises(exceptions.IdNotFoundError):
        routeservice.get_in_system_by_id(SYSTEM_ID, ROUTE_ONE_ID)


def test_get_in_system_by_id(monkeypatch, alert_1_large_view, alert_1_model):
    system = models.System(id=SYSTEM_ID)
    route_one = models.Route(system=system, id=ROUTE_ONE_ID, pk=ROUTE_ONE_PK)

    monkeypatch.setattr(routequeries, "get_in_system_by_id", lambda *args: route_one)
    monkeypatch.setattr(
        routequeries, "calculate_periodicity", lambda *args: RAW_FREQUENCY
    )
    monkeypatch.setattr(
        alertqueries,
        "get_route_pk_to_active_alerts",
        lambda *args: {
            ROUTE_ONE_PK: [(alert_1_model.active_periods[0], alert_1_model)]
        },
    )
    monkeypatch.setattr(
        servicemapmanager, "build_route_service_maps_response", lambda *args: []
    )

    expected = views.RouteLarge(
        id=ROUTE_ONE_ID,
        periodicity=int(RAW_FREQUENCY / 6) / 10,
        color=None,
        short_name=None,
        long_name=None,
        description=None,
        url=None,
        type=None,
        _system_id=SYSTEM_ID,
        alerts=[alert_1_large_view],
        service_maps=[],
    )

    actual = routeservice.get_in_system_by_id(SYSTEM_ID, ROUTE_ONE_ID)

    assert expected == actual
