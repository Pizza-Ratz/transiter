from transiter import models
from transiter.data.queries import alertqueries
import datetime
import pytest

ALERT_ID_1 = "1"
ALERT_ID_2 = "2"
TIME_1 = datetime.datetime.utcfromtimestamp(1000)
TIME_2 = datetime.datetime.utcfromtimestamp(2000)
TIME_3 = datetime.datetime.utcfromtimestamp(3000)

# TODO: empty input test


@pytest.mark.parametrize(
    "alert_start,alert_end,current_time,expect_result",
    [
        [None, TIME_3, TIME_2, True],
        [TIME_1, None, TIME_2, True],
        [TIME_1, TIME_3, TIME_1, True],
        [TIME_1, TIME_3, TIME_2, True],
        [TIME_1, TIME_3, TIME_3, True],
        [TIME_1, TIME_2, TIME_3, False],
        [TIME_2, TIME_3, TIME_1, False],
        [TIME_2, None, TIME_1, False],
        [None, TIME_2, TIME_3, False],
    ],
)
def test_list_alerts__routes(
    add_model,
    system_1,
    route_1_1,
    route_1_2,
    alert_start,
    alert_end,
    current_time,
    expect_result,
):
    alert = add_model(
        models.Alert(
            id=ALERT_ID_1,
            system_pk=system_1.pk,
            active_periods=[
                models.AlertActivePeriod(starts_at=alert_start, ends_at=alert_end)
            ],
        )
    )
    alert.routes = [route_1_1]
    alert_2 = add_model(
        models.Alert(
            id=ALERT_ID_2,
            system_pk=system_1.pk,
            active_periods=[
                models.AlertActivePeriod(starts_at=alert_start, ends_at=alert_end)
            ],
        )
    )
    alert_2.routes = [route_1_2]

    result = alertqueries.get_route_pk_to_active_alerts(
        route_pks=[route_1_1.pk], current_time=current_time
    )

    if expect_result:
        assert {route_1_1.pk: [(alert.active_periods[0], alert)]} == result
    else:
        assert {route_1_1.pk: []} == result


def test_list_alerts__de_duplicate_active_periods(
    add_model, system_1, route_1_1,
):
    alert = add_model(
        models.Alert(
            id=ALERT_ID_1,
            system_pk=system_1.pk,
            active_periods=[
                models.AlertActivePeriod(starts_at=TIME_1, ends_at=TIME_3),
                models.AlertActivePeriod(starts_at=TIME_1, ends_at=TIME_3),
            ],
        )
    )
    alert.routes = [route_1_1]

    result = alertqueries.get_route_pk_to_active_alerts(
        route_pks=[route_1_1.pk], current_time=TIME_2
    )

    assert [alert] == [alert for _, alert in result[route_1_1.pk]]
