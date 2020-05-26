import datetime
import itertools

import pytest
import pytz
from google.transit import gtfs_realtime_pb2 as library_gtfs_rt_pb2

from transiter import parse
from transiter.parse import gtfsrealtime
from transiter.parse import transiter_gtfs_rt_pb2

ALERT_ID = "alert_id"
LANGUAGE = "ie-ga"
URL = "url"
HEADER = "header"
DESCRIPTION = "description"
TIME_1 = datetime.datetime.utcfromtimestamp(3000).replace(tzinfo=pytz.UTC)
TIME_2 = datetime.datetime.utcfromtimestamp(60000).replace(tzinfo=pytz.UTC)
TRIP_ID = "trip_id"
ROUTE_ID = "route_id"
STOP_ID = "stop_id"
AGENCY_ID = "agency_id"
TRACK = "track"
TRIP_DIRECTION_ID = True
SCHEDULE_RELATIONSHIP = parse.Trip.ScheduleRelationship.ADDED
SCHEDULE_RELATIONSHIP_STOP_TIME = parse.TripStopTime.ScheduleRelationship.SKIPPED
DELAY = 324
DELAY_2 = 75
UNCERTAINTY_1 = 213
UNCERTAINTY_2 = 214
STOP_SEQUENCE = 4


def build_test_parse_alerts_params(gtfs):
    return [
        [
            gtfs.Alert(cause=parse.Alert.Cause.DEMONSTRATION.value),
            parse.Alert(
                id=ALERT_ID,
                cause=parse.Alert.Cause.DEMONSTRATION,
                effect=parse.Alert.Effect.UNKNOWN_EFFECT,
            ),
        ],
        [
            gtfs.Alert(effect=parse.Alert.Effect.ADDITIONAL_SERVICE.value),
            parse.Alert(
                id=ALERT_ID,
                cause=parse.Alert.Cause.UNKNOWN_CAUSE,
                effect=parse.Alert.Effect.ADDITIONAL_SERVICE,
            ),
        ],
        *[
            [
                gtfs.Alert(
                    header_text=gtfs.TranslatedString(
                        translation=[
                            gtfs.TranslatedString.Translation(
                                text=HEADER, language=language
                            )
                        ]
                    ),
                    description_text=gtfs.TranslatedString(
                        translation=[
                            gtfs.TranslatedString.Translation(
                                text=DESCRIPTION, language=language
                            )
                        ]
                    ),
                    url=gtfs.TranslatedString(
                        translation=[
                            gtfs.TranslatedString.Translation(
                                text=URL, language=language
                            )
                        ]
                    ),
                ),
                parse.Alert(
                    id=ALERT_ID,
                    messages=[
                        parse.AlertMessage(
                            header=HEADER,
                            description=DESCRIPTION,
                            url=URL,
                            language=language,
                        )
                    ],
                ),
            ]
            for language in [LANGUAGE, None]
        ],
        [
            gtfs.Alert(
                active_period=[
                    gtfs.TimeRange(
                        start=int(TIME_1.timestamp()), end=int(TIME_2.timestamp())
                    )
                ]
            ),
            parse.Alert(
                id=ALERT_ID,
                active_periods=[
                    parse.AlertActivePeriod(starts_at=TIME_1, ends_at=TIME_2)
                ],
            ),
        ],
        [
            gtfs.Alert(
                informed_entity=[
                    gtfs.EntitySelector(
                        trip=gtfs.TripDescriptor(trip_id=TRIP_ID, route_id=ROUTE_ID)
                    )
                ]
            ),
            parse.Alert(id=ALERT_ID, trip_ids=[TRIP_ID]),
        ],
        [
            gtfs.Alert(
                informed_entity=[
                    gtfs.EntitySelector(trip=gtfs.TripDescriptor(route_id=ROUTE_ID))
                ]
            ),
            parse.Alert(id=ALERT_ID, route_ids=[ROUTE_ID]),
        ],
        [
            gtfs.Alert(informed_entity=[gtfs.EntitySelector(route_id=ROUTE_ID)]),
            parse.Alert(id=ALERT_ID, route_ids=[ROUTE_ID]),
        ],
        [
            gtfs.Alert(informed_entity=[gtfs.EntitySelector(agency_id=AGENCY_ID)]),
            parse.Alert(id=ALERT_ID, agency_ids=[AGENCY_ID]),
        ],
        [
            gtfs.Alert(informed_entity=[gtfs.EntitySelector(stop_id=STOP_ID)]),
            parse.Alert(id=ALERT_ID, stop_ids=[STOP_ID]),
        ],
    ]


@pytest.mark.parametrize(
    "input_alert,expected_alert,gtfs",
    itertools.chain.from_iterable(
        [
            (input_alert, expected_alert, gtfs_rt_pb2)
            for input_alert, expected_alert in build_test_parse_alerts_params(
                gtfs_rt_pb2
            )
        ]
        for gtfs_rt_pb2 in [transiter_gtfs_rt_pb2, library_gtfs_rt_pb2]
    ),
)
def test_parse_alerts(input_alert, expected_alert, gtfs):
    alert_message = gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0"),
        entity=[gtfs.FeedEntity(id=ALERT_ID, alert=input_alert)],
    )

    parser = gtfsrealtime.GtfsRealtimeParser()
    parser.load_content(alert_message.SerializeToString())
    actual_alerts = list(parser.get_alerts())

    assert [expected_alert] == actual_alerts


@pytest.mark.parametrize("gtfs", [transiter_gtfs_rt_pb2, library_gtfs_rt_pb2])
def test_parse_alerts__trip_ignored(gtfs):
    alert_message = gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0"),
        entity=[
            gtfs.FeedEntity(
                id=ALERT_ID,
                trip_update=gtfs.TripUpdate(trip=gtfs.TripDescriptor(trip_id=ALERT_ID)),
            )
        ],
    )

    parser = gtfsrealtime.GtfsRealtimeParser()
    parser.load_content(alert_message.SerializeToString())
    actual_alerts = list(parser.get_alerts())

    assert [] == actual_alerts


def test_parse_alerts__transiter_extension():
    gtfs = transiter_gtfs_rt_pb2

    alert_extension_key = gtfs.Alert._extensions_by_number[
        gtfsrealtime.TRANSITER_EXTENSION_ID
    ]

    input_alert = gtfs.Alert()
    additional_data = input_alert.Extensions[alert_extension_key]
    additional_data.created_at = int(TIME_1.timestamp())
    additional_data.updated_at = int(TIME_2.timestamp())
    additional_data.sort_order = 59
    alert_message = gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0"),
        entity=[gtfs.FeedEntity(id=ALERT_ID, alert=input_alert)],
    )

    expected_alert = parse.Alert(
        id=ALERT_ID, created_at=TIME_1, updated_at=TIME_2, sort_order=59
    )

    parser = gtfsrealtime.GtfsRealtimeParser()
    parser.load_content(alert_message.SerializeToString())
    actual_alerts = list(parser.get_alerts())

    assert [expected_alert] == actual_alerts


def build_test_parse_trip_params(gtfs):
    return [
        [  # Check nullable fields
            gtfs.TripUpdate(trip=gtfs.TripDescriptor(trip_id=TRIP_ID)),
            parse.Trip(id=TRIP_ID),
        ],
        [  # Check fields in the trip descriptor
            gtfs.TripUpdate(
                trip=gtfs.TripDescriptor(
                    trip_id=TRIP_ID,
                    route_id=ROUTE_ID,
                    direction_id=TRIP_DIRECTION_ID,
                    schedule_relationship=SCHEDULE_RELATIONSHIP.value,
                )
            ),
            parse.Trip(
                id=TRIP_ID,
                route_id=ROUTE_ID,
                direction_id=TRIP_DIRECTION_ID,
                schedule_relationship=SCHEDULE_RELATIONSHIP,
            ),
        ],
        [  # Check start time field in the trip descriptor
            gtfs.TripUpdate(
                trip=gtfs.TripDescriptor(trip_id=TRIP_ID, start_time="11:22:33")
            ),
            parse.Trip(
                id=TRIP_ID,
                start_time=datetime.datetime.now().replace(
                    hour=11, minute=22, second=33, microsecond=0
                ),
            ),
        ],
        [  # Check start time and date field in the trip descriptor
            gtfs.TripUpdate(
                trip=gtfs.TripDescriptor(
                    trip_id=TRIP_ID, start_date="19900326", start_time="11:22:33"
                )
            ),
            parse.Trip(
                id=TRIP_ID, start_time=datetime.datetime(1990, 3, 26, 11, 22, 33)
            ),
        ],
        [  # Check fields in the trip update
            gtfs.TripUpdate(
                trip=gtfs.TripDescriptor(trip_id=TRIP_ID),
                timestamp=int(TIME_1.timestamp()),
                delay=DELAY,
            ),
            parse.Trip(id=TRIP_ID, updated_at=TIME_1, delay=DELAY),
        ],
        [  # Check nullable fields in StopTimeUpdate
            gtfs.TripUpdate(
                trip=gtfs.TripDescriptor(trip_id=TRIP_ID),
                stop_time_update=[
                    gtfs.TripUpdate.StopTimeUpdate(
                        stop_id=STOP_ID,
                        arrival=gtfs.TripUpdate.StopTimeEvent(
                            time=int(TIME_1.timestamp())
                        ),
                    )
                ],
            ),
            parse.Trip(
                id=TRIP_ID,
                stop_times=[parse.TripStopTime(stop_id=STOP_ID, arrival_time=TIME_1)],
            ),
        ],
        [  # Check all fields in StopTimeUpdate
            gtfs.TripUpdate(
                trip=gtfs.TripDescriptor(trip_id=TRIP_ID),
                stop_time_update=[
                    gtfs.TripUpdate.StopTimeUpdate(
                        stop_id=STOP_ID,
                        stop_sequence=STOP_SEQUENCE,
                        schedule_relationship=SCHEDULE_RELATIONSHIP_STOP_TIME.value,
                        arrival=gtfs.TripUpdate.StopTimeEvent(
                            time=int(TIME_1.timestamp()),
                            delay=DELAY,
                            uncertainty=UNCERTAINTY_1,
                        ),
                        departure=gtfs.TripUpdate.StopTimeEvent(
                            time=int(TIME_2.timestamp()),
                            delay=DELAY_2,
                            uncertainty=UNCERTAINTY_2,
                        ),
                    )
                ],
            ),
            parse.Trip(
                id=TRIP_ID,
                stop_times=[
                    parse.TripStopTime(
                        stop_id=STOP_ID,
                        stop_sequence=STOP_SEQUENCE,
                        schedule_relationship=SCHEDULE_RELATIONSHIP_STOP_TIME,
                        arrival_time=TIME_1,
                        arrival_delay=DELAY,
                        arrival_uncertainty=UNCERTAINTY_1,
                        departure_time=TIME_2,
                        departure_delay=DELAY_2,
                        departure_uncertainty=UNCERTAINTY_2,
                    )
                ],
            ),
        ],
    ]


@pytest.mark.parametrize(
    "input_trip,expected_trip,gtfs",
    itertools.chain.from_iterable(
        [
            (input_trip, expected_trip, gtfs_rt_pb2)
            for input_trip, expected_trip in build_test_parse_trip_params(gtfs_rt_pb2)
        ]
        for gtfs_rt_pb2 in [transiter_gtfs_rt_pb2, library_gtfs_rt_pb2]
    ),
)
def test_parse_trips(input_trip, expected_trip, gtfs):
    trip_message = gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0"),
        entity=[gtfs.FeedEntity(id=TRIP_ID, trip_update=input_trip)],
    )

    parser = gtfsrealtime.GtfsRealtimeParser()
    parser.load_content(trip_message.SerializeToString())
    actual_trips = list(parser.get_trips())

    assert [expected_trip] == actual_trips


def test_parse_trips__transiter_extension():
    gtfs = transiter_gtfs_rt_pb2

    stop_time_extension_key = gtfs.TripUpdate.StopTimeUpdate._extensions_by_number[
        gtfsrealtime.TRANSITER_EXTENSION_ID
    ]

    input_stop_time_update = gtfs.TripUpdate.StopTimeUpdate(stop_id=STOP_ID)
    additional_data = input_stop_time_update.Extensions[stop_time_extension_key]
    additional_data.track = TRACK
    trip_message = gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0"),
        entity=[
            gtfs.FeedEntity(
                id=TRIP_ID,
                trip_update=gtfs.TripUpdate(
                    trip=gtfs.TripDescriptor(trip_id=TRIP_ID),
                    stop_time_update=[input_stop_time_update],
                ),
            )
        ],
    )

    expected_trip = parse.Trip(
        id=TRIP_ID, stop_times=[parse.TripStopTime(stop_id=STOP_ID, track=TRACK)]
    )

    parser = gtfsrealtime.GtfsRealtimeParser()
    parser.load_content(trip_message.SerializeToString())
    actual_trips = list(parser.get_trips())

    assert [expected_trip] == actual_trips
