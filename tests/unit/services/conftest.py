from transiter.db import models
import pytest
import datetime
from transiter.services import views

SYSTEM_ID = "1"
ROUTE_ONE_PK = 2
ROUTE_ONE_ID = "3"
ROUTE_TWO_PK = 4
ROUTE_TWO_ID = "5"
ALERT_ID = "6"
ALERT_HEADER = "Header"
ALERT_DESCRIPTION = "Description"
SERVICE_MAP_ONE_GROUP_ID = "1000"
SERVICE_MAP_TWO_GROUP_ID = "1001"
STOP_ONE_ID = "7"
STOP_ONE_NAME = "7-Name"
STOP_TWO_ID = "8"
STOP_TWO_NAME = "8-Name"
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


@pytest.fixture
def system_1_model():
    return models.System(id=SYSTEM_ID)


@pytest.fixture
def route_1_model(system_1_model):
    return models.Route(
        system=system_1_model,
        id=ROUTE_ONE_ID,
        color="route_1_color",
        short_name="route_1_short_name",
        long_name="route_1_long_name",
        description="route_1_description",
        url="route_1_url",
        type=models.Route.Type.FUNICULAR,
        pk=ROUTE_ONE_PK,
    )


@pytest.fixture
def route_1_small_view():
    return views.Route(id=ROUTE_ONE_ID, color="route_1_color", _system_id=SYSTEM_ID)


@pytest.fixture
def route_1_large_view():
    return views.RouteLarge(
        id=ROUTE_ONE_ID,
        periodicity=0,
        color="route_1_color",
        short_name="route_1_short_name",
        long_name="route_1_long_name",
        description="route_1_description",
        url="route_1_url",
        type=models.Route.Type.FUNICULAR,
        _system_id=SYSTEM_ID,
    )


@pytest.fixture
def route_2_model(system_1_model):
    return models.Route(
        system=system_1_model, id=ROUTE_TWO_ID, color="route_2_color", pk=ROUTE_TWO_PK
    )


@pytest.fixture
def route_2_small_view():
    return views.Route(id=ROUTE_TWO_ID, color="route_2_color", _system_id=SYSTEM_ID)


@pytest.fixture
def stop_1_model(system):
    return models.Stop(id=STOP_ONE_ID, name=STOP_ONE_NAME, system=system)


@pytest.fixture
def stop_1_small_view(system):
    return views.Stop(id=STOP_ONE_ID, name=STOP_ONE_NAME, _system_id=SYSTEM_ID)


@pytest.fixture
def stop_2_model(system):
    return models.Stop(id=STOP_TWO_ID, name=STOP_TWO_NAME, system=system)


@pytest.fixture
def stop_2_small_view(system):
    return views.Stop(id=STOP_TWO_ID, name=STOP_TWO_NAME, _system_id=SYSTEM_ID)
