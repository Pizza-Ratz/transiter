from transiter.services import transfersconfigservice
from transiter.db import models
from transiter.db.queries import stopqueries
import pytest

SYSTEM_1_ID = "1"
SYSTEM_2_ID = "2"
STOP_1_ID = "3"
STOP_2_ID = "4"
STOP_3_ID = "5"
SYSTEM_1 = models.System(id=SYSTEM_1_ID)
SYSTEM_2 = models.System(id=SYSTEM_2_ID)


def list_all_in_system_factory(stops):
    return lambda system_id: [stop for stop in stops if stop.system.id == system_id]


@pytest.mark.parametrize(
    "stops,distance,expected_tuples",
    [
        [  # Base case
            [
                models.Stop(id=STOP_1_ID, latitude=1, longitude=1, system=SYSTEM_1),
                models.Stop(id=STOP_2_ID, latitude=2, longitude=2, system=SYSTEM_1),
                models.Stop(id=STOP_3_ID, latitude=1.4, longitude=1, system=SYSTEM_2),
            ],
            50000,
            {(STOP_1_ID, STOP_3_ID), (STOP_3_ID, STOP_1_ID)},
        ],
        [  # No matches
            [
                models.Stop(id=STOP_1_ID, latitude=1, longitude=1, system=SYSTEM_1),
                models.Stop(id=STOP_2_ID, latitude=2, longitude=2, system=SYSTEM_1),
                models.Stop(id=STOP_3_ID, latitude=1.4, longitude=1, system=SYSTEM_2),
            ],
            500,
            set(),
        ],
        [  # All stops in one system
            [
                models.Stop(id=STOP_1_ID, latitude=1, longitude=1, system=SYSTEM_1),
                models.Stop(id=STOP_2_ID, latitude=2, longitude=2, system=SYSTEM_1),
                models.Stop(id=STOP_3_ID, latitude=1.4, longitude=1, system=SYSTEM_1),
            ],
            50000,
            set(),
        ],
    ],
)
def test_build_transfers(monkeypatch, stops, distance, expected_tuples):
    monkeypatch.setattr(
        stopqueries,
        "list_all_in_system_with_no_parent",
        list_all_in_system_factory(stops),
    )

    actual_pairs = {
        (transfer.from_stop.id, transfer.to_stop.id)
        for transfer in transfersconfigservice._build_transfers(
            [SYSTEM_1, SYSTEM_2], distance
        )
    }

    assert expected_tuples == actual_pairs
