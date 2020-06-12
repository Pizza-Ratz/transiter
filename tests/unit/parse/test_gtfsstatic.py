import datetime
import io
import unittest
import zipfile
from unittest import mock

import pytest

from transiter import parse
from transiter.db import models
from transiter.parse import gtfsstatic as gtfsstaticparser

ROUTE_ID = "L"
ROUTE_COLOR = "red"
ROUTE_DESCRIPTION = "All times"

STOP_ID = "N1"
STOP_NAME = "This stop"
STOP_ID_2 = "N2"
STOP_NAME_2 = "This stop 2"
STOP_LON = "3.67"
STOP_LAT = "4.003"

SERVICE_ID = "M"
TRIP_ID = "Z"


def test_parse_routes():
    gtfs_static_file = mock.Mock()
    gtfs_static_file.routes.return_value = [
        {
            "route_id": ROUTE_ID,
            "route_color": ROUTE_COLOR,
            "route_desc": ROUTE_DESCRIPTION,
            "route_type": models.Route.Type.RAIL.value,
        }
    ]

    expected_route = parse.Route(
        id=ROUTE_ID,
        color=ROUTE_COLOR,
        description=ROUTE_DESCRIPTION,
        text_color="000000",
        type=models.Route.Type.RAIL,
    )

    assert [expected_route] == list(gtfsstaticparser._parse_routes(gtfs_static_file))


def test_parse(monkeypatch):
    monkeypatch.setattr(gtfsstaticparser, "_parse_routes", lambda *args, **kwargs: [1])
    monkeypatch.setattr(gtfsstaticparser, "_parse_stops", lambda *args, **kwargs: [2])
    monkeypatch.setattr(
        gtfsstaticparser, "_parse_schedule", lambda *args, **kwargs: [3]
    )
    monkeypatch.setattr(gtfsstaticparser, "_GtfsStaticFile", mock.MagicMock())

    parser = gtfsstaticparser.GtfsStaticParser()
    parser.load_content(b"")

    assert [1] == list(parser.get_routes())
    assert [2] == list(parser.get_stops())
    assert [3] == list(parser.get_scheduled_services())


@pytest.fixture
def mock_create_station(monkeypatch):
    mock_create = mock.MagicMock()
    monkeypatch.setattr(
        gtfsstaticparser, "_create_station_from_child_stops", mock_create
    )
    return mock_create


def test_parse_stops__single_stop(mock_create_station):
    gtfs_static_file = mock.Mock()
    gtfs_static_file.stops.return_value = [
        {
            "stop_id": STOP_ID,
            "stop_name": STOP_NAME,
            "stop_lon": STOP_LON,
            "stop_lat": STOP_LAT,
            "location_type": "0",
        }
    ]
    gtfs_static_file.transfers.return_value = []

    expected_stop = parse.Stop(
        id=STOP_ID,
        name=STOP_NAME,
        longitude=float(STOP_LON),
        latitude=float(STOP_LAT),
        type=parse.Stop.Type.PLATFORM,
    )

    assert [expected_stop] == list(
        gtfsstaticparser._parse_stops(
            gtfs_static_file, gtfsstaticparser._TransfersConfig()
        )
    )


def test_parse_stops__parent_and_child_stop(mock_create_station):
    gtfs_static_file = mock.Mock()
    gtfs_static_file.stops.return_value = [
        {
            "stop_id": STOP_ID,
            "stop_name": STOP_NAME,
            "stop_lon": STOP_LON,
            "stop_lat": STOP_LAT,
            "location_type": "0",
            "parent_station": STOP_ID_2,
        },
        {
            "stop_id": STOP_ID_2,
            "stop_name": STOP_NAME_2,
            "stop_lon": STOP_LON,
            "stop_lat": STOP_LAT,
            "location_type": "1",
            "parent_station": "",
        },
    ]
    gtfs_static_file.transfers.return_value = []

    expected_stop_2 = parse.Stop(
        id=STOP_ID_2,
        name=STOP_NAME_2,
        longitude=float(STOP_LON),
        latitude=float(STOP_LAT),
        type=parse.Stop.Type.STATION,
    )
    expected_stop_1 = parse.Stop(
        id=STOP_ID,
        name=STOP_NAME,
        longitude=float(STOP_LON),
        latitude=float(STOP_LAT),
        type=parse.Stop.Type.PLATFORM,
        parent_stop=expected_stop_2,
    )

    actual_stops = list(
        gtfsstaticparser._parse_stops(
            gtfs_static_file, gtfsstaticparser._TransfersConfig()
        )
    )

    assert [expected_stop_1, expected_stop_2] == actual_stops


@pytest.mark.parametrize(
    "transfers_strategy,expect_station",
    [
        [gtfsstaticparser._TransfersStrategy.GROUP_STATIONS, True],
        [gtfsstaticparser._TransfersStrategy.DEFAULT, False],
    ],
)
def test_parse_stops__group_stations(
    mock_create_station, transfers_strategy, expect_station
):
    gtfs_static_file = mock.Mock()
    gtfs_static_file.stops.return_value = [
        {
            "stop_id": STOP_ID,
            "stop_name": STOP_NAME,
            "stop_lon": STOP_LON,
            "stop_lat": STOP_LAT,
            "location_type": "1",
        },
        {
            "stop_id": STOP_ID_2,
            "stop_name": STOP_NAME_2,
            "stop_lon": STOP_LON,
            "stop_lat": STOP_LAT,
            "location_type": "1",
        },
    ]
    gtfs_static_file.transfers.return_value = [
        {"from_stop_id": STOP_ID, "to_stop_id": STOP_ID_2},
        {"from_stop_id": STOP_ID, "to_stop_id": STOP_ID},
    ]

    expected_station = parse.Stop(
        id="FakeID",
        name="",
        longitude=0,
        latitude=0,
        type=parse.Stop.Type.GROUPED_STATION,
    )
    mock_create_station.return_value = expected_station
    expected_stop_1 = parse.Stop(
        id=STOP_ID,
        name=STOP_NAME,
        longitude=float(STOP_LON),
        latitude=float(STOP_LAT),
        type=parse.Stop.Type.STATION,
    )
    expected_stop_2 = parse.Stop(
        id=STOP_ID_2,
        name=STOP_NAME_2,
        longitude=float(STOP_LON),
        latitude=float(STOP_LAT),
        type=parse.Stop.Type.STATION,
    )
    if expect_station:
        expected_stop_1.parent_stop = expected_station
        expected_stop_2.parent_stop = expected_station

    actual_stops = list(
        gtfsstaticparser._parse_stops(
            gtfs_static_file,
            gtfsstaticparser._TransfersConfig(default_strategy=transfers_strategy),
        )
    )

    expected = [expected_stop_1, expected_stop_2]
    if expect_station:
        expected.append(expected_station)

    assert expected == actual_stops


def test_create_station_from_child_stops():
    child_1 = parse.Stop(
        id="A", name="Name 1", latitude=4, longitude=1, type=parse.Stop.Type.STATION
    )
    child_2 = parse.Stop(
        id="B", name="Name 1", latitude=1, longitude=1, type=parse.Stop.Type.STATION
    )
    child_3 = parse.Stop(
        id="C", name="Name 2", latitude=1, longitude=1, type=parse.Stop.Type.STATION
    )

    expected_station = parse.Stop(
        id="A-B-C",
        name="Name 1",
        latitude=2,
        longitude=1,
        type=parse.Stop.Type.GROUPED_STATION,
    )

    actual_station = gtfsstaticparser._create_station_from_child_stops(
        [child_1, child_2, child_3]
    )

    assert expected_station == actual_station


def test_create_station_from_child_stops_hybrid_name():
    child_1 = parse.Stop(
        id="A", name="Name 1", latitude=3, longitude=1, type=parse.Stop.Type.STATION
    )
    child_2 = parse.Stop(
        id="B", name="Name 2", latitude=1, longitude=1, type=parse.Stop.Type.STATION
    )

    expected_station = parse.Stop(
        id="A-B",
        name="Name 1 / Name 2",
        latitude=2,
        longitude=1,
        type=parse.Stop.Type.GROUPED_STATION,
    )

    actual_station = gtfsstaticparser._create_station_from_child_stops(
        [child_1, child_2]
    )

    assert expected_station == actual_station


def test_create_station_from_child_stops_substring_case():
    child_1 = parse.Stop(
        id="A", name="Name 1", latitude=3, longitude=1, type=parse.Stop.Type.STATION
    )
    child_2 = parse.Stop(
        id="B",
        name="Name 1 (and more)",
        latitude=1,
        longitude=1,
        type=parse.Stop.Type.STATION,
    )

    expected_station = parse.Stop(
        id="A-B",
        name="Name 1 (and more)",
        latitude=2,
        longitude=1,
        type=parse.Stop.Type.GROUPED_STATION,
    )

    actual_station = gtfsstaticparser._create_station_from_child_stops(
        [child_1, child_2]
    )

    assert expected_station == actual_station


@pytest.mark.parametrize(
    "input_direction,output_direction",
    [["1", True], ["0", False], ["unknown", None], ["", None]],
)
def test_parse_services_with_trips(input_direction, output_direction):
    gtfs_static_file = mock.Mock()

    gtfs_static_file.trip_frequencies.return_value = [
        {
            "trip_id": TRIP_ID,
            "start_time": "03:04:05",
            "end_time": "06:07:08",
            "headway": 20,
        },
        {
            "trip_id": "Unknown trip ID",
            "start_time": "03:04:05",
            "end_time": "06:07:08",
            "headway": 26,
        },
    ]
    frequency = parse.ScheduledTripFrequency(
        start_time=datetime.time(3, 4, 5),
        end_time=datetime.time(6, 7, 8),
        headway=20,
        frequency_based=True,
    )

    gtfs_static_file.stop_times.return_value = [
        {
            "trip_id": TRIP_ID,
            "stop_id": STOP_ID,
            "stop_sequence": "1",
            "departure_time": "11:12:13",
            "arrival_time": "11:12:13",
        },
        {
            "trip_id": "Unknown trip ID",
            "stop_id": STOP_ID_2,
            "stop_sequence": "1",
            "departure_time": "11:12:13",
            "arrival_time": "11:12:13",
        },
    ]
    stop_time = parse.ScheduledTripStopTime(
        stop_sequence=1,
        stop_id=STOP_ID,
        departure_time=datetime.time(hour=11, minute=12, second=13),
        arrival_time=datetime.time(hour=11, minute=12, second=13),
    )

    gtfs_static_file.trips.return_value = [
        {
            "service_id": SERVICE_ID,
            "trip_id": TRIP_ID,
            "route_id": ROUTE_ID,
            "direction_id": input_direction,
        },
        {
            "service_id": "Unknown service ID",
            "trip_id": TRIP_ID,
            "route_id": ROUTE_ID,
            "direction_id": input_direction,
        },
    ]
    trip = parse.ScheduledTrip(
        id=TRIP_ID,
        route_id=ROUTE_ID,
        direction_id=output_direction,
        stop_times=[stop_time],
        frequencies=[frequency],
    )

    gtfs_static_file.calendar.return_value = [
        {
            "service_id": SERVICE_ID,
            "monday": "1",
            "tuesday": "1",
            "wednesday": "1",
            "thursday": "0",
            "friday": "0",
            "saturday": "0",
            "sunday": "0",
            "start_date": "20180101",
            "end_date": "20181231",
        }
    ]
    gtfs_static_file.calendar_dates.return_value = []
    service = parse.ScheduledService(
        id=SERVICE_ID,
        monday=True,
        tuesday=True,
        wednesday=True,
        thursday=False,
        friday=False,
        saturday=False,
        sunday=False,
        start_date=datetime.date(year=2018, month=1, day=1),
        end_date=datetime.date(year=2018, month=12, day=31),
        trips=[trip],
    )

    actual_services = list(gtfsstaticparser._parse_schedule(gtfs_static_file))

    assert [service] == actual_services


@pytest.mark.parametrize("calendar_set", [True, False])
@pytest.mark.parametrize(
    "exception_type,expected_added_dates,expected_removed_dates",
    [
        ["1", [datetime.date(year=2019, month=3, day=4)], []],
        ["2", [], [datetime.date(year=2019, month=3, day=4)]],
    ],
)
def test_parse_services__exception_days_handling(
    calendar_set, exception_type, expected_added_dates, expected_removed_dates
):
    gtfs_static_file = mock.Mock()
    gtfs_static_file.trips.return_value = []
    gtfs_static_file.stop_times.return_value = []
    gtfs_static_file.trip_frequencies.return_value = []

    if calendar_set:
        gtfs_static_file.calendar.return_value = [
            {
                "service_id": SERVICE_ID,
                "monday": "1",
                "tuesday": "1",
                "wednesday": "1",
                "thursday": "0",
                "friday": "0",
                "saturday": "0",
                "sunday": "0",
                "start_date": "20180101",
                "end_date": "20181231",
            }
        ]
    else:
        gtfs_static_file.calendar.return_value = []

    gtfs_static_file.calendar_dates.return_value = [
        {"service_id": SERVICE_ID, "exception_type": exception_type, "date": "20190304"}
    ]

    service = parse.ScheduledService(
        id=SERVICE_ID,
        monday=calendar_set,
        tuesday=calendar_set,
        wednesday=calendar_set,
        thursday=False,
        friday=False,
        saturday=False,
        sunday=False,
        start_date=datetime.date(year=2018, month=1, day=1) if calendar_set else None,
        end_date=datetime.date(year=2018, month=12, day=31) if calendar_set else None,
        added_dates=expected_added_dates,
        removed_dates=expected_removed_dates,
    )

    actual_services = list(gtfsstaticparser._parse_schedule(gtfs_static_file))

    assert [service] == actual_services


class TestReadZipFile(unittest.TestCase):

    HEADER_1 = "id"
    HEADER_2 = "name"
    VALUE_1_1 = "1"
    VALUE_1_2 = "Stop"
    VALUE_2_1 = "2"
    VALUE_2_2 = "Route"

    def test_file_exists(self):
        """[GTFS Static Util] Read Zip archive - file exists"""
        csv = """{},{}\n{},{}\n{},{}""".format(
            self.HEADER_1,
            self.HEADER_2,
            self.VALUE_1_1,
            self.VALUE_1_2,
            self.VALUE_2_1,
            self.VALUE_2_2,
        )
        expected = [
            {self.HEADER_1: self.VALUE_1_1, self.HEADER_2: self.VALUE_1_2},
            {self.HEADER_1: self.VALUE_2_1, self.HEADER_2: self.VALUE_2_2},
        ]

        file_name_to_func_name = {
            gtfsstaticparser._GtfsStaticFile._InternalFileName.CALENDAR: "calendar",
            gtfsstaticparser._GtfsStaticFile._InternalFileName.ROUTES: "routes",
            gtfsstaticparser._GtfsStaticFile._InternalFileName.STOPS: "stops",
            gtfsstaticparser._GtfsStaticFile._InternalFileName.STOP_TIMES: "stop_times",
            gtfsstaticparser._GtfsStaticFile._InternalFileName.TRANSFERS: "transfers",
            gtfsstaticparser._GtfsStaticFile._InternalFileName.TRIPS: "trips",
        }

        for file_name, func_name in file_name_to_func_name.items():
            binary_content = self._create_zip(file_name.value, csv)
            gtfs_file = gtfsstaticparser._GtfsStaticFile(binary_content)
            func = getattr(gtfs_file, func_name)
            actual = list(func())

            self.assertEqual(expected, actual)

    def test_file_does_not_exist(self):
        """[GTFS Static Util] Read Zip archive - file does not exist"""
        csv = """{},{}\n{},{}\n{},{}""".format(
            self.HEADER_1,
            self.HEADER_2,
            self.VALUE_1_1,
            self.VALUE_1_2,
            self.VALUE_2_1,
            self.VALUE_2_2,
        )
        binary_content = self._create_zip(
            gtfsstaticparser._GtfsStaticFile._InternalFileName.STOPS.value, csv
        )

        actual = list(gtfsstaticparser._GtfsStaticFile(binary_content).routes())

        self.assertEqual([], actual)

    @staticmethod
    def _create_zip(file_name, file_content):
        buff = io.BytesIO()
        zip_file = zipfile.ZipFile(buff, mode="w")
        zip_file.writestr(file_name, file_content)
        zip_file.close()
        buff.seek(0)
        return buff.read()


@pytest.mark.parametrize(
    "input_blob,expected",
    [
        [None, gtfsstaticparser._TransfersConfig()],
        [
            {"strategy": "group_stations"},
            gtfsstaticparser._TransfersConfig(
                default_strategy=gtfsstaticparser._TransfersStrategy.GROUP_STATIONS
            ),
        ],
        [
            {"exceptions": [["A", "B"], ["C", "D"]]},
            gtfsstaticparser._TransfersConfig(exceptions=[{"A", "B"}, {"C", "D"}]),
        ],
    ],
)
def test_transfers_config__load(input_blob, expected):
    actual = gtfsstaticparser._TransfersConfig.load_from_options_blob(input_blob)

    assert expected == actual


@pytest.mark.parametrize(
    "input_blob",
    [
        {"unexpected_key": "value"},
        {"exceptions": "not_a_list"},
        {"exceptions": [{"stop_ids": ["a"]}]},
        {"exceptions": [{"strategy": "default"}]},
        {"strategy": "unknown"},
        {"exceptions": [{"strategy": "unknown", "stop_ids": ["a"]}]},
    ],
)
def test_transfers_config__load_error(input_blob):
    with pytest.raises(Exception):
        gtfsstaticparser._TransfersConfig.load_from_options_blob(input_blob)


@pytest.mark.parametrize(
    "stop_1_id,stop_2_id,expected",
    [
        ["A", "B", gtfsstaticparser._TransfersStrategy.GROUP_STATIONS],
        ["A", "C", gtfsstaticparser._TransfersStrategy.GROUP_STATIONS],
        ["B", "A", gtfsstaticparser._TransfersStrategy.GROUP_STATIONS],
        ["B", "C", gtfsstaticparser._TransfersStrategy.DEFAULT],
        ["C", "A", gtfsstaticparser._TransfersStrategy.GROUP_STATIONS],
        ["C", "B", gtfsstaticparser._TransfersStrategy.DEFAULT],
    ],
)
def test_transfers_config__get_strategy(stop_1_id, stop_2_id, expected):
    config = gtfsstaticparser._TransfersConfig(
        default_strategy=gtfsstaticparser._TransfersStrategy.GROUP_STATIONS,
        exceptions=[{"B", "C"}],
    )

    assert config.get_strategy(stop_1_id, stop_2_id) == expected


@pytest.mark.parametrize(
    "input_rows,transfers_config,expected_transfers",
    [
        [
            [
                {
                    "from_stop_id": STOP_ID,
                    "to_stop_id": STOP_ID_2,
                    "min_transfer_time": 543,
                }
            ],
            gtfsstaticparser._TransfersConfig(),
            [
                parse.Transfer(
                    from_stop_id=STOP_ID, to_stop_id=STOP_ID_2, min_transfer_time=543
                )
            ],
        ],
        [
            [{"from_stop_id": STOP_ID, "to_stop_id": STOP_ID_2, "transfer_type": ""}],
            gtfsstaticparser._TransfersConfig(),
            [parse.Transfer(from_stop_id=STOP_ID, to_stop_id=STOP_ID_2)],
        ],
        [
            [{"from_stop_id": STOP_ID, "to_stop_id": STOP_ID_2, "transfer_type": "1"}],
            gtfsstaticparser._TransfersConfig(),
            [
                parse.Transfer(
                    from_stop_id=STOP_ID,
                    to_stop_id=STOP_ID_2,
                    type=parse.Transfer.Type.COORDINATED,
                )
            ],
        ],
        [
            [{"from_stop_id": STOP_ID, "to_stop_id": STOP_ID_2}],
            gtfsstaticparser._TransfersConfig(),
            [parse.Transfer(from_stop_id=STOP_ID, to_stop_id=STOP_ID_2)],
        ],
        [
            [{"from_stop_id": STOP_ID, "to_stop_id": STOP_ID}],
            gtfsstaticparser._TransfersConfig(),
            [],
        ],
        [
            [{"from_stop_id": STOP_ID, "to_stop_id": STOP_ID}],
            gtfsstaticparser._TransfersConfig(
                default_strategy=gtfsstaticparser._TransfersStrategy.GROUP_STATIONS
            ),
            [],
        ],
        [
            [{"from_stop_id": STOP_ID, "to_stop_id": STOP_ID}],
            gtfsstaticparser._TransfersConfig(
                exceptions=[
                    gtfsstaticparser._TransfersConfigException(
                        strategy=gtfsstaticparser._TransfersStrategy.GROUP_STATIONS,
                        stop_ids={STOP_ID, STOP_ID_2},
                    )
                ]
            ),
            [],
        ],
    ],
)
def test_parse_transfers(input_rows, transfers_config, expected_transfers):
    gtfs_static_file = mock.Mock()
    gtfs_static_file.transfers.return_value = input_rows

    actual_transfers = list(
        gtfsstaticparser._parse_transfers(gtfs_static_file, transfers_config)
    )

    assert expected_transfers == actual_transfers
