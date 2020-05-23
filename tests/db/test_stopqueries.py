import datetime

import pytest

from transiter import models
from transiter.db.queries import stopqueries


def test_list_all_in_system(system_1, stop_1_1, stop_1_2, stop_2_1):
    assert [stop_1_1, stop_1_2] == stopqueries.list_all_in_system(system_1.id)


def test_list_all_in_system__no_stops(system_1, stop_2_1):
    assert [] == stopqueries.list_all_in_system(system_1.id)


def test_list_all_in_system__no_system(system_1):
    assert [] == stopqueries.list_all_in_system("unknown_id")


def test_get_in_system_by_id(system_1, stop_1_1, stop_1_2):
    assert stop_1_2 == stopqueries.get_in_system_by_id(system_1.id, stop_1_2.id)


def test_get_in_system_by_id__no_stop(system_1, stop_1_1, stop_1_2):
    assert None is stopqueries.get_in_system_by_id(system_1.id, "unknown_id")


def test_get_in_system_by_id__no_system(system_1, stop_1_1, stop_1_2):
    assert None is stopqueries.get_in_system_by_id("unknown_id", stop_1_2.id)


def test_get_id_to_pk_map_in_system(system_1, stop_1_1, stop_1_2, stop_2_1):
    expected = {
        stop_1_1.id: stop_1_1.pk,
        stop_2_1.id: None,
        "unknown_id": None,
    }

    actual = stopqueries.get_id_to_pk_map_in_system(system_1.pk, expected.keys())

    assert expected == actual


def test_get_id_to_pk_map_in_system__all_stops(system_1, stop_1_1, stop_1_2, stop_2_1):
    expected = {
        stop_1_1.id: stop_1_1.pk,
        stop_1_2.id: stop_1_2.pk,
    }

    actual = stopqueries.get_id_to_pk_map_in_system(system_1.pk)

    assert expected == actual


def test_list_stop_time_updates_at_stops__no_stop_times(
    stop_1_4, trip_1, trip_2, trip_3
):
    actual_stop_times = stopqueries.list_stop_time_updates_at_stops([])

    assert [] == actual_stop_times


def test_list_stop_time_updates_at_stops(stop_1_4, trip_1, trip_2, trip_3):
    actual_stop_times = stopqueries.list_stop_time_updates_at_stops([stop_1_4.pk])
    actual_trips = [actual_stop_time.trip for actual_stop_time in actual_stop_times]

    assert [trip_1, trip_2, trip_3] == actual_trips


def test_list_stop_time_updates_at_stops__earliest_time(
    stop_1_4, trip_1, trip_2, trip_3
):
    actual_stop_times = stopqueries.list_stop_time_updates_at_stops(
        [stop_1_4.pk], earliest_time=datetime.datetime(2018, 11, 2, 10, 30, 0)
    )
    actual_trips = [actual_stop_time.trip for actual_stop_time in actual_stop_times]

    assert [trip_2, trip_3] == actual_trips


def test_list_stop_time_updates_at_stops__latest_time(stop_1_4, trip_1, trip_2, trip_3):
    actual_stop_times = stopqueries.list_stop_time_updates_at_stops(
        [stop_1_4.pk], latest_time=datetime.datetime(2018, 11, 2, 11, 30, 0)
    )
    actual_trips = [actual_stop_time.trip for actual_stop_time in actual_stop_times]

    assert [trip_1, trip_2] == actual_trips


def test_list_stop_time_updates_at_stops__earliest_and_latest_time(
    stop_1_4, trip_1, trip_2, trip_3
):
    actual_stop_times = stopqueries.list_stop_time_updates_at_stops(
        [stop_1_4.pk],
        earliest_time=datetime.datetime(2018, 11, 2, 10, 30, 0),
        latest_time=datetime.datetime(2018, 11, 2, 11, 30, 0),
    )
    actual_trips = [actual_stop_time.trip for actual_stop_time in actual_stop_times]

    assert [trip_2] == actual_trips


def test_get_stop_pk_to_station_pk(
    system_1, stop_1_1, stop_1_2, stop_1_3, stop_1_4, stop_2_1
):
    expected = {
        stop_1_1.pk: stop_1_1.pk,
        stop_1_2.pk: stop_1_2.pk,
        stop_1_3.pk: stop_1_2.pk,
        stop_1_4.pk: stop_1_4.pk,
    }

    actual = stopqueries.get_stop_pk_to_station_pk_map_in_system(system_1.id)

    assert expected == actual


@pytest.mark.parametrize("base_pk", [1000, 1001, 1002, 1003, 1004, 1005])
def test_list_all_stops_in_stop_tree(add_model, system_1, base_pk):
    #      2
    #    / | \
    #   1  3  4
    #  /   |
    # 0    5
    add_model(models.Stop(pk=1002, system=system_1, type=models.Stop.Type.STATION))
    add_model(
        models.Stop(
            pk=1001, parent_stop_pk=1002, system=system_1, type=models.Stop.Type.STATION
        )
    )
    add_model(
        models.Stop(
            pk=1000, parent_stop_pk=1001, system=system_1, type=models.Stop.Type.STATION
        )
    )
    add_model(
        models.Stop(
            pk=1003, parent_stop_pk=1002, system=system_1, type=models.Stop.Type.STATION
        )
    )
    add_model(
        models.Stop(
            pk=1005, parent_stop_pk=1003, system=system_1, type=models.Stop.Type.STATION
        )
    )
    add_model(
        models.Stop(
            pk=1004, parent_stop_pk=1002, system=system_1, type=models.Stop.Type.STATION
        )
    )

    # Red herring
    add_model(models.Stop(pk=1012, system=system_1, type=models.Stop.Type.STATION))

    expected_pks = {1000, 1001, 1002, 1003, 1004, 1005}

    actual_pks = {stop.pk for stop in stopqueries.list_all_stops_in_stop_tree(base_pk)}

    assert expected_pks == actual_pks


@pytest.mark.parametrize("stations_only", [True, False])
def test_build_stop_pk_to_descendant_pks_map(add_model, system_1, stations_only):
    #      2
    #    / | \
    #   1  3  4
    #  /   |
    # 0    5
    add_model(models.Stop(pk=1002, system=system_1, type=models.Stop.Type.STATION))
    add_model(
        models.Stop(
            pk=1001, parent_stop_pk=1002, system=system_1, type=models.Stop.Type.STATION
        )
    )
    add_model(
        models.Stop(
            pk=1000,
            parent_stop_pk=1001,
            system=system_1,
            type=models.Stop.Type.PLATFORM,
        )
    )
    add_model(
        models.Stop(
            pk=1003, parent_stop_pk=1002, system=system_1, type=models.Stop.Type.STATION
        )
    )
    add_model(
        models.Stop(
            pk=1005,
            parent_stop_pk=1003,
            system=system_1,
            type=models.Stop.Type.PLATFORM,
        )
    )
    add_model(
        models.Stop(
            pk=1004, parent_stop_pk=1002, system=system_1, type=models.Stop.Type.STATION
        )
    )

    # Red herring
    add_model(models.Stop(pk=1012, system=system_1, type=models.Stop.Type.STATION))

    if stations_only:
        expected_map = {1002: {1001, 1002, 1003, 1004}}
    else:
        expected_map = {1002: {1000, 1001, 1002, 1003, 1004, 1005}}

    actual_map = stopqueries.build_stop_pk_to_descendant_pks_map(
        [1002], stations_only=stations_only
    )
    assert expected_map == actual_map


def test_list_direction_rules(add_model, stop_1_1, stop_1_2, stop_1_3):
    rule_1 = add_model(models.DirectionRule(stop=stop_1_1))
    rule_2 = add_model(models.DirectionRule(stop=stop_1_2))
    add_model(models.DirectionRule(stop=stop_1_3))

    assert [rule_1, rule_2] == stopqueries.list_direction_rules_for_stops(
        [stop_1_1.pk, stop_1_2.pk]
    )
